"""SQLAlchemy ORM models — import all tables for Alembic autogenerate."""

from app.models.amenities import Amenity, ConfigurationAmenity, ProjectAmenity
from app.models.base import Base
from app.models.conversation import Conversation, ConversationMessage
from app.models.lead import Lead, LeadProjectInterest, SiteVisit
from app.models.location import City, Locality, LocalityZoneLink, LocationZone
from app.models.media import (
    ConfigurationFloorPlan,
    ProjectImage,
    ProjectNearbyPlace,
    ProjectReraEntry,
)
from app.models.property import Project, PropertyConfiguration, PropertyType, Unit

__all__ = [
    "Base",
    "Amenity",
    "ConfigurationAmenity",
    "ProjectAmenity",
    "City",
    "Locality",
    "LocalityZoneLink",
    "LocationZone",
    "ConfigurationFloorPlan",
    "ProjectImage",
    "ProjectNearbyPlace",
    "ProjectReraEntry",
    "Conversation",
    "ConversationMessage",
    "Lead",
    "LeadProjectInterest",
    "SiteVisit",
    "Project",
    "PropertyConfiguration",
    "PropertyType",
    "Unit",
]
