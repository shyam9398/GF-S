import asyncio
from pprint import pprint

from app.bis.bis_web import BISWebProvider
from app.bis.retrieval_service import BISRetrievalService
from app.bis.evidence_service import BISEvidenceService


async def main():

    provider = BISWebProvider()

    try:

        procurement = {
            "product": "Industrial Safety Helmet",
            "product_category": "Industrial safety helmet",
            "intended_application": (
                "Construction and industrial workplace safety"
            ),
            "procurement_purpose": (
                "Procurement of protective helmets "
                "for industrial workers"
            ),
            "materials": ["Thermoplastic"],
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

        print("=" * 70)
        print("STEP 1: RETRIEVAL")
        print("=" * 70)

        retrieval = BISRetrievalService(
            provider=provider
        )

        discovery = await retrieval.discover_standards(
            procurement
        )

        candidates = discovery.get(
            "candidates",
            []
        )

        print(
            "Candidates:",
            len(candidates)
        )

        for candidate in candidates:
            print(
                candidate.get("standardNumber"),
                "-",
                candidate.get("standardName")
            )

        print("\n")
        print("=" * 70)
        print("STEP 2: EVIDENCE ENRICHMENT")
        print("=" * 70)

        evidence_service = BISEvidenceService(
            provider=provider
        )

        enriched_result = (
            await evidence_service.enrich_candidates(
                candidates
            )
        )

        print(
            "Result type:",
            type(enriched_result)
        )

        print(
            "Result keys:",
            list(enriched_result.keys())
        )

        enriched_candidates = enriched_result.get(
            "results",
            []
        )

        print(
            "Enriched candidates:",
            len(enriched_candidates)
        )

        for index, item in enumerate(
            enriched_candidates,
            start=1
        ):

            print("\n")
            print("=" * 70)
            print(
                f"ENRICHED CANDIDATE {index}"
            )
            print("=" * 70)

            print(
                "Item keys:",
                list(item.keys())
            )

            # -------------------------------------------------
            # CANDIDATE
            # -------------------------------------------------

            candidate = item.get(
                "candidate",
                {}
            )

            print("\n")
            print("-" * 70)
            print("CANDIDATE")
            print("-" * 70)

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

            # -------------------------------------------------
            # EVIDENCE
            # -------------------------------------------------

            evidence = item.get(
                "evidence",
                {}
            )

            print("\n")
            print("-" * 70)
            print("EVIDENCE")
            print("-" * 70)

            print(
                "Evidence keys:",
                list(evidence.keys())
            )

            # -------------------------------------------------
            # STANDARD DETAIL
            # -------------------------------------------------

            standard = evidence.get(
                "standard"
            )

            print("\n")
            print("-" * 70)
            print("STANDARD EVIDENCE")
            print("-" * 70)

            print(
                "Type:",
                type(standard)
            )

            pprint(
                standard
            )

            # -------------------------------------------------
            # ALL ERRORS
            # -------------------------------------------------

            print("\n")
            print("-" * 70)
            print("CAPTURED ERRORS")
            print("-" * 70)

            errors = evidence.get(
                "errors",
                []
            )

            if errors:

                pprint(
                    errors
                )

            else:

                print(
                    "No captured errors."
                )

            # -------------------------------------------------
            # TOP LEVEL STATUS
            # -------------------------------------------------

            print("\n")
            print("-" * 70)
            print("TOP LEVEL STATUS")
            print("-" * 70)

            print(
                "Success:",
                item.get(
                    "success"
                )
            )

            print(
                "Partial evidence:",
                item.get(
                    "partial_evidence"
                )
            )

            # -------------------------------------------------
            # INDIVIDUAL EVIDENCE STATUS
            # -------------------------------------------------

            print("\n")
            print("-" * 70)
            print("ENDPOINT STATUS")
            print("-" * 70)

            for key, value in evidence.items():

                if isinstance(
                    value,
                    dict
                ):

                    if "success" in value:

                        print(
                            f"{key}: "
                            f"success={value.get('success')}"
                        )

    except Exception as error:

        print("\n")
        print("=" * 70)
        print("TEST FAILED")
        print("=" * 70)

        print(
            "Error type:",
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

    asyncio.run(
        main()
    )