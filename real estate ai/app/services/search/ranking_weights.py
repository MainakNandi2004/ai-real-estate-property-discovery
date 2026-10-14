from dataclasses import dataclass


@dataclass(frozen=True)
class RankingWeights:
    """Explainable integer weights — not percentages."""

    bhk: int = 10
    budget: int = 10
    city: int = 8
    locality: int = 8
    zone: int = 8
    property_type: int = 6
    amenity: int = 5
    availability: int = 4


DEFAULT_RANKING_WEIGHTS = RankingWeights()
