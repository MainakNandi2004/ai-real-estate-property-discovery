from decimal import Decimal

from app.models import PropertyConfiguration, ProjectAmenity
from app.schemas.search import MatchReason, MatchReasonCode, SearchCriteria


def _project_amenity_codes(configuration: PropertyConfiguration) -> set[str]:
    project = configuration.project
    return {link.amenity.code for link in project.amenity_links if link.amenity}


class MatchingService:
    """Deterministic match evaluation against database-backed rows."""

    def evaluate(
        self,
        configuration: PropertyConfiguration,
        criteria: SearchCriteria,
        *,
        strict: bool = True,
    ) -> tuple[list[MatchReason], list[str]]:
        reasons: list[MatchReason] = []
        failed: list[str] = []

        project = configuration.project
        locality = project.locality
        city = locality.city

        if criteria.bhk is not None:
            if configuration.bhk == criteria.bhk:
                reasons.append(
                    MatchReason(
                        code=MatchReasonCode.BHK,
                        message=f"BHK matches requested {criteria.bhk}.",
                    )
                )
            elif strict:
                failed.append(f"bhk:{criteria.bhk}")

        if criteria.min_budget is not None or criteria.max_budget is not None:
            price = configuration.price
            if price is None:
                if strict:
                    failed.append("budget:price_unknown")
            else:
                budget_ok = True
                if criteria.min_budget is not None and price < criteria.min_budget:
                    budget_ok = False
                if criteria.max_budget is not None and price > criteria.max_budget:
                    budget_ok = False
                if budget_ok:
                    reasons.append(
                        MatchReason(
                            code=MatchReasonCode.BUDGET,
                            message="Price is within the stated budget range.",
                        )
                    )
                elif strict:
                    failed.append("budget")

        if criteria.city_id is not None:
            if city.id == criteria.city_id:
                reasons.append(
                    MatchReason(
                        code=MatchReasonCode.CITY,
                        message=f"Located in city {city.name}.",
                    )
                )
            elif strict:
                failed.append(f"city_id:{criteria.city_id}")

        if criteria.city_slug:
            if city.slug == criteria.city_slug:
                reasons.append(
                    MatchReason(
                        code=MatchReasonCode.CITY,
                        message=f"Located in city {city.name}.",
                    )
                )
            elif strict:
                failed.append(f"city:{criteria.city_slug}")

        if criteria.locality_ids or criteria.locality_slugs:
            locality_ok = False
            if criteria.locality_ids and locality.id in criteria.locality_ids:
                locality_ok = True
            if criteria.locality_slugs and locality.slug in criteria.locality_slugs:
                locality_ok = True
            if locality_ok:
                reasons.append(
                    MatchReason(
                        code=MatchReasonCode.LOCALITY,
                        message=f"Located in {locality.name}.",
                    )
                )
            elif strict:
                failed.append("locality")

        if criteria.zone_ids or criteria.zone_slugs:
            zone_slugs = {link.zone.slug for link in locality.zone_links if link.zone}
            zone_ids = {link.zone.id for link in locality.zone_links if link.zone}
            zone_ok = False
            if criteria.zone_ids and zone_ids.intersection(criteria.zone_ids):
                zone_ok = True
            if criteria.zone_slugs and zone_slugs.intersection(set(criteria.zone_slugs)):
                zone_ok = True
            if zone_ok:
                reasons.append(
                    MatchReason(
                        code=MatchReasonCode.ZONE,
                        message="Located in a matching area zone.",
                    )
                )
            elif strict:
                failed.append("zone")

        if criteria.property_type_code:
            code = project.property_type.code if project.property_type else None
            if code == criteria.property_type_code:
                reasons.append(
                    MatchReason(
                        code=MatchReasonCode.PROPERTY_TYPE,
                        message=f"Property type is {code}.",
                    )
                )
            elif strict:
                failed.append(f"property_type:{criteria.property_type_code}")

        if criteria.amenity_codes:
            codes = _project_amenity_codes(configuration)
            missing = [c for c in criteria.amenity_codes if c not in codes]
            if not missing:
                reasons.append(
                    MatchReason(
                        code=MatchReasonCode.AMENITY,
                        message="Includes all requested amenities.",
                    )
                )
            elif strict:
                failed.append(f"amenities:{','.join(missing)}")

        if criteria.availability.value != "any":
            status = configuration.availability_status
            if criteria.availability.value == "available" and status == "available":
                reasons.append(
                    MatchReason(
                        code=MatchReasonCode.AVAILABILITY,
                        message="Marked as available.",
                    )
                )
            elif criteria.availability.value == "exclude_sold_out" and status != "sold_out":
                reasons.append(
                    MatchReason(
                        code=MatchReasonCode.AVAILABILITY,
                        message="Not marked as sold out.",
                    )
                )
            elif strict and criteria.availability.value == "available":
                failed.append("availability")

        return reasons, failed

    def rank_score(self, reasons: list[MatchReason], weights=None) -> int:
        from app.services.search.ranking_weights import DEFAULT_RANKING_WEIGHTS

        w = weights or DEFAULT_RANKING_WEIGHTS
        score = 0
        for reason in reasons:
            if reason.code == MatchReasonCode.BHK:
                score += w.bhk
            elif reason.code == MatchReasonCode.BUDGET:
                score += w.budget
            elif reason.code == MatchReasonCode.CITY:
                score += w.city
            elif reason.code == MatchReasonCode.LOCALITY:
                score += w.locality
            elif reason.code == MatchReasonCode.ZONE:
                score += w.zone
            elif reason.code == MatchReasonCode.PROPERTY_TYPE:
                score += w.property_type
            elif reason.code == MatchReasonCode.AMENITY:
                score += w.amenity
            elif reason.code == MatchReasonCode.AVAILABILITY:
                score += w.availability
        return score
