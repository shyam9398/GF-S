import logging
import re
from typing import Any

from app.bis.compatibility_service import BISCompatibilityService
from app.bis.semantic_service import BISSemanticService

logger = logging.getLogger(__name__)


class BISApplicabilityService:
    """
    Evidence-aware applicability evaluation for BIS standards.

    IMPORTANT:
    - BIS standards are never invented here.
    - Standard identity comes from the retrieval/evidence layer.
    - Gemini output is not treated as authoritative BIS evidence.
    - Evidence availability is separated from applicability.
    - Direct applicability requires meaningful procurement alignment.
    - Supporting relationships such as testing, sampling, safety,
      terminology and normative references are preserved.
    - Insufficient evidence remains NEEDS_VERIFICATION.
    """

    DIRECT = "DIRECTLY_APPLICABLE"
    SUPPORTING = "RELATED_SUPPORTING"
    TEST_METHOD = "TEST_METHOD"
    SAMPLING = "SAMPLING_METHOD"
    SAFETY = "SAFETY_RELATED"
    NORMATIVE = "NORMATIVE_REFERENCE"
    TERMINOLOGY = "TERMINOLOGY_REFERENCE"
    POTENTIAL = "POTENTIALLY_RELEVANT"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NEEDS_VERIFICATION = "NEEDS_VERIFICATION"

    def __init__(
        self,
        minimum_direct_score: float = 0.50,
        semantic_service: BISSemanticService | None = None,
        compatibility_service: BISCompatibilityService | None = None,
    ):
        self.minimum_direct_score = minimum_direct_score
        self.semantic_service = semantic_service or BISSemanticService()
        self.compatibility_service = (
            compatibility_service or BISCompatibilityService()
        )

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean(value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, list):
            return " ".join(
                BISApplicabilityService._clean(item)
                for item in value
            )

        if isinstance(value, dict):
            return " ".join(
                BISApplicabilityService._clean(item)
                for item in value.values()
            )

        return str(value).strip()

    @staticmethod
    def _lower(value: Any) -> str:
        return BISApplicabilityService._clean(value).lower()

    @staticmethod
    def _tokens(value: Any) -> set[str]:
        text = BISApplicabilityService._lower(value)

        return {
            token
            for token in re.findall(
                r"[a-z0-9]+",
                text,
            )
            if len(token) >= 3
        }

    @staticmethod
    def _extract_standard_number(
        candidate: dict[str, Any],
    ) -> str | None:
        return (
            candidate.get("standardNumber")
            or candidate.get("standard_number")
        )

    @staticmethod
    def _extract_standard_name(
        candidate: dict[str, Any],
    ) -> str | None:
        return (
            candidate.get("standardName")
            or candidate.get("standard_name")
        )

    @staticmethod
    def _extract_evidence(
        enriched_candidate: dict[str, Any],
    ) -> dict[str, Any]:
        evidence = enriched_candidate.get("evidence")

        if isinstance(evidence, dict):
            return evidence

        return {}

    @staticmethod
    def _extract_result_data(
        evidence_item: Any,
    ) -> Any:
        if not isinstance(evidence_item, dict):
            return None

        data = evidence_item.get("data")

        if isinstance(data, dict) and "data" in data:
            return data.get("data")

        return data

    @staticmethod
    def _is_successful(
        evidence_item: Any,
    ) -> bool:
        return (
            isinstance(evidence_item, dict)
            and evidence_item.get("success") is True
        )

    @staticmethod
    def _record_text(
        record: Any,
    ) -> str:
        if isinstance(record, dict):
            preferred_fields = [
                "standardNumber",
                "standard_number",
                "standardName",
                "standard_name",
                "shortTitle",
                "title",
                "name",
                "description",
                "relationship",
                "relationshipType",
                "type",
                "remarks",
                "remarksDescription",
            ]

            parts: list[str] = []

            for field in preferred_fields:
                value = record.get(field)

                if value:
                    parts.append(
                        BISApplicabilityService._clean(value)
                    )

            if parts:
                return " ".join(parts)

        return BISApplicabilityService._clean(record)

    @staticmethod
    def _contains_any(
        text: str,
        phrases: list[str],
    ) -> bool:
        value = text.lower()

        return any(
            phrase.lower() in value
            for phrase in phrases
        )

    # ------------------------------------------------------------------
    # Procurement text
    # ------------------------------------------------------------------

    @staticmethod
    def build_procurement_text(
        procurement: dict[str, Any],
    ) -> str:
        fields = [
            "product_name",
            "product",
            "product_category",
            "description",
            "procurement_purpose",
            "intended_application",
            "material",
            "materials",
            "technical_specifications",
            "technical_requirements",
            "performance_requirements",
            "safety_requirements",
            "hazards",
            "testing_requirements",
            "certification_context",
        ]

        parts: list[str] = []

        for field in fields:
            value = procurement.get(field)

            if value:
                parts.append(
                    f"{field}: "
                    f"{BISApplicabilityService._clean(value)}"
                )

        return " ".join(parts)

    # ------------------------------------------------------------------
    # Standard text
    # ------------------------------------------------------------------

    @staticmethod
    def build_standard_text(
        candidate: dict[str, Any],
        evidence: dict[str, Any],
    ) -> str:
        parts: list[str] = []

        fields = [
            "standardNumber",
            "standardName",
            "standardNameInHindi",
            "matched_standard",
            "shortTitle",
            "typeOfStandardId",
            "groupName",
            "subGroupName",
            "subSubGroupName",
            "committeeName",
            "departmentName",
            "equivalentIs",
        ]

        for field in fields:
            if candidate.get(field):
                parts.append(
                    BISApplicabilityService._clean(
                        candidate.get(field)
                    )
                )

        standard_result = evidence.get("standard")

        if isinstance(
            standard_result,
            dict,
        ):
            standard_data = standard_result.get("data")

            if isinstance(
                standard_data,
                dict,
            ):
                if isinstance(
                    standard_data.get("data"),
                    dict,
                ):
                    standard_data = standard_data.get(
                        "data"
                    )

                for field in [
                    "standardName",
                    "standardNumber",
                    "standardNameInHindi",
                    "shortTitle",
                    "typeOfStandardId",
                    "groupName",
                    "subGroupName",
                    "subSubGroupName",
                    "committeeName",
                    "departmentName",
                    "equivalentIs",
                ]:
                    if standard_data.get(field):
                        parts.append(
                            BISApplicabilityService._clean(
                                standard_data.get(field)
                            )
                        )

        return " ".join(parts)

    # ------------------------------------------------------------------
    # Keyword overlap
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_token_overlap(
        procurement_text: str,
        standard_text: str,
    ) -> dict[str, Any]:
        procurement_tokens = (
            BISApplicabilityService._tokens(
                procurement_text
            )
        )

        standard_tokens = (
            BISApplicabilityService._tokens(
                standard_text
            )
        )

        if (
            not procurement_tokens
            or not standard_tokens
        ):
            return {
                "score": 0.0,
                "matched_tokens": [],
                "procurement_token_count": len(
                    procurement_tokens
                ),
                "standard_token_count": len(
                    standard_tokens
                ),
            }

        matched = sorted(
            procurement_tokens.intersection(
                standard_tokens
            )
        )

        union = (
            procurement_tokens.union(
                standard_tokens
            )
        )

        score = (
            len(matched) / len(union)
            if union
            else 0.0
        )

        return {
            "score": round(
                score,
                4,
            ),
            "matched_tokens": matched,
            "procurement_token_count": len(
                procurement_tokens
            ),
            "standard_token_count": len(
                standard_tokens
            ),
        }

    # ------------------------------------------------------------------
    # Field-aware applicability signals
    # ------------------------------------------------------------------

    @staticmethod
    def _build_requirement_groups(
        procurement: dict[str, Any],
    ) -> dict[str, str]:
        return {
            "product": BISApplicabilityService._clean(
                procurement.get("product_name")
                or procurement.get("product")
            ),
            "category": BISApplicabilityService._clean(
                procurement.get("product_category")
            ),
            "application": BISApplicabilityService._clean(
                procurement.get("application")
                or procurement.get("intended_application")
            ),
            "technical": BISApplicabilityService._clean(
                procurement.get("technical_specifications")
                or procurement.get("technical_requirements")
            ),
            "performance": BISApplicabilityService._clean(
                procurement.get("performance_requirements")
            ),
            "safety": BISApplicabilityService._clean(
                procurement.get("safety_requirements")
                or procurement.get("hazards")
            ),
            "testing": BISApplicabilityService._clean(
                procurement.get("testing_requirements")
            ),
            "material": BISApplicabilityService._clean(
                procurement.get("materials")
                or procurement.get("material")
            ),
            "keyword": BISApplicabilityService._clean(
                procurement.get("keywords")
                or procurement.get("search_keywords")
            ),
        }

    @classmethod
    def _field_token_match(
        cls,
        field_text: str,
        target_text: str,
    ) -> dict[str, Any]:
        field_tokens = cls._tokens(field_text)
        target_tokens = cls._tokens(target_text)

        if not field_tokens:
            return {"score": 0.0, "matched_tokens": []}

        clean_field = cls._clean(field_text).lower()
        clean_target = cls._clean(target_text).lower()

        # Direct phrase match gives full score
        if len(clean_field) > 3 and clean_field in clean_target:
            return {
                "score": 1.0,
                "matched_tokens": sorted(field_tokens),
            }

        matched = set()
        for f in field_tokens:
            for t in target_tokens:
                # Match identical tokens or common singular/plural stems
                if f == t:
                    matched.add(f)
                    break
                if (
                    len(f) > 3
                    and len(t) > 3
                    and (f.startswith(t[:4]) or t.startswith(f[:4]))
                ):
                    matched.add(f)
                    break

        coverage = len(matched) / len(field_tokens) if field_tokens else 0.0
        return {
            "score": round(coverage, 4),
            "matched_tokens": sorted(matched),
        }

    @classmethod
    def _field_match_score(
        cls,
        procurement: dict[str, Any],
        standard_text: str,
    ) -> dict[str, Any]:
        groups = (
            cls._build_requirement_groups(
                procurement
            )
        )

        results: dict[str, Any] = {}

        # Section 13 Deterministic Ranking Weights:
        # Product Match 30%, Application Match 25%, Technical Match 20%,
        # Material Match 10%, Safety Match 10%, Keyword Match 5%
        weights = {
            "product": 0.30,
            "application": 0.25,
            "technical": 0.20,
            "material": 0.10,
            "safety": 0.10,
            "keyword": 0.05,
        }

        weighted_score = 0.0
        active_weight = 0.0

        for field, value in groups.items():
            if not value:
                continue

            match_res = cls._field_token_match(
                value,
                standard_text,
            )

            score = match_res["score"]
            weight = weights.get(
                field,
                0.0,
            )

            weighted_score += (
                score * weight
            )
            active_weight += weight

            results[field] = {
                "score": score,
                "matched_tokens": match_res[
                    "matched_tokens"
                ],
            }

        normalized = (
            weighted_score / active_weight
            if active_weight
            else 0.0
        )

        return {
            "score": round(
                normalized,
                4,
            ),
            "fields": results,
        }

    # ------------------------------------------------------------------
    # Cross-reference extraction
    # ------------------------------------------------------------------

    @staticmethod
    def extract_relationships(
        evidence: dict[str, Any],
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Extract BIS relationship records.

        Current BIS response shape:

        {
            "success": true,
            "data": [
                {
                    "relationshipType": "CROSS_REFERENCE",
                    "standardNumber": "IS 7692:2024",
                    ...
                },
                {
                    "relationshipType": "CROSS_FOLLOW_REFERENCE",
                    ...
                }
            ]
        }

        Older/nested response shapes are also supported.
        """

        relationship_result = evidence.get(
            "relationships"
        )

        if not isinstance(
            relationship_result,
            dict,
        ):
            return {
                "cross_references": [],
                "cross_follow_references": [],
            }

        if not relationship_result.get(
            "success"
        ):
            return {
                "cross_references": [],
                "cross_follow_references": [],
            }

        data = relationship_result.get(
            "data"
        )

        # --------------------------------------------------------------
        # Handle nested response:
        #
        # data = {
        #     "data": [...]
        # }
        #
        # or:
        #
        # data = {
        #     "crossRefData": [...],
        #     "crossFollowRefData": [...]
        # }
        # --------------------------------------------------------------

        if isinstance(
            data,
            dict,
        ):
            if isinstance(
                data.get("data"),
                list,
            ):
                data = data.get(
                    "data"
                )

            else:
                cross_ref = data.get(
                    "crossRefData"
                )

                cross_follow = data.get(
                    "crossFollowRefData"
                )

                if (
                    isinstance(cross_ref, list)
                    or isinstance(cross_follow, list)
                ):
                    return {
                        "cross_references": (
                            cross_ref
                            if isinstance(
                                cross_ref,
                                list,
                            )
                            else []
                        ),
                        "cross_follow_references": (
                            cross_follow
                            if isinstance(
                                cross_follow,
                                list,
                            )
                            else []
                        ),
                    }

                return {
                    "cross_references": [],
                    "cross_follow_references": [],
                }

        # --------------------------------------------------------------
        # Current BIS response is a direct list.
        # --------------------------------------------------------------

        if not isinstance(
            data,
            list,
        ):
            return {
                "cross_references": [],
                "cross_follow_references": [],
            }

        cross_references: list[
            dict[str, Any]
        ] = []

        cross_follow_references: list[
            dict[str, Any]
        ] = []

        for record in data:
            if not isinstance(
                record,
                dict,
            ):
                continue

            relationship_type = str(
                record.get(
                    "relationshipType"
                )
                or record.get(
                    "relationship_type"
                )
                or ""
            ).upper()

            if relationship_type == (
                "CROSS_REFERENCE"
            ):
                cross_references.append(
                    record
                )

            elif relationship_type == (
                "CROSS_FOLLOW_REFERENCE"
            ):
                cross_follow_references.append(
                    record
                )

        return {
            "cross_references": (
                cross_references
            ),
            "cross_follow_references": (
                cross_follow_references
            ),
        }

    # ------------------------------------------------------------------
    # Relationship classification
    # ------------------------------------------------------------------

    @classmethod
    def classify_relationship_text(
        cls,
        text: str,
    ) -> str | None:
        value = cls._lower(
            text
        )

        if cls._contains_any(
            value,
            [
                "test method",
                "methods of test",
                "method of test",
                "testing method",
                "test for",
                "method for testing",
                "methods for testing",
                "test procedures",
                "testing",
            ],
        ):
            return cls.TEST_METHOD

        if cls._contains_any(
            value,
            [
                "sampling",
                "sample",
                "sampling method",
                "methods of sampling",
                "method for sampling",
            ],
        ):
            return cls.SAMPLING

        if cls._contains_any(
            value,
            [
                "terminology",
                "definitions",
                "vocabulary",
                "glossary",
            ],
        ):
            return cls.TERMINOLOGY

        if cls._contains_any(
            value,
            [
                "safety",
                "protective",
                "protection",
                "hazard",
            ],
        ):
            return cls.SAFETY

        if cls._contains_any(
            value,
            [
                "normative reference",
                "normative references",
                "referred standard",
                "reference standard",
                "references",
                "referenced standard",
            ],
        ):
            return cls.NORMATIVE

        return None

    # ------------------------------------------------------------------
    # Evidence indicators
    # ------------------------------------------------------------------

    @staticmethod
    def build_evidence_indicators(
        evidence: dict[str, Any],
    ) -> dict[str, Any]:
        amendments = evidence.get(
            "amendments"
        )

        relationships = evidence.get(
            "relationships"
        )

        summary = evidence.get(
            "summary"
        )

        product_manuals = evidence.get(
            "product_manuals"
        )

        licenses = evidence.get(
            "licenses"
        )

        crs = evidence.get(
            "crs"
        )

        mcs = evidence.get(
            "mcs"
        )

        laboratories = evidence.get(
            "laboratories"
        )

        indicators = {
            "has_standard_details": (
                BISApplicabilityService._is_successful(
                    evidence.get(
                        "standard"
                    )
                )
            ),
            "has_amendment_evidence": (
                BISApplicabilityService._is_successful(
                    amendments
                )
            ),
            "has_relationship_evidence": (
                BISApplicabilityService._is_successful(
                    relationships
                )
            ),
            "has_summary_metadata": (
                BISApplicabilityService._is_successful(
                    summary
                )
            ),
            "has_product_manual_metadata": (
                BISApplicabilityService._is_successful(
                    product_manuals
                )
            ),
            "has_license_evidence": (
                BISApplicabilityService._is_successful(
                    licenses
                )
            ),
            "has_crs_evidence": (
                BISApplicabilityService._is_successful(
                    crs
                )
            ),
            "has_mcs_evidence": (
                BISApplicabilityService._is_successful(
                    mcs
                )
            ),
            "has_laboratory_evidence": (
                BISApplicabilityService._is_successful(
                    laboratories
                )
            ),
        }

        # Evidence confidence is deliberately separate from
        # applicability. A successful endpoint does not prove
        # that the standard applies to the procurement.
        confidence = 0.0

        if indicators[
            "has_standard_details"
        ]:
            confidence += 0.45

        if indicators[
            "has_relationship_evidence"
        ]:
            confidence += 0.15

        if indicators[
            "has_amendment_evidence"
        ]:
            confidence += 0.10

        if indicators[
            "has_summary_metadata"
        ]:
            confidence += 0.05

        if indicators[
            "has_product_manual_metadata"
        ]:
            confidence += 0.05

        if indicators[
            "has_license_evidence"
        ]:
            confidence += 0.05

        if indicators[
            "has_crs_evidence"
        ]:
            confidence += 0.05

        if indicators[
            "has_mcs_evidence"
        ]:
            confidence += 0.05

        if indicators[
            "has_laboratory_evidence"
        ]:
            confidence += 0.05

        indicators[
            "evidence_confidence"
        ] = round(
            min(
                1.0,
                confidence,
            ),
            4,
        )

        return indicators

    # ------------------------------------------------------------------
    # Status / version information
    # ------------------------------------------------------------------

    @staticmethod
    def extract_status_information(
        candidate: dict[str, Any],
        evidence: dict[str, Any],
    ) -> dict[str, Any]:
        detail = evidence.get(
            "standard"
        )

        detail_data: dict[str, Any] = {}

        if isinstance(
            detail,
            dict,
        ):
            data = detail.get(
                "data"
            )

            if isinstance(
                data,
                dict,
            ):
                detail_data = data

                if isinstance(
                    data.get("data"),
                    dict,
                ):
                    detail_data = data.get(
                        "data"
                    )

        return {
            "withdraw_status": (
                detail_data.get(
                    "withdrawStatus"
                )
                if detail_data
                else candidate.get(
                    "withdrawStatus"
                )
            ),
            "withdraw_on": (
                detail_data.get(
                    "withdrawOn"
                )
                if detail_data
                else candidate.get(
                    "withdrawOn"
                )
            ),
            "valid_upto": (
                detail_data.get(
                    "validUpto"
                )
                if detail_data
                else candidate.get(
                    "validUpto"
                )
            ),
            "published_on": (
                detail_data.get(
                    "publishedOn"
                )
                if detail_data
                else candidate.get(
                    "publishedOn"
                )
            ),
            "review_on": detail_data.get(
                "reviewOn"
            ),
            "reaffirmation_year": (
                detail_data.get(
                    "reAffirmationYear"
                )
            ),
            "revision_count": (
                detail_data.get(
                    "noOfRevision"
                )
            ),
            "amendment_count": (
                detail_data.get(
                    "noOfAmendment"
                )
            ),
            "superseded_by": (
                detail_data.get(
                    "superseded_byis"
                )
            ),
        }

    # ------------------------------------------------------------------
    # Certification evidence
    # ------------------------------------------------------------------

    @staticmethod
    def extract_certification_summary(
        evidence: dict[str, Any],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "crs_records": 0,
            "mcs_records": 0,
            "license_records": 0,
            "laboratory_records": 0,
        }

        for field, output_key in [
            (
                "crs",
                "crs_records",
            ),
            (
                "mcs",
                "mcs_records",
            ),
            (
                "licenses",
                "license_records",
            ),
            (
                "laboratories",
                "laboratory_records",
            ),
        ]:
            value = evidence.get(
                field
            )

            if not isinstance(
                value,
                dict,
            ):
                continue

            data = value.get(
                "data"
            )

            if isinstance(
                data,
                dict,
            ):
                for key in [
                    "records",
                    "items",
                    "data",
                    "product_manuals_details",
                ]:
                    records = data.get(
                        key
                    )

                    if isinstance(
                        records,
                        list,
                    ):
                        result[
                            output_key
                        ] = len(
                            records
                        )
                        break

            elif isinstance(
                data,
                list,
            ):
                result[
                    output_key
                ] = len(
                    data
                )

        return result

    # ------------------------------------------------------------------
    # Applicability score
    # ------------------------------------------------------------------

    def calculate_applicability_signal(
        self,
        procurement_text: str,
        standard_text: str,
        *,
        evidence: dict[str, Any],
        procurement: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        overlap = (
            self.calculate_token_overlap(
                procurement_text,
                standard_text,
            )
        )

        lexical_score = overlap[
            "score"
        ]

        evidence_indicators = (
            self.build_evidence_indicators(
                evidence
            )
        )

        field_match = {
            "score": 0.0,
            "fields": {},
        }

        if procurement:
            field_match = (
                self._field_match_score(
                    procurement,
                    standard_text,
                )
            )

        # The lexical score remains visible and explainable.
        #
        # The field-aware score is stronger because product,
        # category, application, technical and safety requirements
        # do not all have equal importance.
        #
        # Neither score alone is considered proof of applicability.

        semantic_alignment = max(
            lexical_score,
            field_match[
                "score"
            ],
        )

        relationships = (
            self.extract_relationships(
                evidence
            )
        )

        relationship_count = (
            len(
                relationships[
                    "cross_references"
                ]
            )
            +
            len(
                relationships[
                    "cross_follow_references"
                ]
            )
        )

        relationship_signal = min(
            0.10,
            relationship_count * 0.02,
        )

        evidence_confidence = (
            evidence_indicators[
                "evidence_confidence"
            ]
        )

        # Evidence confidence is intentionally capped in its
        # contribution to applicability. It demonstrates that
        # authoritative BIS evidence was found; it does not mean
        # the procurement necessarily requires that standard.

        evidence_signal = min(
            0.15,
            evidence_confidence * 0.15,
        )

        signal = min(
            1.0,
            (
                semantic_alignment * 0.75
                +
                evidence_signal
                +
                relationship_signal
            ),
        )

        return {
            "lexical_overlap": overlap,

            "field_alignment": field_match,

            "semantic_alignment": round(
                semantic_alignment,
                4,
            ),

            "evidence_confidence": (
                evidence_confidence
            ),

            "evidence_signal": round(
                evidence_signal,
                4,
            ),

            "relationship_signal": round(
                relationship_signal,
                4,
            ),

            "evidence_bonus": round(
                evidence_signal
                +
                relationship_signal,
                4,
            ),

            "signal_score": round(
                signal,
                4,
            ),
        }

    # ------------------------------------------------------------------
    # Single candidate evaluation
    # ------------------------------------------------------------------

    def evaluate_candidate(
        self,
        procurement: dict[str, Any],
        enriched_candidate: dict[str, Any],
    ) -> dict[str, Any]:
        candidate = enriched_candidate.get(
            "candidate",
            {},
        )

        evidence = self._extract_evidence(
            enriched_candidate
        )

        standard_number = (
            self._extract_standard_number(
                candidate
            )
        )

        standard_name = (
            self._extract_standard_name(
                candidate
            )
        )

        procurement_text = (
            self.build_procurement_text(
                procurement
            )
        )

        standard_text = (
            self.build_standard_text(
                candidate,
                evidence,
            )
        )

        signal = (
            self.calculate_applicability_signal(
                procurement_text,
                standard_text,
                evidence=evidence,
                procurement=procurement,
            )
        )

        relationships = (
            self.extract_relationships(
                evidence
            )
        )

        relationship_matches: list[
            dict[str, Any]
        ] = []

        for relation_type, records in [
            (
                "cross_reference",
                relationships[
                    "cross_references"
                ],
            ),
            (
                "cross_follow_reference",
                relationships[
                    "cross_follow_references"
                ],
            ),
        ]:
            for record in records:
                relation_text = (
                    self._record_text(
                        record
                    )
                )

                classification = (
                    self.classify_relationship_text(
                        relation_text
                    )
                )

                relationship_matches.append(
                    {
                        "type": relation_type,
                        "classification": (
                            classification
                            or self.SUPPORTING
                        ),
                        "record": record,
                    }
                )

        status = (
            self.extract_status_information(
                candidate,
                evidence,
            )
        )

        certification = (
            self.extract_certification_summary(
                evidence
            )
        )

        evidence_indicators = (
            self.build_evidence_indicators(
                evidence
            )
        )

        # --------------------------------------------------------------
        # Step 5 & 6: Semantic similarity and Product Compatibility
        # --------------------------------------------------------------
        requested_product = (
            procurement.get("product_name")
            or procurement.get("product")
            or ""
        )
        standard_title = standard_name or ""

        # Step 6: Semantic similarity (sentence-transformers embedding cosine similarity)
        semantic_sim = 0.0
        try:
            semantic_sim = self.semantic_service.compute_similarity(
                procurement_text,
                [standard_text],
            )[0]
        except Exception as exc:
            logger.warning(f"[SEMANTIC] Error computing semantic similarity: {exc}")
            semantic_sim = signal.get("semantic_alignment", 0.0)

        logger.info(f"[SEMANTIC] Standard: {standard_number} Similarity score: {semantic_sim:.4f}")

        # Step 5 & 8: Product compatibility determination
        compatibility, compat_reason = self.compatibility_service.evaluate_compatibility(
            requested_product,
            standard_title,
            standard_scope=standard_text,
            semantic_similarity=semantic_sim,
        )

        logger.info(
            f"[COMPATIBILITY] Requested: '{requested_product}' "
            f"Candidate: '{standard_number} - {standard_title}' "
            f"Decision: {compatibility} Reason: {compat_reason}"
        )

        # --------------------------------------------------------------
        # Step 7: Product-Centric Scoring Model (Total = 100%)
        # Product Compatibility: 40%
        # Semantic Similarity:   25%
        # Application Match:     15%
        # Technical Match:       10%
        # Safety/Material Match: 10%
        # --------------------------------------------------------------
        field_alignment = signal.get("field_alignment", {})
        fields = field_alignment.get("fields", {})

        app_score = fields.get("application", {}).get("score", 0.0)
        tech_score = fields.get("technical", {}).get("score", 0.0)
        mat_score = fields.get("material", {}).get("score", 0.0)
        safety_score = fields.get("safety", {}).get("score", 0.0)
        safety_mat_score = max(safety_score, mat_score)

        if compatibility == self.compatibility_service.DIRECT_MATCH:
            product_compat_score = 1.0
        elif compatibility == self.compatibility_service.RELATED_MATCH:
            product_compat_score = 0.5
        elif compatibility == self.compatibility_service.UNKNOWN:
            product_compat_score = 0.25
        else:  # MISMATCH
            product_compat_score = 0.0

        raw_score = (
            (product_compat_score * 0.40)
            + (semantic_sim * 0.25)
            + (app_score * 0.15)
            + (tech_score * 0.10)
            + (safety_mat_score * 0.10)
        )

        reasons: list[str] = []

        if not standard_number:
            reasons.append("The candidate has no normalized BIS standard number.")

        if not self._is_successful(evidence.get("standard")):
            reasons.append("Authoritative BIS standard details were not successfully retrieved.")

        # --------------------------------------------------------------
        # HARD RULE (STEP 7 & 8):
        # IF product compatibility is MISMATCH:
        #   classification = "NOT_APPLICABLE"
        #   Apply strong score penalty / score cap (<= 30%)
        # --------------------------------------------------------------
        if compatibility == self.compatibility_service.MISMATCH:
            classification = self.NOT_APPLICABLE
            human_classification = "Not Applicable"
            final_score = min(0.30, raw_score * 0.30)
            reasons.append(compat_reason)
            reasons.append("Product mismatch: standard covers a different product domain.")

        elif compatibility == self.compatibility_service.DIRECT_MATCH:
            reasons.append(compat_reason)
            reasons.append("The procurement requirements show direct alignment with the BIS standard specification.")

            if raw_score >= 0.65 or semantic_sim >= 0.70:
                classification = self.DIRECT
                human_classification = "Highly Applicable"
                final_score = 0.85 + min(0.12, raw_score * 0.12)
            else:
                classification = self.DIRECT
                human_classification = "Applicable"
                final_score = 0.72 + min(0.12, raw_score * 0.12)

        elif compatibility == self.compatibility_service.RELATED_MATCH:
            reasons.append(compat_reason)
            classification = self.SUPPORTING
            human_classification = "Related"
            final_score = 0.40 + min(0.25, raw_score * 0.25)

        else:  # UNKNOWN
            classification = self.NEEDS_VERIFICATION
            human_classification = "Needs Verification"
            final_score = raw_score
            reasons.append("Insufficient evidence to establish direct product applicability.")

        # Withdrawn / Superseded status check
        if status.get("withdraw_status") == 1:
            if classification == self.DIRECT:
                classification = self.NEEDS_VERIFICATION
                human_classification = "Needs Verification"
            reasons.append("BIS evidence indicates withdrawal status; current applicability requires verification.")

        if status.get("superseded_by"):
            reasons.append(f"Standard is superseded by {status.get('superseded_by')}; verification required.")

        score_pct = int(round(final_score * 100))

        logger.info(
            f"[RANKING] Product: {product_compat_score:.2f} Semantic: {semantic_sim:.2f} "
            f"App: {app_score:.2f} Tech: {tech_score:.2f} Final: {score_pct}% ({human_classification})"
        )

        signal["signal_score"] = round(final_score, 4)

        return {
            "standard_number": standard_number,

            "standard_name": standard_name,

            "classification": classification,
            "human_classification": human_classification,
            "applicability_score": score_pct,
            "compatibility": compatibility,
            "compat_reason": compat_reason,
            "semantic_similarity": round(semantic_sim, 4),

            "signal": signal,

            "status": status,

            "certification": certification,

            "relationships": {
                "cross_reference_count": len(
                    relationships[
                        "cross_references"
                    ]
                ),

                "cross_follow_reference_count": len(
                    relationships[
                        "cross_follow_references"
                    ]
                ),

                "classified_relationships": (
                    relationship_matches
                ),
            },

            "evidence_indicators": (
                evidence_indicators
            ),

            "reasons": reasons,

            "evidence": evidence,

            "candidate": candidate,
        }

    # ------------------------------------------------------------------
    # Evidence graph
    # ------------------------------------------------------------------

    def build_evidence_graph(
        self,
        evaluations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        nodes: list[
            dict[str, Any]
        ] = []

        edges: list[
            dict[str, Any]
        ] = []

        for evaluation in evaluations:
            standard_number = (
                evaluation.get(
                    "standard_number"
                )
            )

            if not standard_number:
                continue

            standard_node_id = (
                f"standard:{standard_number}"
            )

            nodes.append(
                {
                    "id": standard_node_id,
                    "type": "standard",
                    "standard_number": (
                        standard_number
                    ),
                    "standard_name": (
                        evaluation.get(
                            "standard_name"
                        )
                    ),
                    "classification": (
                        evaluation.get(
                            "classification"
                        )
                    ),
                }
            )

            relationships = (
                evaluation.get(
                    "relationships",
                    {},
                )
            )

            classified = (
                relationships.get(
                    "classified_relationships",
                    [],
                )
            )

            for relation in classified:
                record = relation.get(
                    "record",
                    {},
                )

                related_number = (
                    record.get(
                        "standardNumber"
                    )
                    or record.get(
                        "standard_number"
                    )
                    or record.get(
                        "isNumber"
                    )
                    or record.get(
                        "is_number"
                    )
                )

                if not related_number:
                    continue

                related_node_id = (
                    f"standard:{related_number}"
                )

                if not any(
                    node["id"]
                    == related_node_id
                    for node in nodes
                ):
                    nodes.append(
                        {
                            "id": related_node_id,
                            "type": "standard",
                            "standard_number": (
                                related_number
                            ),
                            "standard_name": (
                                record.get(
                                    "standardName"
                                )
                                or record.get(
                                    "standard_name"
                                )
                            ),
                        }
                    )

                edges.append(
                    {
                        "source": (
                            standard_node_id
                        ),
                        "target": (
                            related_node_id
                        ),
                        "type": (
                            relation.get(
                                "classification"
                            )
                            or self.SUPPORTING
                        ),
                        "source_type": (
                            relation.get(
                                "type"
                            )
                        ),
                        "evidence": record,
                    }
                )

        unique_nodes: dict[
            str,
            dict[str, Any],
        ] = {}

        for node in nodes:
            unique_nodes[
                node["id"]
            ] = node

        unique_edges: dict[
            tuple[str, str, str],
            dict[str, Any],
        ] = {}

        for edge in edges:
            key = (
                edge["source"],
                edge["target"],
                edge["type"],
            )

            unique_edges[key] = edge

        return {
            "nodes": list(
                unique_nodes.values()
            ),
            "edges": list(
                unique_edges.values()
            ),
        }

    # ------------------------------------------------------------------
    # Evaluate complete candidate set
    # ------------------------------------------------------------------

    def evaluate_candidates(
        self,
        procurement: dict[str, Any],
        enriched_candidates: list[
            dict[str, Any]
        ],
    ) -> dict[str, Any]:
        evaluations = [
            self.evaluate_candidate(
                procurement,
                candidate,
            )
            for candidate in enriched_candidates
        ]

        graph = (
            self.build_evidence_graph(
                evaluations
            )
        )

        counts: dict[
            str,
            int,
        ] = {}

        for evaluation in evaluations:
            classification = (
                evaluation.get(
                    "classification",
                    self.NEEDS_VERIFICATION,
                )
            )

            counts[classification] = (
                counts.get(
                    classification,
                    0,
                )
                + 1
            )

        return {
            "success": True,

            "total_candidates": len(
                evaluations
            ),

            "classification_counts": counts,

            "evaluations": evaluations,

            "evidence_graph": graph,

            "important_note": (
                "Classification is an evidence-based "
                "applicability signal. It is not a substitute "
                "for official BIS or legal verification where "
                "the available evidence is insufficient."
            ),
        }