from __future__ import annotations

import re
from typing import Any


class BISQueryPlanner:
    """
    Creates dynamic search queries for BIS standards.

    Gemini provides procurement concepts such as:
    - product
    - product category
    - intended application
    - materials
    - technical requirements
    - performance requirements
    - safety requirements
    - hazards
    - testing requirements
    - certification context
    - search keywords

    This planner converts those concepts into BIS search
    queries.

    IMPORTANT:
    - This class does NOT generate Indian Standard numbers.
    - Standard identifiers must originate from BIS responses.
    - Gemini-generated values are treated only as search concepts.
    - Any value that looks like an IS/ISO/IEC standard identifier
      is excluded from search concepts.
    - Queries remain product-agnostic.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    DEFAULT_MAX_QUERIES = 20

    def __init__(
        self,
        max_queries: int = DEFAULT_MAX_QUERIES,
    ):
        self.max_queries = max(
            1,
            int(max_queries),
        )

    # =========================================================
    # TEXT NORMALIZATION
    # =========================================================

    @staticmethod
    def _clean_text(
        value: Any,
    ) -> str:

        if value is None:
            return ""

        if isinstance(
            value,
            str,
        ):
            return " ".join(
                value.strip().split()
            )

        return ""

    # =========================================================
    # STANDARD IDENTIFIER DETECTION
    # =========================================================

    @staticmethod
    def _looks_like_standard_identifier(
        value: str,
    ) -> bool:
        """
        Reject strings that look like authoritative standard
        identifiers.

        Examples:
        IS 2925
        IS 4151:2015
        ISO 3873
        IEC 62368-1

        These identifiers must come from BIS retrieval,
        not from Gemini-generated search concepts.
        """

        if not value:
            return False

        patterns = [
            r"\bIS[\s:-]*\d{2,6}(?::\d{4})?\b",
            r"\bISO[\s:-]*\d{2,6}(?::\d{4})?\b",
            r"\bIEC[\s:-]*\d{2,6}(?::\d{4})?\b",
        ]

        return any(
            re.search(
                pattern,
                value,
                flags=re.IGNORECASE,
            )
            for pattern in patterns
        )

    # =========================================================
    # LIST NORMALIZATION
    # =========================================================

    @classmethod
    def _clean_list(
        cls,
        value: Any,
    ) -> list[str]:

        if value is None:
            return []

        if isinstance(
            value,
            str,
        ):
            cleaned = cls._clean_text(
                value
            )

            if not cleaned:
                return []

            if cls._looks_like_standard_identifier(
                cleaned
            ):
                return []

            return [cleaned]

        if not isinstance(
            value,
            list,
        ):
            return []

        result: list[str] = []

        for item in value:

            cleaned = cls._clean_text(
                item
            )

            if not cleaned:
                continue

            if cls._looks_like_standard_identifier(
                cleaned
            ):
                continue

            result.append(
                cleaned
            )

        return result

    # =========================================================
    # DEDUPLICATE QUERIES
    # =========================================================

    @staticmethod
    def _deduplicate(
        queries: list[str],
    ) -> list[str]:

        seen: set[str] = set()

        result: list[str] = []

        for query in queries:

            if not isinstance(
                query,
                str,
            ):
                continue

            cleaned = " ".join(
                query.strip().split()
            )

            if not cleaned:
                continue

            # Never allow a generated query containing an
            # apparent standard identifier to pass through.
            if BISQueryPlanner._looks_like_standard_identifier(
                cleaned
            ):
                continue

            normalized = cleaned.casefold()

            if normalized in seen:
                continue

            seen.add(
                normalized
            )

            result.append(
                cleaned
            )

        return result

    # =========================================================
    # COMBINE TERMS
    # =========================================================

    @staticmethod
    def _combine(
        *values: str,
    ) -> str:

        parts: list[str] = []

        for value in values:

            cleaned = (
                " ".join(
                    value.strip().split()
                )
                if value
                else ""
            )

            if not cleaned:
                continue

            if BISQueryPlanner._looks_like_standard_identifier(
                cleaned
            ):
                continue

            parts.append(
                cleaned
            )

        return " ".join(parts)

    # =========================================================
    # BUILD PRODUCT QUERIES
    # =========================================================

    def _product_queries(
        self,
        data: dict[str, Any],
    ) -> list[str]:

        queries: list[str] = []

        product = self._clean_text(
            data.get("product")
        )

        category = self._clean_text(
            data.get("product_category")
        )

        application = self._clean_text(
            data.get("intended_application")
        )

        procurement = self._clean_text(
            data.get("procurement_purpose")
        )

        if product:
            queries.append(
                product
            )

        query = self._combine(
            product,
            category,
        )

        if query:
            queries.append(
                query
            )

        query = self._combine(
            product,
            application,
        )

        if query:
            queries.append(
                query
            )

        query = self._combine(
            category,
            application,
        )

        if query:
            queries.append(
                query
            )

        query = self._combine(
            product,
            procurement,
        )

        if query:
            queries.append(
                query
            )

        return queries

    # =========================================================
    # BUILD MATERIAL QUERIES
    # =========================================================

    def _material_queries(
        self,
        data: dict[str, Any],
    ) -> list[str]:

        queries: list[str] = []

        product = self._clean_text(
            data.get("product")
        )

        category = self._clean_text(
            data.get("product_category")
        )

        application = self._clean_text(
            data.get("intended_application")
        )

        materials = self._clean_list(
            data.get("materials")
        )

        for material in materials:

            # Prefer product/material context over
            # material-only searches.
            query = self._combine(
                product,
                material,
            )

            if query:
                queries.append(
                    query
                )

            query = self._combine(
                category,
                material,
            )

            if query:
                queries.append(
                    query
                )

            query = self._combine(
                material,
                application,
            )

            if query:
                queries.append(
                    query
                )

        return queries

    # =========================================================
    # BUILD TECHNICAL QUERIES
    # =========================================================

    def _technical_queries(
        self,
        data: dict[str, Any],
    ) -> list[str]:

        queries: list[str] = []

        product = self._clean_text(
            data.get("product")
        )

        technical = self._clean_list(
            data.get(
                "technical_requirements"
            )
        )

        for requirement in technical:

            query = self._combine(
                product,
                requirement,
            )

            if query:
                queries.append(
                    query
                )

        return queries

    # =========================================================
    # BUILD PERFORMANCE QUERIES
    # =========================================================

    def _performance_queries(
        self,
        data: dict[str, Any],
    ) -> list[str]:

        queries: list[str] = []

        product = self._clean_text(
            data.get("product")
        )

        performance = self._clean_list(
            data.get(
                "performance_requirements"
            )
        )

        for requirement in performance:

            query = self._combine(
                product,
                requirement,
            )

            if query:
                queries.append(
                    query
                )

        return queries

    # =========================================================
    # BUILD SAFETY QUERIES
    # =========================================================

    def _safety_queries(
        self,
        data: dict[str, Any],
    ) -> list[str]:

        queries: list[str] = []

        product = self._clean_text(
            data.get("product")
        )

        safety = self._clean_list(
            data.get(
                "safety_requirements"
            )
        )

        hazards = self._clean_list(
            data.get(
                "hazards"
            )
        )

        for requirement in safety:

            query = self._combine(
                product,
                requirement,
            )

            if query:
                queries.append(
                    query
                )

        for hazard in hazards:

            query = self._combine(
                product,
                hazard,
            )

            if query:
                queries.append(
                    query
                )

        return queries

    # =========================================================
    # BUILD TESTING QUERIES
    # =========================================================

    def _testing_queries(
        self,
        data: dict[str, Any],
    ) -> list[str]:

        queries: list[str] = []

        product = self._clean_text(
            data.get("product")
        )

        testing = self._clean_list(
            data.get(
                "testing_requirements"
            )
        )

        for requirement in testing:

            query = self._combine(
                product,
                requirement,
            )

            if query:
                queries.append(
                    query
                )

        return queries

    # =========================================================
    # BUILD CERTIFICATION CONTEXT QUERIES
    # =========================================================

    def _certification_queries(
        self,
        data: dict[str, Any],
    ) -> list[str]:

        queries: list[str] = []

        product = self._clean_text(
            data.get("product")
        )

        certification = self._clean_text(
            data.get(
                "certification_context"
            )
        )

        if not certification:
            return queries

        if self._looks_like_standard_identifier(
            certification
        ):
            return queries

        query = self._combine(
            product,
            certification,
        )

        if query:
            queries.append(
                query
            )

        return queries

    # =========================================================
    # BUILD SEARCH KEYWORD QUERIES
    # =========================================================

    def _keyword_queries(
        self,
        data: dict[str, Any],
    ) -> list[str]:

        keywords = self._clean_list(
            data.get(
                "search_keywords"
            )
        )

        product = self._clean_text(
            data.get("product")
        )

        queries: list[str] = []

        for keyword in keywords:

            query = self._combine(
                product,
                keyword,
            )

            if query:
                queries.append(
                    query
                )

        return queries

    # =========================================================
    # MAIN QUERY PLANNING
    # =========================================================

    def build_queries(
        self,
        requirements: dict[str, Any],
    ) -> list[str]:

        if not isinstance(
            requirements,
            dict,
        ):
            return []

        queries: list[str] = []

        # -----------------------------------------------------
        # 1. PRODUCT
        # -----------------------------------------------------

        queries.extend(
            self._product_queries(
                requirements
            )
        )

        # -----------------------------------------------------
        # 2. MATERIAL
        # -----------------------------------------------------

        queries.extend(
            self._material_queries(
                requirements
            )
        )

        # -----------------------------------------------------
        # 3. TECHNICAL
        # -----------------------------------------------------

        queries.extend(
            self._technical_queries(
                requirements
            )
        )

        # -----------------------------------------------------
        # 4. PERFORMANCE
        # -----------------------------------------------------

        queries.extend(
            self._performance_queries(
                requirements
            )
        )

        # -----------------------------------------------------
        # 5. SAFETY + HAZARDS
        # -----------------------------------------------------

        queries.extend(
            self._safety_queries(
                requirements
            )
        )

        # -----------------------------------------------------
        # 6. TESTING
        # -----------------------------------------------------

        queries.extend(
            self._testing_queries(
                requirements
            )
        )

        # -----------------------------------------------------
        # 7. CERTIFICATION
        # -----------------------------------------------------

        queries.extend(
            self._certification_queries(
                requirements
            )
        )

        # -----------------------------------------------------
        # 8. SEARCH KEYWORDS
        # -----------------------------------------------------

        queries.extend(
            self._keyword_queries(
                requirements
            )
        )

        # -----------------------------------------------------
        # DEDUPLICATE + SAFETY FILTER
        # -----------------------------------------------------

        queries = self._deduplicate(
            queries
        )

        # -----------------------------------------------------
        # LIMIT
        # -----------------------------------------------------

        return queries[
            : self.max_queries
        ]

    # =========================================================
    # BUILD QUERY METADATA
    # =========================================================

    def build_query_plan(
        self,
        requirements: dict[str, Any],
    ) -> dict[str, Any]:

        queries = self.build_queries(
            requirements
        )

        return {
            "queries": queries,

            "query_count": len(
                queries
            ),

            "source": (
                "procurement_requirements"
            ),

            "standard_numbers_generated": False,

            "standard_identifiers_from_gemini_used": False,

            "max_queries": self.max_queries,
        }