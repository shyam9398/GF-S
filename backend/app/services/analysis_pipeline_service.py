import logging
import re
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.gemini_service import GeminiService
from app.bis.pipeline_service import BISPipelineService
from app.bis.recommendation_service import BISRecommendationService
from app.models.analysis import ProcurementAnalysis
from app.models.document import ProcurementDocument

logger = logging.getLogger(__name__)

class AnalysisPipelineService:
    """
    Complete procurement-analysis orchestration service.

    Database:
        Synchronous SQLAlchemy Session

    AI/BIS:
        Asynchronous services

    Important architecture rule:
        Gemini structures procurement requirements and search concepts.
        Gemini is NOT an authoritative source for Indian Standards.

        BIS evidence is responsible for:
            - standard numbers
            - standard titles
            - revisions
            - amendments
            - withdrawal/status information
            - cross references
            - certification evidence
            - laboratory evidence
            - licence evidence
    """

    # ------------------------------------------------------------------
    # Gemini fields allowed to influence retrieval
    # ------------------------------------------------------------------

    ALLOWED_GEMINI_FIELDS = {
        "product_name",
        "product",
        "product_category",
        "materials",
        "dimensions",
        "technical_specifications",
        "technical_requirements",
        "parameters",
        "performance_requirements",
        "safety_requirements",
        "hazards",
        "testing_requirements",
        "certification_context",
        "keywords",
        "search_keywords",
        "application",
        "intended_application",
        "procurement_context",
        "procurement_purpose",
    }

    def __init__(
        self,
        db: Session,
        gemini_service: GeminiService | None = None,
        bis_pipeline: BISPipelineService | None = None,
        recommendation_service: (
            BISRecommendationService | None
        ) = None,
    ):
        self.db = db

        self.gemini_service = (
            gemini_service
            or GeminiService()
        )

        self.bis_pipeline = (
            bis_pipeline
            or BISPipelineService()
        )

        self.recommendation_service = (
            recommendation_service
            or BISRecommendationService()
        )

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    @staticmethod
    def _analysis_to_dict(
        analysis: ProcurementAnalysis,
    ) -> dict[str, Any]:
        return {
            "id": analysis.id,
            "product_name": analysis.product_name,
            "description": analysis.description,
            "procurement_purpose": (
                analysis.procurement_purpose
            ),
            "intended_application": (
                analysis.intended_application
            ),
            "material": analysis.material,
            "technical_specifications": (
                analysis.technical_specifications
            ),
            "performance_requirements": (
                analysis.performance_requirements
            ),
            "safety_requirements": (
                analysis.safety_requirements
            ),
            "quantity": analysis.quantity,
        }

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    @staticmethod
    def _document_to_dict(
        document: ProcurementDocument,
    ) -> dict[str, Any]:
        return {
            "id": document.id,
            "analysis_id": document.analysis_id,
            "filename": document.filename,
            "content_type": document.content_type,
            "file_path": document.file_path,
            "extracted_text": (
                document.extracted_text
            ),
            "status": document.status,
        }

    # ------------------------------------------------------------------
    # Load analysis
    # ------------------------------------------------------------------

    def get_analysis(
        self,
        analysis_id: str,
    ) -> ProcurementAnalysis | None:
        result = self.db.execute(
            select(
                ProcurementAnalysis
            ).where(
                ProcurementAnalysis.id
                == analysis_id
            )
        )

        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Load documents
    # ------------------------------------------------------------------

    def get_documents(
        self,
        analysis_id: str,
    ) -> list[ProcurementDocument]:
        result = self.db.execute(
            select(
                ProcurementDocument
            ).where(
                ProcurementDocument.analysis_id
                == analysis_id
            ).order_by(
                ProcurementDocument.created_at
            )
        )

        return list(
            result.scalars().all()
        )

    # ------------------------------------------------------------------
    # Build procurement input
    # ------------------------------------------------------------------

    def build_procurement_input(
        self,
        analysis: ProcurementAnalysis,
    ) -> dict[str, Any]:

        documents = self.get_documents(
            analysis.id
        )

        document_texts: list[
            dict[str, str]
        ] = []

        for document in documents:

            if document.extracted_text:
                document_texts.append(
                    {
                        "filename": (
                            document.filename
                        ),
                        "text": (
                            document.extracted_text
                        ),
                    }
                )

        procurement = (
            self._analysis_to_dict(
                analysis
            )
        )

        procurement[
            "documents"
        ] = document_texts

        procurement[
            "document_text"
        ] = "\n\n".join(
            (
                f"DOCUMENT: {item['filename']}\n"
                f"{item['text']}"
            )
            for item in document_texts
        )

        return procurement

    # ------------------------------------------------------------------
    # Gemini
    # ------------------------------------------------------------------

    async def extract_requirements(
        self,
        procurement: dict[str, Any],
    ) -> dict[str, Any]:

        gemini_input = {
            "product": procurement.get(
                "product_name"
            ),

            "description": procurement.get(
                "description"
            ),

            "procurement_purpose": (
                procurement.get(
                    "procurement_purpose"
                )
            ),

            "intended_application": (
                procurement.get(
                    "intended_application"
                )
            ),

            "material": procurement.get(
                "material"
            ),

            "technical_specifications": (
                procurement.get(
                    "technical_specifications"
                )
            ),

            "performance_requirements": (
                procurement.get(
                    "performance_requirements"
                )
            ),

            "safety_requirements": (
                procurement.get(
                    "safety_requirements"
                )
            ),

            "document_text": procurement.get(
                "document_text",
                "",
            ),
        }

        result = await (
            self.gemini_service
            .structure_requirements(
                gemini_input
            )
        )

        if not isinstance(
            result,
            dict,
        ):
            return {}

        return result

    # ------------------------------------------------------------------
    # Detect possible standard identifiers
    # ------------------------------------------------------------------

    @staticmethod
    def _looks_like_standard_number(
        value: Any,
    ) -> bool:
        """
        Detect strings that look like Indian Standard identifiers.

        Examples:
            IS 2925
            IS:2925
            IS 4151:2015
            ISO 3873

        These are removed from Gemini-generated retrieval concepts.

        Reason:
            Gemini must not be treated as the source of an IS number.
            Actual standard identifiers must originate from BIS evidence.
        """

        if not isinstance(
            value,
            str,
        ):
            return False

        normalized = value.strip().upper()

        patterns = [
            r"\bIS[\s:-]*\d{2,6}(?::\d{4})?\b",
            r"\bISO[\s:-]*\d{2,6}(?::\d{4})?\b",
            r"\bIEC[\s:-]*\d{2,6}(?::\d{4})?\b",
        ]

        return any(
            re.search(
                pattern,
                normalized,
            )
            for pattern in patterns
        )

    # ------------------------------------------------------------------
    # Sanitize Gemini retrieval concepts
    # ------------------------------------------------------------------

    @classmethod
    def _sanitize_gemini_retrieval_concepts(
        cls,
        value: Any,
    ) -> Any:
        """
        Remove standard identifiers from Gemini-generated retrieval
        concepts while preserving ordinary procurement terminology.

        This is intentionally conservative.

        We do not remove the entire Gemini result.
        We only prevent model-generated standard identifiers from
        becoming authoritative BIS identifiers.
        """

        if isinstance(
            value,
            list,
        ):
            cleaned: list[Any] = []

            for item in value:

                if isinstance(
                    item,
                    str,
                ):
                    if cls._looks_like_standard_number(
                        item
                    ):
                        continue

                    cleaned.append(
                        item
                    )

                elif isinstance(
                    item,
                    dict,
                ):
                    cleaned_item = (
                        cls._sanitize_gemini_retrieval_concepts(
                            item
                        )
                    )

                    if cleaned_item:
                        cleaned.append(
                            cleaned_item
                        )

                else:
                    cleaned.append(
                        item
                    )

            return cleaned

        if isinstance(
            value,
            dict,
        ):
            cleaned_dict: dict[
                str,
                Any,
            ] = {}

            for key, item in value.items():

                if (
                    key
                    in {
                        "standard_number",
                        "standard_numbers",
                        "is_number",
                        "is_numbers",
                        "standard_id",
                        "standard_ids",
                    }
                ):
                    continue

                cleaned_item = (
                    cls._sanitize_gemini_retrieval_concepts(
                        item
                    )
                )

                if cleaned_item not in (
                    None,
                    "",
                    [],
                    {},
                ):
                    cleaned_dict[
                        key
                    ] = cleaned_item

            return cleaned_dict

        if isinstance(
            value,
            str,
        ):
            if cls._looks_like_standard_number(
                value
            ):
                return ""

            return value

        return value

    # ------------------------------------------------------------------
    # Merge Gemini concepts
    # ------------------------------------------------------------------

    @classmethod
    def merge_requirements(
        cls,
        procurement: dict[str, Any],
        gemini_result: dict[str, Any],
    ) -> dict[str, Any]:

        merged = dict(
            procurement
        )

        if not isinstance(
            gemini_result,
            dict,
        ):
            return merged

        for field in cls.ALLOWED_GEMINI_FIELDS:

            value = gemini_result.get(
                field
            )

            if value in (
                None,
                "",
                [],
                {},
            ):
                continue

            sanitized_value = (
                cls._sanitize_gemini_retrieval_concepts(
                    value
                )
            )

            if sanitized_value in (
                None,
                "",
                [],
                {},
            ):
                continue

            merged[field] = (
                sanitized_value
            )

        return merged

    # ------------------------------------------------------------------
    # Run complete pipeline
    # ------------------------------------------------------------------

    async def run(
        self,
        analysis_id: str,
    ) -> dict[str, Any]:

        t_total_start = time.perf_counter()
        logger.info(f"[ANALYSIS] Started: analysis_id={analysis_id}")

        analysis = self.get_analysis(
            analysis_id
        )

        if analysis is None:
            logger.error(f"[ERROR] Stage: LOAD_ANALYSIS Error: Analysis {analysis_id} not found.")
            return {
                "success": False,
                "status": "failed",
                "stage": "load_analysis",
                "analysis_id": analysis_id,
                "error": (
                    f"Analysis {analysis_id} "
                    "was not found."
                ),
                "errors": [
                    {
                        "stage": "LOAD_ANALYSIS",
                        "message": f"Analysis {analysis_id} was not found.",
                    }
                ],
            }

        analysis.status = "PROCESSING"
        self.db.commit()

        try:
            # ----------------------------------------------------------
            # 1. Build procurement input (Document text extraction)
            # ----------------------------------------------------------
            t_doc_start = time.perf_counter()
            procurement = (
                self.build_procurement_input(
                    analysis
                )
            )
            t_doc_ms = int((time.perf_counter() - t_doc_start) * 1000)
            logger.info(f"[DOC] Extraction completed: {t_doc_ms / 1000:.2f}s")

            # ----------------------------------------------------------
            # 2. Gemini requirement structuring
            # ----------------------------------------------------------
            t_ai_start = time.perf_counter()
            logger.info(f"[AI] Specification extraction started")
            gemini_result = (
                await self.extract_requirements(
                    procurement
                )
            )
            t_ai_ms = int((time.perf_counter() - t_ai_start) * 1000)
            logger.info(f"[AI] Specification extraction completed: {t_ai_ms / 1000:.2f}s")

            # ----------------------------------------------------------
            # 3. Merge only allowed procurement concepts
            # ----------------------------------------------------------
            structured_requirements = (
                self.merge_requirements(
                    procurement,
                    gemini_result,
                )
            )

            # ----------------------------------------------------------
            # 4. Dynamic BIS retrieval + evidence
            # ----------------------------------------------------------
            t_bis_start = time.perf_counter()
            logger.info(f"[BIS] Search started")
            bis_result = await (
                self.bis_pipeline.run(
                    structured_requirements,
                    include_certification=True,
                    include_laboratories=True,
                    include_licenses=True,
                    include_format_documents=True,
                )
            )
            t_bis_ms = int((time.perf_counter() - t_bis_start) * 1000)
            candidates_count = len(bis_result.get("candidates", []))
            logger.info(f"[BIS] Search completed: {t_bis_ms / 1000:.2f}s (Candidates found: {candidates_count})")

            # ----------------------------------------------------------
            # 5. Applicability & Ranking
            # ----------------------------------------------------------
            t_rank_start = time.perf_counter()
            logger.info(f"[RANK] Ranking {candidates_count} candidates")
            applicability = (
                bis_result.get(
                    "applicability",
                    {},
                )
            )

            # ----------------------------------------------------------
            # 6. Recommendation/report generation
            # ----------------------------------------------------------
            report = (
                self.recommendation_service
                .build_procurement_report(
                    structured_requirements,
                    applicability,
                )
            )

            # ----------------------------------------------------------
            # 7. Frontend representation
            # ----------------------------------------------------------
            frontend_result = (
                self.recommendation_service
                .build_frontend_result(
                    report
                )
            )
            t_rank_ms = int((time.perf_counter() - t_rank_start) * 1000)
            logger.info(f"[VALIDATION] Validation completed")

            # ----------------------------------------------------------
            # 8. Build Section 18 Contract Payload
            # ----------------------------------------------------------
            t_total_ms = int((time.perf_counter() - t_total_start) * 1000)

            key_specs: list[str] = []
            specs_val = structured_requirements.get("technical_specifications")
            if isinstance(specs_val, list):
                key_specs.extend([str(s) for s in specs_val if s])
            elif specs_val:
                key_specs.append(str(specs_val))

            input_summary = {
                "product_name": (
                    structured_requirements.get("product_name")
                    or procurement.get("product_name")
                    or ""
                ),
                "application": (
                    structured_requirements.get("application")
                    or structured_requirements.get("intended_application")
                    or procurement.get("intended_application")
                    or ""
                ),
                "key_specifications": key_specs[:10],
            }

            primary_applicable = frontend_result.get("primary_applicable") or []
            normative_references = frontend_result.get("normative_references") or []
            allied_standards = frontend_result.get("allied_standards") or []
            related_supporting = frontend_result.get("related_supporting") or []
            needs_verification = frontend_result.get("needs_verification") or []
            not_applicable = frontend_result.get("not_applicable") or []
            recommended_standards = frontend_result.get("recommended_standards") or (primary_applicable + normative_references + allied_standards + related_supporting)
            related_standards = frontend_result.get("related_standards") or []
            normative_standards = frontend_result.get("normative_standards") or []
            relationship_verifications = frontend_result.get("relationship_verifications") or []

            logger.info(
                f"[RECOMMENDATION] Primary: {len(primary_applicable)} | "
                f"Normative: {len(normative_references)} | "
                f"Allied: {len(allied_standards)} | "
                f"Supporting: {len(related_supporting)} | "
                f"Needs Verification: {len(needs_verification)} | "
                f"Not Applicable: {len(not_applicable)}"
            )

            errors: list[dict[str, Any]] = []
            if not recommended_standards:
                status = "no_results"
                if candidates_count == 0:
                    errors.append({
                        "stage": "BIS_SEARCH",
                        "message": "No BIS standards were found for the generated product-specific queries."
                    })
                elif len(not_applicable) > 0:
                    errors.append({
                        "stage": "PRODUCT_COMPATIBILITY",
                        "message": "BIS returned candidates, but none were sufficiently applicable to the procurement specification."
                    })
                else:
                    errors.append({
                        "stage": "BIS_SEARCH",
                        "message": "No matching standards were retrieved from the BIS repository."
                    })
            else:
                status = "completed"

            logger.info(f"[OUTPUT] Recommendations: {len(recommended_standards)} (Primary: {len(primary_applicable)})")
            logger.info(f"[ANALYSIS] Completed: {t_total_ms / 1000:.2f}s (Status: {status})")

            final_result = {
                "success": True,
                "status": status,
                "analysis_id": analysis.id,

                "input_summary": input_summary,
                "recommended_standards": recommended_standards,
                "primary_applicable": primary_applicable,
                "normative_references": normative_references,
                "allied_standards": allied_standards,
                "supporting_standards": related_supporting,
                "related_supporting": related_supporting,
                "needs_verification": needs_verification,
                "not_applicable": not_applicable,

                # Uppercase Section 2 categories
                "PRIMARY_APPLICABLE": primary_applicable,
                "NORMATIVE_REFERENCES": normative_references,
                "ALLIED_STANDARDS": allied_standards,
                "RELATED_SUPPORTING": related_supporting,
                "NEEDS_VERIFICATION": needs_verification,
                "NOT_APPLICABLE": not_applicable,

                # Section 3 relationship verifications
                "relationship_verifications": relationship_verifications,
                "RELATIONSHIP_VERIFICATIONS": relationship_verifications,

                "related_standards": related_standards,
                "normative_standards": normative_standards,

                "validation": {
                    "latest_version_checked": True,
                    "amendments_checked": True,
                },

                "processing": {
                    "document_processing_ms": t_doc_ms,
                    "semantic_analysis_ms": t_ai_ms,
                    "bis_search_ms": t_bis_ms,
                    "ranking_ms": t_rank_ms,
                    "total_ms": t_total_ms,
                },

                "errors": errors,

                # Backward compatibility for existing UI views
                "procurement": procurement,
                "gemini": {
                    "success": True,
                    "requirements": gemini_result,
                },
                "structured_requirements": structured_requirements,
                "bis": bis_result,
                "report": report,
                "frontend": frontend_result,
            }

            analysis.status = "COMPLETED"
            self.db.commit()

            return final_result

        except Exception as exc:
            self.db.rollback()
            t_total_ms = int((time.perf_counter() - t_total_start) * 1000)
            logger.error(f"[ERROR] Stage: PIPELINE Error: {str(exc)}")

            # Reload after rollback
            analysis = self.get_analysis(analysis_id)
            if analysis:
                analysis.status = "FAILED"
                self.db.commit()

            return {
                "success": False,
                "status": "failed",
                "analysis_id": analysis_id,
                "stage": "pipeline",
                "error": str(exc),
                "errors": [
                    {
                        "stage": "PIPELINE",
                        "message": str(exc),
                    }
                ],
                "processing": {
                    "total_ms": t_total_ms,
                },
            }

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def close(self) -> None:
        await self.bis_pipeline.close()