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
        res = " ".join(words[:n]).strip()
        while res and res.split()[-1].lower() in {"for", "of", "in", "with", "to", "and", "by"}:
            words = res.split()[:-1]
            res = " ".join(words).strip()
        return res

    GENERIC_TERMS = {
        "industrial",
        "safety",
        "equipment",
        "protection",
        "protective",
        "general",
        "specification",
        "standard",
        "selection",
        "maintenance",
        "care",
        "guide",
        "guidelines",
        "commercial",
        "domestic",
        "requirements",
        "grade",
        "class",
        "type",
        "purpose",
        "use",
        "heavy",
        "light",
        "medium",
        "supply",
        "transmission",
        "distribution",
        "code",
        "practice",
    }

    @classmethod
    def _extract_product_nouns(cls, product_text: str) -> list[str]:
        """
        Extract meaningful product head terms/nouns from product name.
        Example:
            'Industrial Safety Helmet' -> ['helmet', 'safety helmet']
            'Steel Pipe for Drinking Water' -> ['pipe', 'steel pipe']
        """
        words = [w.lower() for w in cls._clean_text(product_text).split()]
        if not words:
            return []

        # Find words not in generic terms
        specific_words = [w for w in words if w not in cls.GENERIC_TERMS and len(w) > 2]
        if not specific_words:
            # Fall back to the last word
            return [words[-1]]

        nouns = list(specific_words)
        # Also include last 2 words if last word is specific
        if len(words) >= 2 and words[-1] in specific_words:
            nouns.append(f"{words[-2]} {words[-1]}")

        return nouns

    @classmethod
    def _is_query_product_centric(cls, query: str, product_nouns: list[str]) -> bool:
        """
        Reject queries that contain only generic terms and lack the product noun.
        """
        q_words = [w.lower() for w in query.split()]
        if not q_words:
            return False

        # Reject if all words are generic
        if all(w in cls.GENERIC_TERMS for w in q_words):
            return False

        # If product nouns are identified, query MUST contain at least one product noun or stem
        if product_nouns:
            q_text = " ".join(q_words)
            has_product_term = False
            for noun in product_nouns:
                noun_stem = noun[:4] if len(noun) >= 4 else noun
                if noun in q_text or noun_stem in q_text:
                    has_product_term = True
                    break
            if not has_product_term:
                return False

        return True

    # =========================================================
    # DYNAMIC QUERY GENERATION
    # =========================================================

    def build_queries(
        self,
        requirements: dict[str, Any],
    ) -> list[str]:
        """
        Dynamically generate 3–5 focused, product-centric search queries.
        """
        import logging
        logger = logging.getLogger(__name__)

        if not isinstance(requirements, dict):
            return []

        product_raw = (
            requirements.get("product_name")
            or requirements.get("product")
            or ""
        )
        product = self._clean_text(product_raw)

        # Extract base product by stripping trailing preposition clauses
        # e.g. "Steel Pipe for Drinking Water" -> "Steel Pipe"
        base_product = product
        for prep in [" for ", " of ", " to ", " in ", " with "]:
            if prep in product.lower():
                base_product = product[:product.lower().index(prep)].strip()
                break

        application = self._clean_text(
            requirements.get("application") or requirements.get("intended_application")
        )
        materials = self._clean_list(requirements.get("materials"))
        keywords = self._clean_list(
            requirements.get("keywords") or requirements.get("search_keywords")
        )

        product_nouns = self._extract_product_nouns(base_product)
        base_words = base_product.split()
        core_product_noun = base_words[-1] if base_words else (product_nouns[-1] if product_nouns else "")

        candidates: list[str] = []

        # 1. Base clean product name (e.g. "Steel Pipe", "Industrial Safety Helmet")
        if base_product:
            candidates.append(base_product)

        # 2. Short base product phrase (e.g. "Safety Helmet", "Steel Pipe")
        if len(base_words) >= 2:
            candidates.append(" ".join(base_words[-2:]))

        # 3. Product-specific synonyms from keywords
        for kw in keywords:
            kw_clean = self._clean_text(kw)
            if kw_clean and self._is_query_product_centric(kw_clean, product_nouns):
                candidates.append(self._first_n_words(kw_clean, 3))

        # 4. Product + Key Application (e.g. "Steel Pipe Water", "Helmet Construction")
        if core_product_noun and application:
            app_words = [w for w in application.split() if w.lower() not in self.GENERIC_TERMS]
            if app_words:
                candidates.append(f"{base_product} {app_words[0].title()}")

        # 5. Material + Core Product (e.g. "Steel Pipe", "Polycarbonate Helmet")
        if core_product_noun and materials:
            mat_first = materials[0].split()[0] if materials[0].split() else ""
            if mat_first and mat_first.lower() not in self.GENERIC_TERMS:
                candidates.append(f"{mat_first.title()} {core_product_noun.title()}")

        # 6. Fallback: Core noun alone (e.g. "Helmet", "Pipe", "Cement")
        if core_product_noun:
            candidates.append(core_product_noun.title())

        # Filter, normalize, deduplicate, and enforce product-centricity
        seen: set[str] = set()
        final_queries: list[str] = []

        for query in candidates:
            query = query.strip()
            if not query or len(query) < 2:
                continue
            if self._looks_like_standard_identifier(query):
                continue

            # Length bounded to 3-4 words max
            words = query.split()
            if len(words) > 4:
                query = " ".join(words[:4])

            # Enforce product-centric filter (STEP 3)
            if not self._is_query_product_centric(query, product_nouns):
                continue

            norm = query.casefold()
            if norm in seen:
                continue
            seen.add(norm)
            final_queries.append(query)

            if len(final_queries) >= self.max_queries:
                break

        logger.info(f"[QUERY PLANNER] Generated queries: {final_queries}")
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