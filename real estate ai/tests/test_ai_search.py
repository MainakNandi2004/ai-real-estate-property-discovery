"""
Integration tests for AISearchService.

Strategy:
- The extraction layer (Gemini) is always mocked — no real API call.
- PropertySearchService and PostgreSQL are exercised for real, using the
  shared `sample_catalog` + `db_session` fixtures from conftest.py.
"""
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.ai.requirement_extraction import BudgetUnit, ExtractedRequirements
from app.schemas.search import SearchOutcomeKind
from app.services.ai_search_service import AISearchErrorKind, AISearchService
from app.services.extraction_service import InsufficientRequirementsError


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_service(db_session):
    return AISearchService(db_session)


def _patch_extraction(requirements: ExtractedRequirements):
    """Patch extract_requirements to return a fixed ExtractedRequirements object."""
    return patch(
        "app.services.ai_search_service.extract_requirements",
        return_value=requirements,
    )


# ── Successful exact search ───────────────────────────────────────────────────

class TestSuccessfulSearch:
    def test_exact_match_2bhk_with_parking(self, sample_catalog, db_session):
        """
        2 BHK in test-locality under 70 lakh with parking → EXACT match
        (sample_catalog has a 2 BHK at 65 lakh with parking).
        """
        extracted = ExtractedRequirements(
            bhk="2",
            localities=["Test Locality"],
            max_budget_number=70,
            max_budget_unit=BudgetUnit.LAKH,
            amenities=["parking"],
        )
        with _patch_extraction(extracted):
            service = _make_service(db_session)
            result = service.search_from_query("2 BHK in Test Locality under 70 lakh with parking")

        assert not isinstance(result, type(None))
        from app.services.ai_search_service import AISearchError
        assert not isinstance(result, AISearchError)
        assert result.kind == SearchOutcomeKind.EXACT
        assert len(result.results) >= 1
        assert all(r.bhk == Decimal("2") for r in result.results)

    def test_exact_match_by_city_slug(self, sample_catalog, db_session):
        """City-only search (slug) should find both configurations in the catalog."""
        extracted = ExtractedRequirements(
            city="Test Metro",
        )
        with _patch_extraction(extracted):
            service = _make_service(db_session)
            result = service.search_from_query("Show me properties in Test Metro")

        from app.services.ai_search_service import AISearchError
        assert not isinstance(result, AISearchError)
        assert result.kind in {SearchOutcomeKind.EXACT, SearchOutcomeKind.PARTIAL}
        assert len(result.results) >= 1

    def test_search_returns_correct_bhk(self, sample_catalog, db_session):
        """BHK filter is correctly passed through to PropertySearchService."""
        extracted = ExtractedRequirements(
            bhk="3",
            city="Test Metro",
        )
        with _patch_extraction(extracted):
            service = _make_service(db_session)
            result = service.search_from_query("3 BHK in Test Metro")

        from app.services.ai_search_service import AISearchError
        assert not isinstance(result, AISearchError)
        assert result.kind == SearchOutcomeKind.EXACT
        for r in result.results:
            assert r.bhk == Decimal("3")

    def test_budget_conversion_passed_to_search(self, sample_catalog, db_session):
        """80 lakh budget → Decimal(8000000) reaches PropertySearchService correctly."""
        extracted = ExtractedRequirements(
            city="Test Metro",
            max_budget_number=80,
            max_budget_unit=BudgetUnit.LAKH,
        )
        with _patch_extraction(extracted):
            service = _make_service(db_session)
            result = service.search_from_query("properties under 80 lakh in Test Metro")

        from app.services.ai_search_service import AISearchError
        assert not isinstance(result, AISearchError)
        # Both 65L and 95L configs exist; only 65L is under 80L
        assert all(
            r.price is not None and r.price <= Decimal("8000000")
            for r in result.results
        )


# ── No matching properties ────────────────────────────────────────────────────

class TestNoMatchingProperties:
    def test_impossible_bhk_returns_none_outcome(self, sample_catalog, db_session):
        """5 BHK doesn't exist in the test catalog — should return NONE outcome."""
        extracted = ExtractedRequirements(
            bhk="5",
            city="Test Metro",
        )
        with _patch_extraction(extracted):
            service = _make_service(db_session)
            result = service.search_from_query("5 BHK in Test Metro")

        from app.services.ai_search_service import AISearchError
        assert not isinstance(result, AISearchError)
        assert result.kind == SearchOutcomeKind.NONE

    def test_very_low_budget_returns_partial_or_none(self, sample_catalog, db_session):
        """Budget of 1 lakh will match nothing in the catalog."""
        extracted = ExtractedRequirements(
            city="Test Metro",
            max_budget_number=1,
            max_budget_unit=BudgetUnit.LAKH,
        )
        with _patch_extraction(extracted):
            service = _make_service(db_session)
            result = service.search_from_query("property under 1 lakh in Test Metro")

        from app.services.ai_search_service import AISearchError
        assert not isinstance(result, AISearchError)
        assert result.kind in {SearchOutcomeKind.PARTIAL, SearchOutcomeKind.NONE}


# ── Insufficient / vague requirements ────────────────────────────────────────

class TestInsufficientRequirements:
    def test_vague_query_returns_error(self, db_session):
        """'Show me properties' → no criteria extracted → AISearchError."""
        extracted = ExtractedRequirements()  # nothing set
        with _patch_extraction(extracted):
            service = _make_service(db_session)
            result = service.search_from_query("Show me some properties.")

        from app.services.ai_search_service import AISearchError
        assert isinstance(result, AISearchError)
        assert result.kind == AISearchErrorKind.INSUFFICIENT_REQUIREMENTS
        assert len(result.message) > 10

    def test_error_message_is_user_friendly(self, db_session):
        """Error message should be human-readable, not a stack trace."""
        extracted = ExtractedRequirements()
        with _patch_extraction(extracted):
            service = _make_service(db_session)
            result = service.search_from_query("anything")

        from app.services.ai_search_service import AISearchError
        assert isinstance(result, AISearchError)
        assert result.kind == AISearchErrorKind.INSUFFICIENT_REQUIREMENTS
        # Should not contain Python internals
        assert "Traceback" not in result.message
        assert "Exception" not in result.message


# ── Extraction / search errors ────────────────────────────────────────────────

class TestErrorHandling:
    def test_extraction_exception_returns_error(self, db_session):
        """If Gemini SDK raises, pipeline returns EXTRACTION_FAILED error."""
        with patch(
            "app.services.ai_search_service.extract_requirements",
            side_effect=RuntimeError("Gemini API timeout"),
        ):
            service = _make_service(db_session)
            result = service.search_from_query("3 BHK in New Town")

        from app.services.ai_search_service import AISearchError
        assert isinstance(result, AISearchError)
        assert result.kind == AISearchErrorKind.EXTRACTION_FAILED
        assert "Gemini API timeout" in result.message

    def test_result_is_never_none(self, sample_catalog, db_session):
        """search_from_query must always return something, never None."""
        extracted = ExtractedRequirements(city="Test Metro")
        with _patch_extraction(extracted):
            service = _make_service(db_session)
            result = service.search_from_query("properties in Test Metro")

        assert result is not None
