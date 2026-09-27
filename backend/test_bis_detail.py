import asyncio

from app.bis.bis_web import BISWebProvider


async def main():

    provider = BISWebProvider()

    try:

        # =====================================================
        # STEP 1: SEARCH BIS
        # =====================================================

        print("\n========== BIS SEARCH ==========\n")

        results = await provider.search_standards(
            "IS 2925:1984"
        )

        print("Results:", len(results))

        if not results:
            print("No BIS standards found.")
            return

        for index, item in enumerate(results, start=1):

            print(
                f"{index}. "
                f"{item.get('standardNumber')} | "
                f"{item.get('standardName')} | "
                f"standardId={item.get('standardId')}"
            )

        # =====================================================
        # STEP 2: SELECT FIRST BIS RECORD
        # =====================================================

        search_record = results[0]

        search_enc_id = search_record.get(
            "standardEncId"
        )

        if not search_enc_id:

            print(
                "\nERROR: BIS did not return standardEncId."
            )

            return

        # =====================================================
        # STEP 3: GET COMPLETE BIS STANDARD DETAILS
        # =====================================================

        print("\n========== BIS DETAIL ==========\n")

        detail = await provider.get_standard(
            search_enc_id
        )

        if not detail:

            print(
                "ERROR: BIS standard detail was not returned."
            )

            return

        print(
            "Standard Number:",
            detail.get("standardNumber")
        )

        print(
            "Standard Name:",
            detail.get("standardName")
        )

        print(
            "Published On:",
            detail.get("publishedOn")
        )

        print(
            "Revision Count:",
            detail.get("noOfRevision")
        )

        print(
            "Amendment Count:",
            detail.get("noOfAmendment")
        )

        print(
            "Standard Type:",
            detail.get("typeOfStandardId")
        )

        print(
            "Reaffirmation Year:",
            detail.get("reAffirmationYear")
        )

        print(
            "Review On:",
            detail.get("reviewOn")
        )

        print(
            "Withdraw Status:",
            detail.get("withdrawStatus")
        )

        print(
            "Withdraw On:",
            detail.get("withdrawOn")
        )

        print(
            "Equivalent Standard:",
            detail.get("equivalentIs")
        )

        print(
            "Superseded By:",
            detail.get("superseded_byis")
        )

        print(
            "Committee:",
            detail.get("committeeName")
        )

        print(
            "Department:",
            detail.get("departmentName")
        )

        print(
            "Document:",
            detail.get("is_documents")
        )

        # =====================================================
        # STEP 4: GET AMENDMENTS
        # =====================================================

        print("\n========== BIS AMENDMENTS ==========\n")

        # IMPORTANT:
        # BIS amendment API expects the encrypted standardId
        # returned by the detail API.

        amendment_standard_id = detail.get(
            "standardId"
        )

        if not amendment_standard_id:

            print(
                "ERROR: Detail response does not contain "
                "the encrypted standardId."
            )

            return

        amendments = await provider.get_amendments(
            amendment_standard_id
        )

        print(
            "Total amendments:",
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
        # END
        # =====================================================

        print("\n========== TEST COMPLETED ==========\n")

    except Exception as error:

        print(
            "\nERROR:",
            type(error).__name__,
        )

        print(
            "Message:",
            str(error),
        )

    finally:

        await provider.close()


asyncio.run(main())