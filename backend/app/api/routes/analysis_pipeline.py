from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.analysis_result import AnalysisResult
from app.services.analysis_pipeline_service import (
    AnalysisPipelineService,
)


router = APIRouter(
    prefix="/api/analyses",
    tags=["Analysis Pipeline"],
)


# ----------------------------------------------------------------------
# Run complete analysis
# ----------------------------------------------------------------------

@router.post("/{analysis_id}/run")
async def run_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
):
    """
    Execute the complete AI + BIS recommendation pipeline
    and persist the result in PostgreSQL.
    """

    service = AnalysisPipelineService(
        db=db
    )

    try:
        result = await service.run(
            analysis_id
        )

        # --------------------------------------------------------------
        # Pipeline-level failure
        # --------------------------------------------------------------

        if not result.get(
            "success",
            False,
        ):
            stage = result.get(
                "stage"
            )

            if stage == "load_analysis":
                status_code = 404
            else:
                status_code = 500

            raise HTTPException(
                status_code=status_code,
                detail=result,
            )

        # --------------------------------------------------------------
        # Serialize complete pipeline result
        # --------------------------------------------------------------

        result_json = json.dumps(
            result,
            default=str,
            ensure_ascii=False,
        )

        # --------------------------------------------------------------
        # Find existing persisted result
        # --------------------------------------------------------------

        existing = db.execute(
            select(
                AnalysisResult
            ).where(
                AnalysisResult.analysis_id
                == analysis_id
            )
        ).scalar_one_or_none()

        now = datetime.now(
            timezone.utc
        )

        # --------------------------------------------------------------
        # Update existing result
        # --------------------------------------------------------------

        if existing is not None:

            existing.result_json = (
                result_json
            )

            existing.updated_at = now

        # --------------------------------------------------------------
        # Create first result
        # --------------------------------------------------------------

        else:

            existing = AnalysisResult(
                id=str(
                    uuid.uuid4()
                ),
                analysis_id=analysis_id,
                result_json=result_json,
                created_at=now,
                updated_at=now,
            )

            db.add(existing)

        db.commit()

        return result

    except HTTPException:
        # Preserve intentional HTTP errors.
        db.rollback()
        raise

    except Exception as error:
        # --------------------------------------------------------------
        # Unexpected persistence/API failure
        # --------------------------------------------------------------

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail={
                "message": (
                    "The analysis pipeline could not "
                    "complete successfully."
                ),
                "analysis_id": analysis_id,
                "error": str(error),
            },
        )

    finally:
        await service.close()


# ----------------------------------------------------------------------
# Get complete persisted results
# ----------------------------------------------------------------------

@router.get(
    "/{analysis_id}/results"
)
def get_analysis_results(
    analysis_id: str,
    db: Session = Depends(get_db),
):
    """
    Return the complete persisted pipeline result.
    """

    result = db.execute(
        select(
            AnalysisResult
        ).where(
            AnalysisResult.analysis_id
            == analysis_id
        )
    ).scalar_one_or_none()

    if result is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": (
                    "No pipeline result is available "
                    "for this analysis yet."
                ),
                "analysis_id": analysis_id,
            },
        )

    try:
        return json.loads(
            result.result_json
        )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail={
                "message": (
                    "The stored analysis result "
                    "could not be decoded."
                ),
                "analysis_id": analysis_id,
            },
        )


# ----------------------------------------------------------------------
# Get frontend summary
# ----------------------------------------------------------------------

@router.get(
    "/{analysis_id}/results/summary"
)
def get_analysis_result_summary(
    analysis_id: str,
    db: Session = Depends(get_db),
):
    """
    Return only the frontend-friendly recommendation result.
    """

    result = db.execute(
        select(
            AnalysisResult
        ).where(
            AnalysisResult.analysis_id
            == analysis_id
        )
    ).scalar_one_or_none()

    if result is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": (
                    "No pipeline result is available "
                    "for this analysis yet."
                ),
                "analysis_id": analysis_id,
            },
        )

    try:
        stored_result: dict[str, Any] = (
            json.loads(
                result.result_json
            )
        )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail={
                "message": (
                    "The stored analysis result "
                    "could not be decoded."
                ),
                "analysis_id": analysis_id,
            },
        )

    frontend = stored_result.get(
        "frontend"
    )

    if frontend is None:
        raise HTTPException(
            status_code=500,
            detail={
                "message": (
                    "Stored pipeline result does not "
                    "contain a frontend summary."
                ),
                "analysis_id": analysis_id,
            },
        )

    return frontend