"""
Unit tests for Phase 9.1 — AI requirement extraction hardening.

All Gemini calls are mocked; no real API key is required.
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.ai.requirement_extraction import BudgetUnit, ExtractedRequirements
from app.services.extraction_service import (
    InsufficientRequirementsError,
    _convert_budget,
    build_search_criteria,
    process_user_query,
)


# ── Budget conversion (pure Python, no mocking needed) ───────────────────────

class TestBudgetConversion:
    def test_80_lakh(self):
        result = _convert_budget(80, BudgetUnit.LAKH)
        assert result == Decimal("8000000")

    def test_1_point_2_crore(self):
        result = _convert_budget(1.2, BudgetUnit.CRORE)
        assert result == Decimal("12000000")

    def test_50_lakh(self):
        result = _convert_budget(50, BudgetUnit.LAKH)
        assert result == Decimal("5000000")

    def test_500_thousand(self):
        result = _convert_budget(500, BudgetUnit.THOUSAND)
        assert result == Decimal("500000")

    def test_direct_rupees(self):
        result = _convert_budget(250000, BudgetUnit.RUPEES)
        assert result == Decimal("250000")

    def test_missing_number_returns_none(self):
        assert _convert_budget(None, BudgetUnit.LAKH) is None

    def test_missing_unit_returns_none(self):
        assert _convert_budget(80, None) is None

    def test_both_none_returns_none(self):
        assert _convert_budget(None, None) is None


# ── BHK extraction (build_search_criteria, no LLM call) ─────────────────────

class TestBhkExtraction:
    def _make_req(self, bhk: str | None) -> ExtractedRequirements:
        return ExtractedRequirements(bhk=bhk, city="Kolkata")

    def test_bhk_1(self):
        criteria = build_search_criteria(self._make_req("1"))
        assert criteria.bhk == Decimal("1")

    def test_bhk_2(self):
        criteria = build_search_criteria(self._make_req("2"))
        assert criteria.bhk == Decimal("2")

    def test_bhk_3(self):
        criteria = build_search_criteria(self._make_req("3"))
        assert criteria.bhk == Decimal("3")

    def test_bhk_4(self):
        criteria = build_search_criteria(self._make_req("4"))
        assert criteria.bhk == Decimal("4")

    def test_bhk_none_leaves_criteria_bhk_none(self):
        criteria = build_search_criteria(self._make_req(None))
        assert criteria.bhk is None


# ── Full criteria building (no LLM call) ─────────────────────────────────────

class TestBuildSearchCriteria:
    def test_full_example(self):
        req = ExtractedRequirements(
            bhk="3",
            localities=["New Town"],
            city="Kolkata",
            max_budget_number=80,
            max_budget_unit=BudgetUnit.LAKH,
            amenities=["parking"],
        )
        criteria = build_search_criteria(req)

        assert criteria.bhk == Decimal("3")
        assert criteria.city_slug == "kolkata"
        assert criteria.locality_slugs == ["new-town"]
        assert criteria.max_budget == Decimal("8000000")
        assert criteria.min_budget is None
        assert criteria.amenity_codes == ["parking"]

    def test_crore_budget(self):
        req = ExtractedRequirements(
            city="Mumbai",
            max_budget_number=1.2,
            max_budget_unit=BudgetUnit.CRORE,
        )
        criteria = build_search_criteria(req)
        assert criteria.max_budget == Decimal("12000000")

    def test_both_min_and_max_budget(self):
        req = ExtractedRequirements(
            city="Pune",
            min_budget_number=50,
            min_budget_unit=BudgetUnit.LAKH,
            max_budget_number=80,
            max_budget_unit=BudgetUnit.LAKH,
        )
        criteria = build_search_criteria(req)
        assert criteria.min_budget == Decimal("5000000")
        assert criteria.max_budget == Decimal("8000000")


# ── Vague / empty query handling ─────────────────────────────────────────────

class TestInsufficientRequirements:
    def test_completely_empty_raises(self):
        req = ExtractedRequirements()
        with pytest.raises(InsufficientRequirementsError):
            build_search_criteria(req)

    def test_vague_query_raises(self):
        """Simulates a Gemini response where nothing useful was extracted."""
        req = ExtractedRequirements(
            bhk=None,
            localities=[],
            city=None,
            max_budget_number=None,
            max_budget_unit=None,
            amenities=[],
            property_type=None,
        )
        with pytest.raises(InsufficientRequirementsError) as exc_info:
            build_search_criteria(req)
        assert "clarify" in str(exc_info.value).lower() or "criteria" in str(exc_info.value).lower()

    def test_error_message_is_user_friendly(self):
        with pytest.raises(InsufficientRequirementsError) as exc_info:
            build_search_criteria(ExtractedRequirements())
        assert len(str(exc_info.value)) > 10  # not an empty message


# ── End-to-end with mocked LLM ───────────────────────────────────────────────

class TestProcessUserQueryMocked:
    @patch("app.ai.requirement_extraction.get_llm_client")
    def test_full_pipeline_3bhk_new_town_80lakh(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.generate_structured.return_value = ExtractedRequirements(
            bhk="3",
            localities=["New Town"],
            city=None,
            max_budget_number=80,
            max_budget_unit=BudgetUnit.LAKH,
            amenities=["parking"],
        )

        criteria = process_user_query("I want a 3 BHK in New Town under 80 lakh with parking")

        assert criteria.bhk == Decimal("3")
        assert criteria.locality_slugs == ["new-town"]
        assert criteria.max_budget == Decimal("8000000")
        assert criteria.amenity_codes == ["parking"]
        mock_client.generate_structured.assert_called_once()

    @patch("app.ai.requirement_extraction.get_llm_client")
    def test_vague_query_raises_in_pipeline(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.generate_structured.return_value = ExtractedRequirements()

        with pytest.raises(InsufficientRequirementsError):
            process_user_query("Show me some properties.")
