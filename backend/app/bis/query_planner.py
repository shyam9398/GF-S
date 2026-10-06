from __future__ import annotations

import re
from typing import Any


class BISQueryPlanner:
    """
    Creates dynamic, focused search queries for BIS standards.

    Per SIH 2026 requirements (Section 11):
    - Do NOT send long multi-sentence procurement texts or massive concatenated phrases to BIS search.
    - Generate 3–5 focused queries dynamically from the structured specification.
    - BIS search indexes titles, scopes, and keywords; queries should be concise (1–4 words).
    - NEVER generate fake Indian Standard numbers.
    - Strictly exclude IS/ISO/IEC standard identifiers from search concepts.
    """

    DEFAULT_MAX_QUERIES = 5

    def __init__(
        self,
        max_queries: int = DEFAULT_MAX_QUERIES,
    ):
        self.max_queries = max(
            3,
            min(int(max_queries), 5),
        )

    # =========================================================
    # TEXT NORMALIZATION & CLEANING
    # =========================================================

    @staticmethod
    def _clean_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            # Remove punctuation except hyphens
            cleaned = re.sub(r"[^\w\s-]", " ", value)
            return " ".join(cleaned.strip().split())
        return ""

    @staticmethod
    def _looks_like_standard_identifier(value: str) -> bool:
        if not value:
            return False
        patterns = [
            r"\bIS[\s:-]*\d{2,6}(?::\d{4})?\b",
            r"\bISO[\s:-]*\d{2,6}(?::\d{4})?\b",
            r"\bIEC[\s:-]*\d{2,6}(?::\d{4})?\b",
        ]
        return any(
            re.search(pattern, value, flags=re.IGNORECASE)
            for pattern in patterns
        )

    @classmethod
    def _clean_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            cleaned = cls._clean_text(value)
            return [cleaned] if cleaned and not cls._looks_like_standard_identifier(cleaned) else []
        if isinstance(value, list):
            result: list[str] = []
            for item in value:
                cleaned = cls._clean_text(item)
                if cleaned and not cls._looks_like_standard_identifier(cleaned):
                    result.append(cleaned)
            return result
        return []

    @staticmethod
    def _first_n_words(text: str, n: int = 3) -> str:
        words = text.split()
        return " ".join(words[:n])

    # =========================================================
    # DYNAMIC QUERY GENERATION
    # =========================================================

    def build_queries(
        self,
        requirements: dict[str, Any],
    ) -> list[str]:
        """
        Dynamically generate 3–5 focused search queries from the structured specification.
        """
        if not isinstance(requirements, dict):
            return []

        product_raw = (
            requirements.get("product_name")
            or requirements.get("product")
            or ""
        )
        product = self._clean_text(product_raw)

        category = self._clean_text(requirements.get("product_category"))
        application = self._clean_text(
            requirements.get("application") or requirements.get("intended_application")
        )
        materials = self._clean_list(requirements.get("materials"))
        technical = self._clean_list(
            requirements.get("technical_specifications")
            or requirements.get("technical_requirements")
        )
        keywords = self._clean_list(
            requirements.get("keywords") or requirements.get("search_keywords")
        )

        candidates: list[str] = []

        # 1. Primary Product Query (clean product phrase, max 3-4 words)
        if product:
            candidates.append(self._first_n_words(product, 4))
            product_words = product.split()
            # If product name has 3+ words (e.g. "Industrial Safety Helmet"), also add concise 2-word form (e.g. "safety helmet")
            if len(product_words) >= 3:
                candidates.append(" ".join(product_words[-2:]))
                candidates.append(" ".join(product_words[:2]))
            elif len(product_words) == 2:
                candidates.append(product_words[-1])  # noun alone, e.g. "helmet"

        # 2. Product + Key Application or Material (focused 2-3 words)
        core_product = product_words[-1] if product else ""
        if len(product_words) >= 2:
            core_product = " ".join(product_words[-2:])

        if core_product and application:
            app_words = application.split()
            if app_words:
                candidates.append(f"{core_product} {app_words[0]}")

        if core_product and materials:
            mat_first = materials[0].split()[0] if materials[0].split() else ""
            if mat_first:
                candidates.append(f"{mat_first} {core_product}")

        # 3. Product + Key Technical Spec
        if core_product and technical:
            tech_words = technical[0].split()
            if tech_words:
                candidates.append(f"{core_product} {tech_words[0]}")

        # 4. Top Specification Keywords
        for kw in keywords[:3]:
            kw_clean = self._clean_text(kw)
            if kw_clean and len(kw_clean.split()) <= 3:
                candidates.append(kw_clean)

        # 5. Fallback Category Query if product is sparse
        if category and not product:
            candidates.append(self._first_n_words(category, 3))

        # Filter, normalize and deduplicate
        seen: set[str] = set()
        final_queries: list[str] = []

        for query in candidates:
            query = query.strip()
            if not query or len(query) < 2:
                continue
            if self._looks_like_standard_identifier(query):
                continue
            # Keep query length bounded (maximum 4 words)
            words = query.split()
            if len(words) > 4:
                query = " ".join(words[:4])

            norm = query.casefold()
            if norm in seen:
                continue
            seen.add(norm)
            final_queries.append(query)

            if len(final_queries) >= self.max_queries:
                break

        return final_queries

    def build_query_plan(
        self,
        requirements: dict[str, Any],
    ) -> dict[str, Any]:
        queries = self.build_queries(requirements)

        return {
            "queries": queries,
            "query_count": len(queries),
            "source": "procurement_requirements",
            "standard_numbers_generated": False,
            "standard_identifiers_from_gemini_used": False,
            "max_queries": self.max_queries,
        }