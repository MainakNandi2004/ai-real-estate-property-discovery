from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
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


class PropertyType(Base):
    __tablename__ = "property_types"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(80), nullable=False)

    projects: Mapped[list[Project]] = relationship(back_populates="property_type")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    locality_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("localities.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    property_type_id: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("property_types.id", ondelete="RESTRICT"), index=True
    )
    project_status: Mapped[str | None] = mapped_column(String(40))
    address_line: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    description: Mapped[str | None] = mapped_column(Text)
    possession_date: Mapped[date | None] = mapped_column(Date)
    possession_label: Mapped[str | None] = mapped_column(String(120))
    other_verified_information: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    locality: Mapped["Locality"] = relationship(back_populates="projects")  # noqa: F821
    property_type: Mapped[PropertyType | None] = relationship(back_populates="projects")
    configurations: Mapped[list[PropertyConfiguration]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    amenity_links: Mapped[list["ProjectAmenity"]] = relationship(  # noqa: F821
        back_populates="project", cascade="all, delete-orphan"
    )
    images: Mapped[list["ProjectImage"]] = relationship(  # noqa: F821
        back_populates="project", cascade="all, delete-orphan"
    )
    nearby_places: Mapped[list["ProjectNearbyPlace"]] = relationship(  # noqa: F821
        back_populates="project", cascade="all, delete-orphan"
    )
    rera_entries: Mapped[list["ProjectReraEntry"]] = relationship(  # noqa: F821
        back_populates="project", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "ix_projects_active_status",
            "project_status",
            postgresql_where=(is_active.is_(True)),
        ),
    )


class PropertyConfiguration(Base):
    __tablename__ = "property_configurations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str | None] = mapped_column(String(80))
    bhk: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    bedrooms: Mapped[int | None] = mapped_column(SmallInteger)
    area_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    area_unit: Mapped[str | None] = mapped_column(String(20))
    price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    price_unit: Mapped[str | None] = mapped_column(String(20))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")
    availability_status: Mapped[str | None] = mapped_column(String(40), index=True)
    parking_included: Mapped[bool | None] = mapped_column(Boolean)
    parking_details: Mapped[str | None] = mapped_column(Text)
    possession_date: Mapped[date | None] = mapped_column(Date)
    possession_label: Mapped[str | None] = mapped_column(String(120))
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="configurations")
    units: Mapped[list[Unit]] = relationship(
        back_populates="configuration", cascade="all, delete-orphan"
    )
    floor_plans: Mapped[list["ConfigurationFloorPlan"]] = relationship(  # noqa: F821
        back_populates="configuration", cascade="all, delete-orphan"
    )
    amenity_links: Mapped[list["ConfigurationAmenity"]] = relationship(  # noqa: F821
        back_populates="configuration", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("bhk IS NULL OR bhk > 0", name="ck_property_configurations_bhk_positive"),
        CheckConstraint("price IS NULL OR price >= 0", name="ck_property_configurations_price_nonneg"),
        CheckConstraint(
            "area_value IS NULL OR area_value > 0", name="ck_property_configurations_area_positive"
        ),
        Index("ix_property_configurations_project_bhk", "project_id", "bhk"),
        Index(
            "ix_property_configurations_price",
            "price",
            postgresql_where=(price.isnot(None)),
        ),
    )


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    configuration_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("property_configurations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unit_code: Mapped[str] = mapped_column(String(80), nullable=False)
    floor: Mapped[str | None] = mapped_column(String(20))
    availability_status: Mapped[str | None] = mapped_column(String(40), index=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    area_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    configuration: Mapped[PropertyConfiguration] = relationship(back_populates="units")

    __table_args__ = (
        UniqueConstraint("configuration_id", "unit_code", name="uq_units_configuration_code"),
        CheckConstraint("price IS NULL OR price >= 0", name="ck_units_price_nonneg"),
        CheckConstraint("area_value IS NULL OR area_value > 0", name="ck_units_area_positive"),
    )

