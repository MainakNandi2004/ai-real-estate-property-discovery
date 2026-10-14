from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Locality, LocalityZoneLink, Project, ProjectAmenity, PropertyConfiguration
from app.repositories.property_repository import PropertyRepository
from app.schemas.search import (
    ConfigurationSearchResult,
    SearchCriteria,
    SearchOutcome,
    SearchOutcomeKind,
)
from app.services.search.matching import MatchingService


class PropertySearchService:
    """Deterministic search, ranking, and no-match handling."""

    RELAXATION_ORDER = [
        "amenity_codes",
        "property_type_code",
        "max_budget",
        "min_budget",
        "locality",
        "zone",
    ]

    def __init__(self, session: Session) -> None:
        self._repo = PropertyRepository(session)
        self._matcher = MatchingService()
        self._session = session

    def search(self, criteria: SearchCriteria, *, limit: int = 50) -> SearchOutcome:
        if not criteria.has_any_criterion():
            return SearchOutcome(
                kind=SearchOutcomeKind.NONE,
                unmatched_requirements=["insufficient_criteria"],
                message_hint="At least one search criterion is required.",
            )

        configurations = self._load_for_matching(
            self._repo.search_configurations(criteria, limit=limit)
        )
        exact = self._build_results(configurations, criteria, strict=True)
        exact = [r for r in exact if not r.failed_criteria]

        if exact:
            exact.sort(key=lambda r: r.rank_score, reverse=True)
            return SearchOutcome(kind=SearchOutcomeKind.EXACT, results=exact)

        partial = self._build_results(configurations, criteria, strict=False)
        partial = [r for r in partial if r.match_reasons]
        if partial:
            partial.sort(key=lambda r: r.rank_score, reverse=True)
            unmatched = self._summarize_unmatched(partial)
            return SearchOutcome(
                kind=SearchOutcomeKind.PARTIAL,
                results=partial,
                unmatched_requirements=unmatched,
                message_hint="Some criteria did not match exactly; partial matches returned.",
            )

        return self._relax_and_search(criteria, limit=limit)

    def _relax_and_search(self, criteria: SearchCriteria, *, limit: int) -> SearchOutcome:
        accumulated_unmatched: list[str] = []

        for drop in self.RELAXATION_ORDER:
            if not self._criterion_active(criteria, drop):
                continue

            relaxed_configs = self._load_for_matching(
                self._repo.search_configurations_relaxed(
                    criteria, drop_fields=[drop], limit=limit
                )
            )
            if not relaxed_configs:
                accumulated_unmatched.append(drop)
                continue

            partial = self._build_results(relaxed_configs, criteria, strict=False)
            partial = [r for r in partial if r.match_reasons]
            if partial:
                partial.sort(key=lambda r: r.rank_score, reverse=True)
                accumulated_unmatched.append(drop)
                return SearchOutcome(
                    kind=SearchOutcomeKind.PARTIAL,
                    results=partial,
                    unmatched_requirements=accumulated_unmatched,
                    message_hint=(
                        f"No exact match; alternatives shown after relaxing: {drop}."
                    ),
                )
            accumulated_unmatched.append(drop)

        return SearchOutcome(
            kind=SearchOutcomeKind.NONE,
            unmatched_requirements=accumulated_unmatched or ["no_data"],
            message_hint="No matching configurations found in the database.",
        )

    def _criterion_active(self, criteria: SearchCriteria, field: str) -> bool:
        if field == "bhk":
            return criteria.bhk is not None
        if field == "min_budget":
            return criteria.min_budget is not None
        if field == "max_budget":
            return criteria.max_budget is not None
        if field == "amenity_codes":
            return bool(criteria.amenity_codes)
        if field == "property_type_code":
            return bool(criteria.property_type_code)
        if field == "locality":
            return bool(criteria.locality_ids or criteria.locality_slugs)
        if field == "zone":
            return bool(criteria.zone_ids or criteria.zone_slugs)
        return False

    def _load_for_matching(
        self, configurations: list[PropertyConfiguration]
    ) -> list[PropertyConfiguration]:
        if not configurations:
            return []
        ids = [c.id for c in configurations]
        stmt = (
            select(PropertyConfiguration)
            .where(PropertyConfiguration.id.in_(ids))
            .options(
                selectinload(PropertyConfiguration.project)
                .selectinload(Project.locality)
                .selectinload(Locality.zone_links)
                .selectinload(LocalityZoneLink.zone),
                selectinload(PropertyConfiguration.project)
                .selectinload(Project.amenity_links)
                .selectinload(ProjectAmenity.amenity),
                selectinload(PropertyConfiguration.project).selectinload(Project.property_type),
            )
        )
        loaded = list(self._session.scalars(stmt).unique().all())
        order = {cid: idx for idx, cid in enumerate(ids)}
        loaded.sort(key=lambda c: order.get(c.id, 9999))
        return loaded

    def _build_results(
        self,
        configurations: list[PropertyConfiguration],
        criteria: SearchCriteria,
        *,
        strict: bool,
    ) -> list[ConfigurationSearchResult]:
        results: list[ConfigurationSearchResult] = []
        for config in configurations:
            reasons, failed = self._matcher.evaluate(config, criteria, strict=strict)
            project = config.project
            locality = project.locality
            city = locality.city
            results.append(
                ConfigurationSearchResult(
                    configuration_id=config.id,
                    project_id=project.id,
                    project_name=project.name,
                    project_slug=project.slug,
                    bhk=config.bhk,
                    price=config.price,
                    currency=config.currency,
                    availability_status=config.availability_status,
                    locality_name=locality.name,
                    city_name=city.name,
                    property_type_code=project.property_type.code if project.property_type else None,
                    match_reasons=reasons,
                    failed_criteria=failed,
                    rank_score=self._matcher.rank_score(reasons),
                )
            )
        return results

    def _summarize_unmatched(self, results: list[ConfigurationSearchResult]) -> list[str]:
        failed_sets = [set(r.failed_criteria) for r in results if r.failed_criteria]
        if not failed_sets:
            return []
        common = set.intersection(*failed_sets) if len(failed_sets) > 1 else failed_sets[0]
        return sorted(common)
