from __future__ import annotations

import re
from typing import Any


class BISApplicabilityService:
    """
    Builds an evidence graph and evaluates how BIS standards relate to
    a procurement requirement.

    IMPORTANT:
    - This service does not invent BIS standards.
    - It does not treat search results alone as proof of applicability.
    - It does not hard-code helmet-specific standards.
    - It preserves evidence and explains why a relationship exists.
    - If evidence is insufficient, it returns NEEDS_VERIFICATION.
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

    def __init__(self, minimum_direct_score: float = 0.65):
        self.minimum_direct_score = minimum_direct_score

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

        evidence = enriched_candidate.get(
            "evidence"
        )

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
                    f"{field}: {BISApplicabilityService._clean(value)}"
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

        if isinstance(standard_result, dict):
            standard_data = standard_result.get("data")

            if isinstance(standard_data, dict):
                for field in [
                    "standardName",
                    "standardNumber",
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

        procurement_tokens = BISApplicabilityService._tokens(
            procurement_text
        )

        standard_tokens = BISApplicabilityService._tokens(
            standard_text
        )

        if not procurement_tokens or not standard_tokens:
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

        # Jaccard overlap is used only as an explainable lexical signal.
        union = procurement_tokens.union(
            standard_tokens
        )

        score = (
            len(matched) / len(union)
            if union
            else 0.0
        )

        return {
            "score": round(score, 4),
            "matched_tokens": matched,
            "procurement_token_count": len(
                procurement_tokens
            ),
            "standard_token_count": len(
                standard_tokens
            ),
        }

    # ------------------------------------------------------------------
    # Cross-reference extraction
    # ------------------------------------------------------------------

    @staticmethod
    def extract_relationships(
        evidence: dict[str, Any],
    ) -> dict[str, list[dict[str, Any]]]:

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

        if isinstance(data, dict) and "data" in data:
            data = data.get("data")

        if not isinstance(data, dict):
            return {
                "cross_references": [],
                "cross_follow_references": [],
            }

        cross_ref = data.get(
            "crossRefData"
        )

        cross_follow = data.get(
            "crossFollowRefData"
        )

        return {
            "cross_references": (
                cross_ref
                if isinstance(cross_ref, list)
                else []
            ),
            "cross_follow_references": (
                cross_follow
                if isinstance(cross_follow, list)
                else []
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

        value = cls._lower(text)

        if any(
            phrase in value
            for phrase in [
                "test method",
                "methods of test",
                "method of test",
                "testing method",
                "test for",
            ]
        ):
            return cls.TEST_METHOD

        if any(
            phrase in value
            for phrase in [
                "sampling",
                "sample",
                "sampling method",
            ]
        ):
            return cls.SAMPLING

        if any(
            phrase in value
            for phrase in [
                "terminology",
                "definitions",
                "vocabulary",
            ]
        ):
            return cls.TERMINOLOGY

        if any(
            phrase in value
            for phrase in [
                "safety",
                "protective",
                "protection",
                "hazard",
            ]
        ):
            return cls.SAFETY

        if any(
            phrase in value
            for phrase in [
                "normative reference",
                "normative references",
                "referred standard",
                "reference standard",
            ]
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

        return {
            "has_standard_details": (
                BISApplicabilityService._is_successful(
                    evidence.get("standard")
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

        if isinstance(detail, dict):
            data = detail.get("data")

            if isinstance(data, dict):
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
            ("crs", "crs_records"),
            ("mcs", "mcs_records"),
            ("licenses", "license_records"),
            ("laboratories", "laboratory_records"),
        ]:

            value = evidence.get(field)

            if not isinstance(value, dict):
                continue

            data = value.get("data")

            if isinstance(data, dict):
                for key in [
                    "records",
                    "items",
                    "data",
                    "product_manuals_details",
                ]:
                    records = data.get(key)

                    if isinstance(records, list):
                        result[output_key] = len(
                            records
                        )
                        break

            elif isinstance(data, list):
                result[output_key] = len(data)

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
    ) -> dict[str, Any]:

        overlap = self.calculate_token_overlap(
            procurement_text,
            standard_text,
        )

        score = overlap["score"]

        evidence_indicators = (
            self.build_evidence_indicators(
                evidence
            )
        )

        # Evidence availability is a confidence signal,
        # not proof of applicability.
        evidence_bonus = 0.0

        if evidence_indicators[
            "has_standard_details"
        ]:
            evidence_bonus += 0.10

        if evidence_indicators[
            "has_relationship_evidence"
        ]:
            evidence_bonus += 0.05

        if evidence_indicators[
            "has_amendment_evidence"
        ]:
            evidence_bonus += 0.03

        signal = min(
            1.0,
            score + evidence_bonus,
        )

        return {
            "lexical_overlap": overlap,
            "evidence_bonus": round(
                evidence_bonus,
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
            )
        )

        relationships = (
            self.extract_relationships(
                evidence
            )
        )

        relationship_matches: list[dict[str, Any]] = []

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

                relation_text = self._clean(
                    record
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

        status = self.extract_status_information(
            candidate,
            evidence,
        )

        certification = (
            self.extract_certification_summary(
                evidence
            )
        )

        # --------------------------------------------------------------
        # Conservative classification
        # --------------------------------------------------------------

        classification = self.NEEDS_VERIFICATION
        reasons: list[str] = []

        if not standard_number:
            reasons.append(
                "The candidate has no normalized BIS standard number."
            )

        if not evidence.get(
            "standard",
        ):
            reasons.append(
                "Authoritative BIS standard details were not retrieved."
            )

        if signal["signal_score"] >= (
            self.minimum_direct_score
        ):
            classification = self.DIRECT
            reasons.append(
                "The candidate has a measurable textual "
                "match with the procurement requirements."
            )

        elif relationship_matches:
            classification = self.SUPPORTING
            reasons.append(
                "BIS relationship evidence was found, "
                "but direct applicability was not established."
            )

        elif signal["signal_score"] >= 0.30:
            classification = self.POTENTIAL
            reasons.append(
                "The candidate has partial textual overlap "
                "with the procurement requirements."
            )

        else:
            classification = self.NEEDS_VERIFICATION
            reasons.append(
                "Available evidence is insufficient to "
                "establish direct applicability."
            )

        # A withdrawn candidate must not automatically become a
        # recommended current standard.
        if status.get(
            "withdraw_status"
        ) == 1:

            classification = self.NEEDS_VERIFICATION

            reasons.append(
                "BIS search/detail evidence indicates "
                "withdrawal status; current applicability "
                "requires verification."
            )

        return {
            "standard_number": standard_number,
            "standard_name": standard_name,

            "classification": classification,

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
                self.build_evidence_indicators(
                    evidence
                )
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

        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []

        for evaluation in evaluations:

            standard_number = evaluation.get(
                "standard_number"
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
                    "standard_number": standard_number,
                    "standard_name": evaluation.get(
                        "standard_name"
                    ),
                    "classification": evaluation.get(
                        "classification"
                    ),
                }
            )

            relationships = evaluation.get(
                "relationships",
                {}
            )

            classified = relationships.get(
                "classified_relationships",
                []
            )

            for relation in classified:

                record = relation.get(
                    "record",
                    {}
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
                        "source": standard_node_id,
                        "target": related_node_id,
                        "type": (
                            relation.get(
                                "classification"
                            )
                            or self.SUPPORTING
                        ),
                        "source_type": (
                            relation.get("type")
                        ),
                        "evidence": record,
                    }
                )

        # Deduplicate nodes
        unique_nodes: dict[str, dict[str, Any]] = {}

        for node in nodes:
            unique_nodes[node["id"]] = node

        # Deduplicate edges
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
        enriched_candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:

        evaluations = [
            self.evaluate_candidate(
                procurement,
                candidate,
            )
            for candidate in enriched_candidates
        ]

        graph = self.build_evidence_graph(
            evaluations
        )

        counts: dict[str, int] = {}

        for evaluation in evaluations:
            classification = evaluation.get(
                "classification",
                self.NEEDS_VERIFICATION,
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
                "for official BIS/legal verification where "
                "the available evidence is insufficient."
            ),
        }