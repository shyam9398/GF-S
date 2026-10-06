import asyncio
import json
import logging
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from app.core.database import SessionLocal
from app.models.analysis import ProcurementAnalysis
from app.services.analysis_pipeline_service import AnalysisPipelineService

async def main():
    db = SessionLocal()
    try:
        # Create a realistic test procurement analysis
        analysis = ProcurementAnalysis(
            product_name="Industrial Safety Helmet",
            description="Procurement of protective safety helmets for construction and industrial workers. High-density polyethylene shell with adjustable suspension and chin strap.",
            intended_application="Head protection for construction workers against falling objects and mechanical impact",
            material="High-density polyethylene (HDPE) or polycarbonate",
            technical_specifications="Impact resistance, penetration resistance, electrical insulation up to 440V, adjustable head harness 52-60 cm",
            performance_requirements="Shock absorption test, penetration resistance test, flammability test",
            safety_requirements="Conformity to Indian Standards for industrial safety helmets",
            quantity=500,
            status="CREATED"
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        print(f"Created analysis ID: {analysis.id}")

        service = AnalysisPipelineService(db=db)
        t0 = time.time()
        print("Starting pipeline run...")
        result = await service.run(analysis.id)
        elapsed = time.time() - t0
        print(f"Pipeline finished in {elapsed:.2f} seconds.")

        print("\n=== PIPELINE RESULT SUMMARY ===")
        print(f"Success: {result.get('success')}")
        print(f"Status: {result.get('status')}")
        print(f"Input Summary: {json.dumps(result.get('input_summary'), indent=2)}")
        print(f"Processing Timings: {json.dumps(result.get('processing'), indent=2)}")
        print(f"Errors: {result.get('errors')}")

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
