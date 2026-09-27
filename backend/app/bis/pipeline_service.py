from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.bis.applicability_service import BISApplicabilityService
from app.bis.evidence_service import BISEvidenceService
from app.bis.retrieval_service import BISRetrievalService


class BISPipelineService:
    """
    Complete BIS evidence and applicability pipeline.

    Pipeline:

        Procurement requirements
                ↓
        BIS query planning
                ↓
        BIS discovery
                ↓
        Candidate normalization
                ↓
        BIS authoritative evidence
                ↓
        Applicability evaluation
                ↓
        Evidence graph

    This service only orchestrates the pipeline.

    It does NOT:
    - invent BIS standards
    - generate fake standard numbers
    - treat Gemini output as BIS evidence
    - automatically make legal/compliance determinations
    - hard-code a product category
    - select a single "best" standard
    """

    def __init__(
        self,
        retrieval_service: BISRetrievalService | None = None,
        evidence_service: BISEvidenceService | None = None,
        applicability_service: BISApplicabilityService | None = None,
    ) -> None:
        self.retrieval_service = (
            retrieval_service
            or BISRetrievalService()
        )

        self.evidence_service = (
            evidence_service
            or BISEvidenceService()
        )

        self.applicability_service = (
            applicability_service
            or BISApplicabilityService()
        )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    @staticmethod
    def _clean_requirements(
        requirements: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not requirements:
            return {}

        cleaned: dict[str, Any] = {}

        for key, value in requirements.items():
            if value is None:
                continue

            if value == "":
                continue

            if value == []:
                continue

            if value == {}:
                continue

            cleaned[key] = value

        return cleaned

    # ------------------------------------------------------------------
    # Pipeline validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_requirements(
        requirements: dict[str, Any],
    ) -> dict[str, Any]:
        errors: list[str] = []

        product_name = (
            requirements.get("product_name")
            or requirements.get("product")
        )

        description = requirements.get(
            "description"
        )

        if not product_name and not description:
            errors.append(
                "At least product_name or description "
                "is required."
            )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    # ------------------------------------------------------------------
    # Stage 1: Discovery
    # ------------------------------------------------------------------

    async def discover(
        self,
        requirements: dict[str, Any],
    ) -> dict[str, Any]:
        return await (
            self.retrieval_service
            .discover_standards(
                requirements
            )
        )

    # ------------------------------------------------------------------
    # Stage 2: Evidence enrichment
    # ------------------------------------------------------------------

    async def enrich(
        self,
        discovery_result: dict[str, Any],
        *,
        include_certification: bool = True,
        include_laboratories: bool = True,
        include_licenses: bool = True,
        include_format_documents: bool = True,
    ) -> dict[str, Any]:
        return await (
            self.evidence_service
            .enrich_discovery_result(
                discovery_result,
                include_certification=(
                    include_certification
                ),
                include_laboratories=(
                    include_laboratories
                ),
                include_licenses=(
                    include_licenses
                ),
                include_format_documents=(
                    include_format_documents
                ),
            )
        )

    # ------------------------------------------------------------------
    # Stage 3: Applicability
    # ------------------------------------------------------------------

    def evaluate(
        self,
        requirements: dict[str, Any],
        enrichment_result: dict[str, Any],
    ) -> dict[str, Any]:
        enrichment = enrichment_result.get(
            "enrichment",
            {},
        )

        if not isinstance(
            enrichment,
            dict,
        ):
            enrichment = {}

        enriched_candidates = enrichment.get(
            "results",
            [],
        )

        if not isinstance(
            enriched_candidates,
            list,
        ):
            enriched_candidates = []

        return (
            self.applicability_service
            .evaluate_candidates(
                requirements,
                enriched_candidates,
            )
        )

    # ------------------------------------------------------------------
    # Coverage helper
    # ------------------------------------------------------------------

    @staticmethod
    def _build_coverage(
        discovery_result: dict[str, Any],
        enrichment_result: dict[str, Any],
        applicability_result: dict[str, Any],
    ) -> dict[str, Any]:
        discovery_coverage = (
            discovery_result.get(
                "coverage",
                {},
            )
        )

        if not isinstance(
            discovery_coverage,
            dict,
        ):
            discovery_coverage = {}

        enrichment = enrichment_result.get(
            "enrichment",
            {},
        )

        if not isinstance(
            enrichment,
            dict,
        ):
            enrichment = {}

        classification_counts = (
            applicability_result.get(
                "classification_counts",
                {},
            )
        )

        if not isinstance(
            classification_counts,
            dict,
        ):
            classification_counts = {}

        return {
            "planned_queries": (
                discovery_coverage.get(
                    "planned_queries",
                    0,
                )
            ),

            "executed_queries": (
                discovery_coverage.get(
                    "executed_queries",
                    0,
                )
            ),

            "successful_queries": (
                discovery_coverage.get(
                    "successful_queries",
                    0,
                )
            ),

            "failed_queries": (
                discovery_coverage.get(
                    "failed_queries",
                    0,
                )
            ),

            "raw_records": (
                discovery_coverage.get(
                    "raw_records",
                    0,
                )
            ),

            "unique_standards": (
                discovery_coverage.get(
                    "unique_standards",
                    0,
                )
            ),

            "enriched_candidates": (
                enrichment.get(
                    "successful_candidates",
                    0,
                )
            ),

            "failed_enrichment": (
                enrichment.get(
                    "failed_candidates",
                    0,
                )
            ),

            "partial_evidence_count": (
                enrichment.get(
                    "partial_evidence_count",
                    0,
                )
            ),

            "classification_counts": (
                classification_counts
            ),
        }

    # ------------------------------------------------------------------
    # Complete execution
    # ------------------------------------------------------------------

    async def run(
        self,
        requirements: dict[str, Any],
        *,
        include_certification: bool = True,
        include_laboratories: bool = True,
        include_licenses: bool = True,
        include_format_documents: bool = True,
    ) -> dict[str, Any]:
        started_at = self._utc_now()

        requirements = (
            self._clean_requirements(
                requirements
            )
        )

        validation = (
            self._validate_requirements(
                requirements
            )
        )

        if not validation["valid"]:
            return {
                "success": False,
                "stage": "validation",
                "started_at": started_at,
                "completed_at": self._utc_now(),
                "requirements": requirements,
                "errors": validation["errors"],
            }

        # --------------------------------------------------------------
        # Stage 1: Discovery
        # --------------------------------------------------------------

        discovery_result = await self.discover(
            requirements
        )

        if not isinstance(
            discovery_result,
            dict,
        ):
            discovery_result = {
                "success": False,
                "candidates": [],
                "coverage": {},
                "errors": [
                    "BIS discovery returned an invalid response."
                ],
            }

        candidates = discovery_result.get(
            "candidates",
            [],
        )

        if not isinstance(
            candidates,
            list,
        ):
            candidates = []

        # --------------------------------------------------------------
        # No candidates
        # --------------------------------------------------------------

        if not candidates:
            empty_enrichment = {
                "total_candidates": 0,
                "successful_candidates": 0,
                "failed_candidates": 0,
                "partial_evidence_count": 0,
                "results": [],
            }

            empty_applicability = {
                "success": True,
                "total_candidates": 0,
                "classification_counts": {},
                "evaluations": [],
                "evidence_graph": {
                    "nodes": [],
                    "edges": [],
                },
            }

            coverage = self._build_coverage(
                discovery_result,
                {
                    "enrichment": empty_enrichment
                },
                empty_applicability,
            )

            return {
                "success": False,

                "stage": "discovery",

                "started_at": started_at,

                "completed_at": self._utc_now(),

                "requirements": requirements,

                "discovery": discovery_result,

                "enrichment": {
                    "total_candidates": 0,
                    "successful_candidates": 0,
                    "failed_candidates": 0,
                    "partial_evidence_count": 0,
                    "results": [],
                },

                "applicability": empty_applicability,

                "coverage": coverage,

                "errors": [
                    (
                        "No BIS candidate standards were "
                        "discovered from the generated search "
                        "concepts."
                    )
                ],

                "warnings": [
                    (
                        "No candidate standards were discovered. "
                        "The system cannot establish applicability "
                        "without authoritative BIS candidates."
                    )
                ],
            }

        # --------------------------------------------------------------
        # Stage 2: BIS evidence enrichment
        # --------------------------------------------------------------

        enrichment_result = await self.enrich(
            discovery_result,
            include_certification=(
                include_certification
            ),
            include_laboratories=(
                include_laboratories
            ),
            include_licenses=(
                include_licenses
            ),
            include_format_documents=(
                include_format_documents
            ),
        )

        if not isinstance(
            enrichment_result,
            dict,
        ):
            enrichment_result = {
                "success": False,
                "enrichment": {
                    "total_candidates": len(
                        candidates
                    ),
                    "successful_candidates": 0,
                    "failed_candidates": len(
                        candidates
                    ),
                    "partial_evidence_count": 0,
                    "results": [],
                },
                "errors": [
                    (
                        "BIS evidence enrichment returned "
                        "an invalid response."
                    )
                ],
            }

        # --------------------------------------------------------------
        # Stage 3: Applicability evaluation
        # --------------------------------------------------------------

        applicability_result = self.evaluate(
            requirements,
            enrichment_result,
        )

        if not isinstance(
            applicability_result,
            dict,
        ):
            applicability_result = {
                "success": False,
                "total_candidates": 0,
                "classification_counts": {},
                "evaluations": [],
                "evidence_graph": {
                    "nodes": [],
                    "edges": [],
                },
            }

        # --------------------------------------------------------------
        # Coverage
        # --------------------------------------------------------------

        coverage = self._build_coverage(
            discovery_result,
            enrichment_result,
            applicability_result,
        )

        completed_at = self._utc_now()

        warnings = self._build_warnings(
            discovery_result,
            enrichment_result,
            applicability_result,
        )

        return {
            "success": True,

            "pipeline": {
                "started_at": started_at,
                "completed_at": completed_at,

                "stages": [
                    "requirements",
                    "bis_discovery",
                    "candidate_normalization",
                    "bis_evidence_enrichment",
                    "applicability_evaluation",
                    "evidence_graph",
                ],
            },

            "requirements": requirements,

            "discovery": discovery_result,

            "enrichment": enrichment_result,

            "applicability": applicability_result,

            "coverage": coverage,

            "warnings": warnings,
        }

    # ------------------------------------------------------------------
    # Warnings
    # ------------------------------------------------------------------

    @staticmethod
    def _build_warnings(
        discovery_result: dict[str, Any],
        enrichment_result: dict[str, Any],
        applicability_result: dict[str, Any],
    ) -> list[str]:
        warnings: list[str] = []

        discovery_coverage = (
            discovery_result.get(
                "coverage",
                {},
            )
        )

        if not isinstance(
            discovery_coverage,
            dict,
        ):
            discovery_coverage = {}

        # --------------------------------------------------------------
        # Discovery coverage
        # --------------------------------------------------------------

        if discovery_coverage.get(
            "failed_queries",
            0,
        ) > 0:
            warnings.append(
                "Some BIS search queries failed. "
                "The result should be treated as a coverage "
                "report rather than an exhaustive search."
            )

        if discovery_coverage.get(
            "executed_queries",
            0,
        ) < discovery_coverage.get(
            "planned_queries",
            0,
        ):
            warnings.append(
                "Not all planned BIS search concepts were "
                "successfully executed."
            )

        # --------------------------------------------------------------
        # Evidence enrichment
        # --------------------------------------------------------------

        enrichment = enrichment_result.get(
            "enrichment",
            {},
        )

        if not isinstance(
            enrichment,
            dict,
        ):
            enrichment = {}

        failed_candidates = enrichment.get(
            "failed_candidates",
            0,
        )

        if failed_candidates > 0:
            warnings.append(
                "Some discovered standards could not be "
                "enriched with authoritative BIS evidence."
            )

        partial_evidence_count = enrichment.get(
            "partial_evidence_count",
            0,
        )

        if partial_evidence_count > 0:
            warnings.append(
                "Some standards have partial BIS evidence because "
                "one or more optional evidence sources could not "
                "be retrieved."
            )

        # --------------------------------------------------------------
        # Applicability
        # --------------------------------------------------------------

        counts = applicability_result.get(
            "classification_counts",
            {},
        )

        if not isinstance(
            counts,
            dict,
        ):
            counts = {}

        if counts.get(
            BISApplicabilityService.NEEDS_VERIFICATION,
            0,
        ) > 0:
            warnings.append(
                "Some candidates require additional verification "
                "before being used in procurement specifications."
            )

        if counts.get(
            BISApplicabilityService.POTENTIAL,
            0,
        ) > 0:
            warnings.append(
                "Some candidates show partial relevance but "
                "direct applicability was not established."
            )

        # --------------------------------------------------------------
        # Status warnings
        # --------------------------------------------------------------

        evaluations = applicability_result.get(
            "evaluations",
            [],
        )

        if isinstance(
            evaluations,
            list,
        ):
            withdrawn_count = 0
            superseded_count = 0

            for evaluation in evaluations:
                if not isinstance(
                    evaluation,
                    dict,
                ):
                    continue

                status = evaluation.get(
                    "status",
                    {},
                )

                if not isinstance(
                    status,
                    dict,
                ):
                    continue

                if status.get(
                    "withdraw_status"
                ) == 1:
                    withdrawn_count += 1

                if status.get(
                    "superseded_by"
                ):
                    superseded_count += 1

            if withdrawn_count > 0:
                warnings.append(
                    "One or more candidates have BIS withdrawal "
                    "status and require current-status verification."
                )

            if superseded_count > 0:
                warnings.append(
                    "One or more candidates contain a superseding "
                    "standard reference that should be reviewed."
                )

        # --------------------------------------------------------------
        # Auditability
        # --------------------------------------------------------------

        warnings.append(
            "BIS search and evidence retrieval are dynamic. "
            "Source evidence, retrieval timestamps, query "
            "concepts, and standard versions should be retained "
            "for auditability."
        )

        return warnings

    # ------------------------------------------------------------------
    # Compact result for compatibility
    # ------------------------------------------------------------------

    @staticmethod
    def build_frontend_result(
        pipeline_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Compatibility helper.

        The primary frontend transformation is handled by
        BISRecommendationService.build_frontend_result().

        This method intentionally returns the evidence/applicability
        information already present in the pipeline rather than
        creating a second recommendation-ranking implementation.
        """

        applicability = pipeline_result.get(
            "applicability",
            {},
        )

        if not isinstance(
            applicability,
            dict,
        ):
            applicability = {}

        evaluations = applicability.get(
            "evaluations",
            [],
        )

        if not isinstance(
            evaluations,
            list,
        ):
            evaluations = []

        standards: list[dict[str, Any]] = []

        for evaluation in evaluations:
            if not isinstance(
                evaluation,
                dict,
            ):
                continue

            signal = evaluation.get(
                "signal",
                {},
            )

            if not isinstance(
                signal,
                dict,
            ):
                signal = {}

            lexical_overlap = signal.get(
                "lexical_overlap",
                {},
            )

            if not isinstance(
                lexical_overlap,
                dict,
            ):
                lexical_overlap = {}

            standards.append(
                {
                    "standard_number": evaluation.get(
                        "standard_number"
                    ),

                    "standard_name": evaluation.get(
                        "standard_name"
                    ),

                    "classification": evaluation.get(
                        "classification"
                    ),

                    "signal_score": signal.get(
                        "signal_score"
                    ),

                    "lexical_overlap": lexical_overlap.get(
                        "score"
                    ),

                    "status": evaluation.get(
                        "status",
                        {},
                    ),

                    "certification": evaluation.get(
                        "certification",
                        {},
                    ),

                    "reasons": evaluation.get(
                        "reasons",
                        [],
                    ),

                    "evidence_indicators": (
                        evaluation.get(
                            "evidence_indicators",
                            {},
                        )
                    ),

                    "relationships": (
                        evaluation.get(
                            "relationships",
                            {},
                        )
                    ),
                }
            )

        return {
            "success": pipeline_result.get(
                "success",
                False,
            ),

            "standards": standards,

            "classification_counts": (
                applicability.get(
                    "classification_counts",
                    {},
                )
            ),

            "coverage": pipeline_result.get(
                "coverage",
                {},
            ),

            "warnings": pipeline_result.get(
                "warnings",
                [],
            ),

            "evidence_graph": applicability.get(
                "evidence_graph",
                {
                    "nodes": [],
                    "edges": [],
                },
            ),
        }

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    async def close(self) -> None:
        await self.evidence_service.close()