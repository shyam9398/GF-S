from __future__ import annotations

from typing import Any

from app.bis.applicability_service import BISApplicabilityService


class BISRecommendationService:
    """
    Converts BIS applicability/evidence evaluations into a
    procurement-facing evidence report.

    IMPORTANT:
    - Never creates BIS standard numbers.
    - Never treats Gemini output as authoritative BIS evidence.
    - Never makes a legal or statutory compliance determination.
    - Preserves NEEDS_VERIFICATION items.
    - Uses evidence collected from BIS retrieval.
    - Does not declare one standard as the "best" standard.
    - Applicability signals are evidence indicators, not legal conclusions.
    """

    def __init__(self) -> None:
        self.applicability_service = BISApplicabilityService()

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean(value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, list):
            return " ".join(
                BISRecommendationService._clean(item)
                for item in value
            )

        if isinstance(value, dict):
            return " ".join(
                BISRecommendationService._clean(item)
                for item in value.values()
            )

        return str(value).strip()

    @staticmethod
    def _standard_number(
        evaluation: dict[str, Any],
    ) -> str | None:
        value = evaluation.get("standard_number")

        if value is None:
            return None

        value = str(value).strip()

        return value or None

    @staticmethod
    def _standard_name(
        evaluation: dict[str, Any],
    ) -> str | None:
        value = evaluation.get("standard_name")

        if value is None:
            return None

        value = str(value).strip()

        return value or None

    @staticmethod
    def _classification(
        evaluation: dict[str, Any],
    ) -> str:
        return evaluation.get(
            "classification",
            BISApplicabilityService.NEEDS_VERIFICATION,
        )

    # ------------------------------------------------------------------
    # Evidence extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _get_evidence(
        evaluation: dict[str, Any],
        name: str,
    ) -> dict[str, Any]:
        evidence = evaluation.get("evidence", {})

        if not isinstance(evidence, dict):
            return {}

        value = evidence.get(name)

        if isinstance(value, dict):
            return value

        return {}

    @staticmethod
    def _get_data(
        evidence_item: dict[str, Any],
    ) -> Any:
        data = evidence_item.get("data")

        if isinstance(data, dict) and "data" in data:
            return data.get("data")

        return data

    # ------------------------------------------------------------------
    # Version / amendment information
    # ------------------------------------------------------------------

    def build_version_information(
        self,
        evaluation: dict[str, Any],
    ) -> dict[str, Any]:
        status = evaluation.get("status", {})

        if not isinstance(status, dict):
            status = {}

        amendments = self._get_evidence(
            evaluation,
            "amendments",
        )

        amendment_data = self._get_data(amendments)

        amendment_records: list[Any] = []

        if isinstance(amendment_data, list):
            amendment_records = amendment_data

        elif isinstance(amendment_data, dict):
            for key in [
                "records",
                "items",
                "data",
                "amendments",
                "amendmentDetails",
            ]:
                value = amendment_data.get(key)

                if isinstance(value, list):
                    amendment_records = value
                    break

        return {
            "published_on": status.get("published_on"),
            "valid_upto": status.get("valid_upto"),
            "review_on": status.get("review_on"),
            "reaffirmation_year": status.get("reaffirmation_year"),
            "revision_count": status.get("revision_count"),
            "amendment_count": status.get("amendment_count"),
            "withdraw_status": status.get("withdraw_status"),
            "withdraw_on": status.get("withdraw_on"),
            "superseded_by": status.get("superseded_by"),
            "amendments": amendment_records,
        }

    # ------------------------------------------------------------------
    # Relationship extraction
    # ------------------------------------------------------------------

    def build_related_standards(
        self,
        evaluation: dict[str, Any],
    ) -> list[dict[str, Any]]:
        relationships = evaluation.get(
            "relationships",
            {},
        )

        if not isinstance(relationships, dict):
            return []

        classified = relationships.get(
            "classified_relationships",
            [],
        )

        if not isinstance(classified, list):
            return []

        results: list[dict[str, Any]] = []

        for relationship in classified:
            if not isinstance(relationship, dict):
                continue

            record = relationship.get("record", {})

            if not isinstance(record, dict):
                continue

            standard_number = (
                record.get("standardNumber")
                or record.get("standard_number")
                or record.get("isNumber")
                or record.get("is_number")
            )

            standard_name = (
                record.get("standardName")
                or record.get("standard_name")
                or record.get("standardNameInEnglish")
            )

            results.append(
                {
                    "standard_number": standard_number,
                    "standard_name": standard_name,
                    "relationship_type": relationship.get(
                        "classification"
                    ),
                    "source_type": relationship.get("type"),
                    "evidence": record,
                }
            )

        return results

    # ------------------------------------------------------------------
    # Certification / conformity
    # ------------------------------------------------------------------

    def build_conformity_information(
        self,
        evaluation: dict[str, Any],
    ) -> dict[str, Any]:
        certification = evaluation.get(
            "certification",
            {},
        )

        if not isinstance(certification, dict):
            certification = {}

        licenses = self._get_evidence(
            evaluation,
            "licenses",
        )

        crs = self._get_evidence(
            evaluation,
            "crs",
        )

        mcs = self._get_evidence(
            evaluation,
            "mcs",
        )

        laboratories = self._get_evidence(
            evaluation,
            "laboratories",
        )

        return {
            "license_records": certification.get(
                "license_records",
                0,
            ),
            "crs_records": certification.get(
                "crs_records",
                0,
            ),
            "mcs_records": certification.get(
                "mcs_records",
                0,
            ),
            "laboratory_records": certification.get(
                "laboratory_records",
                0,
            ),
            "license_evidence_available": (
                licenses.get("success") is True
            ),
            "crs_evidence_available": (
                crs.get("success") is True
            ),
            "mcs_evidence_available": (
                mcs.get("success") is True
            ),
            "laboratory_evidence_available": (
                laboratories.get("success") is True
            ),
            "note": (
                "BIS dataset records are evidence retrieved from "
                "BIS services. Their presence or absence alone "
                "must not be interpreted as a legal certification "
                "or compliance determination."
            ),
        }

    # ------------------------------------------------------------------
    # Evidence availability
    # ------------------------------------------------------------------

    def build_evidence_summary(
        self,
        evaluation: dict[str, Any],
    ) -> dict[str, Any]:
        indicators = evaluation.get(
            "evidence_indicators",
            {},
        )

        if not isinstance(indicators, dict):
            indicators = {}

        evidence = evaluation.get(
            "evidence",
            {},
        )

        if not isinstance(evidence, dict):
            evidence = {}

        available: list[str] = []
        unavailable: list[str] = []

        mapping = {
            "standard_details": "has_standard_details",
            "amendments": "has_amendment_evidence",
            "relationships": "has_relationship_evidence",
            "summary": "has_summary_metadata",
            "product_manual": "has_product_manual_metadata",
            "licenses": "has_license_evidence",
            "crs": "has_crs_evidence",
            "mcs": "has_mcs_evidence",
            "laboratories": "has_laboratory_evidence",
        }

        for name, indicator in mapping.items():
            if indicators.get(indicator):
                available.append(name)
            else:
                unavailable.append(name)

        errors = evidence.get("errors", [])

        if not isinstance(errors, list):
            errors = []

        partial_evidence = bool(
            evidence.get("partial_evidence", False)
        )

        return {
            "available": available,
            "unavailable": unavailable,
            "error_count": len(errors),
            "partial_evidence": partial_evidence,
        }

    # ------------------------------------------------------------------
    # Applicability signal
    # ------------------------------------------------------------------

    @staticmethod
    def build_applicability_signal(
        evaluation: dict[str, Any],
    ) -> dict[str, Any]:
        signal = evaluation.get(
            "signal",
            {},
        )

        if not isinstance(signal, dict):
            signal = {}

        lexical_overlap = signal.get(
            "lexical_overlap",
            {},
        )

        if not isinstance(lexical_overlap, dict):
            lexical_overlap = {}

        return {
            "signal_score": signal.get(
                "signal_score"
            ),
            "lexical_overlap_score": lexical_overlap.get(
                "score"
            ),
            "matched_tokens": lexical_overlap.get(
                "matched_tokens",
                [],
            ),
            "procurement_token_count": lexical_overlap.get(
                "procurement_token_count",
                0,
            ),
            "standard_token_count": lexical_overlap.get(
                "standard_token_count",
                0,
            ),
            "evidence_bonus": signal.get(
                "evidence_bonus",
                0.0,
            ),
            "interpretation": (
                "This is an evidence-based retrieval/applicability "
                "signal. It is not a legal, regulatory, or "
                "certification conclusion."
            ),
        }

    # ------------------------------------------------------------------
    # Recommendation level
    # ------------------------------------------------------------------

    @staticmethod
    def _recommendation_level(
        classification: str,
    ) -> str:
        if classification == BISApplicabilityService.DIRECT:
            return "RECOMMENDED_FOR_REVIEW"

        if classification == BISApplicabilityService.SUPPORTING:
            return "SUPPORTING_STANDARD"

        if classification == BISApplicabilityService.TEST_METHOD:
            return "TEST_METHOD_REFERENCE"

        if classification == BISApplicabilityService.SAMPLING:
            return "SAMPLING_REFERENCE"

        if classification == BISApplicabilityService.SAFETY:
            return "SAFETY_REFERENCE"

        if classification == BISApplicabilityService.NORMATIVE:
            return "NORMATIVE_REFERENCE"

        if classification == BISApplicabilityService.TERMINOLOGY:
            return "TERMINOLOGY_REFERENCE"

        if classification == BISApplicabilityService.POTENTIAL:
            return "POTENTIAL_MATCH"

        if classification == BISApplicabilityService.NOT_APPLICABLE:
            return "NOT_RECOMMENDED"

        return "NEEDS_VERIFICATION"

    # ------------------------------------------------------------------
    # Verification state
    # ------------------------------------------------------------------

    @staticmethod
    def _verification_reasons(
        evaluation: dict[str, Any],
    ) -> list[str]:
        reasons: list[str] = []

        classification = evaluation.get(
            "classification"
        )

        if classification == BISApplicabilityService.NEEDS_VERIFICATION:
            reasons.append(
                "The available evidence is insufficient to "
                "establish direct applicability."
            )

        status = evaluation.get(
            "status",
            {},
        )

        if isinstance(status, dict):
            if status.get("withdraw_status") == 1:
                reasons.append(
                    "BIS evidence indicates that the standard "
                    "has withdrawal status; current applicability "
                    "requires verification."
                )

            if status.get("superseded_by"):
                reasons.append(
                    "BIS evidence indicates a superseding "
                    "standard reference that should be reviewed."
                )

        evidence_summary = evaluation.get(
            "evidence_indicators",
            {},
        )

        if isinstance(evidence_summary, dict):
            if not evidence_summary.get(
                "has_standard_details",
                False,
            ):
                reasons.append(
                    "Authoritative BIS standard details were "
                    "not successfully retrieved."
                )

        return reasons

    @staticmethod
    def _human_classification(classification: str, score: float) -> str:
        if classification == BISApplicabilityService.DIRECT:
            return "Highly Applicable" if score >= 0.75 else "Applicable"
        elif classification in (
            BISApplicabilityService.SUPPORTING,
            BISApplicabilityService.TEST_METHOD,
            BISApplicabilityService.SAMPLING,
            BISApplicabilityService.SAFETY,
            BISApplicabilityService.NORMATIVE,
            BISApplicabilityService.TERMINOLOGY,
        ):
            return "Related"
        elif score >= 0.60:
            return "Applicable"
        elif score >= 0.35:
            return "Related"
        else:
            return "Low Relevance"

    # ------------------------------------------------------------------
    # Single recommendation
    # ------------------------------------------------------------------

    def build_recommendation(
        self,
        evaluation: dict[str, Any],
    ) -> dict[str, Any]:
        standard_number = self._standard_number(
            evaluation
        )

        standard_name = self._standard_name(
            evaluation
        )

        classification = self._classification(
            evaluation
        )

        reasons = evaluation.get(
            "reasons",
            [],
        )

        if not isinstance(reasons, list):
            reasons = []

        verification_reasons = self._verification_reasons(
            evaluation
        )

        combined_reasons: list[str] = []

        for reason in reasons + verification_reasons:
            reason_text = self._clean(reason)

            if reason_text and reason_text not in combined_reasons:
                combined_reasons.append(reason_text)

        version = self.build_version_information(
            evaluation
        )

        related = self.build_related_standards(
            evaluation
        )

        conformity = self.build_conformity_information(
            evaluation
        )

        evidence_summary = self.build_evidence_summary(
            evaluation
        )

        applicability_signal = self.build_applicability_signal(
            evaluation
        )

        verification_required = (
            classification
            == BISApplicabilityService.NEEDS_VERIFICATION
            or version.get("withdraw_status") == 1
            or bool(version.get("superseded_by"))
            or evidence_summary.get(
                "partial_evidence",
                False,
            )
        )

        if evaluation.get("applicability_score") is not None:
            applicability_score_pct = int(evaluation["applicability_score"])
            human_class = evaluation.get("human_classification") or self._human_classification(classification, applicability_score_pct / 100)
        else:
            score_val = applicability_signal.get("signal_score") or 0.65
            if classification == BISApplicabilityService.DIRECT:
                applicability_score_pct = int(round(80 + min(16, score_val * 25)))
                human_class = "Highly Applicable" if applicability_score_pct >= 85 else "Applicable"
            elif classification == BISApplicabilityService.NOT_APPLICABLE:
                applicability_score_pct = min(30, int(round(score_val * 100)))
                human_class = "Not Applicable"
            else:
                applicability_score_pct = int(round(score_val * 100))
                human_class = self._human_classification(classification, score_val)

        evidence_list: list[str] = []
        if version.get("published_on"):
            evidence_list.append(f"Official BIS Publication Date: {version.get('published_on')}")
        if version.get("revision_count") is not None and version.get("revision_count") != "":
            evidence_list.append(f"Standard Revision: {version.get('revision_count')}")
        if version.get("amendment_count") is not None and version.get("amendment_count") != "":
            evidence_list.append(f"Recorded Amendments: {version.get('amendment_count')}")
        if conformity.get("license_records"):
            evidence_list.append(f"Active BIS Certification Licences: {conformity.get('license_records')}")
        if conformity.get("laboratory_records"):
            evidence_list.append(f"Recognized Testing Laboratories: {conformity.get('laboratory_records')}")
        if related:
            evidence_list.append(f"Referenced Allied Standards: {len(related)} standards identified in BIS records")
        if not evidence_list:
            evidence_list.append("Standard identified in authoritative BIS database query match.")

        normative_refs = [
            r for r in related
            if "normative" in str(r.get("relationship_type", "")).lower()
        ]

        source_url = (
            f"https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/knowyourstandards/is_details"
        )

        return {
            "standard_number": standard_number,
            "standard_name": standard_name,
            "title": standard_name,

            "classification": classification,
            "human_classification": human_class,
            "compatibility": evaluation.get("compatibility") or "UNKNOWN",
            "semantic_similarity": evaluation.get("semantic_similarity") or 0.0,

            "applicability_score": applicability_score_pct,
            "why_recommended": combined_reasons,
            "evidence": evidence_list,
            "source_url": source_url,

            "recommendation_level": (
                self._recommendation_level(
                    classification
                )
            ),

            "applicability_signal": (
                applicability_signal.get(
                    "signal_score"
                )
            ),

            "applicability_signal_details": (
                applicability_signal
            ),

            "lexical_match": (
                applicability_signal.get(
                    "lexical_overlap_score"
                )
            ),

            "reasons": combined_reasons,

            "verification_required": verification_required,

            "verification_reasons": (
                verification_reasons
            ),

            "version_information": version,
            "revision": str(version.get("revision_count") or ""),
            "amendments": version.get("amendments") or [],

            "related_standards": related,
            "normative_references": normative_refs,

            "conformity": conformity,

            "evidence_summary": evidence_summary,

            "source_evidence": evaluation.get(
                "evidence",
                {},
            ),
        }

    # ------------------------------------------------------------------
    # Build complete recommendation set
    # ------------------------------------------------------------------

    def build_recommendations(
        self,
        applicability_result: dict[str, Any],
    ) -> dict[str, Any]:
        evaluations = applicability_result.get(
            "evaluations",
            [],
        )

        if not isinstance(evaluations, list):
            evaluations = []

        recommendations = [
            self.build_recommendation(
                evaluation
            )
            for evaluation in evaluations
            if isinstance(evaluation, dict)
        ]

        groups = {
            "direct": [],
            "supporting": [],
            "test_methods": [],
            "sampling_methods": [],
            "safety": [],
            "normative": [],
            "terminology": [],
            "potential": [],
            "needs_verification": [],
            "not_applicable": [],
        }

        classification_map = {
            BISApplicabilityService.DIRECT: "direct",
            BISApplicabilityService.SUPPORTING: "supporting",
            BISApplicabilityService.TEST_METHOD: "test_methods",
            BISApplicabilityService.SAMPLING: "sampling_methods",
            BISApplicabilityService.SAFETY: "safety",
            BISApplicabilityService.NORMATIVE: "normative",
            BISApplicabilityService.TERMINOLOGY: "terminology",
            BISApplicabilityService.POTENTIAL: "potential",
            BISApplicabilityService.NEEDS_VERIFICATION: (
                "needs_verification"
            ),
            BISApplicabilityService.NOT_APPLICABLE: (
                "not_applicable"
            ),
        }

        for recommendation in recommendations:
            classification = recommendation.get(
                "classification"
            )

            group = classification_map.get(
                classification,
                "needs_verification",
            )

            groups[group].append(
                recommendation
            )

        return {
            "success": True,

            "total": len(
                recommendations
            ),

            "recommendations": recommendations,

            "groups": groups,

            "summary": {
                key: len(value)
                for key, value in groups.items()
            },

            "important_note": (
                "Recommendations are generated from retrieved "
                "BIS evidence and applicability signals. "
                "They are intended to support procurement-specification "
                "review and do not replace official BIS or legal "
                "verification."
            ),
        }

    # ------------------------------------------------------------------
    # Final procurement report
    # ------------------------------------------------------------------

    def build_procurement_report(
        self,
        procurement: dict[str, Any],
        applicability_result: dict[str, Any],
    ) -> dict[str, Any]:
        recommendation_result = (
            self.build_recommendations(
                applicability_result
            )
        )

        coverage = {
            "candidate_count": (
                applicability_result.get(
                    "total_candidates",
                    0,
                )
            ),
            "classification_counts": (
                applicability_result.get(
                    "classification_counts",
                    {},
                )
            ),
        }

        # Preserve additional pipeline coverage information
        # when it is available.
        for key in [
            "planned_queries",
            "executed_queries",
            "successful_queries",
            "failed_queries",
            "raw_records",
            "unique_standards",
            "enriched_candidates",
            "failed_enrichment",
            "partial_evidence_count",
        ]:
            if key in applicability_result:
                coverage[key] = applicability_result.get(
                    key
                )

        return {
            "procurement": procurement,

            "recommendation_result": (
                recommendation_result
            ),

            "evidence_graph": (
                applicability_result.get(
                    "evidence_graph",
                    {
                        "nodes": [],
                        "edges": [],
                    },
                )
            ),

            "coverage": coverage,

            "disclaimer": (
                "This report provides evidence-based support "
                "for identifying potentially applicable Indian "
                "Standards from retrieved BIS information. "
                "It does not constitute a legal, regulatory, "
                "certification, or compliance determination. "
                "Standards requiring verification should be "
                "checked against the current authoritative BIS "
                "information."
            ),
        }

    # ------------------------------------------------------------------
    # Frontend response
    # ------------------------------------------------------------------

    def build_frontend_result(
        self,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        recommendation_result = report.get(
            "recommendation_result",
            {},
        )

        if not isinstance(
            recommendation_result,
            dict,
        ):
            recommendation_result = {}

        recommendations = recommendation_result.get(
            "recommendations",
            [],
        )

        if not isinstance(
            recommendations,
            list,
        ):
            recommendations = []

        frontend_standards: list[dict[str, Any]] = []

        for item in recommendations:
            if not isinstance(item, dict):
                continue

            frontend_standards.append(
                {
                    "standard_number": item.get(
                        "standard_number"
                    ),

                    "standard_name": item.get(
                        "standard_name"
                    ),

                    "classification": item.get(
                        "classification"
                    ),

                    "recommendation_level": item.get(
                        "recommendation_level"
                    ),

                    "applicability_signal": item.get(
                        "applicability_signal"
                    ),

                    "applicability_signal_details": (
                        item.get(
                            "applicability_signal_details",
                            {},
                        )
                    ),

                    "lexical_match": item.get(
                        "lexical_match"
                    ),

                    "verification_required": item.get(
                        "verification_required"
                    ),

                    "verification_reasons": item.get(
                        "verification_reasons",
                        [],
                    ),

                    "reasons": item.get(
                        "reasons",
                        [],
                    ),

                    "title": item.get("title") or item.get("standard_name"),
                    "human_classification": item.get("human_classification") or item.get("classification"),
                    "applicability_score": item.get("applicability_score"),
                    "why_recommended": item.get("why_recommended") or item.get("reasons") or [],
                    "evidence": item.get("evidence") or [],
                    "source_url": item.get("source_url"),
                    "revision": item.get("revision"),
                    "amendments": item.get("amendments") or [],
                    "normative_references": item.get("normative_references") or [],

                    "compatibility": item.get("compatibility") or "UNKNOWN",
                    "semantic_similarity": item.get("semantic_similarity") or 0.0,

                    "version_information": item.get(
                        "version_information",
                        {},
                    ),

                    "standard_role": item.get("standard_role") or "PRODUCT_SPECIFICATION",
                    "role_description": item.get("role_description") or "Product Specification",
                    "certification": item.get("certification") or {},
                    "lifecycle_status": item.get("lifecycle_status") or "Active",
                    "compat_reason": item.get("compat_reason") or "",
                    "rejection_reason": item.get("compat_reason") if item.get("compatibility") == "MISMATCH" else None,

                    "related_standards": item.get(
                        "related_standards",
                        [],
                    ),

                    "conformity": item.get(
                        "conformity",
                        {},
                    ),

                    "evidence_summary": item.get(
                        "evidence_summary",
                        {},
                    ),
                }
            )

        # Categorize into 5 distinct categories:
        # 1. PRIMARY_APPLICABLE (Product Specification role ONLY, Direct Match, Active)
        # 2. NORMATIVE_REFERENCES (Cross-referenced / Normative standards)
        # 3. ALLIED_STANDARDS (Allied / System companion standards)
        # 4. RELATED_SUPPORTING (Test methods, sampling, materials, headforms, guides)
        # 5. NEEDS_VERIFICATION (Withdrawn, superseded, insufficient evidence)
        # 6. NOT_APPLICABLE (Product scope mismatch, rejected)
        primary_applicable: list[dict[str, Any]] = []
        normative_references: list[dict[str, Any]] = []
        allied_standards: list[dict[str, Any]] = []
        related_supporting: list[dict[str, Any]] = []
        needs_verification: list[dict[str, Any]] = []
        not_applicable: list[dict[str, Any]] = []

        for s in frontend_standards:
            h_class = s.get("human_classification", "")
            compat = s.get("compatibility", "")
            classif = s.get("classification", "")
            role = s.get("standard_role", "")
            score = s.get("applicability_score") or 0

            # Ensure why_recommended is both a list and a string summary
            why_list = s.get("why_recommended") or s.get("reasons") or []
            if isinstance(why_list, list) and why_list:
                s["why_recommended"] = why_list
                s["why_recommended_summary"] = "; ".join(str(w) for w in why_list)
            elif isinstance(why_list, str):
                s["why_recommended"] = [why_list]
                s["why_recommended_summary"] = why_list
            else:
                s["why_recommended"] = ["Standard identified from authoritative BIS retrieval."]
                s["why_recommended_summary"] = "Standard identified from authoritative BIS retrieval."

            # Hard gate checks
            if compat == "MISMATCH" or classif == BISApplicabilityService.NOT_APPLICABLE or h_class in ("Not Applicable", "Low Relevance") or role == "RELATED_PRODUCT" or score < 35:
                s["rejection_reason"] = s.get("rejection_reason") or s.get("compat_reason") or "Product scope does not match the procurement specification."
                not_applicable.append(s)
            elif compat == "UNKNOWN" or classif == BISApplicabilityService.NEEDS_VERIFICATION or "Needs Verification" in h_class or s.get("verification_required"):
                needs_verification.append(s)
            elif classif in ("PRIMARY_APPLICABLE", "DIRECTLY_APPLICABLE") and role == "PRODUCT_SPECIFICATION" and compat == "DIRECT_MATCH" and score >= 70:
                primary_applicable.append(s)
            elif classif == "NORMATIVE_REFERENCE" or "Normative" in h_class:
                normative_references.append(s)
            elif classif == "ALLIED_STANDARD" or "Allied" in h_class:
                allied_standards.append(s)
            else:
                related_supporting.append(s)

        # Sort all categories in descending applicability order
        primary_applicable.sort(key=lambda x: x.get("applicability_score") or 0, reverse=True)
        normative_references.sort(key=lambda x: x.get("applicability_score") or 0, reverse=True)
        allied_standards.sort(key=lambda x: x.get("applicability_score") or 0, reverse=True)
        related_supporting.sort(key=lambda x: x.get("applicability_score") or 0, reverse=True)
        needs_verification.sort(key=lambda x: x.get("applicability_score") or 0, reverse=True)
        not_applicable.sort(key=lambda x: x.get("applicability_score") or 0, reverse=True)

        # Build Engine 3 Relationship Verification for Primary Applicable standards
        relationship_verifications = [
            self.build_relationship_verification(p)
            for p in primary_applicable[:5]
        ]

        # Collect related and normative standards
        all_related = []
        all_normative = []
        for s in frontend_standards:
            for r in s.get("related_standards", []):
                if r not in all_related:
                    all_related.append(r)
            for n in s.get("normative_references", []):
                if n not in all_normative:
                    all_normative.append(n)

        # Also populate normative_references from cross-reference records if normative tab is empty
        if not normative_references:
            for r in all_normative:
                normative_references.append({
                    "standard_number": r.get("standard_number") if isinstance(r, dict) else str(r),
                    "standard_name": r.get("standard_name") if isinstance(r, dict) else "Normative Reference cited in standard",
                    "title": r.get("standard_name") if isinstance(r, dict) else "Normative Reference cited in standard",
                    "classification": "NORMATIVE_REFERENCE",
                    "human_classification": "Normative Reference",
                    "standard_role": "TEST_METHOD",
                    "role_description": "Normative Reference",
                    "applicability_score": 80,
                    "compatibility": "DIRECT_MATCH",
                    "why_recommended": ["Explicitly cited by Primary Applicable Standard."],
                    "why_recommended_summary": "Explicitly cited by Primary Applicable Standard.",
                    "evidence": ["BIS Cross Reference Record: Normative Standard Citation"],
                    "certification": {"status": "VOLUNTARY", "label": "Voluntary", "is_mandatory": False, "reason": "Referenced specification under primary standard"},
                    "lifecycle_status": "Active",
                })

        return {
            "success": True,

            "standards": frontend_standards,
            "recommended_standards": primary_applicable + normative_references + allied_standards + related_supporting,
            "primary_applicable": primary_applicable,
            "normative_references": normative_references,
            "allied_standards": allied_standards,
            "supporting_standards": related_supporting,
            "related_supporting": related_supporting,
            "needs_verification": needs_verification,
            "not_applicable": not_applicable,

            # Uppercase keys matching Section 2 specification
            "PRIMARY_APPLICABLE": primary_applicable,
            "NORMATIVE_REFERENCES": normative_references,
            "ALLIED_STANDARDS": allied_standards,
            "RELATED_SUPPORTING": related_supporting,
            "NEEDS_VERIFICATION": needs_verification,
            "NOT_APPLICABLE": not_applicable,

            # Section 3: BIS relationship and evidence verification
            "relationship_verifications": relationship_verifications,
            "RELATIONSHIP_VERIFICATIONS": relationship_verifications,

            "related_standards": all_related,
            "normative_standards": all_normative,

            "summary": recommendation_result.get(
                "summary",
                {},
            ),

            "evidence_graph": report.get(
                "evidence_graph",
                {
                    "nodes": [],
                    "edges": [],
                },
            ),

            "coverage": report.get(
                "coverage",
                {},
            ),

            "disclaimer": report.get(
                "disclaimer"
            ),
        }

    # ------------------------------------------------------------------
    # Engine 3: BIS Relationship and Evidence Verification
    # ------------------------------------------------------------------

    def build_relationship_verification(
        self,
        primary_standard: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Identify Normative References, Allied Standards, and Related/Supporting
        Standards for a primary standard with evidence sources.
        """
        related_records = primary_standard.get("related_standards", [])
        normative_refs: list[dict[str, Any]] = []
        allied_stds: list[dict[str, Any]] = []
        related_supporting: list[dict[str, Any]] = []

        for rel in related_records:
            if not isinstance(rel, dict):
                continue
            std_num = rel.get("standard_number") or ""
            std_title = rel.get("standard_name") or ""
            rel_type = str(rel.get("relationship_type", "")).upper()
            src_type = str(rel.get("source_type", "")).upper()
            evidence_str = f"BIS {src_type or 'CROSS_REFERENCE'} record: {std_num}"
            evidence_source = "BIS Cross Reference Details"
            source_url = f"https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/knowyourstandards/is_details"

            if "NORMATIVE" in rel_type or "REFERENCE" in rel_type or "CROSS_REFERENCE" in src_type:
                normative_refs.append({
                    "standard_number": std_num,
                    "title": std_title,
                    "relationship": "NORMATIVE_REFERENCE",
                    "evidence": evidence_str,
                    "evidence_source": evidence_source,
                    "source_url": source_url,
                })
            elif "ALLIED" in rel_type or "ASSOCIATED" in rel_type or "CROSS_FOLLOW_REFERENCE" in src_type:
                allied_stds.append({
                    "standard_number": std_num,
                    "title": std_title,
                    "relationship": "ALLIED_STANDARD",
                    "evidence": evidence_str,
                    "evidence_source": evidence_source,
                    "source_url": source_url,
                })
            else:
                related_supporting.append({
                    "standard_number": std_num,
                    "title": std_title,
                    "relationship": "RELATED_SUPPORTING",
                    "evidence": evidence_str,
                    "evidence_source": evidence_source,
                    "source_url": source_url,
                })

        return {
            "primary_standard": {
                "standard_number": primary_standard.get("standard_number") or "",
                "title": primary_standard.get("title") or primary_standard.get("standard_name") or "",
                "applicability_score": primary_standard.get("applicability_score") or 0,
            },
            "normative_references": normative_refs,
            "allied_standards": allied_stds,
            "related_supporting_standards": related_supporting,
        }