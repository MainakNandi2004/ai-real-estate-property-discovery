from decimal import Decimal

import pytest

from app.repositories.property_repository import PropertyRepository
from app.schemas.search import SearchCriteria, SearchOutcomeKind
from app.services.search.property_search_service import PropertySearchService


def test_repository_get_project(sample_catalog, db_session):
    repo = PropertyRepository(db_session)
    project = repo.get_project_by_id(sample_catalog["project"].id)
    assert project is not None
    assert project.name == "Test Project Alpha"
    assert len(project.configurations) >= 2


def test_search_exact_bhk_and_budget(sample_catalog, db_session):
    service = PropertySearchService(db_session)
    criteria = SearchCriteria(
        bhk=Decimal("2"),
        max_budget=Decimal("7000000"),
        city_slug="test-metro",
    )
    outcome = service.search(criteria)
    assert outcome.kind == SearchOutcomeKind.EXACT
    assert len(outcome.results) == 1
    result = outcome.results[0]
    assert result.bhk == Decimal("2")
    assert any(r.code.value == "bhk_matched" for r in result.match_reasons)
    assert result.rank_score > 0
    assert not any("%" in r.message for r in result.match_reasons)


def test_search_no_match_returns_none(sample_catalog, db_session):
    service = PropertySearchService(db_session)
    criteria = SearchCriteria(
        bhk=Decimal("5"),
        city_slug="test-metro",
    )
    outcome = service.search(criteria)
    assert outcome.kind == SearchOutcomeKind.NONE


def test_search_partial_budget(sample_catalog, db_session):
    service = PropertySearchService(db_session)
    criteria = SearchCriteria(
        bhk=Decimal("3"),
        max_budget=Decimal("5000000"),
        city_slug="test-metro",
    )
    outcome = service.search(criteria)
    assert outcome.kind in {SearchOutcomeKind.PARTIAL, SearchOutcomeKind.NONE}
    if outcome.kind == SearchOutcomeKind.PARTIAL:
        assert outcome.unmatched_requirements
        assert outcome.results


def test_search_by_zone(sample_catalog, db_session):
    service = PropertySearchService(db_session)
    criteria = SearchCriteria(
        zone_slug="test-south",
        bhk=Decimal("2"),
    )
    outcome = service.search(criteria)
    assert outcome.kind == SearchOutcomeKind.EXACT
    assert len(outcome.results) >= 1


def test_search_amenity_filter(sample_catalog, db_session):
    service = PropertySearchService(db_session)
    criteria = SearchCriteria(
        amenity_codes=["parking"],
        city_slug="test-metro",
    )
    outcome = service.search(criteria)
    assert outcome.kind == SearchOutcomeKind.EXACT
    assert len(outcome.results) >= 1


def test_insufficient_criteria(db_session):
    service = PropertySearchService(db_session)
    outcome = service.search(SearchCriteria())
    assert outcome.kind == SearchOutcomeKind.NONE
    assert "insufficient_criteria" in outcome.unmatched_requirements
