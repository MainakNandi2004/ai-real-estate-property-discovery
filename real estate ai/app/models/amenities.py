from sqlalchemy import BigInteger, ForeignKey, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Amenity(Base):
    __tablename__ = "amenities"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str | None] = mapped_column(String(60))

    project_links: Mapped[list["ProjectAmenity"]] = relationship(back_populates="amenity")
    configuration_links: Mapped[list["ConfigurationAmenity"]] = relationship(
        back_populates="amenity"
    )


class ProjectAmenity(Base):
    __tablename__ = "project_amenities"

    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    amenity_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("amenities.id", ondelete="RESTRICT"), primary_key=True, index=True
    )
    details: Mapped[str | None] = mapped_column(Text)

    project: Mapped["Project"] = relationship(back_populates="amenity_links")
    amenity: Mapped[Amenity] = relationship(back_populates="project_links")


class ConfigurationAmenity(Base):
    __tablename__ = "configuration_amenities"

    configuration_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("property_configurations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    amenity_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("amenities.id", ondelete="RESTRICT"), primary_key=True
    )
    details: Mapped[str | None] = mapped_column(Text)

    configuration: Mapped["PropertyConfiguration"] = relationship(back_populates="amenity_links")
    amenity: Mapped[Amenity] = relationship(back_populates="configuration_links")

