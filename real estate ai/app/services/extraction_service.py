import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from app.ai.requirement_extraction import BudgetUnit, ExtractedRequirements, extract_requirements
from app.schemas.search import SearchCriteria


# ── Budget unit multipliers ─────────────────────────────────────────────────

_BUDGET_MULTIPLIERS: dict[BudgetUnit, int] = {
    BudgetUnit.RUPEES: 1,
    BudgetUnit.THOUSAND: 1_000,
    BudgetUnit.LAKH: 100_000,
    BudgetUnit.CRORE: 10_000_000,
}


def _convert_budget(number: Optional[float], unit: Optional[BudgetUnit]) -> Optional[Decimal]:
    """
    Deterministically convert a raw budget number + unit into INR as Decimal.
    Returns None if either component is absent.
    """
    if number is None or unit is None:
        return None
    multiplier = _BUDGET_MULTIPLIERS[unit]
    try:
        return Decimal(str(number)) * Decimal(multiplier)
    except InvalidOperation:
        return None


def _to_slug(text: str) -> str:
    """Convert text to a basic slug format."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


# ── Validation ───────────────────────────────────────────────────────────────

class InsufficientRequirementsError(ValueError):
    """
    Raised when the extracted requirements contain no usable search criterion.
    The caller should ask the user to clarify.
    """
    pass


def _has_meaningful_criterion(requirements: ExtractedRequirements) -> bool:
    """Return True if at least one useful search field was extracted."""
    return any([
        requirements.bhk is not None,
        bool(requirements.localities),
        bool(requirements.city),
        requirements.max_budget_number is not None,
        requirements.min_budget_number is not None,
        bool(requirements.property_type),
        bool(requirements.amenities),
    ])


# ── Core mapping ─────────────────────────────────────────────────────────────

def build_search_criteria(requirements: ExtractedRequirements) -> SearchCriteria:
    """
    Convert the LLM's extracted requirements into the deterministic SearchCriteria schema.

    Raises:
        InsufficientRequirementsError: if no meaningful criterion was extracted.
    """
    if not _has_meaningful_criterion(requirements):
        raise InsufficientRequirementsError(
            "No searchable criteria were found in the query. "
            "Please specify at least a location, BHK, budget, or property type."
        )

    criteria = SearchCriteria()

    # BHK — extracted as string to avoid float imprecision
    if requirements.bhk is not None:
        try:
            criteria.bhk = Decimal(requirements.bhk)
        except InvalidOperation:
            pass  # silently drop unparseable BHK; don't corrupt the search

    # Budget — deterministic Python conversion, no LLM arithmetic
    criteria.min_budget = _convert_budget(
        requirements.min_budget_number, requirements.min_budget_unit
    )
    criteria.max_budget = _convert_budget(
        requirements.max_budget_number, requirements.max_budget_unit
    )

    if requirements.city:
        criteria.city_slug = _to_slug(requirements.city)

    if requirements.localities:
        criteria.locality_slugs = [_to_slug(loc) for loc in requirements.localities]

    if requirements.property_type:
        criteria.property_type_code = _to_slug(requirements.property_type)

    if requirements.amenities:
        criteria.amenity_codes = [_to_slug(amenity) for amenity in requirements.amenities]

    return criteria


def process_user_query(query: str) -> SearchCriteria:
    """
    End-to-end flow: Natural language query → LLM Extraction → Validation → SearchCriteria.

    Raises:
        InsufficientRequirementsError: if the query yields no usable criteria.
    """
    requirements = extract_requirements(query)
    return build_search_criteria(requirements)
