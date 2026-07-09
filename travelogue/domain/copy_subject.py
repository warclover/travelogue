"""Resolve the primary subject for rule-based copy (title vs place vs EXIF)."""

from __future__ import annotations

from collections import Counter

GENERIC_PLACES = frozenset({"旅途", "未知", ""})


def is_generic_place(name: str | None) -> bool:
    cleaned = (name or "").strip()
    return not cleaned or cleaned in GENERIC_PLACES


def dominant_asset_cities(assets: list[dict]) -> list[str]:
    cities: list[str] = []
    for asset in assets:
        city = (asset.get("place") or {}).get("city")
        if isinstance(city, str):
            cleaned = city.strip()
            if cleaned and not is_generic_place(cleaned):
                cities.append(cleaned)
    if not cities:
        return []
    return [name for name, _ in Counter(cities).most_common(3)]


def _place_matches_geo(place: str, cities: list[str]) -> bool:
    for city in cities:
        if not city:
            continue
        if city == place or city in place or place in city:
            return True
    return False


def place_conflicts_with_title(
    title: str,
    place: str,
    assets: list[dict] | None,
) -> bool:
    """True when GPS-derived place likely overrides a thematic magazine title."""
    if is_generic_place(title) or is_generic_place(place):
        return False
    if place in title or title in place:
        return False
    if not assets:
        return False
    return _place_matches_geo(place, dominant_asset_cities(assets))


def places_user_set(intent: dict | None) -> bool:
    return bool((intent or {}).get("placesUserSet"))


def narrative_copy_subject(
    meta: dict,
    *,
    intent: dict | None = None,
    assets: list[dict] | None = None,
) -> str:
    """Prefer magazine title unless the user explicitly set a non-conflicting place."""
    title = (meta.get("title") or "").strip()
    places = [str(p).strip() for p in (meta.get("places") or []) if str(p).strip()]
    place = places[0] if places else "旅途"

    if not places_user_set(intent):
        if title:
            return title[:32]
        return place[:32] if not is_generic_place(place) else "旅途"

    if is_generic_place(place) and title:
        return title[:32]

    if title and place_conflicts_with_title(title, place, assets):
        return title[:32]

    return place[:32]


def user_place_explicit(meta: dict, *, intent: dict | None = None) -> bool:
    if not places_user_set(intent):
        return False
    places = [str(p).strip() for p in (meta.get("places") or []) if str(p).strip()]
    return bool(places) and not is_generic_place(places[0])


def suppress_chapter_geo_places(
    meta: dict,
    *,
    intent: dict | None = None,
    assets: list[dict] | None = None,
) -> bool:
    """Hide GPS-derived chapter/meta places when the magazine title is the editorial subject."""
    if places_user_set(intent):
        return False
    title = (meta.get("title") or "").strip()
    if not title:
        return False
    places = [str(p).strip() for p in (meta.get("places") or []) if str(p).strip()]
    place = places[0] if places else ""
    if not place or is_generic_place(place):
        return True
    return place_conflicts_with_title(title, place, assets)


def filter_chapter_places_for_copy(
    chapter_places: list[str] | None,
    meta: dict,
    *,
    intent: dict | None = None,
    assets: list[dict] | None = None,
) -> list[str]:
    if suppress_chapter_geo_places(meta, intent=intent, assets=assets):
        return []
    return [str(p).strip() for p in (chapter_places or []) if str(p).strip()]


def effective_meta_places(
    meta: dict,
    *,
    intent: dict | None = None,
    assets: list[dict] | None = None,
) -> list[str]:
    """Places used for anchor scoring — thematic title when GPS places are suppressed."""
    if suppress_chapter_geo_places(meta, intent=intent, assets=assets):
        subject = narrative_copy_subject(meta, intent=intent, assets=assets)
        if subject and not is_generic_place(subject):
            return [subject]
        return []
    return [str(p).strip() for p in (meta.get("places") or []) if str(p).strip()]
