from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class BISCompatibilityService:
    """
    Evaluates whether a candidate BIS standard actually covers the requested
    procurement product, preventing generic keyword overlap from falsely promoting
    mismatched standards (e.g., foot/arm protection for industrial safety helmet).
    """

    DIRECT_MATCH = "DIRECT_MATCH"
    RELATED_MATCH = "RELATED_MATCH"
    MISMATCH = "MISMATCH"
    UNKNOWN = "UNKNOWN"

    # Conflicting body/product domains for personal protective equipment
    PPE_DOMAIN_MAP = {
        "head": {
            "keywords": ["helmet", "helmets", "hard hat", "hard hats", "headgear", "head protection", "bump cap"],
            "conflicts": ["foot", "leg", "arm", "hand", "clothing", "net", "fall arrest", "eye", "respiratory", "hearing"],
        },
        "foot": {
            "keywords": ["foot", "feet", "leg", "legs", "footwear", "boot", "boots", "shoe", "shoes"],
            "conflicts": ["head", "helmet", "arm", "hand", "net", "clothing", "eye", "hearing"],
        },
        "hand": {
            "keywords": ["arm", "arms", "hand", "hands", "glove", "gloves", "mitten", "mittens", "sleeve"],
            "conflicts": ["head", "helmet", "foot", "leg", "net", "clothing", "eye", "hearing"],
        },
        "fall_net": {
            "keywords": ["safety net", "safety nets", "industrial safety net", "netting"],
            "conflicts": ["head", "helmet", "foot", "leg", "arm", "hand", "clothing"],
        },
        "clothing": {
            "keywords": ["clothing", "apparel", "garment", "garments", "suit", "jacket", "apron"],
            "conflicts": ["head", "helmet", "foot", "leg", "arm", "hand", "net"],
        },
        "eye_face": {
            "keywords": ["eye", "face shield", "faceshield", "goggle", "goggles", "spectacle", "visor"],
            "conflicts": ["foot", "leg", "arm", "hand", "net", "clothing"],
        },
        "respiratory": {
            "keywords": ["respiratory", "respirator", "mask", "masks", "breathing apparatus"],
            "conflicts": ["foot", "leg", "arm", "hand", "net", "clothing"],
        },
    }

    # Distinct industrial product categories and their incompatible counterparts
    PRODUCT_FAMILIES = {
        "pipe": {
            "keywords": ["pipe", "pipes", "piping", "tube", "tubes", "tubing", "conduit"],
            "related": ["fitting", "fittings", "flange", "flanges", "valve", "valves", "joint", "joints", "gasket"],
            "conflicts": ["helmet", "shoe", "boot", "cable", "cement", "battery", "textile"],
        },
        "cable": {
            "keywords": ["cable", "cables", "conductor", "conductors", "wire", "wires", "cord", "cords"],
            "related": ["insulation", "sheath", "connector", "terminal", "joint"],
            "conflicts": ["pipe", "helmet", "shoe", "boot", "cement", "net"],
        },
        "cement": {
            "keywords": ["cement", "cements", "clinker"],
            "related": ["concrete", "mortar", "aggregate", "sand", "admixture"],
            "conflicts": ["pipe", "cable", "helmet", "shoe", "net", "steel"],
        },
        "steel_structural": {
            "keywords": ["structural steel", "steel section", "steel bar", "steel beam", "rebar", "reinforcement"],
            "related": ["wire", "fastener", "bolt", "nut"],
            "conflicts": ["clothing", "shoe", "helmet", "cement"],
        },
    }

    @staticmethod
    def _clean(text: Any) -> str:
        if not text:
            return ""
        return " ".join(str(text).strip().lower().split())

    @classmethod
    def _extract_primary_domain(cls, product_name: str) -> str | None:
        p_clean = cls._clean(product_name)
        for domain, conf in cls.PPE_DOMAIN_MAP.items():
            for kw in conf["keywords"]:
                if kw in p_clean:
                    return domain
        for family, conf in cls.PRODUCT_FAMILIES.items():
            for kw in conf["keywords"]:
                if kw in p_clean:
                    return family
        return None

    @classmethod
    def evaluate_compatibility(
        cls,
        requested_product: str,
        standard_title: str,
        standard_scope: str = "",
        semantic_similarity: float = 0.0,
    ) -> tuple[str, str]:
        """
        Determine product compatibility between requested product and candidate standard.
        Returns (decision, reason):
            decision: DIRECT_MATCH | RELATED_MATCH | MISMATCH | UNKNOWN
            reason: human-readable explanation
        """
        p_clean = cls._clean(requested_product)
        s_title = cls._clean(standard_title)
        s_scope = cls._clean(standard_scope)
        target_text = f"{s_title} {s_scope}".strip()

        if not p_clean or not s_title:
            return cls.UNKNOWN, "Insufficient product or standard title information."

        # 1. Exact phrase match
        if len(p_clean) > 3 and p_clean in target_text:
            return cls.DIRECT_MATCH, f"Exact product match: '{requested_product}' is explicitly covered in standard."

        # 2. Check PPE Domain conflicts (e.g. Helmet vs Foot/Leg, Arms/Hands, Nets, Clothing)
        domain = cls._extract_primary_domain(p_clean)
        if domain in cls.PPE_DOMAIN_MAP:
            domain_info = cls.PPE_DOMAIN_MAP[domain]
            # Check if standard explicitly mentions the domain's product keywords
            has_domain_target = any(kw in s_title for kw in domain_info["keywords"])
            
            # Check if standard explicitly belongs to a conflicting domain
            conflicting_detected = []
            for conflict_domain in domain_info["conflicts"]:
                conflict_keywords = cls.PPE_DOMAIN_MAP.get(conflict_domain, {}).get("keywords", [conflict_domain])
                for ckw in conflict_keywords:
                    # Match conflict keyword in standard title
                    pattern = r"\b" + re.escape(ckw) + r"\b"
                    if re.search(pattern, s_title):
                        conflicting_detected.append(ckw)
                        break

            if has_domain_target:
                return cls.DIRECT_MATCH, f"Standard title specifically covers {domain} protection ('{standard_title}')."

            if conflicting_detected:
                conflict_str = ", ".join(conflicting_detected)
                return cls.MISMATCH, f"Product mismatch: requested product is {domain} protection, but standard addresses {conflict_str} ('{standard_title}')."

        # 3. Check General Product Families (Pipe, Cable, Cement, etc.)
        if domain in cls.PRODUCT_FAMILIES:
            family_info = cls.PRODUCT_FAMILIES[domain]
            has_family_target = any(kw in s_title for kw in family_info["keywords"])
            has_family_related = any(kw in s_title for kw in family_info.get("related", []))
            has_family_conflict = any(re.search(r"\b" + re.escape(kw) + r"\b", s_title) for kw in family_info.get("conflicts", []))

            if has_family_target:
                return cls.DIRECT_MATCH, f"Standard title specifically covers {domain} product line ('{standard_title}')."
            if has_family_related:
                return cls.RELATED_MATCH, f"Standard covers related {domain} components or fittings ('{standard_title}')."
            if has_family_conflict:
                return cls.MISMATCH, f"Product mismatch: standard covers incompatible product domain ('{standard_title}')."

        # 4. Token & Head Noun Check
        p_tokens = set(p_clean.split()) - {"industrial", "safety", "for", "and", "of", "the", "in", "with", "equipment", "protective", "specification"}
        s_tokens = set(s_title.split())

        if p_tokens:
            common = p_tokens.intersection(s_tokens)
            # If all core nouns match or head noun matches
            if len(common) == len(p_tokens):
                return cls.DIRECT_MATCH, f"All core product terms ({', '.join(common)}) match standard title."
            if len(common) > 0 and semantic_similarity >= 0.70:
                return cls.DIRECT_MATCH, f"Core product term ({', '.join(common)}) matches with high semantic similarity ({semantic_similarity:.2f})."
            if len(common) > 0 and semantic_similarity >= 0.50:
                return cls.RELATED_MATCH, f"Partial product match ({', '.join(common)}) with supporting relevance."

        # 5. Semantic similarity based categorization if no direct keywords
        if semantic_similarity >= 0.78:
            return cls.DIRECT_MATCH, f"High semantic similarity ({semantic_similarity:.2f}) indicates product alignment."
        elif semantic_similarity >= 0.52:
            return cls.RELATED_MATCH, f"Moderate semantic similarity ({semantic_similarity:.2f}) indicates related applicability."
        else:
            return cls.MISMATCH, f"Low semantic similarity ({semantic_similarity:.2f}) and absent product head noun in '{standard_title}'."
