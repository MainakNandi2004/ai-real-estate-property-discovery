from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session

from app.ai.requirement_extraction import extract_requirements
from app.schemas.search import SearchCriteria, SearchOutcome, SearchOutcomeKind
from app.services.extraction_service import (
    InsufficientRequirementsError,
    build_search_criteria,
)
from app.services.search.property_search_service import PropertySearchService


class AISearchErrorKind(str, Enum):
    INSUFFICIENT_REQUIREMENTS = "insufficient_requirements"
    EXTRACTION_FAILED = "extraction_failed"
    SEARCH_ERROR = "search_error"


@dataclass(frozen=True)
class AISearchError:
    """
    Returned instead of raising when the pipeline cannot produce a valid search.
    Callers inspect `kind` to decide how to respond to the user.
    """

    kind: AISearchErrorKind
    message: str


class AISearchService:
    """
    Thin pipeline: natural-language query → AI extraction → PropertySearchService.

    Responsibilities:
    - Delegate natural-language parsing to the extraction layer.
    - Validate the result into a SearchCriteria.
    - Pass SearchCriteria to the EXISTING, unmodified PropertySearchService.
    - Never allow Gemini to touch PostgreSQL.
    - Never invent property data.

    This class does NOT subclass or modify PropertySearchService.
    """

    def __init__(self, session: Session, *, limit: int = 50) -> None:
        self._search_service = PropertySearchService(session)
        self._limit = limit

    def search_from_query(
        self, query: str
    ) -> SearchOutcome | AISearchError:
        """
        Run the full AI → search pipeline.

        Returns:
            SearchOutcome  — on success (may be EXACT, PARTIAL, or NONE).
            AISearchError  — on pipeline failure (extraction error, vague query, etc.).
        """
        # ── Step 1: AI extraction ──────────────────────────────────────────
        try:
            requirements = extract_requirements(query)
        except Exception as exc:  # noqa: BLE001 — surface Gemini SDK / network errors
            return AISearchError(
                kind=AISearchErrorKind.EXTRACTION_FAILED,
                message=f"Could not extract requirements from your query: {exc}",
            )

        # ── Step 2: Validation → SearchCriteria ───────────────────────────
        try:
            criteria: SearchCriteria = build_search_criteria(requirements)
        except InsufficientRequirementsError as exc:
            return AISearchError(
                kind=AISearchErrorKind.INSUFFICIENT_REQUIREMENTS,
                message=str(exc),
            )

        # ── Step 3: Deterministic search via existing service ─────────────
        try:
            return self._search_service.search(criteria, limit=self._limit)
        except Exception as exc:  # noqa: BLE001 — surface DB errors
            return AISearchError(
                kind=AISearchErrorKind.SEARCH_ERROR,
                message=f"Search failed: {exc}",
            )
