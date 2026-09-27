import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProcurementAnalysis(Base):
    __tablename__ = "procurement_analyses"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    procurement_purpose: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    intended_application: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    material: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    technical_specifications: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    performance_requirements: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    safety_requirements: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    quantity: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="CREATED",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )