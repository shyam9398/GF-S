from app.ai.gemini_service import analyze_procurement_requirement


sample_text = """
The department intends to procure 1,000 industrial safety
helmets for personnel engaged in construction, maintenance,
civil works and related site activities.

The helmets should provide protection against impact hazards
associated with falling objects.

The helmet should have a durable shell, internal harness or
suspension arrangement, adjustable head size and secure
retention during normal work activities.

The supplier should provide technical documentation, test
reports and applicable conformity or certification evidence.
"""


try:
    result = analyze_procurement_requirement(
        sample_text
    )

    print("\n========== GEMINI ANALYSIS ==========\n")

    for key, value in result.items():
        print(f"{key}: {value}")

    print("\n========== SUCCESS ==========\n")

except Exception as error:
    print("\n========== GEMINI FAILED ==========\n")
    print(type(error).__name__)
    print(error)