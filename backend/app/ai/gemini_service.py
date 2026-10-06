import json
import logging
import time
from typing import Any

from google import genai
from google.genai.errors import ServerError, ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """
    AI-powered procurement specification understanding engine.

    Gemini is used ONLY to understand and structure procurement
    specifications. Gemini does NOT invent Indian Standard (IS) numbers.
    All Indian Standards originate from authoritative BIS sources.
    """

    CANDIDATE_MODELS = [
        "gemini-flash-lite-latest",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-flash-latest",
    ]

    SYSTEM_INSTRUCTION = (
        "You are an expert in procurement specifications and Indian Standards.\n\n"
        "Analyze the uploaded procurement specification using the extracted Docling text.\n\n"
        "Your task is to identify the exact product being procured and its important technical context.\n"
        "Extract only information supported by the document.\n\n"
        "Rules:\n"
        "1. Do not invent missing information.\n"
        "2. Do not confuse similar products.\n"
        "3. Prioritize product identity over generic keywords.\n"
        "4. Preserve important technical values, units and requirements.\n"
        "5. Generate 3–5 concise BIS search queries of 1–4 words each in the 'keywords' field.\n"
        "6. Queries must represent the actual product, product category, material or key technical term.\n"
        "7. Do not generate long procurement sentences.\n"
        "8. The semantic analysis must be product-centric.\n"
        "9. If information is uncertain, mark it as uncertain instead of guessing.\n"
        "10. Do not generate Indian Standard (IS) numbers; IS standards originate only from authoritative BIS sources.\n\n"
        "Return strict JSON matching the requested schema."
    )

    JSON_SCHEMA_INSTRUCTION = """
Return strict JSON:

{
  "product_name": "",
  "product_category": "",
  "application": "",
  "materials": [],
  "dimensions": [],
  "technical_specifications": [],
  "parameters": [],
  "performance_requirements": [],
  "testing_requirements": [],
  "safety_requirements": [],
  "keywords": [],
  "procurement_context": ""
}

Do NOT invent missing information.
If something is not present, return null or []. Do not guess.
Ensure 'product_name' specifies the exact product, and 'keywords' contain product-specific multi-word phrases (1-4 words each).
"""

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

    def _call_model_with_fallback(self, prompt: str) -> str:
        """
        Execute generate_content with model fallbacks and retry on transient errors.
        """
        last_error = None

        for model in self.CANDIDATE_MODELS:
            for attempt in range(2):
                try:
                    logger.info(f"[AI] Attempting generate_content with {model} (attempt {attempt + 1})")
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )
                    text = (response.text or "").strip()
                    if text:
                        return text
                except (ServerError, ClientError) as exc:
                    last_error = exc
                    logger.warning(f"[AI] Model {model} attempt {attempt + 1} failed: {exc}")
                    time.sleep(1.0)
                except Exception as exc:
                    last_error = exc
                    logger.warning(f"[AI] Model {model} unexpected error: {exc}")
                    break

        raise RuntimeError(
            f"All AI candidate models failed. Last error: {last_error}"
        )

    def analyze_procurement_requirement(
        self,
        document_text: Any,
    ) -> dict[str, Any]:
        """
        Analyze and structure procurement requirements using Gemini.
        Returns the structured schema requested in Section 6.
        """
        if isinstance(document_text, dict):
            parts = []
            for k, v in document_text.items():
                if v:
                    parts.append(f"{k.upper()}: {v}")
            clean_text = "\n\n".join(parts)
        else:
            clean_text = str(document_text or "").strip()

        if not clean_text:
            return {
                "product_name": None,
                "product_category": None,
                "application": None,
                "materials": [],
                "dimensions": [],
                "technical_specifications": [],
                "parameters": [],
                "performance_requirements": [],
                "testing_requirements": [],
                "safety_requirements": [],
                "keywords": [],
                "procurement_context": None,
            }

        prompt = f"""{self.SYSTEM_INSTRUCTION}

{self.JSON_SCHEMA_INSTRUCTION}

PROCUREMENT DOCUMENT CONTENT:
{clean_text}
"""

        raw_text = self._call_model_with_fallback(prompt)

        # Strip markdown code blocks
        clean_json = raw_text.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        elif clean_json.startswith("```"):
            clean_json = clean_json[3:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        clean_json = clean_json.strip()

        try:
            result = json.loads(clean_json)
        except json.JSONDecodeError as exc:
            logger.error(f"[AI] JSON decoding failed: {clean_json[:300]}")
            raise ValueError(
                f"Gemini returned invalid JSON: {clean_json[:300]}"
            ) from exc

        if not isinstance(result, dict):
            raise ValueError("Gemini response must be a JSON object.")

        # Ensure all required schema fields exist
        normalized: dict[str, Any] = {
            "product_name": result.get("product_name") or result.get("product") or None,
            "product_category": result.get("product_category") or None,
            "application": result.get("application") or result.get("intended_application") or None,
            "materials": result.get("materials") if isinstance(result.get("materials"), list) else [],
            "dimensions": result.get("dimensions") if isinstance(result.get("dimensions"), list) else [],
            "technical_specifications": (
                result.get("technical_specifications")
                if isinstance(result.get("technical_specifications"), list)
                else result.get("technical_requirements") if isinstance(result.get("technical_requirements"), list) else []
            ),
            "parameters": result.get("parameters") if isinstance(result.get("parameters"), list) else [],
            "performance_requirements": (
                result.get("performance_requirements")
                if isinstance(result.get("performance_requirements"), list)
                else []
            ),
            "testing_requirements": (
                result.get("testing_requirements")
                if isinstance(result.get("testing_requirements"), list)
                else []
            ),
            "safety_requirements": (
                result.get("safety_requirements")
                if isinstance(result.get("safety_requirements"), list)
                else []
            ),
            "keywords": (
                result.get("keywords")
                if isinstance(result.get("keywords"), list)
                else result.get("search_keywords") if isinstance(result.get("search_keywords"), list) else []
            ),
            "procurement_context": result.get("procurement_context") or result.get("procurement_purpose") or None,
        }

        # Also supply legacy keys so downstream consumers don't break
        normalized["product"] = normalized["product_name"]
        normalized["intended_application"] = normalized["application"]
        normalized["technical_requirements"] = normalized["technical_specifications"]
        normalized["search_keywords"] = normalized["keywords"]
        normalized["procurement_purpose"] = normalized["procurement_context"]

        return normalized

    async def structure_requirements(
        self,
        document_text: Any,
    ) -> dict[str, Any]:
        """
        Async interface used by AnalysisPipelineService.
        """
        return self.analyze_procurement_requirement(
            document_text
        )


def analyze_procurement_requirement(
    document_text: Any,
) -> dict[str, Any]:
    service = GeminiService()
    return service.analyze_procurement_requirement(
        document_text
    )