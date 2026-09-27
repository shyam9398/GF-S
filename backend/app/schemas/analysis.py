from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AnalysisCreate(BaseModel):
    product_name: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str = Field(
        min_length=1,
    )

    procurement_purpose: str | None = None

    intended_application: str | None = None

    material: str | None = None

    technical_specifications: str | None = None

    performance_requirements: str | None = None

    safety_requirements: str | None = None

    quantity: int | None = Field(
        default=None,
        ge=1,
    )


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: str
    product_name: str
    description: str
    procurement_purpose: str | None
    intended_application: str | None
    material: str | None
    technical_specifications: str | None
    performance_requirements: str | None
    safety_requirements: str | None
    quantity: int | None
    status: str
    created_at: datetime
    updated_at: datetime