from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.gemini_service import GeminiService
from app.bis.pipeline_service import BISPipelineService
from app.bis.recommendation_service import BISRecommendationService
from app.models.analysis import ProcurementAnalysis
from app.models.document import ProcurementDocument

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
        "product_category",
        "materials",
        "technical_requirements",
        "performance_requirements",
        "safety_requirements",
        "hazards",
        "testing_requirements",
        "certification_context",
        "search_keywords",
        "intended_application",
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

        analysis = self.get_analysis(
            analysis_id
        )

        if analysis is None:
            return {
                "success": False,
                "stage": "load_analysis",
                "analysis_id": analysis_id,
                "error": (
                    f"Analysis {analysis_id} "
                    "was not found."
                ),
            }

        analysis.status = "PROCESSING"

        self.db.commit()

        try:

            # ----------------------------------------------------------
            # 1. Build procurement input
            # ----------------------------------------------------------

            procurement = (
                self.build_procurement_input(
                    analysis
                )
            )

            # ----------------------------------------------------------
            # 2. Gemini requirement structuring
            # ----------------------------------------------------------

            gemini_result = (
                await self.extract_requirements(
                    procurement
                )
            )

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

            bis_result = await (
                self.bis_pipeline.run(
                    structured_requirements,
                    include_certification=True,
                    include_laboratories=True,
                    include_licenses=True,
                    include_format_documents=True,
                )
            )

            # ----------------------------------------------------------
            # 5. Applicability
            # ----------------------------------------------------------

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

            # ----------------------------------------------------------
            # 8. Final persisted result
            # ----------------------------------------------------------

            final_result = {
                "success": True,

                "analysis_id": analysis.id,

                "procurement": procurement,

                "gemini": {
                    "success": True,
                    "requirements": gemini_result,
                },

                "structured_requirements": (
                    structured_requirements
                ),

                "bis": bis_result,

                "report": report,

                "frontend": frontend_result,
            }

            analysis.status = "COMPLETED"

            self.db.commit()

            return final_result

        except Exception as exc:

            self.db.rollback()

            # ----------------------------------------------------------
            # Reload after rollback
            # ----------------------------------------------------------

            analysis = self.get_analysis(
                analysis_id
            )

            if analysis:

                analysis.status = "FAILED"

                self.db.commit()

            return {
                "success": False,
                "analysis_id": analysis_id,
                "stage": "pipeline",
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def close(self) -> None:
        await self.bis_pipeline.close()