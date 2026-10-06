import asyncio
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from app.core.database import SessionLocal
from app.models.analysis import ProcurementAnalysis
from app.services.analysis_pipeline_service import AnalysisPipelineService

async def main():
    db = SessionLocal()
    try:
        analysis = ProcurementAnalysis(
            product_name="Steel Pipe for Drinking Water",
            description="Procurement of longitudinally submerged arc welded (LSAW) or seamless steel pipes for potable water transmission and distribution mains. Cement mortar lining internally and 3-layer polyethylene coating externally.",
            intended_application="Municipal potable drinking water distribution and supply lines under pressure",
            material="Carbon steel grade Fe 410 or equivalent",
            technical_specifications="Nominal diameter DN 300 to DN 1200, pressure rating PN 16, hydraulic test pressure 2.5 MPa, socket and spigot joints with rubber gasket",
            performance_requirements="Hydrostatic pressure test, tensile test, bend test, flattening test, adhesion test for coating",
            safety_requirements="Non-toxic internal lining suitable for human drinking water contact",
            quantity=1200,
            status="CREATED"
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        print(f"Created analysis ID: {analysis.id}")

        service = AnalysisPipelineService(db=db)
        t0 = time.time()
        print("Starting pipeline run for Steel Pipe...")
        result = await service.run(analysis.id)
        elapsed = time.time() - t0
        print(f"Pipeline finished in {elapsed:.2f} seconds.")

        print("\n=== PIPELINE RESULT SUMMARY ===")
        print(f"Success: {result.get('success')}")
        print(f"Status: {result.get('status')}")
        print(f"Input Summary: {json.dumps(result.get('input_summary'), indent=2)}")
        print(f"Processing Timings: {json.dumps(result.get('processing'), indent=2)}")

        standards = result.get("recommended_standards", [])
        print(f"\nRecommended Standards Count: {len(standards)}")
        for i, s in enumerate(standards[:5], 1):
            print(f"\n--- Standard {i} ---")
            print(f"Number: {s.get('standard_number')}")
            print(f"Title: {s.get('title') or s.get('standard_name')}")
            print(f"Classification: {s.get('human_classification') or s.get('classification')}")
            print(f"Applicability Score: {s.get('applicability_score')}%")
            print(f"Why Recommended: {s.get('why_recommended')[:2]}")
            print(f"Evidence: {s.get('evidence')[:2]}")
            print(f"Source URL: {s.get('source_url')}")
            print(f"Revision: {s.get('revision')}")

        await service.close()

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
