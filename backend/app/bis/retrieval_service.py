from __future__ import annotations

import asyncio
from typing import Any

from app.bis.bis_web import BISWebProvider
from app.bis.normalizer import BISStandardNormalizer
from app.bis.query_planner import BISQueryPlanner


class BISRetrievalService:
    """
    Coordinates dynamic BIS standard discovery.

    Flow:

        Procurement requirements
                ↓
        BISQueryPlanner
                ↓
        Multiple BIS search queries
                ↓
        BISWebProvider
                ↓
        Raw BIS search records
                ↓
        BISStandardNormalizer
                ↓
        Canonical candidate standards

    This service does not invent Indian Standard numbers.

    All standard identifiers must originate from BIS responses.
    """

    DEFAULT_MAX_CONCURRENT_SEARCHES = 4

    def __init__(
        self,
        provider: BISWebProvider | None = None,
        query_planner: BISQueryPlanner | None = None,
        normalizer: BISStandardNormalizer | None = None,
        max_concurrent_searches: int = DEFAULT_MAX_CONCURRENT_SEARCHES,
    ):
        self.provider = (
            provider
            if provider is not None
            else BISWebProvider()
        )

        self.query_planner = (
            query_planner
            if query_planner is not None
            else BISQueryPlanner()
        )

        self.normalizer = (
            normalizer
            if normalizer is not None
            else BISStandardNormalizer()
        )

        self.max_concurrent_searches = max(
            1,
            int(max_concurrent_searches),
        )

        self._search_semaphore = asyncio.Semaphore(
            self.max_concurrent_searches
        )

    # =========================================================
    # SEARCH ONE QUERY
    # =========================================================

    async def search_query(
        self,
        query: str,
    ) -> dict[str, Any]:

        if not isinstance(query, str):
            query = str(query or "")

        query = query.strip()

        if not query:
            return {
                "query": query,
                "records": [],
                "record_count": 0,
                "success": False,
                "error": "Empty BIS search query.",
            }

        async with self._search_semaphore:

            try:
                records = (
                    await self.provider.search_standards(
                        query
                    )
                )

                if not isinstance(
                    records,
                    list,
                ):
                    records = []

                return {
                    "query": query,
                    "records": records,
                    "record_count": len(records),
                    "success": True,
                    "error": None,
                }

            except Exception as exc:

                return {
                    "query": query,
                    "records": [],
                    "record_count": 0,
                    "success": False,
                    "error": (
                        f"{type(exc).__name__}: {exc}"
                    ),
                }

    # =========================================================
    # SEARCH ALL PLANNED QUERIES
    # =========================================================

    async def search_queries(
        self,
        queries: list[str],
    ) -> list[dict[str, Any]]:

        if not isinstance(
            queries,
            list,
        ):
            return []

        cleaned_queries: list[str] = []
        seen_queries: set[str] = set()

        for query in queries:

            if not isinstance(
                query,
                str,
            ):
                continue

            cleaned = query.strip()

            if not cleaned:
                continue

            # Avoid sending exactly identical queries
            # more than once.
            normalized = cleaned.casefold()

            if normalized in seen_queries:
                continue

            seen_queries.add(normalized)

            cleaned_queries.append(
                cleaned
            )

        if not cleaned_queries:
            return []

        # Search concepts are independent, so execute them
        # concurrently with bounded concurrency.
        tasks = [
            self.search_query(query)
            for query in cleaned_queries
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=False,
        )

        return list(results)

    # =========================================================
    # COLLECT RAW RECORDS
    # =========================================================

    @staticmethod
    def collect_raw_records(
        search_results: list[
            dict[str, Any]
        ],
    ) -> list[dict[str, Any]]:

        records: list[
            dict[str, Any]
        ] = []

        for result in search_results:

            if not isinstance(
                result,
                dict,
            ):
                continue

            query = result.get(
                "query",
                "",
            )

            query_records = result.get(
                "records",
                [],
            )

            if not isinstance(
                query_records,
                list,
            ):
                continue

            for record in query_records:

                if not isinstance(
                    record,
                    dict,
                ):
                    continue

                enriched = dict(
                    record
                )

                # Preserve the query that discovered
                # this BIS record.
                enriched[
                    "_retrieval_query"
                ] = query

                records.append(
                    enriched
                )

        return records

    # =========================================================
    # NORMALIZE CANDIDATES
    # =========================================================

    def normalize_candidates(
        self,
        raw_records: list[
            dict[str, Any]
        ],
    ) -> list[dict[str, Any]]:

        candidates = (
            self.normalizer
            .build_canonical_standard(
                raw_records
            )
        )

        if not isinstance(
            candidates,
            list,
        ):
            return []

        return candidates

    # =========================================================
    # BUILD RETRIEVAL COVERAGE
    # =========================================================

    @staticmethod
    def build_coverage(
        query_plan: dict[str, Any],
        search_results: list[
            dict[str, Any]
        ],
        raw_records: list[
            dict[str, Any]
        ],
        candidates: list[
            dict[str, Any]
        ],
    ) -> dict[str, Any]:

        if not isinstance(
            query_plan,
            dict,
        ):
            query_plan = {}

        if not isinstance(
            search_results,
            list,
        ):
            search_results = []

        if not isinstance(
            raw_records,
            list,
        ):
            raw_records = []

        if not isinstance(
            candidates,
            list,
        ):
            candidates = []

        planned_queries = query_plan.get(
            "queries",
            [],
        )

        if not isinstance(
            planned_queries,
            list,
        ):
            planned_queries = []

        successful_queries = [
            result
            for result in search_results
            if isinstance(result, dict)
            and result.get("success") is True
        ]

        failed_queries = [
            result
            for result in search_results
            if isinstance(result, dict)
            and result.get("success") is False
        ]

        queries_with_results = [
            result
            for result in successful_queries
            if result.get(
                "record_count",
                0,
            ) > 0
        ]

        unique_standard_numbers: set[str] = set()

        for candidate in candidates:

            if not isinstance(
                candidate,
                dict,
            ):
                continue

            standard_number = (
                candidate.get(
                    "standardNumber"
                )
                or candidate.get(
                    "standard_number"
                )
            )

            if standard_number:
                unique_standard_numbers.add(
                    str(standard_number).strip()
                )

        # Count actual raw records that have a canonical
        # standard number. This is a more meaningful
        # duplicate metric than simply comparing all raw
        # records against the number of unique standards.
        raw_records_with_standard_number = 0

        for record in raw_records:

            if not isinstance(
                record,
                dict,
            ):
                continue

            standard_number = (
                record.get(
                    "standardNumber"
                )
                or record.get(
                    "standard_number"
                )
            )

            if standard_number:
                raw_records_with_standard_number += 1

        duplicate_record_count = max(
            0,
            raw_records_with_standard_number
            - len(unique_standard_numbers),
        )

        return {
            "planned_query_count": len(
                planned_queries
            ),

            "executed_query_count": len(
                search_results
            ),

            "successful_query_count": len(
                successful_queries
            ),

            "failed_query_count": len(
                failed_queries
            ),

            "queries_with_results": len(
                queries_with_results
            ),

            "raw_record_count": len(
                raw_records
            ),

            "raw_records_with_standard_number": (
                raw_records_with_standard_number
            ),

            "unique_standard_count": len(
                unique_standard_numbers
            ),

            "duplicate_record_count": (
                duplicate_record_count
            ),

            "coverage_complete": (
                len(failed_queries) == 0
                and len(search_results)
                == len(planned_queries)
            ),
        }

    # =========================================================
    # DISCOVER STANDARDS
    # =========================================================

    async def discover_standards(
        self,
        requirements: dict[str, Any],
    ) -> dict[str, Any]:

        # -----------------------------------------------------
        # STEP 1 — CREATE QUERY PLAN
        # -----------------------------------------------------

        query_plan = (
            self.query_planner
            .build_query_plan(
                requirements
            )
        )

        if not isinstance(
            query_plan,
            dict,
        ):
            query_plan = {
                "queries": [],
                "errors": [
                    "BIS query planner returned an invalid response."
                ],
            }

        queries = query_plan.get(
            "queries",
            [],
        )

        if not isinstance(
            queries,
            list,
        ):
            queries = []

        # -----------------------------------------------------
        # STEP 2 — EXECUTE BIS SEARCHES
        # -----------------------------------------------------

        search_results = (
            await self.search_queries(
                queries
            )
        )

        # -----------------------------------------------------
        # STEP 3 — COLLECT RAW BIS RECORDS
        # -----------------------------------------------------

        raw_records = (
            self.collect_raw_records(
                search_results
            )
        )

        # -----------------------------------------------------
        # STEP 4 — NORMALIZE / DEDUPLICATE
        # -----------------------------------------------------

        candidates = (
            self.normalize_candidates(
                raw_records
            )
        )

        # -----------------------------------------------------
        # STEP 5 — COVERAGE REPORT
        # -----------------------------------------------------

        coverage = self.build_coverage(
            query_plan=query_plan,
            search_results=search_results,
            raw_records=raw_records,
            candidates=candidates,
        )

        # -----------------------------------------------------
        # FINAL RESULT
        # -----------------------------------------------------

        return {
            "success": (
                coverage.get(
                    "successful_query_count",
                    0,
                ) > 0
            ),

            "query_plan": query_plan,

            "search_results": search_results,

            "raw_records": raw_records,

            "candidates": candidates,

            "coverage": coverage,
        }

    # =========================================================
    # CLOSE
    # =========================================================

    async def close(self) -> None:
        await self.provider.close()