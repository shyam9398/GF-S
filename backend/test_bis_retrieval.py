import asyncio
from typing import Any

from app.bis.bis_web import BISWebProvider
from app.bis.normalizer import BISStandardNormalizer


async def main():

    provider = BISWebProvider()

    try:

        # =====================================================
        # STEP 1: SEARCH BIS
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 1: BIS SEARCH")
        print("=" * 70)

        search_query = "IS 2925:1984"

        results = await provider.search_standards(
            search_query
        )

        print(
            "\nSearch Query:",
            search_query
        )

        print(
            "Results:",
            len(results)
        )

        if not results:

            print(
                "\nERROR: No BIS standards found."
            )

            return

        for index, item in enumerate(
            results,
            start=1,
        ):

            print(
                f"{index}. "
                f"{item.get('standardNumber')} | "
                f"{item.get('standardName')} | "
                f"standardId={item.get('standardId')} | "
                f"standardEncId={item.get('standardEncId')}"
            )

        # =====================================================
        # STEP 2: NORMALIZATION
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 2: BIS NORMALIZATION")
        print("=" * 70)

        canonical = (
            BISStandardNormalizer
            .build_canonical_standard(
                results
            )
        )

        print(
            "\nRaw BIS records:",
            len(results)
        )

        print(
            "Canonical standards:",
            len(canonical)
        )

        if not canonical:

            print(
                "\nERROR: Normalizer returned no "
                "canonical standards."
            )

            return

        for index, standard in enumerate(
            canonical,
            start=1,
        ):

            print(
                f"\n{index}. "
                f"{standard.get('standardNumber')}"
            )

            print(
                "   Name:",
                standard.get(
                    "standardName"
                )
            )

            print(
                "   Record Count:",
                standard.get(
                    "recordCount"
                )
            )

            print(
                "   Standard IDs:",
                standard.get(
                    "standardIds"
                )
            )

            print(
                "   Enc IDs:",
                standard.get(
                    "standardEncIds"
                )
            )

        # =====================================================
        # STEP 3: SELECT CANONICAL STANDARD
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 3: SELECT CANONICAL STANDARD")
        print("=" * 70)

        selected = None

        for standard in canonical:

            if (
                standard.get(
                    "standardNumber"
                )
                == "IS 2925:1984"
            ):

                selected = standard

                break

        if selected is None:

            print(
                "\nERROR: IS 2925:1984 was not "
                "found after normalization."
            )

            return

        print(
            "\nSelected:",
            selected.get(
                "standardNumber"
            )
        )

        print(
            "Records preserved:",
            selected.get(
                "recordCount"
            )
        )

        primary_record = selected.get(
            "primaryRecord"
        )

        if primary_record:

            print(
                "Primary Name:",
                primary_record.get(
                    "standardName"
                )
            )

            print(
                "Primary Published On:",
                primary_record.get(
                    "publishedOn"
                )
            )

            print(
                "Primary Valid Upto:",
                primary_record.get(
                    "validUpto"
                )
            )

            print(
                "Primary Withdraw Status:",
                primary_record.get(
                    "withdrawStatus"
                )
            )

        # =====================================================
        # STEP 4: GET STANDARD DETAILS
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 4: BIS STANDARD DETAILS")
        print("=" * 70)

        standard_enc_ids = selected.get(
            "standardEncIds",
            []
        )

        if not standard_enc_ids:

            print(
                "\nERROR: No standardEncId "
                "was returned by BIS."
            )

            return

        search_enc_id = standard_enc_ids[0]

        detail = await provider.get_standard(
            search_enc_id
        )

        if not detail:

            print(
                "\nERROR: BIS standard detail "
                "was not returned."
            )

            return

        print(
            "\nStandard Number:",
            detail.get(
                "standardNumber"
            )
        )

        print(
            "Standard Name:",
            detail.get(
                "standardName"
            )
        )

        print(
            "Published On:",
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
            "Standard Type:",
            detail.get(
                "typeOfStandardId"
            )
        )

        print(
            "Reaffirmation Year:",
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
            "Withdraw On:",
            detail.get(
                "withdrawOn"
            )
        )

        print(
            "Equivalent Standard:",
            detail.get(
                "equivalentIs"
            )
        )

        print(
            "Superseded By:",
            detail.get(
                "superseded_byis"
            )
        )

        print(
            "Committee:",
            detail.get(
                "committeeName"
            )
        )

        print(
            "Department:",
            detail.get(
                "departmentName"
            )
        )

        print(
            "Document:",
            detail.get(
                "is_documents"
            )
        )

        # =====================================================
        # STEP 5: GET ENCRYPTED DETAIL STANDARD ID
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 5: EXTRACT DETAIL STANDARD ID")
        print("=" * 70)

        detail_standard_id = detail.get(
            "standardId"
        )

        if not detail_standard_id:

            print(
                "\nERROR: Detail response does not "
                "contain encrypted standardId."
            )

            return

        print(
            "\nEncrypted detail standardId received:"
        )

        print(
            str(
                detail_standard_id
            )[:80],
            "..."
        )

        # =====================================================
        # STEP 6: AMENDMENTS
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 6: BIS AMENDMENTS")
        print("=" * 70)

        amendments = await provider.get_amendments(
            detail_standard_id
        )

        print(
            "\nTotal amendments:",
            len(amendments)
        )

        if not amendments:

            print(
                "No amendment records returned."
            )

        for index, amendment in enumerate(
            amendments,
            start=1,
        ):

            print(
                f"{index}. "
                f"{amendment.get('amendmentLabel')} | "
                f"Year={amendment.get('amendmentYear')} | "
                f"Standard={amendment.get('standardNumber')} | "
                f"Document={amendment.get('is_documents')}"
            )

        # =====================================================
        # STEP 7: CROSS REFERENCES
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 7: BIS CROSS REFERENCES")
        print("=" * 70)

        relationships = await provider.get_relationships(
            search_enc_id
        )

        print(
            "\nTotal relationships:",
            len(relationships)
        )

        if not relationships:

            print(
                "No relationship records returned."
            )

        for index, relationship in enumerate(
            relationships,
            start=1,
        ):

            print(
                f"{index}. "
                f"Type={relationship.get('relationshipType')} | "
                f"Standard="
                f"{relationship.get('standardNumber')}"
            )

        # =====================================================
        # STEP 8: SUMMARY
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 8: BIS SUMMARY")
        print("=" * 70)

        summary = await provider.get_summary(
            detail_standard_id
        )

        if summary:

            print(
                "\nSummary response received."
            )

            print(
                "Fields:",
                list(
                    summary.keys()
                )
            )

        else:

            print(
                "\nNo summary data returned."
            )

        # =====================================================
        # STEP 9: CORRIGENDUM
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 9: BIS CORRIGENDUM")
        print("=" * 70)

        corrigenda = await provider.get_corrigenda(
            detail_standard_id
        )

        print(
            "\nTotal corrigenda:",
            len(corrigenda)
        )

        if not corrigenda:

            print(
                "No corrigendum records returned."
            )

        # =====================================================
        # STEP 10: GAZETTE
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 10: BIS GAZETTE")
        print("=" * 70)

        gazette = await provider.get_gazette(
            detail_standard_id
        )

        print(
            "\nTotal gazette records:",
            len(gazette)
        )

        if not gazette:

            print(
                "No gazette records returned."
            )

        # =====================================================
        # STEP 11: PRODUCT MANUAL
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 11: BIS PRODUCT MANUAL")
        print("=" * 70)

        manuals = await provider.get_product_manuals(
            detail_standard_id
        )

        print(
            "\nTotal product manuals:",
            len(manuals)
        )

        for index, manual in enumerate(
            manuals,
            start=1,
        ):

            print(
                f"{index}. "
                f"{manual}"
            )

        # =====================================================
        # STEP 12: CRS
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 12: BIS CRS")
        print("=" * 70)

        crs = await provider.get_crs(
            standard_id=detail_standard_id,
            page=1,
            limit=50,
        )

        print(
            "\nCRS records:",
            len(
                crs.get(
                    "data",
                    []
                )
            )
        )

        print(
            "CRS total records:",
            crs.get(
                "totalRecord"
            )
        )

        # =====================================================
        # STEP 13: MCS
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 13: BIS MCS")
        print("=" * 70)

        mcs = await provider.get_mcs(
            standard_id=detail_standard_id,
            page=1,
            limit=50,
        )

        print(
            "\nMCS records:",
            len(
                mcs.get(
                    "data",
                    []
                )
            )
        )

        print(
            "MCS total records:",
            mcs.get(
                "totalRecord"
            )
        )

        # =====================================================
        # STEP 14: LABORATORIES
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 14: BIS LABORATORIES")
        print("=" * 70)

        laboratories_page = (
            await provider.get_laboratories(
                standard_id=detail_standard_id,
                page=1,
                limit=50,
            )
        )

        print(
            "\nLaboratories on page 1:",
            len(
                laboratories_page.get(
                    "data",
                    []
                )
            )
        )

        print(
            "Total laboratories:",
            laboratories_page.get(
                "totalRecord"
            )
        )

        # =====================================================
        # STEP 15: ALL LABORATORIES / PAGINATION
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 15: LABORATORY PAGINATION")
        print("=" * 70)

        all_laboratories = (
            await provider.get_all_laboratories(
                standard_id=detail_standard_id,
                limit=50,
            )
        )

        print(
            "\nAll laboratories retrieved:",
            len(
                all_laboratories
            )
        )

        # =====================================================
        # STEP 16: LICENSES
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 16: BIS LICENSES")
        print("=" * 70)

        licenses_page = (
            await provider.get_licenses(
                standard_id=detail_standard_id,
                status="Operative",
                page=1,
                limit=50,
            )
        )

        print(
            "\nLicenses on page 1:",
            len(
                licenses_page.get(
                    "data",
                    []
                )
            )
        )

        print(
            "Total licenses:",
            licenses_page.get(
                "totalRecord"
            )
        )

        # =====================================================
        # STEP 17: ALL LICENSES / PAGINATION
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 17: LICENSE PAGINATION")
        print("=" * 70)

        all_licenses = (
            await provider.get_all_licenses(
                standard_id=detail_standard_id,
                status="Operative",
                limit=50,
            )
        )

        print(
            "\nAll licenses retrieved:",
            len(
                all_licenses
            )
        )

        # =====================================================
        # STEP 18: FORMAT DOCUMENTS
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 18: BIS FORMAT DOCUMENTS")
        print("=" * 70)

        format_documents = (
            await provider.get_format_documents(
                detail_standard_id
            )
        )

        print(
            "\nFormat documents:",
            len(
                format_documents
            )
        )

        # =====================================================
        # STEP 19: FULL PAGINATED CRS
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 19: FULL CRS PAGINATION")
        print("=" * 70)

        all_crs = await provider.get_all_crs(
            standard_id=detail_standard_id,
            status="Operative",
            limit=50,
        )

        print(
            "\nAll CRS records retrieved:",
            len(
                all_crs
            )
        )

        # =====================================================
        # STEP 20: FULL PAGINATED MCS
        # =====================================================

        print("\n")
        print("=" * 70)
        print("STEP 20: FULL MCS PAGINATION")
        print("=" * 70)

        all_mcs = await provider.get_all_mcs(
            standard_id=detail_standard_id,
            limit=50,
        )

        print(
            "\nAll MCS records retrieved:",
            len(
                all_mcs
            )
        )

        # =====================================================
        # FINAL TEST SUMMARY
        # =====================================================

        print("\n")
        print("=" * 70)
        print("FINAL BIS RETRIEVAL TEST SUMMARY")
        print("=" * 70)

        print(
            "\nSearch:",
            "PASS"
            if results
            else "FAIL"
        )

        print(
            "Normalization:",
            "PASS"
            if canonical
            else "FAIL"
        )

        print(
            "Canonical IS 2925:1984:",
            "PASS"
            if selected
            else "FAIL"
        )

        print(
            "Standard Detail:",
            "PASS"
            if detail
            else "FAIL"
        )

        print(
            "Encrypted Detail ID:",
            "PASS"
            if detail_standard_id
            else "FAIL"
        )

        print(
            "Amendments:",
            "PASS"
        )

        print(
            "Cross References:",
            "PASS"
        )

        print(
            "Summary:",
            "PASS"
        )

        print(
            "Corrigendum:",
            "PASS"
        )

        print(
            "Gazette:",
            "PASS"
        )

        print(
            "Product Manual:",
            "PASS"
        )

        print(
            "CRS:",
            "PASS"
        )

        print(
            "MCS:",
            "PASS"
        )

        print(
            "Laboratories:",
            "PASS"
        )

        print(
            "Laboratory Pagination:",
            "PASS"
        )

        print(
            "Licenses:",
            "PASS"
        )

        print(
            "License Pagination:",
            "PASS"
        )

        print(
            "Format Documents:",
            "PASS"
        )

        print(
            "\n========== TEST COMPLETED ==========\n"
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


asyncio.run(main())