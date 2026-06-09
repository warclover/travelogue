"""Cover closing helpers: closing asset pick (S1 last screen / S2 last chapter)."""

from __future__ import annotations

from colorsys import rgb_to_hls

from travelogue.render.cover_opening import (
    cover_asset_aspect,
    cover_focal_point,
    cover_use_contain_fit,
)

_EVENING_TAGS = frozenset({"night", "evening", "dusk", "sunset"})
# Align with cover_opening portrait contain threshold: ar >= 1.2 → landscape for web closing.
_LANDSCAPE_MIN_AR = 1.2


def _read_dominant_tone(asset: dict) -> str | None:
    tone = asset.get("dominantTone")
    if isinstance(tone, str) and tone.startswith("#"):
        return tone
    color = asset.get("color")
    if isinstance(color, dict):
        ct = color.get("dominantTone")
        if isinstance(ct, str) and ct.startswith("#"):
            return ct
    return None


def _tone_saturation(tone_hex: str | None) -> float:
    if not tone_hex or len(tone_hex) < 7:
        return 0.5
    try:
        r = int(tone_hex[1:3], 16) / 255.0
        g = int(tone_hex[3:5], 16) / 255.0
        b = int(tone_hex[5:7], 16) / 255.0
        _h, _l, sat = rgb_to_hls(r, g, b)
        return float(sat)
    except (TypeError, ValueError):
        return 0.5


def _asset_valid_for_closing(asset_id: str | None, assets: dict[str, dict]) -> bool:
    if not asset_id or asset_id not in assets:
        return False
    asset = assets[asset_id]
    if asset.get("type") == "video":
        return False
    return bool(asset.get("layoutEligible", True))


def _cover_ids_to_exclude(trip: dict) -> set[str]:
    """Cover asset ids that must not be reused on the closing hero."""
    out: set[str] = set()
    primary = str(trip.get("coverAssetId") or "").strip()
    if primary:
        out.add(primary)
    by_layout = (trip.get("curation") or {}).get("coverByLayout") or {}
    if isinstance(by_layout, dict):
        for value in by_layout.values():
            aid = str(value or "").strip()
            if aid:
                out.add(aid)
    return out


def asset_is_landscape(asset: dict) -> bool:
    ar = cover_asset_aspect(asset)
    return ar is not None and ar >= _LANDSCAPE_MIN_AR


def collect_layout_screen_asset_ids(trip: dict) -> set[str]:
    """Asset ids already placed on layout screens (正文页)."""
    out: set[str] = set()
    for ch in trip.get("chapters") or []:
        for screen in ch.get("screens") or []:
            for slot in screen.get("slots") or []:
                aid = str(slot.get("assetId") or "").strip()
                if aid:
                    out.add(aid)
    return out


def last_screen_asset_id(trip: dict) -> str | None:
    """S1 · last layout-screen primary slot asset."""
    last_id: str | None = None
    for ch in trip.get("chapters") or []:
        for screen in ch.get("screens") or []:
            slots = screen.get("slots") or []
            if not slots:
                continue
            aid = str(slots[0].get("assetId") or "").strip()
            if aid:
                last_id = aid
    return last_id


def _trip_screen_asset_ids_newest_first(trip: dict) -> list[str]:
    """Screen slot assets from trip end → start (deduped)."""
    out: list[str] = []
    seen: set[str] = set()
    for ch in reversed(trip.get("chapters") or []):
        for screen in reversed(ch.get("screens") or []):
            for slot in reversed(screen.get("slots") or []):
                aid = str(slot.get("assetId") or "").strip()
                if aid and aid not in seen:
                    seen.add(aid)
                    out.append(aid)
    return out


def _chapter_screen_asset_ids(chapter: dict) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for screen in chapter.get("screens") or []:
        for slot in screen.get("slots") or []:
            aid = str(slot.get("assetId") or "").strip()
            if aid and aid not in seen:
                seen.add(aid)
                out.append(aid)
    return out


def _closing_curated_score(asset: dict) -> float:
    """Lower is better: prefer low saturation and evening/night tags."""
    sat = _tone_saturation(_read_dominant_tone(asset))
    tags = asset.get("subjectTags") or asset.get("tags") or []
    tag_set = {str(t).casefold() for t in tags if t}
    evening = 0.0
    if tag_set & {t.casefold() for t in _EVENING_TAGS}:
        evening = -0.22
    return sat + evening


def _unused_closing_asset_ids(
    trip: dict,
    assets: dict[str, dict],
    *,
    screen_used_ids: set[str],
    exclude_ids: set[str],
) -> list[str]:
    """Layout-eligible assets not on any screen and not the cover (soft fresh pick)."""
    out: list[str] = []
    for asset in trip.get("assets") or []:
        aid = str(asset.get("id") or "").strip()
        if not _asset_valid_for_closing(aid, assets):
            continue
        if aid in screen_used_ids or aid in exclude_ids:
            continue
        out.append(aid)
    out.sort(key=lambda aid: _closing_curated_score(assets[aid]))
    return out


