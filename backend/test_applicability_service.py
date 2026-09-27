import asyncio
from pprint import pprint

from app.bis.bis_web import BISWebProvider
from app.bis.retrieval_service import BISRetrievalService
from app.bis.evidence_service import BISEvidenceService
from app.bis.applicability_service import BISApplicabilityService


async def main():

    print("\n")
    print("=" * 70)
    print("FULL APPLICABILITY LAYER INTEGRATION TEST")
    print("=" * 70)

    provider = BISWebProvider()

    try:

        # =========================================================
        # 1. PROCUREMENT REQUIREMENTS
        # =========================================================

        procurement = {
            "product": "Industrial Safety Helmet",

            "product_category": (
                "Industrial safety helmet"
            ),

            "intended_application": (
                "Construction and industrial workplace safety"
            ),

            "procurement_purpose": (
                "Procurement of protective helmets "
                "for industrial workers"
            ),

            "materials": [
                "Thermoplastic"
            ],

            "technical_requirements": [
                "Adjustable head harness",
                "Protective helmet"
            ],

            "performance_requirements": [
                "Impact protection",
                "Protection against falling objects"
            ],

            "safety_requirements": [
                "Head protection",
                "Workplace safety"
            ],

            "testing_requirements": [
                "Impact testing",
                "Helmet testing"
            ],

            "certification_context": [
                "BIS certification"
            ],

            "search_keywords": [
                "industrial safety helmet",
                "construction helmet",
                "protective helmet",
                "impact protection helmet"
            ],
        }

        # =========================================================
        # 2. RETRIEVAL
        # =========================================================

        print("\n")
        print("=" * 70)
        print("STEP 1: RETRIEVAL")
        print("=" * 70)

        retrieval = BISRetrievalService(
            provider=provider
        )

        discovery = await retrieval.discover_standards(
            procurement
        )

        print(
            "\nRetrieval success:",
            discovery.get("success")
        )

        candidates = discovery.get(
            "candidates",
            []
        )

        print(
            "Candidates discovered:",
            len(candidates)
        )

        for candidate in candidates:

            print(
                "\n",
                candidate.get(
                    "standardNumber"
                )
            )

            print(
                candidate.get(
                    "standardName"
                )
            )

        # =========================================================
        # 3. EVIDENCE ENRICHMENT
        # =========================================================

        print("\n")
        print("=" * 70)
        print("STEP 2: EVIDENCE ENRICHMENT")
        print("=" * 70)

        evidence_service = BISEvidenceService(
            provider=provider
        )

        enriched = await evidence_service.enrich_candidates(
            candidates
        )

        print(
            "\nEvidence enrichment result type:",
            type(enriched)
        )

        # Handle the known result structure safely.
        if isinstance(
            enriched,
            dict
        ):

            enriched_candidates = enriched.get(
                "candidates",
                enriched.get(
                    "results",
                    []
                )
            )

        else:

            enriched_candidates = enriched

        print(
            "Enriched candidates:",
            len(enriched_candidates)
        )

        for item in enriched_candidates:

            candidate = item.get(
                "candidate",
                {}
            )

            print(
                "\nCandidate identity:"
            )

            print(
                "Standard number:",
                candidate.get(
                    "standardNumber"
                )
            )

            print(
                "Standard name:",
                candidate.get(
                    "standardName"
                )
            )

        # =========================================================
        # 4. APPLICABILITY
        # =========================================================

        print("\n")
        print("=" * 70)
        print("STEP 3: APPLICABILITY")
        print("=" * 70)

        applicability = BISApplicabilityService(
            minimum_direct_score=0.65
        )

        result = applicability.evaluate_candidates(
            procurement,
            enriched_candidates
        )

        print(
            "\nApplicability success:",
            result.get(
                "success"
            )
        )

        print(
            "Total candidates:",
            result.get(
                "total_candidates"
            )
        )

        print(
            "Classification counts:"
        )

        pprint(
            result.get(
                "classification_counts"
            )
        )

        # =========================================================
        # 5. INDIVIDUAL EVALUATIONS
        # =========================================================

        evaluations = result.get(
            "evaluations",
            []
        )

        print("\n")
        print("=" * 70)
        print("STEP 4: INDIVIDUAL EVALUATIONS")
        print("=" * 70)

        for index, evaluation in enumerate(
            evaluations,
            start=1
        ):

            print("\n")
            print("-" * 70)
            print(
                "EVALUATION",
                index
            )
            print("-" * 70)

            print(
                "Standard number:",
                evaluation.get(
                    "standard_number"
                )
            )

            print(
                "Standard name:",
                evaluation.get(
                    "standard_name"
                )
            )

            print(
                "Classification:",
                evaluation.get(
                    "classification"
                )
            )

            signal = evaluation.get(
                "signal",
                {}
            )

            print(
                "Signal score:",
                signal.get(
                    "signal_score"
                )
            )

            lexical = signal.get(
                "lexical_overlap",
                {}
            )

            print(
                "Lexical score:",
                lexical.get(
                    "score"
                )
            )

            print(
                "Evidence bonus:",
                signal.get(
                    "evidence_bonus"
                )
            )

            print(
                "Reasons:"
            )

            pprint(
                evaluation.get(
                    "reasons",
                    []
                )
            )

            print(
                "Relationships:"
            )

            pprint(
                evaluation.get(
                    "relationships",
                    {}
                )
            )

        # =========================================================
        # 6. EVIDENCE GRAPH
        # =========================================================

        graph = result.get(
            "evidence_graph",
            {}
        )

        print("\n")
        print("=" * 70)
        print("STEP 5: EVIDENCE GRAPH")
        print("=" * 70)

        print(
            "Graph type:",
            type(graph)
        )

        pprint(
            graph
        )

        # =========================================================
        # 7. VALIDATION
        # =========================================================

        print("\n")
        print("=" * 70)
        print("STEP 6: VALIDATION")
        print("=" * 70)

        validation_errors = []

        if not result.get(
            "success"
        ):

            validation_errors.append(
                "Applicability evaluation returned success=False."
            )

        if len(evaluations) != len(
            enriched_candidates
        ):

            validation_errors.append(
                "Number of evaluations does not match "
                "number of enriched candidates."
            )

        for evaluation in evaluations:

            standard_number = evaluation.get(
                "standard_number"
            )

            if not standard_number:

                validation_errors.append(
                    "A candidate lost its normalized "
                    "BIS standard number."
                )

        if validation_errors:

            print(
                "\nAPPLICABILITY TEST REQUIRES REVIEW"
            )

            for error in validation_errors:

                print(
                    "ERROR:",
                    error
                )

        else:

            print(
                "\n"
                "========== APPLICABILITY LAYER TEST PASSED =========="
            )

        # =========================================================
        # 8. IMPORTANT DIAGNOSTIC
        # =========================================================

        print("\n")
        print("=" * 70)
        print("DIAGNOSTIC SUMMARY")
        print("=" * 70)

        print(
            "\nThis test uses:"
        )

        print(
            "✓ Real BIS retrieval"
        )

        print(
            "✓ Real normalized candidates"
        )

        print(
            "✓ Real BIS evidence enrichment"
        )

        print(
            "✓ Current Applicability Service"
        )

        print(
            "\nNo hard-coded standard recommendation "
            "is used."
        )

    except Exception as error:

        print("\n")
        print("=" * 70)
        print("TEST FAILED")
        print("=" * 70)

        print(
            "\nError:",
            type(error).__name__
        )

        print(
            "Message:",
            str(error)
        )

        import traceback

        traceback.print_exc()

    finally:

        await provider.close()


if __name__ == "__main__":
    asyncio.run(main())