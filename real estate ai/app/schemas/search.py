from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class AvailabilityFilter(str, Enum):
    ANY = "any"
    AVAILABLE = "available"
    EXCLUDE_SOLD_OUT = "exclude_sold_out"


class SearchCriteria(BaseModel):
    """Structured search input — no LLM involvement."""

    bhk: Decimal | None = None
    min_budget: Decimal | None = None
    max_budget: Decimal | None = None
    city_id: int | None = None
    city_slug: str | None = None
    locality_ids: list[int] = Field(default_factory=list)
    locality_slugs: list[str] = Field(default_factory=list)
    zone_ids: list[int] = Field(default_factory=list)
    zone_slugs: list[str] = Field(default_factory=list)
    property_type_code: str | None = None
    amenity_codes: list[str] = Field(default_factory=list)
    availability: AvailabilityFilter = AvailabilityFilter.EXCLUDE_SOLD_OUT

    def has_any_criterion(self) -> bool:
        return any(
            [
                self.bhk is not None,
                self.min_budget is not None,
                self.max_budget is not None,
                self.city_id is not None,
                self.city_slug,
                self.locality_ids,
                self.locality_slugs,
                self.zone_ids,
                self.zone_slugs,
                self.property_type_code,
                self.amenity_codes,
            ]
        )


class MatchReasonCode(str, Enum):
    BHK = "bhk_matched"
    BUDGET = "budget_matched"
    CITY = "city_matched"
    LOCALITY = "locality_matched"
    ZONE = "zone_matched"
    PROPERTY_TYPE = "property_type_matched"
    AMENITY = "amenity_matched"
    AVAILABILITY = "availability_matched"


class MatchReason(BaseModel):
    code: MatchReasonCode
    message: str


class ConfigurationSearchResult(BaseModel):
    configuration_id: int
    project_id: int
    project_name: str
    project_slug: str
    bhk: Decimal | None
    price: Decimal | None
    currency: str
    availability_status: str | None
    locality_name: str
    city_name: str
    property_type_code: str | None
    match_reasons: list[MatchReason] = Field(default_factory=list)
    failed_criteria: list[str] = Field(default_factory=list)
    rank_score: int = 0


class SearchOutcomeKind(str, Enum):
    EXACT = "exact_matches"
    PARTIAL = "partial_matches"
    NONE = "no_matches"


class SearchOutcome(BaseModel):
    kind: SearchOutcomeKind
    results: list[ConfigurationSearchResult] = Field(default_factory=list)
    unmatched_requirements: list[str] = Field(default_factory=list)
    message_hint: str | None = None
