"""Narrative copy scope: frame-only vs full chapter/caption generation."""

from __future__ import annotations

from travelogue.curation.asset_caption import (
    apply_caption_to_trip,
    chapter_caption_asset_ids,
    find_item_for_asset,
    resolve_caption,
)

SCOPE_FRAME = "frame"
SCOPE_FRAME_CHAPTERS = "frame_chapters"
SCOPE_FULL = "full"
VALID_SCOPES = frozenset({SCOPE_FRAME, SCOPE_FRAME_CHAPTERS, SCOPE_FULL})


def normalize_scope(raw: str | None) -> str:
    val = str(raw or SCOPE_FRAME).strip().lower()
    if val not in VALID_SCOPES:
        return SCOPE_FRAME
    return val


def resolve_narrative_scope(*, override: str | None = None) -> str:
    if override is not None:
        return normalize_scope(override)
    from travelogue.config import get_config

    return normalize_scope(get_config().narrative.scope)


def captions_allowed(scope: str) -> bool:
    return normalize_scope(scope) == SCOPE_FULL


def chapter_lead_allowed(
    chapter: dict,
    chapters: list[dict],
    scope: str,
) -> bool:
    scope = normalize_scope(scope)
    if scope == SCOPE_FULL:
        return True
    if scope == SCOPE_FRAME:
        return False
    idx = int(chapter.get("index") or 0)
    total = len(chapters)
    if total <= 0:
        return False
    return idx == 1 or idx >= total


def resolve_cover_show_title(trip: dict) -> bool:
    """
    Whether to overlay meta.title on the cover hero.

    frame / frame_chapters: hide when title equals the primary place (hook carries narrative).
    full: show whenever title is set.
    """
    meta = trip.get("meta") or {}
    title = (meta.get("title") or "").strip()
    if not title:
        return False
    scope_raw = (trip.get("curation") or {}).get("narrativeScope")
    scope = normalize_scope(scope_raw) if scope_raw else resolve_narrative_scope()
    if scope == SCOPE_FULL:
        return True
    places = meta.get("places") or []
    primary_place = (places[0] or "").strip() if places else ""
    if primary_place and title == primary_place:
        return False
    return True


def apply_scope_cleanup(trip: dict, scope: str) -> list[str]:
    """
    Remove copy disallowed by scope (preserves user-edited fields).
    Cleared captions set skipCaption so later narrate runs do not refill them.
    """
    scope = normalize_scope(scope)
    if scope == SCOPE_FULL:
        return []

    chapters = trip.get("chapters") or []
    assets = {a["id"]: a for a in trip.get("assets") or [] if a.get("id")}
    cleared: list[str] = []

    if not captions_allowed(scope):
        for ch in chapters:
            for aid in chapter_caption_asset_ids(ch):
                item = find_item_for_asset(ch, aid)
                if item and item.get("edited"):
                    continue
                asset = assets.get(aid)
                if asset and asset.get("edited"):
                    continue
                if not resolve_caption(item, asset).strip():
                    continue
                apply_caption_to_trip(trip, aid, "")
                cleared.append(f"assets.{aid}.caption")

    for ch in chapters:
        if chapter_lead_allowed(ch, chapters, scope):
            continue
        if ch.get("edited"):
            continue
        if (ch.get("lead") or "").strip():
            ch.pop("lead", None)
            cleared.append(f"chapters.{ch.get('id')}.lead")

    return cleared
