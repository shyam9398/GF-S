from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.analysis import ProcurementAnalysis
from app.schemas.analysis import AnalysisCreate, AnalysisResponse


router = APIRouter()


# ------------------------------------------------------------------
# Create Analysis
# ------------------------------------------------------------------

@router.post(
    "",
    response_model=AnalysisResponse,
)
def create_analysis(
    data: AnalysisCreate,
    db: Session = Depends(get_db),
):
    analysis = ProcurementAnalysis(
        product_name=data.product_name,
        description=data.description,
        procurement_purpose=data.procurement_purpose,
        intended_application=data.intended_application,
        material=data.material,
        technical_specifications=data.technical_specifications,
        performance_requirements=data.performance_requirements,
        safety_requirements=data.safety_requirements,
        quantity=data.quantity,
        status="CREATED",
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return analysis


# ------------------------------------------------------------------
# List Analyses
# ------------------------------------------------------------------

@router.get(
    "",
    response_model=list[AnalysisResponse],
)
def list_analyses(
    db: Session = Depends(get_db),
):
    statement = (
        select(ProcurementAnalysis)
        .order_by(
            ProcurementAnalysis.created_at.desc()
        )
    )

    analyses = db.execute(statement).scalars().all()

    return analyses


# ------------------------------------------------------------------
# Get Single Analysis
# ------------------------------------------------------------------

@router.get(
    "/{analysis_id}",
    response_model=AnalysisResponse,
)
def get_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
):
    analysis = db.get(
        ProcurementAnalysis,
        analysis_id,
    )

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    return analysis