def _closing_candidate_ids(
    trip: dict,
    assets: dict[str, dict],
    *,
    screen_used_ids: set[str],
    exclude_ids: set[str],
) -> list[str]:
    """Unused pool first, then screen assets newest-first (soft dedupe)."""
    ordered: list[str] = []
    seen: set[str] = set()
    for aid in _unused_closing_asset_ids(
        trip, assets, screen_used_ids=screen_used_ids, exclude_ids=exclude_ids
    ):
        if aid not in seen:
            seen.add(aid)
            ordered.append(aid)
    for aid in _trip_screen_asset_ids_newest_first(trip):
        if aid in exclude_ids or aid in seen:
            continue
        seen.add(aid)
        ordered.append(aid)
    return ordered


def _pick_best_closing(
    ordered_aids: list[str],
    assets: dict[str, dict],
    *,
    prefer_landscape: bool,
    screen_used_ids: set[str],
    exclude_ids: set[str],
) -> str | None:
    """Rank: (1) not on other pages (2) landscape if web (3) tone (4) recency."""
    eligible = [
        aid
        for aid in ordered_aids
        if _asset_valid_for_closing(aid, assets) and aid not in exclude_ids
    ]
    if not eligible:
        return None

    def rank(aid: str) -> tuple[int, int, float, int]:
        asset = assets[aid]
        on_page = aid in screen_used_ids
        landscape = asset_is_landscape(asset)
        return (
            1 if on_page else 0,
            0 if (not prefer_landscape or landscape) else 1,
            _closing_curated_score(asset),
            ordered_aids.index(aid),
        )

    return min(eligible, key=rank)


def last_chapter_curated_asset_id(
    trip: dict,
    assets: dict[str, dict],
    *,
    prefer_landscape: bool = False,
    screen_used_ids: set[str] | None = None,
    exclude_ids: set[str] | None = None,
) -> str | None:
    """S2 · pick from last chapter screens (low sat / evening bias)."""
    chapters = trip.get("chapters") or []
    if not chapters:
        return None
    used = screen_used_ids if screen_used_ids is not None else collect_layout_screen_asset_ids(trip)
    excluded = exclude_ids if exclude_ids is not None else _cover_ids_to_exclude(trip)
    candidates = [aid for aid in _chapter_screen_asset_ids(chapters[-1]) if aid not in excluded]
    return _pick_best_closing(
        candidates,
        assets,
        prefer_landscape=prefer_landscape,
        screen_used_ids=used,
        exclude_ids=excluded,
    )


def _resolve_closing_allow_cover(
    trip: dict,
    assets: dict[str, dict],
    *,
    prefer_landscape: bool,
    screen_used: set[str],
) -> str | None:
    """Last resort: allow cover reuse so the closing screen still has a hero."""
    ordered = _closing_candidate_ids(
        trip, assets, screen_used_ids=screen_used, exclude_ids=set()
    )
    picked = _pick_best_closing(
        ordered,
        assets,
        prefer_landscape=prefer_landscape,
        screen_used_ids=screen_used,
        exclude_ids=set(),
    )
    if picked:
        return picked
    return last_chapter_curated_asset_id(
        trip,
        assets,
        prefer_landscape=prefer_landscape,
        screen_used_ids=screen_used,
        exclude_ids=set(),
    )


def resolve_closing_asset_id(
    trip: dict,
    assets: dict[str, dict],
    *,
    prefer_landscape: bool = False,
) -> str | None:
    """Pick closing hero: prefer fresh (unused) assets, then screen tail.

    Web: landscape preferred when ``prefer_landscape``. Reusing a screen image is
    allowed when no better candidate exists (soft dedupe, not enforced).
    Cover ids are avoided when possible; if no other eligible asset exists, cover
    may be reused so the closing screen is not dropped at render time.
    """
    screen_used = collect_layout_screen_asset_ids(trip)
    exclude_ids = _cover_ids_to_exclude(trip)
    ordered = _closing_candidate_ids(
        trip, assets, screen_used_ids=screen_used, exclude_ids=exclude_ids
    )
    picked = _pick_best_closing(
        ordered,
        assets,
        prefer_landscape=prefer_landscape,
        screen_used_ids=screen_used,
        exclude_ids=exclude_ids,
    )
    if picked:
        return picked
    picked = last_chapter_curated_asset_id(
        trip,
        assets,
        prefer_landscape=prefer_landscape,
        screen_used_ids=screen_used,
        exclude_ids=exclude_ids,
    )
    if picked:
        return picked
    return _resolve_closing_allow_cover(
        trip, assets, prefer_landscape=prefer_landscape, screen_used=screen_used
    )


def show_closing_title(title: str) -> bool:
    return bool((title or "").strip())


closing_focal_point = cover_focal_point
closing_use_contain_fit = cover_use_contain_fit
