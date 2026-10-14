from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    state: Mapped[str | None] = mapped_column(String(80))
    country: Mapped[str] = mapped_column(String(80), nullable=False, server_default="India")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    localities: Mapped[list[Locality]] = relationship(back_populates="city")
    zones: Mapped[list[LocationZone]] = relationship(back_populates="city")

    __table_args__ = (UniqueConstraint("name", "state", name="uq_cities_name_state"),)


class LocationZone(Base):
    __tablename__ = "location_zones"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    city: Mapped[City] = relationship(back_populates="zones")
    locality_links: Mapped[list[LocalityZoneLink]] = relationship(back_populates="zone")

    __table_args__ = (
        UniqueConstraint("city_id", "slug", name="uq_location_zones_city_slug"),
        UniqueConstraint("city_id", "name", name="uq_location_zones_city_name"),
    )


class Locality(Base):
    __tablename__ = "localities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    city: Mapped[City] = relationship(back_populates="localities")
    zone_links: Mapped[list[LocalityZoneLink]] = relationship(back_populates="locality")
    projects: Mapped[list["Project"]] = relationship(  # noqa: F821
        back_populates="locality"
    )

    __table_args__ = (
        UniqueConstraint("city_id", "slug", name="uq_localities_city_slug"),
        UniqueConstraint("city_id", "name", name="uq_localities_city_name"),
    )


class LocalityZoneLink(Base):
    __tablename__ = "locality_zone_links"

    locality_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("localities.id", ondelete="CASCADE"), primary_key=True
    )
    zone_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("location_zones.id", ondelete="CASCADE"), primary_key=True, index=True
    )

    locality: Mapped[Locality] = relationship(back_populates="zone_links")
    zone: Mapped[LocationZone] = relationship(back_populates="locality_links")

