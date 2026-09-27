import asyncio

from app.bis.bis_web import BISWebProvider
from app.bis.retrieval_service import BISRetrievalService


async def main():

    provider = BISWebProvider()

    try:

        print("\n")
        print("=" * 70)
        print("BIS RETRIEVAL SERVICE INTEGRATION TEST")
        print("=" * 70)

        procurement_requirements = {
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

        retrieval_service = BISRetrievalService(
            provider=provider
        )

        # =====================================================
        # STEP 1
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 1: MULTI-QUERY BIS SEARCH")
        print("=" * 70)

        result = await retrieval_service.discover_standards(
            procurement_requirements
        )

        print(
            "\nDiscovery method executed successfully."
        )

        # =====================================================
        # STEP 2
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 2: DISCOVERY RESULT")
        print("=" * 70)

        print(
            "\nResult type:",
            type(result).__name__
        )

        print(
            "Result keys:",
            list(result.keys())
        )

        # =====================================================
        # STEP 3
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 3: RETRIEVAL COVERAGE")
        print("=" * 70)

        coverage = result.get(
            "coverage",
            {}
        )

        for key, value in coverage.items():

            print(
                f"{key}: {value}"
            )

        # =====================================================
        # STEP 4
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 4: SEARCH RESULTS")
        print("=" * 70)

        search_results = result.get(
            "search_results",
            []
        )

        print(
            "\nSearch result count:",
            len(search_results)
        )

        for index, search_result in enumerate(
            search_results,
            start=1
        ):

            print(
                f"\nSEARCH {index}"
            )

            if isinstance(
                search_result,
                dict
            ):

                print(
                    "Query:",
                    search_result.get(
                        "query"
                    )
                )

                print(
                    "Success:",
                    search_result.get(
                        "success"
                    )
                )

                records = search_result.get(
                    "records",
                    search_result.get(
                        "data",
                        []
                    )
                )

                print(
                    "Records:",
                    len(records)
                    if isinstance(records, list)
                    else "N/A"
                )

            else:

                print(
                    search_result
                )

        # =====================================================
        # STEP 5
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 5: RAW RECORDS")
        print("=" * 70)

        raw_records = result.get(
            "raw_records",
            []
        )

        print(
            "\nRaw record count:",
            len(raw_records)
        )

        for index, record in enumerate(
            raw_records,
            start=1
        ):

            print(
                f"\nRAW RECORD {index}"
            )

            print(
                "Standard Number:",
                record.get(
                    "standardNumber"
                )
            )

            print(
                "Standard Name:",
                record.get(
                    "standardName"
                )
            )

            print(
                "Standard ID:",
                record.get(
                    "standardId"
                )
            )

            print(
                "Retrieved From:",
                record.get(
                    "_retrieval_query"
                )
            )

        # =====================================================
        # STEP 6
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 6: CANONICAL CANDIDATES")
        print("=" * 70)

        candidates = result.get(
            "candidates",
            []
        )

        print(
            "\nCanonical candidate count:",
            len(candidates)
        )

        for index, candidate in enumerate(
            candidates,
            start=1
        ):

            print(
                f"\n{index}. "
                f"{candidate.get('standardNumber')}"
            )

            print(
                "   Name:",
                candidate.get(
                    "standardName"
                )
            )

            print(
                "   Record Count:",
                candidate.get(
                    "recordCount"
                )
            )

            print(
                "   Standard IDs:",
                candidate.get(
                    "standardIds"
                )
            )

            print(
                "   Retrieval Queries:",
                candidate.get(
                    "retrievalQueries"
                )
            )

        # =====================================================
        # STEP 7
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 7: EXPECTED HELMET STANDARD")
        print("=" * 70)

        helmet_standard = None

        for candidate in candidates:

            if (
                candidate.get(
                    "standardNumber"
                )
                == "IS 2925:1984"
            ):

                helmet_standard = candidate
                break

        if helmet_standard:

            print(
                "\nPASS: IS 2925:1984 FOUND"
            )

            print(
                "Name:",
                helmet_standard.get(
                    "standardName"
                )
            )

            print(
                "Records:",
                helmet_standard.get(
                    "recordCount"
                )
            )

        else:

            print(
                "\nINFO: IS 2925:1984 was not "
                "returned by this discovery run."
            )

            print(
                "Returned candidates:"
            )

            for candidate in candidates:

                print(
                    " -",
                    candidate.get(
                        "standardNumber"
                    )
                )

        # =====================================================
        # STEP 8
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 8: DUPLICATE CHECK")
        print("=" * 70)

        standard_numbers = []

        for candidate in candidates:

            standard_number = candidate.get(
                "standardNumber"
            )

            if standard_number:

                standard_numbers.append(
                    standard_number
                )

        duplicate_standard_numbers = [
            number
            for number in set(
                standard_numbers
            )
            if standard_numbers.count(number) > 1
        ]

        print(
            "\nDuplicate canonical standard numbers:",
            len(
                duplicate_standard_numbers
            )
        )

        if duplicate_standard_numbers:

            print(
                "WARNING:",
                duplicate_standard_numbers
            )

        else:

            print(
                "PASS: No duplicate canonical standards."
            )

        # =====================================================
        # STEP 9
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 9: STANDARD NUMBER VALIDATION")
        print("=" * 70)

        invalid_candidates = []

        for candidate in candidates:

            if not candidate.get(
                "standardNumber"
            ):

                invalid_candidates.append(
                    candidate
                )

        print(
            "\nCandidates without standardNumber:",
            len(
                invalid_candidates
            )
        )

        if invalid_candidates:

            print(
                "WARNING: Invalid canonical candidates found."
            )

        else:

            print(
                "PASS: Every candidate has standardNumber."
            )

        # =====================================================
        # STEP 10
        # =====================================================

        print("\n")
        print("=" * 70)
        print("FINAL RETRIEVAL SERVICE RESULT")
        print("=" * 70)

        success = result.get(
            "success",
            False
        )

        print(
            "\nDiscovery success:",
            success
        )

        print(
            "Raw records:",
            len(raw_records)
        )

        print(
            "Canonical candidates:",
            len(candidates)
        )

        print(
            "Duplicate records removed:",
            coverage.get(
                "duplicate_record_count"
            )
        )

        print(
            "Coverage complete:",
            coverage.get(
                "coverage_complete"
            )
        )

        if success and candidates:

            print(
                "\n"
                "========== RETRIEVAL SERVICE TEST PASSED =========="
            )

        elif success:

            print(
                "\n"
                "========== DISCOVERY WORKED, "
                "BUT NO CANDIDATES WERE PRODUCED =========="
            )

        else:

            print(
                "\n"
                "========== RETRIEVAL SERVICE TEST FAILED =========="
            )

    except Exception as error:

        print("\n")
        print("=" * 70)
        print("TEST FAILED")
        print("=" * 70)

        print(
            "\nError Type:",
            type(error).__name__
        )

        print(
            "Message:",
            str(error)
        )

    finally:

        await provider.close()


if __name__ == "__main__":
    asyncio.run(main())