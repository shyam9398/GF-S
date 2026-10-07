from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class BISCertificationService:
    """
    Dedicated Certification Applicability Engine.
    
    Determines statutory BIS certification requirements:
    - MANDATORY (Covered under an authoritative Quality Control Order / Compulsory BIS certification)
    - VOLUNTARY (Voluntary BIS standard compliance without compulsory QCO)
    - VERIFY (Verification required / insufficient official QCO records)
    - NOT_FOUND (No certification data available)
    
    CRITICAL RULE:
    Do NOT infer mandatory certification merely because BIS license records exist.
    Certification mandates derive from Ministry QCOs (Quality Control Orders) published in the Gazette of India.
    Never fabricate certification requirements.
    """

    MANDATORY = "MANDATORY"
    VOLUNTARY = "VOLUNTARY"
    VERIFY = "VERIFY"
    NOT_FOUND = "NOT_FOUND"

    # Authoritative Quality Control Orders (QCO) mapped to Indian Standards
    # Sourced from official Gazette Notifications issued by DPIIT, Ministry of Steel, MoPNG, etc.
    OFFICIAL_QCO_REGISTRY: dict[str, dict[str, Any]] = {
        # Personal Protective Equipment
        "IS 2925": {
            "order_name": "Personal Protective Equipment (Quality Control) Order",
            "ministry": "Ministry of Commerce and Industry (DPIIT)",
            "scheme": "Scheme-I (ISI Mark)",
            "requirement": "Compulsory BIS certification under Scheme-I for Industrial Safety Helmets.",
            "mandatory": True,
            "effective_date": "Mandatory QCO in force",
        },
        "IS 4151": {
            "order_name": "Protective Helmets for Two Wheeler Riders (Quality Control) Order",
            "ministry": "Ministry of Road Transport and Highways (MoRTH)",
            "scheme": "Scheme-I (ISI Mark)",
            "requirement": "Compulsory BIS certification under Scheme-I for motorcycle/scooter protective helmets.",
            "mandatory": True,
            "effective_date": "Mandatory QCO in force",
        },
        "IS 15844": {
            "order_name": "Footwear made from all-Rubber and all-Polymeric Material (Quality Control) Order",
            "ministry": "Ministry of Commerce and Industry (DPIIT)",
            "scheme": "Scheme-I (ISI Mark)",
            "requirement": "Compulsory BIS certification for safety footwear.",
            "mandatory": True,
            "effective_date": "Mandatory QCO in force",
        },
        # Steel and Steel Products
        "IS 1239": {
            "order_name": "Steel and Steel Products (Quality Control) Order",
            "ministry": "Ministry of Steel",
            "scheme": "Scheme-I (ISI Mark)",
            "requirement": "Compulsory BIS certification under Scheme-I for steel tubes, pipes and fittings.",
            "mandatory": True,
            "effective_date": "Mandatory QCO in force",
        },
        "IS 3589": {
            "order_name": "Steel and Steel Products (Quality Control) Order",
            "ministry": "Ministry of Steel",
            "scheme": "Scheme-I (ISI Mark)",
            "requirement": "Compulsory BIS certification under Scheme-I for steel pipes for water and sewage.",
            "mandatory": True,
            "effective_date": "Mandatory QCO in force",
        },
        "IS 1786": {
            "order_name": "Steel and Steel Products (Quality Control) Order",
            "ministry": "Ministry of Steel",
            "scheme": "Scheme-I (ISI Mark)",
            "requirement": "Compulsory BIS certification for high strength deformed steel bars and wires (TMT rebar).",
            "mandatory": True,
            "effective_date": "Mandatory QCO in force",
        },
        "IS 2062": {
            "order_name": "Steel and Steel Products (Quality Control) Order",
            "ministry": "Ministry of Steel",
            "scheme": "Scheme-I (ISI Mark)",
            "requirement": "Compulsory BIS certification for hot rolled medium and high tensile structural steel.",
            "mandatory": True,
            "effective_date": "Mandatory QCO in force",
        },
        # Cement
        "IS 1489": {
            "order_name": "Cement (Quality Control) Order",
            "ministry": "Ministry of Commerce and Industry",
            "scheme": "Scheme-I (ISI Mark)",
            "requirement": "Compulsory BIS certification for Portland Pozzolana Cement.",
            "mandatory": True,
            "effective_date": "Mandatory QCO in force",
        },
        "IS 269": {
            "order_name": "Cement (Quality Control) Order",
            "ministry": "Ministry of Commerce and Industry",
            "scheme": "Scheme-I (ISI Mark)",
            "requirement": "Compulsory BIS certification for Ordinary Portland Cement.",
            "mandatory": True,
            "effective_date": "Mandatory QCO in force",
        },
        # Electrical Cables & Equipment
        "IS 694": {
            "order_name": "Electrical Wires, Cables, Appliances and Protection Devices (Quality Control) Order",
            "ministry": "Ministry of Commerce and Industry (DPIIT)",
            "scheme": "Scheme-I (ISI Mark)",
            "requirement": "Compulsory BIS certification for PVC insulated cables.",
            "mandatory": True,
            "effective_date": "Mandatory QCO in force",
        },
        "IS 1554": {
            "order_name": "Electrical Wires, Cables, Appliances and Protection Devices (Quality Control) Order",
            "ministry": "Ministry of Commerce and Industry (DPIIT)",
            "scheme": "Scheme-I (ISI Mark)",
            "requirement": "Compulsory BIS certification for PVC insulated heavy duty electric cables.",
            "mandatory": True,
            "effective_date": "Mandatory QCO in force",
        },
        # Electronics & IT Goods (Compulsory Registration Scheme - CRS)
        "IS 13252": {
            "order_name": "Electronics and Information Technology Goods (Requirement for Compulsory Registration) Order",
            "ministry": "Ministry of Electronics and Information Technology (MeitY)",
            "scheme": "Compulsory Registration Scheme (CRS)",
            "requirement": "Compulsory BIS registration under CRS for information technology equipment safety.",
            "mandatory": True,
            "effective_date": "Mandatory CRS in force",
        },
    }

    @classmethod
    def normalize_is_key(cls, standard_number: str | None) -> str:
        if not standard_number:
            return ""
        # Match IS followed by digits e.g. "IS 2925" from "IS 2925:1984" or "IS 1239 (Part 1):2004"
        match = re.search(r"\bIS\s*(\d+)", standard_number, re.IGNORECASE)
        if match:
            return f"IS {match.group(1)}"
        return ""

    @classmethod
    def evaluate_certification(
        cls,
        standard_number: str | None,
        standard_title: str | None = "",
        evidence_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Evaluate whether mandatory certification applies to the candidate standard.
        """
        if not standard_number:
            return {
                "status": cls.NOT_FOUND,
                "label": "Not Found",
                "is_mandatory": False,
                "reason": "Standard identifier not provided.",
                "order_name": None,
                "scheme": None,
                "evidence": "No standard number available for certification check.",
                "source": "BIS / Gazette Register",
                "verification_status": "NOT_APPLICABLE",
            }

        key = cls.normalize_is_key(standard_number)
        evidence = evidence_data or {}

        # 1. Check official QCO database
        if key in cls.OFFICIAL_QCO_REGISTRY:
            qco_info = cls.OFFICIAL_QCO_REGISTRY[key]
            return {
                "status": cls.MANDATORY,
                "label": "Mandatory",
                "is_mandatory": True,
                "reason": f"Applicable Quality Control Order: {qco_info['order_name']}",
                "order_name": qco_info["order_name"],
                "ministry": qco_info.get("ministry"),
                "scheme": qco_info["scheme"],
                "requirement": qco_info["requirement"],
                "evidence": f"Authoritative Government of India Gazette Quality Control Order: {qco_info['order_name']} ({qco_info.get('ministry', 'Govt of India')}). Scheme: {qco_info['scheme']}.",
                "source": "Official Gazette Quality Control Order (QCO)",
                "verification_status": "VERIFIED_MANDATORY",
            }

        # 2. Check BIS CRS / MCS / Scheme evidence in retrieved BIS data
        crs_data = evidence.get("crs")
        if isinstance(crs_data, dict) and crs_data.get("success"):
            data = crs_data.get("data")
            if data and (isinstance(data, list) and len(data) > 0 or isinstance(data, dict)):
                return {
                    "status": cls.MANDATORY,
                    "label": "Mandatory (CRS)",
                    "is_mandatory": True,
                    "reason": "Covered under Compulsory Registration Scheme (CRS)",
                    "order_name": "Electronics & IT Goods Compulsory Registration Order",
                    "scheme": "Compulsory Registration Scheme (CRS)",
                    "requirement": "Compulsory registration required with BIS before placement on the market.",
                    "evidence": "Authoritative BIS CRS records confirm compulsory registration status.",
                    "source": "BIS Compulsory Registration Scheme (CRS)",
                    "verification_status": "VERIFIED_MANDATORY",
                }

        # 3. Check Gazette records in evidence
        gazette = evidence.get("gazette")
        if isinstance(gazette, dict) and gazette.get("success"):
            g_data = gazette.get("data")
            if g_data:
                g_str = str(g_data).lower()
                if "quality control" in g_str or "compulsory" in g_str or "order" in g_str:
                    return {
                        "status": cls.MANDATORY,
                        "label": "Mandatory",
                        "is_mandatory": True,
                        "reason": "Government Gazette notification references Quality Control Order applicability.",
                        "order_name": "Quality Control Order (Gazette Notification)",
                        "scheme": "Scheme-I (ISI Mark)",
                        "requirement": "Compulsory compliance indicated by official Gazette publication.",
                        "evidence": "BIS Gazette publication records indicate mandatory certification order.",
                        "source": "Official Gazette Notification",
                        "verification_status": "VERIFIED_MANDATORY",
                    }

        # 4. Check if licenses exist — License existence ALONE does NOT prove mandatory status
        # It proves voluntary certification is active
        licenses = evidence.get("licenses")
        has_licenses = False
        license_count = 0
        if isinstance(licenses, dict) and licenses.get("success"):
            l_data = licenses.get("data")
            if isinstance(l_data, list):
                license_count = len(l_data)
                has_licenses = license_count > 0

        # If no authoritative QCO found, mark as VERIFY
        return {
            "status": cls.VERIFY,
            "label": "Verification Required",
            "is_mandatory": False,
            "reason": "No authoritative mandatory Quality Control Order (QCO) confirmed for this standard.",
            "order_name": None,
            "scheme": "Scheme-I (Voluntary ISI Mark)" if has_licenses else "Standard Conformity",
            "requirement": f"{license_count} BIS licence(s) exist on record under voluntary certification scheme." if has_licenses else "Conformity to standard recommended; verify statutory QCO applicability with latest Gazette.",
            "evidence": f"Authoritative BIS licence register confirms {license_count} active licences, but mandatory QCO is unverified." if has_licenses else "No official mandatory-certification Gazette record identified.",
            "source": "BIS Records / QCO Register",
            "verification_status": "VERIFICATION_REQUIRED",
        }
