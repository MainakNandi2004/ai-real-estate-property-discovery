"""
API-level tests for:
  GET  /
  GET  /health
  GET  /health/db
  POST /api/ai/search

Strategy:
  - AISearchService.search_from_query is mocked in all ai/search tests.
    No real Gemini API call is ever made.
  - The DB session dependency is overridden with a lightweight stub for
    unit-style route tests, so no PostgreSQL connection is required there.
  - Integration tests that DO need the real DB (sample_catalog fixture)
    are clearly marked and use the existing db_session fixture.
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.search import (
    ConfigurationSearchResult,
    MatchReason,
    MatchReasonCode,
    SearchOutcome,
    SearchOutcomeKind,
)
from app.services.ai_search_service import AISearchError, AISearchErrorKind

client = TestClient(app)

# ── Shared fixtures ───────────────────────────────────────────────────────────

def _make_config_result(**overrides) -> ConfigurationSearchResult:
    defaults = dict(
        configuration_id=1,
        project_id=1,
        project_name="Test Project Alpha",
        project_slug="test-project-alpha",
        bhk=Decimal("3"),
        price=Decimal("7500000"),
        currency="INR",
        availability_status="available",
        locality_name="New Town",
        city_name="Kolkata",
        property_type_code="apartment",
        match_reasons=[MatchReason(code=MatchReasonCode.BHK, message="BHK matched: 3")],
        failed_criteria=[],
        rank_score=10,
    )
    defaults.update(overrides)
    return ConfigurationSearchResult(**defaults)


def _exact_outcome() -> SearchOutcome:
    return SearchOutcome(
        kind=SearchOutcomeKind.EXACT,
        results=[_make_config_result()],
        unmatched_requirements=[],
        message_hint=None,
    )


def _no_match_outcome() -> SearchOutcome:
    return SearchOutcome(
        kind=SearchOutcomeKind.NONE,
        results=[],
        unmatched_requirements=["bhk"],
        message_hint="No matching configurations found in the database.",
    )


def _patch_service(return_value):
    return patch(
        "app.api.ai_search.AISearchService.search_from_query",
        return_value=return_value,
    )


# ── Status endpoints ──────────────────────────────────────────────────────────

class TestStatusEndpoints:
    def test_root_returns_200(self):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_root_body(self):
        body = client.get("/").json()
        assert body["status"] == "ok"
        assert body["name"] == "Real Estate AI API"
        assert body["version"] == "0.1.0"
        assert "docs" in body

    def test_health_liveness(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_health_db_shape(self):
        resp = client.get("/health/db")
        assert resp.status_code == 200
        body = resp.json()
        assert "connected" in body
        assert "database" in body
        assert "status" in body


# ── POST /api/ai/search — happy paths ────────────────────────────────────────

class TestAISearchHappyPath:
    def test_exact_match_returns_200(self):
        with _patch_service(_exact_outcome()):
            resp = client.post("/api/ai/search", json={"query": "3 BHK in New Town under 80 lakh with parking"})
        assert resp.status_code == 200

    def test_exact_match_body_structure(self):
        with _patch_service(_exact_outcome()):
            body = client.post("/api/ai/search", json={"query": "3 BHK in New Town"}).json()

        assert body["status"] == "exact_matches"
        assert body["result_count"] == 1
        assert len(body["results"]) == 1
        assert body["results"][0]["project_name"] == "Test Project Alpha"
        assert body["results"][0]["bhk"] == "3"
        assert body["results"][0]["price"] == "7500000"
        assert body["results"][0]["locality_name"] == "New Town"
        assert body["query"] == "3 BHK in New Town"

    def test_no_matches_returns_200_with_empty_results(self):
        with _patch_service(_no_match_outcome()):
            resp = client.post("/api/ai/search", json={"query": "10 BHK in Antarctica"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "no_matches"
        assert body["result_count"] == 0
        assert body["results"] == []
        assert "bhk" in body["unmatched_requirements"]

    def test_partial_match_returns_200(self):
        partial = SearchOutcome(
            kind=SearchOutcomeKind.PARTIAL,
            results=[_make_config_result(failed_criteria=["max_budget"])],
            unmatched_requirements=["max_budget"],
            message_hint="Partial matches returned after relaxing budget.",
        )
        with _patch_service(partial):
            body = client.post("/api/ai/search", json={"query": "3 BHK under 10 lakh"}).json()

        assert body["status"] == "partial_matches"
        assert body["result_count"] == 1
        assert "max_budget" in body["unmatched_requirements"]
        assert body["message"] is not None

    def test_query_is_echoed_in_response(self):
        query = "2 BHK with swimming pool"
        with _patch_service(_exact_outcome()):
            body = client.post("/api/ai/search", json={"query": query}).json()
        assert body["query"] == query


# ── POST /api/ai/search — error paths ────────────────────────────────────────

class TestAISearchErrors:
    def test_insufficient_requirements_returns_422(self):
        error = AISearchError(
            kind=AISearchErrorKind.INSUFFICIENT_REQUIREMENTS,
            message="No searchable criteria were found. Please specify at least a location, BHK, budget, or property type.",
        )
        with _patch_service(error):
            resp = client.post("/api/ai/search", json={"query": "Show me some properties."})
        assert resp.status_code == 422
        body = resp.json()
        assert body["status"] == "insufficient_requirements"
        assert "criteria" in body["message"].lower() or "location" in body["message"].lower()

    def test_extraction_failed_returns_502(self):
        error = AISearchError(
            kind=AISearchErrorKind.EXTRACTION_FAILED,
            message="Could not extract requirements from your query: Gemini API timeout",
        )
        with _patch_service(error):
            resp = client.post("/api/ai/search", json={"query": "3 BHK in Kolkata"})
        assert resp.status_code == 502
        body = resp.json()
        assert body["status"] == "extraction_failed"
        assert "Gemini" in body["message"] or "timeout" in body["message"].lower()

    def test_search_error_returns_500(self):
        error = AISearchError(
            kind=AISearchErrorKind.SEARCH_ERROR,
            message="Search failed: connection refused",
        )
        with _patch_service(error):
            resp = client.post("/api/ai/search", json={"query": "3 BHK in Kolkata"})
        assert resp.status_code == 500
        body = resp.json()
        assert body["status"] == "search_error"

    def test_error_response_echoes_query(self):
        error = AISearchError(
            kind=AISearchErrorKind.INSUFFICIENT_REQUIREMENTS,
            message="No criteria found.",
        )
        query = "give me something nice"
        with _patch_service(error):
            body = client.post("/api/ai/search", json={"query": query}).json()
        assert body["query"] == query


# ── POST /api/ai/search — request validation ─────────────────────────────────

class TestAISearchRequestValidation:
    def test_missing_query_field_returns_422(self):
        resp = client.post("/api/ai/search", json={})
        assert resp.status_code == 422

    def test_empty_query_returns_422(self):
        resp = client.post("/api/ai/search", json={"query": ""})
        assert resp.status_code == 422

    def test_too_short_query_returns_422(self):
        resp = client.post("/api/ai/search", json={"query": "hi"})
        assert resp.status_code == 422

    def test_non_json_body_returns_422(self):
        resp = client.post("/api/ai/search", content="not json", headers={"Content-Type": "application/json"})
        assert resp.status_code == 422


# ── Integration: real DB + mocked extraction ─────────────────────────────────

class TestAISearchIntegration:
    """
    Uses real PostgreSQL (sample_catalog fixture) but mocks the extraction layer.
    Exercises the full route → AISearchService → PropertySearchService → DB path.
    """

    def test_real_db_exact_match(self, sample_catalog, db_session):
        from app.ai.requirement_extraction import BudgetUnit, ExtractedRequirements
        from app.db.session import get_db
        from app.services.ai_search_service import AISearchService

        extracted = ExtractedRequirements(
            bhk="2",
            city="Test Metro",
            max_budget_number=70,
            max_budget_unit=BudgetUnit.LAKH,
            amenities=["parking"],
        )

        # Override the DB dependency to use the test-scoped session
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with patch("app.services.ai_search_service.extract_requirements", return_value=extracted):
                resp = client.post(
                    "/api/ai/search",
                    json={"query": "2 BHK in Test Metro under 70 lakh with parking"},
                )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "exact_matches"
        assert body["result_count"] >= 1
        assert body["results"][0]["bhk"] == "2"

    def test_real_db_no_match(self, sample_catalog, db_session):
        from app.ai.requirement_extraction import ExtractedRequirements
        from app.db.session import get_db

        extracted = ExtractedRequirements(bhk="9", city="Test Metro")

        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with patch("app.services.ai_search_service.extract_requirements", return_value=extracted):
                resp = client.post("/api/ai/search", json={"query": "9 BHK in Test Metro"})
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "no_matches"
        assert body["result_count"] == 0
