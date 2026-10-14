"""
Request and response schemas for the AI search REST API.

These wrap the existing internal schemas (SearchOutcome, ConfigurationSearchResult)
in a consistent, API-level envelope that is easy to understand in Swagger.
"""
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.search import ConfigurationSearchResult, SearchOutcomeKind


# ── Request ───────────────────────────────────────────────────────────────────

class AISearchRequest(BaseModel):
    """Natural-language property search request."""

    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        examples=["I want a 3 BHK in New Town under 80 lakh with parking"],
        description="A natural-language description of the property you are looking for.",
    )


# ── Response ──────────────────────────────────────────────────────────────────

class AISearchResponse(BaseModel):
    """
    Successful (or gracefully-degraded) search response.
    `status` mirrors SearchOutcomeKind values so clients can branch on it.
    """

    status: str = Field(
        description=(
            "One of: 'exact_matches', 'partial_matches', 'no_matches'. "
            "Always present on a 200 response."
        )
    )
    query: str = Field(description="The original query, echoed for traceability.")
    result_count: int = Field(description="Number of results returned.")
    results: list[ConfigurationSearchResult] = Field(
        default_factory=list,
        description="Matching property configurations from PostgreSQL.",
    )
    unmatched_requirements: list[str] = Field(
        default_factory=list,
        description="Criteria from the query that could not be satisfied.",
    )
    message: str | None = Field(
        None,
        description="Human-readable hint about the result quality.",
    )

    @classmethod
    def from_outcome(cls, query: str, outcome: Any) -> "AISearchResponse":
        from app.schemas.search import SearchOutcome
        return cls(
            status=outcome.kind.value,
            query=query,
            result_count=len(outcome.results),
            results=outcome.results,
            unmatched_requirements=outcome.unmatched_requirements,
            message=outcome.message_hint,
        )


class AISearchErrorResponse(BaseModel):
    """Returned for 4xx/5xx responses from the AI search endpoint."""

    status: str = Field(description="Error kind: 'insufficient_requirements', 'extraction_failed', 'search_error'.")
    query: str = Field(description="The original query, echoed for traceability.")
    message: str = Field(description="Human-readable explanation of the error.")
