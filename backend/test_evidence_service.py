import asyncio
from pprint import pprint

from app.bis.bis_web import BISWebProvider
from app.bis.evidence_service import BISEvidenceService


STANDARD_NUMBER = "IS 2925:1984"


def extract_data(value):
    """
    Extract actual records from an Evidence Service
    response structure.

    Expected structure:

    {
        "success": True,
        "endpoint": "...",
        "data": [...],
        "message": "...",
        "error": None
    }
    """

    if isinstance(value, dict):

        data = value.get(
            "data",
            []
        )

        return data

    if isinstance(value, list):

        return value

    if value is None:

        return []

    return [value]


async def main():

    provider = BISWebProvider()

    try:

        print("\n")
        print("=" * 70)
        print("BIS EVIDENCE SERVICE DIAGNOSTIC TEST")
        print("=" * 70)

        # =====================================================
        # STEP 1: SEARCH STANDARD
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 1: FIND STANDARD")
        print("=" * 70)

        search_results = await provider.search_standards(
            STANDARD_NUMBER
        )

        print(
            "\nSearch records:",
            len(search_results)
        )

        if not search_results:

            print(
                "\nERROR: Standard not found."
            )

            return

        standard = None

        for record in search_results:

            if (
                record.get(
                    "standardNumber"
                )
                == STANDARD_NUMBER
            ):

                standard = record

                break

        if standard is None:

            standard = search_results[0]

        print(
            "\nStandard Number:",
            standard.get(
                "standardNumber"
            )
        )

        print(
            "Standard Name:",
            standard.get(
                "standardName"
            )
        )

        print(
            "Standard ID:",
            standard.get(
                "standardId"
            )
        )

        print(
            "Encrypted ID:",
            standard.get(
                "standardEncId"
            )
        )

        # =====================================================
        # STEP 2: STANDARD DETAIL
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 2: STANDARD DETAIL")
        print("=" * 70)

        standard_enc_id = standard.get(
            "standardEncId"
        )

        if not standard_enc_id:

            print(
                "\nERROR: standardEncId missing."
            )

            return

        detail = await provider.get_standard(
            standard_enc_id
        )

        if not detail:

            print(
                "\nERROR: Standard detail unavailable."
            )

            return

        print(
            "\nStandard Number:",
            detail.get(
                "standardNumber"
            )
        )

        print(
            "Name:",
            detail.get(
                "standardName"
            )
        )

        print(
            "Published:",
            detail.get(
                "publishedOn"
            )
        )

        print(
            "Revision Count:",
            detail.get(
                "noOfRevision"
            )
        )

        print(
            "Amendment Count:",
            detail.get(
                "noOfAmendment"
            )
        )

        print(
            "Reaffirmation:",
            detail.get(
                "reAffirmationYear"
            )
        )

        print(
            "Review On:",
            detail.get(
                "reviewOn"
            )
        )

        print(
            "Withdraw Status:",
            detail.get(
                "withdrawStatus"
            )
        )

        print(
            "Superseded By:",
            detail.get(
                "superseded_byis"
            )
        )

        # =====================================================
        # STEP 3: BUILD CANDIDATE
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 3: BUILD CANDIDATE")
        print("=" * 70)

        candidate = dict(
            standard
        )

        candidate[
            "standardNumber"
        ] = STANDARD_NUMBER

        for key, value in detail.items():

            if value is not None:

                candidate[key] = value

        print(
            "\nCandidate prepared."
        )

        # =====================================================
        # STEP 4: EVIDENCE ENRICHMENT
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 4: EVIDENCE ENRICHMENT")
        print("=" * 70)

        evidence_service = BISEvidenceService(
            provider=provider
        )

        enriched = await evidence_service.enrich_candidate(
            candidate
        )

        print(
            "\nEnrichment completed."
        )

        # =====================================================
        # STEP 5: TOP LEVEL
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 5: TOP-LEVEL RESULT")
        print("=" * 70)

        print(
            "\nResult keys:"
        )

        for key in enriched.keys():

            print(
                " -",
                key
            )

        print(
            "\nSuccess:",
            enriched.get(
                "success"
            )
        )

        print(
            "Partial evidence:",
            enriched.get(
                "partial_evidence"
            )
        )

        # =====================================================
        # STEP 6: NESTED EVIDENCE
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 6: NESTED EVIDENCE")
        print("=" * 70)

        evidence = enriched.get(
            "evidence",
            {}
        )

        if not isinstance(
            evidence,
            dict
        ):

            print(
                "\nERROR: Evidence is not a dictionary."
            )

            pprint(
                evidence
            )

            return

        print(
            "\nEvidence keys:"
        )

        for key in evidence.keys():

            print(
                " -",
                key
            )

        # =====================================================
        # STEP 7: EVIDENCE RESPONSE STATUS
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 7: EVIDENCE RESPONSE STATUS")
        print("=" * 70)

        evidence_categories = [
            "standard",
            "amendments",
            "relationships",
            "summary",
            "corrigenda",
            "gazette",
            "product_manuals",
            "crs",
            "mcs",
            "laboratories",
            "licenses",
            "format_documents",
        ]

        for category in evidence_categories:

            value = evidence.get(
                category
            )

            print(
                f"\n{category}:"
            )

            if isinstance(
                value,
                dict
            ):

                print(
                    "  success:",
                    value.get(
                        "success"
                    )
                )

                print(
                    "  endpoint:",
                    value.get(
                        "endpoint"
                    )
                )

                print(
                    "  message:",
                    value.get(
                        "message"
                    )
                )

                print(
                    "  error:",
                    value.get(
                        "error"
                    )
                )

                data = value.get(
                    "data"
                )

                if isinstance(
                    data,
                    list
                ):

                    print(
                        "  data records:",
                        len(data)
                    )

                elif data is None:

                    print(
                        "  data records: 0"
                    )

                else:

                    print(
                        "  data type:",
                        type(data).__name__
                    )

            elif isinstance(
                value,
                list
            ):

                print(
                    "  records:",
                    len(value)
                )

            elif value is None:

                print(
                    "  value: None"
                )

            else:

                print(
                    "  type:",
                    type(value).__name__
                )

        # =====================================================
        # STEP 8: AMENDMENTS
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 8: AMENDMENTS")
        print("=" * 70)

        amendments_response = evidence.get(
            "amendments"
        )

        amendments = extract_data(
            amendments_response
        )

        print(
            "\nAmendment records:",
            len(amendments)
        )

        for index, amendment in enumerate(
            amendments,
            start=1
        ):

            print(
                f"\nAMENDMENT {index}"
            )

            pprint(
                amendment
            )

        # =====================================================
        # STEP 9: RELATIONSHIPS
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 9: RELATIONSHIPS")
        print("=" * 70)

        relationships_response = evidence.get(
            "relationships"
        )

        relationships = extract_data(
            relationships_response
        )

        print(
            "\nRelationship records:",
            len(relationships)
        )

        for index, relationship in enumerate(
            relationships[:15],
            start=1
        ):

            print(
                f"\nRELATIONSHIP {index}"
            )

            pprint(
                relationship
            )

        if len(relationships) > 15:

            print(
                "\n... remaining relationships omitted"
            )

        # =====================================================
        # STEP 10: SUMMARY
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 10: SUMMARY")
        print("=" * 70)

        summary_response = evidence.get(
            "summary"
        )

        summary = extract_data(
            summary_response
        )

        if summary:

            print(
                "\nSummary data available: YES"
            )

            pprint(
                summary
            )

        else:

            print(
                "\nSummary data available: NO"
            )

        # =====================================================
        # STEP 11: OTHER EVIDENCE COUNTS
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 11: OTHER EVIDENCE COUNTS")
        print("=" * 70)

        other_categories = [
            "corrigenda",
            "gazette",
            "product_manuals",
            "crs",
            "mcs",
            "laboratories",
            "licenses",
            "format_documents",
        ]

        category_counts = {}

        for category in other_categories:

            response = evidence.get(
                category
            )

            records = extract_data(
                response
            )

            category_counts[
                category
            ] = len(records)

            print(
                f"{category}: {len(records)}"
            )

        # =====================================================
        # STEP 12: ERRORS
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 12: EVIDENCE ERRORS")
        print("=" * 70)

        errors = evidence.get(
            "errors",
            []
        )

        print(
            "\nEvidence errors:",
            len(errors)
        )

        if errors:

            pprint(
                errors
            )

        # =====================================================
        # STEP 13: FINAL VALIDATION
        # =====================================================

        print("\n")
        print("=" * 70)
        print("FINAL EVIDENCE LAYER RESULT")
        print("=" * 70)

        print(
            "\nStandard:",
            STANDARD_NUMBER
        )

        print(
            "Service success:",
            enriched.get(
                "success"
            )
        )

        print(
            "Partial evidence:",
            enriched.get(
                "partial_evidence"
            )
        )

        print(
            "Amendment records:",
            len(amendments)
        )

        print(
            "Relationship records:",
            len(relationships)
        )

        for category, count in category_counts.items():

            print(
                f"{category}: {count}"
            )

        print(
            "Errors:",
            len(errors)
        )

        if (
            enriched.get("success")
            and not errors
        ):

            print(
                "\n"
                "========== EVIDENCE SERVICE TEST PASSED =========="
            )

        elif enriched.get("success"):

            print(
                "\n"
                "========== EVIDENCE SERVICE PASSED "
                "WITH EVIDENCE ERRORS =========="
            )

        else:

            print(
                "\n"
                "========== EVIDENCE SERVICE FAILED =========="
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

        import traceback

        traceback.print_exc()

    finally:

        await provider.close()


if __name__ == "__main__":
    asyncio.run(main())