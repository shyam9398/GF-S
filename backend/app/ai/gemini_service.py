import json

from google import genai

from app.core.config import settings


class GeminiService:
    """
    Gemini is used only to understand and structure procurement
    requirements.

    Gemini is NOT the source of truth for Indian Standards,
    BIS evidence, revisions, amendments, or certification.
    """

    MODEL = "gemini-3.7-flash"

    SYSTEM_INSTRUCTION = """
You are a procurement specification analysis assistant.

Your job is ONLY to understand and structure the procurement
requirement provided by the user.

You MUST NOT:
- invent Indian Standard (IS) numbers
- invent BIS standards
- claim that a standard applies
- invent certification requirements
- use your own knowledge as authoritative BIS evidence

The actual Indian Standards will be retrieved separately from
authoritative BIS sources.

Your output will be used to create search queries for the
BIS retrieval system.

Extract:
- product
- product category
- intended application
- procurement purpose
- materials
- technical requirements
- performance requirements
- safety requirements
- hazards
- testing requirements
- certification/conformity context
- important keywords for standards retrieval

Return ONLY valid JSON.
"""

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

    def analyze_procurement_requirement(
        self,
        document_text: str,
    ) -> dict:
        """
        Analyze and structure procurement requirements using Gemini.

        Gemini is only used for requirement understanding.
        It must not generate or validate Indian Standard numbers.
        """

        prompt = f"""
{self.SYSTEM_INSTRUCTION}

Analyze the following procurement document.

DOCUMENT:

{document_text}

Return JSON using exactly this structure:

{{
  "product": "",
  "product_category": "",
  "intended_application": [],
  "procurement_purpose": "",
  "materials": [],
  "technical_requirements": [],
  "performance_requirements": [],
  "safety_requirements": [],
  "hazards": [],
  "testing_requirements": [],
  "certification_context": [],
  "search_keywords": []
}}
"""

        response = self.client.models.generate_content(
            model=self.MODEL,
            contents=prompt,
        )

        text = response.text or ""
        text = text.strip()

        # Remove Markdown JSON fences if Gemini returns them.
        if text.startswith("```json"):
            text = text[7:]

        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Gemini returned invalid JSON: {text[:500]}"
            ) from exc

        if not isinstance(result, dict):
            raise ValueError(
                "Gemini response must be a JSON object."
            )

        return result

    async def structure_requirements(
        self,
        document_text: str,
    ) -> dict:
        """
        Async interface used by AnalysisPipelineService.

        The pipeline expects structure_requirements() to be
        awaitable, while the Gemini SDK call above is synchronous.

        Gemini only structures procurement requirements.
        It does not provide authoritative BIS standards.
        """

        return self.analyze_procurement_requirement(
            document_text
        )


# Backward-compatible function.
# Existing code that imports analyze_procurement_requirement()
# will continue to work.
def analyze_procurement_requirement(
    document_text: str,
) -> dict:

    service = GeminiService()

    return service.analyze_procurement_requirement(
        document_text
    )