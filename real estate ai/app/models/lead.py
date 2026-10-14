from __future__ import annotations

import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        index=True,
    )
    name: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(30), index=True)
    email: Mapped[str | None] = mapped_column(String(254))
    requirement_summary: Mapped[str | None] = mapped_column(Text)
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    budget_currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")
    conversation_summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="new")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    conversation: Mapped["Conversation | None"] = relationship(  # noqa: F821
        back_populates="leads"
    )
    project_interests: Mapped[list[LeadProjectInterest]] = relationship(
        back_populates="lead", cascade="all, delete-orphan"
    )
    site_visits: Mapped[list[SiteVisit]] = relationship(
        back_populates="lead", cascade="all, delete-orphan"
    )


class LeadProjectInterest(Base):
    __tablename__ = "lead_project_interests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    configuration_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("property_configurations.id", ondelete="RESTRICT")
    )
    interest_level: Mapped[str | None] = mapped_column(String(30))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    lead: Mapped[Lead] = relationship(back_populates="project_interests")
    project: Mapped["Project"] = relationship()
    configuration: Mapped["PropertyConfiguration | None"] = relationship()


class SiteVisit(Base):
    __tablename__ = "site_visits"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    configuration_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("property_configurations.id", ondelete="SET NULL")
    )
    preferred_date: Mapped[date | None] = mapped_column(Date)
    preferred_time: Mapped[time | None] = mapped_column(Time)
    preferred_time_label: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="requested")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    lead: Mapped[Lead] = relationship(back_populates="site_visits")
    project: Mapped["Project"] = relationship()
    configuration: Mapped["PropertyConfiguration | None"] = relationship()

