from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class BISCompatibilityService:
    """
    Evaluates standard role classification and product compatibility.
    
    CRITICAL SIH 2026 GATES:
    1. Standard Role Gate:
       Only PRODUCT_SPECIFICATION can become PRIMARY_APPLICABLE.
       Test methods, sampling methods, headforms, material specs, components,
       and related products CANNOT become PRIMARY_APPLICABLE.
    2. Product Compatibility Gate:
       A candidate standard must directly cover the specific product being procured.
       Generic keyword overlaps (e.g. motorcycle helmet for industrial helmet,
       or drinking water quality for steel water pipe) are strictly prevented.
    """

    # Product Compatibility decisions
    DIRECT_MATCH = "DIRECT_MATCH"
    RELATED_MATCH = "RELATED_MATCH"
    MISMATCH = "MISMATCH"
    UNKNOWN = "UNKNOWN"

    # Standard Roles
    ROLE_PRODUCT_SPECIFICATION = "PRODUCT_SPECIFICATION"
    ROLE_TEST_METHOD = "TEST_METHOD"
    ROLE_SAMPLING_METHOD = "SAMPLING_METHOD"
    ROLE_HEADFORM = "HEADFORM"
    ROLE_MATERIAL_SPECIFICATION = "MATERIAL_SPECIFICATION"
    ROLE_COMPONENT_SPECIFICATION = "COMPONENT_SPECIFICATION"
    ROLE_INSTALLATION_STANDARD = "INSTALLATION_STANDARD"
    ROLE_TERMINOLOGY = "TERMINOLOGY"
    ROLE_SAFETY_GUIDE = "SAFETY_GUIDE"
    ROLE_MEASUREMENT_METHOD = "MEASUREMENT_METHOD"
    ROLE_RELATED_PRODUCT = "RELATED_PRODUCT"
    ROLE_OTHER = "OTHER"

    # Conflicting body/product domains for personal protective equipment
    PPE_DOMAIN_MAP = {
        "head": {
            "keywords": ["helmet", "helmets", "hard hat", "hard hats", "headgear", "head protection", "bump cap"],
            "conflicts": ["foot", "leg", "arm", "hand", "clothing", "net", "fall arrest", "eye", "respiratory", "hearing", "pipe", "cable", "cement", "chair", "furniture"],
        },
        "foot": {
            "keywords": ["foot", "feet", "leg", "legs", "footwear", "boot", "boots", "shoe", "shoes"],
            "conflicts": ["head", "helmet", "arm", "hand", "net", "clothing", "eye", "hearing", "pipe", "cable", "cement", "chair"],
        },
        "hand": {
            "keywords": ["arm", "arms", "hand", "hands", "glove", "gloves", "mitten", "mittens", "sleeve"],
            "conflicts": ["head", "helmet", "foot", "leg", "net", "clothing", "eye", "hearing", "pipe", "cable", "cement", "chair"],
        },
        "eye_face": {
            "keywords": ["eye", "face shield", "faceshield", "goggle", "goggles", "spectacle"],
            "conflicts": ["foot", "leg", "arm", "hand", "net", "clothing", "pipe", "cable", "chair"],
        },
    }

    PRODUCT_FAMILIES = {
        "pipe": {
            "keywords": ["pipe", "pipes", "piping", "tube", "tubes", "tubing", "conduit"],
            "related": ["fitting", "fittings", "flange", "flanges", "valve", "valves", "joint", "joints", "gasket"],
            "conflicts": ["helmet", "shoe", "boot", "cable", "cement", "battery", "textile", "chair", "furniture"],
        },
        "cable": {
            "keywords": ["cable", "cables", "conductor", "conductors", "wire", "wires", "cord", "cords"],
            "related": ["insulation", "sheath", "connector", "terminal", "joint"],
            "conflicts": ["pipe", "helmet", "shoe", "boot", "cement", "net", "chair", "furniture"],
        },
        "furniture": {
            "keywords": ["chair", "chairs", "desk", "desks", "table", "tables", "cabinet", "seating", "furniture"],
            "related": ["caster", "armrest", "upholstery"],
            "conflicts": ["helmet", "pipe", "cable", "shoe", "cement", "net"],
        },
        "cement": {
            "keywords": ["cement", "cements", "clinker", "concrete"],
            "related": ["mortar", "aggregate", "sand", "admixture"],
            "conflicts": ["pipe", "cable", "helmet", "shoe", "net", "steel", "chair"],
        },
    }

    # Distinct sub-types for product differentiation (prevents motorcycle helmet -> industrial helmet, etc.)
    PRODUCT_SUBTYPES = {
        "industrial_safety_helmet": {
            "req_patterns": [r"industrial\s+safety\s+helmet", r"industrial\s+helmet", r"construction\s+helmet", r"hard\s+hat"],
            "match_patterns": [r"industrial\s+safety\s+helmet", r"industrial\s+protective\s+helmet"],
            "conflict_patterns": [
                (r"motorcycle|scooter|two-wheeler|two wheeler", "Motorcycle/Scooter helmet (not industrial protective helmet)"),
                (r"bicycle|skateboard|roller skate|sports", "Bicycle/Skater sports helmet (not industrial safety helmet)"),
                (r"firefighter|fire fighting|fire-fighting", "Firefighter helmet (not standard industrial safety helmet)"),
            ],
        },
        "steel_water_pipe": {
            "req_patterns": [r"steel\s+(?:pipe|tube|pipes|tubes).*water", r"water.*steel\s+(?:pipe|tube|pipes|tubes)"],
            "match_patterns": [
                r"steel\s+(?:tubes?|pipes?).*(?:water|gas|steam|sewage)",
                r"(?:tubes?|pipes?).*steel.*(?:water|gas|steam)",
                r"mild\s+steel\s+tubes",
            ],
            "conflict_patterns": [
                (r"drinking\s+water\s+-\s+specification|quality\s+of\s+drinking\s+water", "Drinking water quality specification (IS 10500 is a water quality standard, not a steel pipe product)"),
                (r"polyethylene|pvc|plastic|upvc|hdpe|cpvc", "Plastic/PVC pipe material mismatch (procurement is for steel pipe)"),
                (r"cast\s+iron|ductile\s+iron", "Cast/Ductile iron material mismatch (procurement is for steel pipe)"),
                (r"concrete\s+pipe|asbestos", "Concrete pipe material mismatch (procurement is for steel pipe)"),
            ],
        },
        "office_chair": {
            "req_patterns": [r"office\s+chair", r"revolving\s+chair", r"workstation\s+chair", r"ergonomic\s+chair"],
            "match_patterns": [r"office\s+chair", r"revolving\s+chair", r"work\s+chair", r"office\s+furniture\s*-\s*chairs"],
            "conflict_patterns": [
                (r"helmet|pipe|cable|footwear|cement|steel\s+bar", "Entirely unrelated product category"),
            ],
        },
    }

    @staticmethod
    def _clean(text: Any) -> str:
        if not text:
            return ""
        return " ".join(str(text).strip().lower().split())

    @classmethod
    def classify_standard_role(
        cls,
        standard_title: str,
        standard_scope: str = "",
    ) -> tuple[str, str]:
        """
        Classifies the standard into its functional role.
        Returns: (role, reason)
        Only ROLE_PRODUCT_SPECIFICATION can qualify as PRIMARY_APPLICABLE.
        """
        title = cls._clean(standard_title)
        scope = cls._clean(standard_scope)
        text = f"{title} {scope}".strip()

        # 1. HEADFORM (highest priority check for helmet testing apparatus)
        if re.search(r"\bheadforms?\b", title) or re.search(r"\btest\s+headforms?\b", title):
            return (
                cls.ROLE_HEADFORM,
                "Standard specifies headforms/testing apparatus, not a finished product.",
            )

        # 2. SAMPLING METHOD
        if re.search(r"\b(?:methods?\s+(?:for|of)\s+sampling|sampling\s+(?:of|methods?|procedures?))\b", title):
            return (
                cls.ROLE_SAMPLING_METHOD,
                "Standard specifies statistical sampling/lot inspection methods, not product manufacturing specifications.",
            )

        # 3. TEST METHOD / METHOD OF TEST
        if re.search(r"\b(?:methods?\s+of\s+tests?|methods?\s+for\s+tests?|test\s+methods?|testing\s+of|determination\s+of|measurement\s+of\s+(?:shock|impact|penetration|flammability))\b", title):
            return (
                cls.ROLE_TEST_METHOD,
                "Standard specifies testing procedures and test methods, not the product specification.",
            )

        # 4. TERMINOLOGY / GLOSSARY
        if re.search(r"\b(?:glossary\s+of|vocabulary|terminology|definitions?\s+of)\b", title):
            return (
                cls.ROLE_TERMINOLOGY,
                "Standard defines vocabulary and technical terminology, not product specifications.",
            )

        # 5. SAFETY GUIDE / CODE OF PRACTICE FOR SELECTION, CARE & USE
        if re.search(r"\b(?:guide\s+(?:for|on)\s+selection|guide\s+(?:for|on)\s+(?:care|use|maintenance)|guidelines\s+for|recommendations\s+for)\b", title):
            return (
                cls.ROLE_SAFETY_GUIDE,
                "Standard provides guidelines on selection, care and maintenance, not product manufacturing specifications.",
            )

        # 6. INSTALLATION STANDARD / CODE OF PRACTICE FOR LAYING
        if re.search(r"\b(?:code\s+of\s+practice\s+for\s+(?:laying|installation|erecting|fixing)|installation\s+of)\b", title):
            return (
                cls.ROLE_INSTALLATION_STANDARD,
                "Standard specifies code of practice for installation and laying, not product manufacturing specifications.",
            )

        # 7. COMPONENT SPECIFICATION
        if re.search(r"\b(?:visors?|eye\s+protectors?|chin\s*straps?|buckles?|harnesses?|flanges?|valves?|gaskets?|fasteners?)\b", title) or (
            re.search(r"\bfittings?\b", title) and not re.search(r"\b(?:tubes?|pipes?|helmets?)\b", title)
        ):
            return (
                cls.ROLE_COMPONENT_SPECIFICATION,
                "Standard specifies a component/accessory/fitting, not the primary end-product.",
            )

        # 8. MATERIAL SPECIFICATION
        if re.search(r"\b(?:materials?\s+for|raw\s+materials?|moulding\s+materials?|compounds?\s+for|resins?\s+for|grades?\s+of\s+steel|sheets?\s+for)\b", title):
            return (
                cls.ROLE_MATERIAL_SPECIFICATION,
                "Standard specifies raw material grades or chemical compounds, not the end-product specification.",
            )

        # 9. MEASUREMENT METHOD
        if re.search(r"\b(?:methods?\s+of\s+measurement|measurement\s+of\s+dimensions)\b", title):
            return (
                cls.ROLE_MEASUREMENT_METHOD,
                "Standard specifies measurement techniques, not product specifications.",
            )

        # 10. PRODUCT SPECIFICATION
        if (
            re.search(r"\bspecification\s+for\b", title)
            or re.search(r"\b-\s*specification\b", title)
            or re.search(r"\bspecification\b", title)
            or re.search(r"\brequirements?\s+for\b", title)
        ):
            return (
                cls.ROLE_PRODUCT_SPECIFICATION,
                "Standard directly specifies the product requirements and quality parameters.",
            )

        # Default fallback
        return (
            cls.ROLE_PRODUCT_SPECIFICATION if len(title.split()) <= 6 else cls.ROLE_OTHER,
            "Standard describes general technical requirements.",
        )

    @classmethod
    def evaluate_compatibility(
        cls,
        requested_product: str,
        standard_title: str,
        standard_scope: str = "",
        semantic_similarity: float = 0.0,
    ) -> tuple[str, str, str]:
        """
        Determine product compatibility between requested product and candidate standard.
        Returns:
            (compatibility, standard_role, reason)
            compatibility: DIRECT_MATCH | RELATED_MATCH | MISMATCH | UNKNOWN
            standard_role: Role enum string
            reason: Human-readable explanation
        """
        p_clean = cls._clean(requested_product)
        s_title = cls._clean(standard_title)
        s_scope = cls._clean(standard_scope)
        target_text = f"{s_title} {s_scope}".strip()

        if not p_clean or not s_title:
            return cls.UNKNOWN, cls.ROLE_OTHER, "Insufficient product or standard title information."

        # Step 1: Classify standard role
        standard_role, role_reason = cls.classify_standard_role(s_title, s_scope)

        # Step 2: Check Subtype Specializations (e.g. Industrial Safety Helmet vs Motorcycle Helmet)
        for sub_id, cfg in cls.PRODUCT_SUBTYPES.items():
            req_matched = any(re.search(p, p_clean) for p in cfg["req_patterns"])
            if req_matched:
                # Check conflicts first
                for conflict_pat, conflict_reason in cfg.get("conflict_patterns", []):
                    if re.search(conflict_pat, s_title):
                        return (
                            cls.MISMATCH,
                            standard_role if standard_role != cls.ROLE_PRODUCT_SPECIFICATION else cls.ROLE_RELATED_PRODUCT,
                            f"Product scope mismatch: {conflict_reason} ('{standard_title}').",
                        )

                # Check explicit direct match patterns
                direct_matched = any(re.search(p, s_title) for p in cfg.get("match_patterns", []))
                if direct_matched:
                    if standard_role == cls.ROLE_PRODUCT_SPECIFICATION:
                        return (
                            cls.DIRECT_MATCH,
                            standard_role,
                            f"Direct product match: standard specifies the exact requested product '{requested_product}'.",
                        )
                    else:
                        return (
                            cls.RELATED_MATCH,
                            standard_role,
                            f"Standard relates directly to '{requested_product}', but serves as a {standard_role.replace('_', ' ').title()} ({role_reason}).",
                        )

        # Step 3: Exact phrase match
        if len(p_clean) > 3 and p_clean in s_title:
            if standard_role == cls.ROLE_PRODUCT_SPECIFICATION:
                return cls.DIRECT_MATCH, standard_role, f"Exact product match: '{requested_product}' is explicitly covered in standard."
            else:
                return cls.RELATED_MATCH, standard_role, f"Matches product '{requested_product}', but functions as a {standard_role.replace('_', ' ').title()} ({role_reason})."

        # Step 4: Check Cross-Domain Conflicts (PPE domains, pipes, cables, furniture)
        for domain, d_info in cls.PPE_DOMAIN_MAP.items():
            req_in_domain = any(kw in p_clean for kw in d_info["keywords"])
            if req_in_domain:
                # Standard has conflict with requested domain
                for conflict_kw in d_info["conflicts"]:
                    if re.search(r"\b" + re.escape(conflict_kw) + r"\b", s_title):
                        return (
                            cls.MISMATCH,
                            standard_role,
                            f"Product domain mismatch: requested product is {domain} protection, but standard addresses {conflict_kw} ('{standard_title}').",
                        )

        for family, f_info in cls.PRODUCT_FAMILIES.items():
            req_in_family = any(kw in p_clean for kw in f_info["keywords"])
            if req_in_family:
                for conflict_kw in f_info["conflicts"]:
                    if re.search(r"\b" + re.escape(conflict_kw) + r"\b", s_title):
                        return (
                            cls.MISMATCH,
                            standard_role,
                            f"Product domain mismatch: requested product belongs to {family} category, but standard covers conflicting category {conflict_kw} ('{standard_title}').",
                        )

        # Step 5: Token Overlap Check
        p_tokens = set(p_clean.split()) - {"industrial", "safety", "for", "and", "of", "the", "in", "with", "equipment", "protective", "specification"}
        s_tokens = set(s_title.split())

        if p_tokens:
            common = p_tokens.intersection(s_tokens)
            if len(common) == len(p_tokens):
                if standard_role == cls.ROLE_PRODUCT_SPECIFICATION:
                    return cls.DIRECT_MATCH, standard_role, f"All core product terms ({', '.join(common)}) match standard title."
                else:
                    return cls.RELATED_MATCH, standard_role, f"Core product terms match, but standard functions as a {standard_role.replace('_', ' ').title()} ({role_reason})."

            if len(common) > 0 and semantic_similarity >= 0.70:
                if standard_role == cls.ROLE_PRODUCT_SPECIFICATION:
                    return cls.DIRECT_MATCH, standard_role, f"Core product term ({', '.join(common)}) matches with high semantic similarity ({semantic_similarity:.2f})."
                else:
                    return cls.RELATED_MATCH, standard_role, f"Core term matches, but standard functions as {standard_role.replace('_', ' ').title()}."

            if len(common) > 0 and semantic_similarity >= 0.40:
                return cls.RELATED_MATCH, standard_role, f"Partial product match ({', '.join(common)}) with supporting relevance."

        # Step 6: Semantic similarity fallback
        if semantic_similarity >= 0.78:
            if standard_role == cls.ROLE_PRODUCT_SPECIFICATION:
                return cls.DIRECT_MATCH, standard_role, f"High semantic similarity ({semantic_similarity:.2f}) indicates product alignment."
            else:
                return cls.RELATED_MATCH, standard_role, f"High semantic similarity ({semantic_similarity:.2f}), but standard functions as {standard_role.replace('_', ' ').title()}."
        elif semantic_similarity >= 0.50:
            return cls.RELATED_MATCH, standard_role, f"Moderate semantic similarity ({semantic_similarity:.2f}) indicates related applicability."
        else:
            return cls.MISMATCH, standard_role, f"Product scope mismatch: standard does not address requested product '{requested_product}'."
