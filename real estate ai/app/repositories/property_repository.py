from decimal import Decimal

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import (
    Amenity,
    City,
    Locality,
    LocalityZoneLink,
    LocationZone,
    Project,
    ProjectAmenity,
    PropertyConfiguration,
    PropertyType,
)
from app.schemas.search import AvailabilityFilter, SearchCriteria


class PropertyRepository:
    """Database access for projects and configurations only."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_project_by_id(self, project_id: int, *, active_only: bool = True) -> Project | None:
        stmt = (
            select(Project)
            .options(
                joinedload(Project.locality).joinedload(Locality.city),
                joinedload(Project.property_type),
                selectinload(Project.configurations),
                selectinload(Project.amenity_links).joinedload(ProjectAmenity.amenity),
                selectinload(Project.images),
                selectinload(Project.nearby_places),
                selectinload(Project.rera_entries),
            )
            .where(Project.id == project_id)
        )
        if active_only:
            stmt = stmt.where(Project.is_active.is_(True))
        return self._session.scalars(stmt).unique().one_or_none()

    def get_configuration_by_id(
        self, configuration_id: int, *, active_only: bool = True
    ) -> PropertyConfiguration | None:
        stmt = (
            select(PropertyConfiguration)
            .options(
                joinedload(PropertyConfiguration.project)
                .joinedload(Project.locality)
                .joinedload(Locality.city),
                joinedload(PropertyConfiguration.project).joinedload(Project.property_type),
            )
            .where(PropertyConfiguration.id == configuration_id)
        )
        if active_only:
            stmt = stmt.where(
                PropertyConfiguration.is_active.is_(True),
                PropertyConfiguration.project.has(Project.is_active.is_(True)),
            )
        return self._session.scalars(stmt).unique().one_or_none()

    def list_active_projects(self, *, limit: int = 100, offset: int = 0) -> list[Project]:
        stmt = (
            select(Project)
            .options(
                joinedload(Project.locality).joinedload(Locality.city),
                joinedload(Project.property_type),
            )
            .where(Project.is_active.is_(True))
            .order_by(Project.name)
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(stmt).unique().all())

    def list_active_configurations(
        self, *, limit: int = 100, offset: int = 0
    ) -> list[PropertyConfiguration]:
        stmt = (
            select(PropertyConfiguration)
            .join(Project)
            .options(
                joinedload(PropertyConfiguration.project)
                .joinedload(Project.locality)
                .joinedload(Locality.city),
            )
            .where(
                PropertyConfiguration.is_active.is_(True),
                Project.is_active.is_(True),
            )
            .order_by(Project.name, PropertyConfiguration.sort_order)
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(stmt).unique().all())

    def _base_configuration_query(self, criteria: SearchCriteria) -> Select[tuple[PropertyConfiguration]]:
        stmt: Select[tuple[PropertyConfiguration]] = (
            select(PropertyConfiguration)
            .join(Project)
            .join(Locality, Project.locality_id == Locality.id)
            .join(City, Locality.city_id == City.id)
            .outerjoin(PropertyType, Project.property_type_id == PropertyType.id)
            .where(
                PropertyConfiguration.is_active.is_(True),
                Project.is_active.is_(True),
            )
        )

        if criteria.bhk is not None:
            stmt = stmt.where(PropertyConfiguration.bhk == criteria.bhk)

        if criteria.min_budget is not None:
            stmt = stmt.where(
                PropertyConfiguration.price.isnot(None),
                PropertyConfiguration.price >= criteria.min_budget,
            )
        if criteria.max_budget is not None:
            stmt = stmt.where(
                PropertyConfiguration.price.isnot(None),
                PropertyConfiguration.price <= criteria.max_budget,
            )

        if criteria.city_id is not None:
            stmt = stmt.where(City.id == criteria.city_id)
        if criteria.city_slug:
            stmt = stmt.where(City.slug == criteria.city_slug)

        locality_filters: list = []
        if criteria.locality_ids:
            locality_filters.append(Locality.id.in_(criteria.locality_ids))
        if criteria.locality_slugs:
            locality_filters.append(Locality.slug.in_(criteria.locality_slugs))
        if criteria.zone_ids or criteria.zone_slugs:
            zone_subq = select(LocalityZoneLink.locality_id).join(LocationZone)
            if criteria.zone_ids:
                zone_subq = zone_subq.where(LocationZone.id.in_(criteria.zone_ids))
            if criteria.zone_slugs:
                zone_subq = zone_subq.where(LocationZone.slug.in_(criteria.zone_slugs))
            locality_filters.append(Locality.id.in_(zone_subq))
        if locality_filters:
            stmt = stmt.where(or_(*locality_filters))

        if criteria.property_type_code:
            stmt = stmt.where(PropertyType.code == criteria.property_type_code)

        if criteria.availability == AvailabilityFilter.AVAILABLE:
            stmt = stmt.where(PropertyConfiguration.availability_status == "available")
        elif criteria.availability == AvailabilityFilter.EXCLUDE_SOLD_OUT:
            stmt = stmt.where(
                or_(
                    PropertyConfiguration.availability_status.is_(None),
                    PropertyConfiguration.availability_status != "sold_out",
                )
            )

        if criteria.amenity_codes:
            for code in criteria.amenity_codes:
                amenity_exists = (
                    select(ProjectAmenity.project_id)
                    .join(Amenity)
                    .where(
                        ProjectAmenity.project_id == Project.id,
                        Amenity.code == code,
                    )
                    .exists()
                )
                stmt = stmt.where(amenity_exists)

        return stmt

    def search_configurations(
        self, criteria: SearchCriteria, *, limit: int = 50
    ) -> list[PropertyConfiguration]:
        stmt = (
            self._base_configuration_query(criteria)
            .options(
                joinedload(PropertyConfiguration.project)
                .joinedload(Project.locality)
                .joinedload(Locality.city),
                joinedload(PropertyConfiguration.project)
                .joinedload(Project.locality)
                .selectinload(Locality.zone_links)
                .joinedload(LocalityZoneLink.zone),
                joinedload(PropertyConfiguration.project).joinedload(Project.property_type),
                joinedload(PropertyConfiguration.project)
                .selectinload(Project.amenity_links)
                .joinedload(ProjectAmenity.amenity),
            )
            .order_by(Project.name, PropertyConfiguration.sort_order)
            .limit(limit)
        )
        return list(self._session.scalars(stmt).unique().all())

    def search_configurations_relaxed(
        self,
        criteria: SearchCriteria,
        *,
        drop_fields: list[str],
        limit: int = 50,
    ) -> list[PropertyConfiguration]:
        relaxed = criteria.model_copy(deep=True)
        for field in drop_fields:
            if field == "bhk":
                relaxed.bhk = None
            elif field == "min_budget":
                relaxed.min_budget = None
            elif field == "max_budget":
                relaxed.max_budget = None
            elif field == "amenity_codes":
                relaxed.amenity_codes = []
            elif field == "property_type_code":
                relaxed.property_type_code = None
            elif field == "locality":
                relaxed.locality_ids = []
                relaxed.locality_slugs = []
            elif field == "zone":
                relaxed.zone_ids = []
                relaxed.zone_slugs = []
        return self.search_configurations(relaxed, limit=limit)
