from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.ai.llm_client import get_llm_client


class BudgetUnit(str, Enum):
    RUPEES = "rupees"
    THOUSAND = "thousand"
    LAKH = "lakh"
    CRORE = "crore"


class ExtractedRequirements(BaseModel):
    """
    Structured requirements extracted from a user's natural language query.
    Gemini extracts raw values only. No arithmetic is performed by the LLM.
    """

    bhk: Optional[str] = Field(
        None,
        description=(
            "Number of bedrooms as a string. E.g., '3' for 3 BHK, '2' for 2 BHK. "
            "If not mentioned, leave null."
        ),
    )
    localities: List[str] = Field(
        default_factory=list,
        description="List of locality names mentioned in the query, exactly as stated.",
    )
    city: Optional[str] = Field(
        None,
        description="City name if mentioned, exactly as stated. E.g., 'Kolkata', 'Mumbai'.",
    )
    max_budget_number: Optional[float] = Field(
        None,
        description=(
            "The numeric part of the maximum budget only. E.g., for '80 lakh' extract 80. "
            "For '1.2 crore' extract 1.2. Do NOT convert to rupees."
        ),
    )
    max_budget_unit: Optional[BudgetUnit] = Field(
        None,
        description=(
            "The unit of the maximum budget. One of: 'rupees', 'thousand', 'lakh', 'crore'. "
            "Leave null if no maximum budget is mentioned."
        ),
    )
    min_budget_number: Optional[float] = Field(
        None,
        description=(
            "The numeric part of the minimum budget only. E.g., for '50 lakh' extract 50. "
            "Do NOT convert to rupees."
        ),
    )
    min_budget_unit: Optional[BudgetUnit] = Field(
        None,
        description=(
            "The unit of the minimum budget. One of: 'rupees', 'thousand', 'lakh', 'crore'. "
            "Leave null if no minimum budget is mentioned."
        ),
    )
    property_type: Optional[str] = Field(
        None,
        description="Property type if mentioned. E.g., 'apartment', 'villa', 'independent house'.",
    )
    amenities: List[str] = Field(
        default_factory=list,
        description="List of amenities requested. E.g., ['parking', 'gym', 'swimming pool'].",
    )


def extract_requirements(query: str) -> ExtractedRequirements:
    """
    Uses Gemini to extract structured real-estate search requirements from a raw query.
    The LLM only extracts raw values — all numeric conversions happen in Python.
    """
    client = get_llm_client()
    prompt = f"""
    You are a real-estate search assistant. Extract search requirements from the user query below.
    Return ONLY the JSON matching the required schema — do NOT perform any arithmetic or unit conversions.

    Rules:
    - For budgets, extract the number and unit SEPARATELY. Never multiply or convert.
      Example: "80 lakh" → max_budget_number=80, max_budget_unit="lakh"
      Example: "1.2 crore" → max_budget_number=1.2, max_budget_unit="crore"
    - For BHK, extract the digit only as a string. Example: "3 BHK" → bhk="3"
    - Extract locality and city names exactly as written.
    - Extract amenities as plain words (e.g., "parking", "gym").
    - If a field is not mentioned, leave it null or empty.

    User Query: "{query}"
    """
    return client.generate_structured(prompt=prompt, schema=ExtractedRequirements)
