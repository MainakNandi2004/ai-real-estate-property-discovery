from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ProjectImage(Base):
    __tablename__ = "project_images"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    caption: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="images")


class ConfigurationFloorPlan(Base):
    __tablename__ = "configuration_floor_plans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    configuration_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("property_configurations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    caption: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")

    configuration: Mapped["PropertyConfiguration"] = relationship(back_populates="floor_plans")


class ProjectNearbyPlace(Base):
    __tablename__ = "project_nearby_places"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    place_type: Mapped[str | None] = mapped_column(String(60), index=True)
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    notes: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")

    project: Mapped["Project"] = relationship(back_populates="nearby_places")


class ProjectReraEntry(Base):
    __tablename__ = "project_rera_entries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    registration_number: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str | None] = mapped_column(String(80))
    issuer_label: Mapped[str | None] = mapped_column(String(120))
    valid_until: Mapped[date | None] = mapped_column(Date)
    verified_details: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="rera_entries")  # noqa: F821

    __table_args__ = (
        UniqueConstraint(
            "project_id", "registration_number", name="uq_project_rera_project_registration"
        ),
    )

