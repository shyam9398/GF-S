import asyncio
import sys
import logging
from app.bis.compatibility_service import BISCompatibilityService
from app.bis.certification_service import BISCertificationService
from app.bis.applicability_service import BISApplicabilityService
from app.bis.recommendation_service import BISRecommendationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TEST_E2E")

async def run_tests():
    compat = BISCompatibilityService()
    cert = BISCertificationService()
    applicability = BISApplicabilityService()
    recommender = BISRecommendationService()

    print("\n" + "="*70)
    print("RUNNING E2E VALIDATION SUITE FOR PS 26108")
    print("="*70)

    # -------------------------------------------------------------------------
    # TEST 1: Industrial Safety Helmet - Role Gate & Subtype Conflict
    # -------------------------------------------------------------------------
    print("\n--- TEST 1: Industrial Safety Helmet Classification ---")
    procurement_helmet = {
        "product_name": "Industrial Safety Helmet",
        "description": "Industrial safety helmet with HDPE shell, adjustable nape strap and shock absorption for construction workers",
        "intended_application": "Construction site worker head protection",
        "technical_specifications": "HDPE shell, electrical insulation, chin strap",
    }

    test_helmet_standards = [
        {"standard_number": "IS 2925:1984", "title": "Specification for Industrial Safety Helmets", "status": "Active"},
        {"standard_number": "IS 4151:2015", "title": "Protective Helmets for Motorcycle Riders - Specification", "status": "Active"},
        {"standard_number": "IS 18808:2024", "title": "Helmets for Pedal Cyclists and Users of Skateboards and Roller Skates", "status": "Active"},
        {"standard_number": "IS 9695:1980", "title": "Methods for Sampling of Helmets", "status": "Active"},
        {"standard_number": "IS 17286:2019", "title": "Headforms for Use in the Testing of Protective Helmets", "status": "Active"},
    ]

    evaluated_helmet = []
    for std in test_helmet_standards:
        eval_res = applicability.evaluate_candidate(procurement_helmet, std, semantic_score=0.90)
        evaluated_helmet.append(eval_res)
        print(f"Standard: {std['standard_number']:15} | Role: {eval_res['standard_role']:22} | "
              f"Compat: {eval_res['compatibility']:25} | Class: {eval_res['classification']:20} | Score: {eval_res['applicability_score']}")

    # Assertions for Test 1
    is_2925 = next(x for x in evaluated_helmet if "2925" in x["standard_number"])
    is_4151 = next(x for x in evaluated_helmet if "4151" in x["standard_number"])
    is_18808 = next(x for x in evaluated_helmet if "18808" in x["standard_number"])
    is_9695 = next(x for x in evaluated_helmet if "9695" in x["standard_number"])
    is_17286 = next(x for x in evaluated_helmet if "17286" in x["standard_number"])

    assert is_2925["classification"] == "PRIMARY_APPLICABLE", f"IS 2925 should be PRIMARY_APPLICABLE, got {is_2925['classification']}"
    assert is_4151["classification"] != "PRIMARY_APPLICABLE", f"IS 4151 motorcycle helmet must NOT be PRIMARY_APPLICABLE, got {is_4151['classification']}"
    assert is_18808["classification"] != "PRIMARY_APPLICABLE", f"IS 18808 bicycle helmet must NOT be PRIMARY_APPLICABLE, got {is_18808['classification']}"
    assert is_9695["standard_role"] == "SAMPLING_METHOD", f"IS 9695 must have SAMPLING_METHOD role"
    assert is_9695["classification"] != "PRIMARY_APPLICABLE", f"IS 9695 must NOT be primary, got {is_9695['classification']}"
    assert is_17286["standard_role"] == "HEADFORM", f"IS 17286 must have HEADFORM role"
    assert is_17286["classification"] != "PRIMARY_APPLICABLE", f"IS 17286 must NOT be primary, got {is_17286['classification']}"
    print(">>> TEST 1 PASSED: Strict Role Gate & Subtype Filter correctly isolate IS 2925 as the only Primary Standard!")

    # -------------------------------------------------------------------------
    # TEST 2: Steel Pipe for Drinking Water vs Drinking Water Quality
    # -------------------------------------------------------------------------
    print("\n--- TEST 2: Steel Pipe for Drinking Water ---")
    procurement_pipe = {
        "product_name": "Mild Steel Pipes for Drinking Water Supply",
        "description": "Mild steel tubes and pipes for carrying potable water in municipal distribution pipeline",
        "intended_application": "Water conveyance infrastructure",
    }

    test_pipe_standards = [
        {"standard_number": "IS 1239 (Part 1):2004", "title": "Steel Tubes, Tubulars and Other Wrought Steel Fittings - Specification", "status": "Active"},
        {"standard_number": "IS 3589:2001", "title": "Steel Pipes for Water and Sewage - Specification", "status": "Active"},
        {"standard_number": "IS 10500:2012", "title": "Drinking Water - Specification", "status": "Active"},
    ]

    evaluated_pipe = []
    for std in test_pipe_standards:
        eval_res = applicability.evaluate_candidate(procurement_pipe, std, semantic_score=0.85)
        evaluated_pipe.append(eval_res)
        print(f"Standard: {std['standard_number']:25} | Role: {eval_res['standard_role']:22} | "
              f"Compat: {eval_res['compatibility']:25} | Class: {eval_res['classification']:20} | Score: {eval_res['applicability_score']}")

    is_1239 = next(x for x in evaluated_pipe if "1239" in x["standard_number"])
    is_10500 = next(x for x in evaluated_pipe if "10500" in x["standard_number"])
    assert is_1239["classification"] in ("PRIMARY_APPLICABLE", "DIRECTLY_APPLICABLE"), "IS 1239 must be primary for steel pipes"
    assert is_10500["classification"] != "PRIMARY_APPLICABLE", f"IS 10500 (water quality) must NOT be primary for steel pipes! Got {is_10500['classification']}"
    print(">>> TEST 2 PASSED: IS 10500 is filtered out of Primary for steel pipes!")

    # -------------------------------------------------------------------------
    # TEST 3: Gazette Quality Control Order (QCO) Verification
    # -------------------------------------------------------------------------
    print("\n--- TEST 3: Gazette QCO Mandatory Status Verification ---")
    qco_tests = [
        ("IS 2925", "MANDATORY"),
        ("IS 4151", "MANDATORY"),
        ("IS 1239", "MANDATORY"),
        ("IS 13252", "MANDATORY"),
        ("IS 99999", "VERIFY"),
    ]

    for is_num, expected in qco_tests:
        qco_info = cert.evaluate_certification(is_num, "")
        order_str = str(qco_info.get('order_name') or 'N/A')
        print(f"IS: {is_num:10} | QCO Status: {qco_info['status']:12} | Order: {order_str[:40]}")
        assert qco_info["status"] == expected, f"Expected {expected} for {is_num}, got {qco_info['status']}"
    print(">>> TEST 3 PASSED: QCO Mandatory Gazette registry verified accurately!")

    # -------------------------------------------------------------------------
    # TEST 4: Withdrawn / Superseded Lifecycle Check
    # -------------------------------------------------------------------------
    print("\n--- TEST 4: Withdrawn / Superseded Status Verification ---")
    withdrawn_std = {
        "standard_number": "IS 2925:1975",
        "title": "Industrial Safety Helmets (Old)",
        "status": "Withdrawn",
        "withdraw_status": 1,
        "superseded_by": "IS 2925:1984"
    }
    withdrawn_eval = applicability.evaluate_candidate(procurement_helmet, withdrawn_std, semantic_score=0.95)
    print(f"Withdrawn Standard Class: {withdrawn_eval['classification']} | Lifecycle: {withdrawn_eval.get('lifecycle_status')}")
    assert withdrawn_eval["classification"] in ("NEEDS_VERIFICATION", "NOT_APPLICABLE"), "Withdrawn standards must never be PRIMARY_APPLICABLE!"
    print(">>> TEST 4 PASSED: Withdrawn standard prevented from becoming Primary Applicable!")

    # -------------------------------------------------------------------------
    # TEST 5: 6-Way Separation in build_frontend_result
    # -------------------------------------------------------------------------
    print("\n--- TEST 5: 6-Way Separation Verification ---")
    mock_report = {
        "recommendation_result": {
            "recommendations": evaluated_helmet
        }
    }
    frontend_out = recommender.build_frontend_result(mock_report)
    print(f"Primary Applicable count: {len(frontend_out['primary_applicable'])}")
    print(f"Normative References count: {len(frontend_out['normative_references'])}")
    print(f"Allied Standards count: {len(frontend_out['allied_standards'])}")
    print(f"Supporting count: {len(frontend_out['related_supporting'])}")
    print(f"Needs Verification count: {len(frontend_out['needs_verification'])}")
    print(f"Not Applicable count: {len(frontend_out['not_applicable'])}")

    assert len(frontend_out["primary_applicable"]) == 1, f"Expected exactly 1 primary standard, got {len(frontend_out['primary_applicable'])}"
    assert frontend_out["primary_applicable"][0]["standard_number"] == "IS 2925:1984"
    print(">>> TEST 5 PASSED: 6-way separation isolated IS 2925 as the single primary standard!")

    print("\n" + "="*70)
    print("ALL 5 E2E TESTS PASSED SUCCESSFULLY!")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(run_tests())
