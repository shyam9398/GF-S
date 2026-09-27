import asyncio
from pprint import pprint

from app.bis.retrieval_service import BISRetrievalService
from app.bis.evidence_service import BISEvidenceService


async def main():

    procurement = {
        "product_name": "Industrial Safety Helmet",
        "description": "Industrial safety helmet for workers requiring head protection.",
        "product_category": "Industrial Safety Helmet",
        "intended_application": "Industrial workplace head protection",
        "technical_requirements": "Safety helmet suitable for industrial use",
        "safety_requirements": "Protection against head injuries",
    }

    retrieval = BISRetrievalService()

    try:
        result = await retrieval.discover_standards(
            procurement
        )

        candidates = result.get(
            "candidates",
            []
        )

        print("Candidates:", len(candidates))

        if not candidates:
            print("No candidates found.")
            return

        print("\nCandidate:")
        pprint(candidates[0])

        evidence_service = BISEvidenceService()

        try:
            evidence_result = await evidence_service.enrich_candidates(
                candidates
            )

            print("\nEvidence result keys:")
            print(list(evidence_result.keys()))

            enriched = evidence_result.get(
                "results",
                []
            )

            print("\nEnriched candidates:", len(enriched))

            if not enriched:
                print("No enriched candidates.")
                return

            evidence = enriched[0].get(
                "evidence",
                {}
            )

            print("\nEvidence keys:")
            print(list(evidence.keys()))

            print("\nRAW RELATIONSHIP EVIDENCE:")
            pprint(
                evidence.get(
                    "relationships"
                )
            )

        finally:
            await evidence_service.close()

    finally:
        await retrieval.close()


if __name__ == "__main__":
    asyncio.run(main())
