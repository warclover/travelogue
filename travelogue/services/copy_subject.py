"""Resolve the primary subject for rule-based copy (services re-export · M-B1)."""

from travelogue.domain.copy_subject import (  # noqa: F401
    GENERIC_PLACES,
    dominant_asset_cities,
    effective_meta_places,
    filter_chapter_places_for_copy,
    is_generic_place,
    narrative_copy_subject,
    place_conflicts_with_title,
    places_user_set,
    suppress_chapter_geo_places,
    user_place_explicit,
)

__all__ = [
    "GENERIC_PLACES",
    "dominant_asset_cities",
    "effective_meta_places",
    "filter_chapter_places_for_copy",
    "is_generic_place",
    "narrative_copy_subject",
    "place_conflicts_with_title",
    "places_user_set",
    "suppress_chapter_geo_places",
    "user_place_explicit",
]
