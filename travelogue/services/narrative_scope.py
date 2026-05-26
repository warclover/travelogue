"""Narrative copy scope: frame-only vs full chapter/caption generation."""

from __future__ import annotations

from travelogue.constants import VALID_NARRATIVE_SCOPES
from travelogue.curation.asset_caption import (
    apply_caption_to_trip,
    chapter_caption_asset_ids,
    find_item_for_asset,
    resolve_caption,
)
from travelogue.services.errors import NarrateError

SCOPE_FRAME = "frame"
SCOPE_FRAME_CHAPTERS = "frame_chapters"
SCOPE_FULL = "full"
VALID_SCOPES = VALID_NARRATIVE_SCOPES


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


def _chapter_index_values(chapters: list[dict]) -> list[int]:
    out: list[int] = []
    for ch in chapters:
        idx = int(ch.get("index") or 0)
        if idx > 0:
            out.append(idx)
    return out


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
    indices = _chapter_index_values(chapters)
    if not indices:
        return False
    idx = int(chapter.get("index") or 0)
    return idx == min(indices) or idx == max(indices)


def chapter_has_caption_slots(chapter: dict, trip: dict) -> bool:
    """True when scope=full would plan at least one caption for this chapter."""
    assets = {a["id"]: a for a in trip.get("assets") or [] if a.get("id")}
    item_by_asset = {
        it.get("assetId"): it
        for it in chapter.get("items") or []
        if it.get("type") == "media-card" and it.get("assetId")
    }
    for aid in chapter_caption_asset_ids(chapter):
        item = item_by_asset.get(aid)
        if item and item.get("edited"):
            continue
        asset = assets.get(aid)
        if asset and asset.get("edited"):
            continue
        if asset and asset.get("skipCaption"):
            continue
        return True
    return False


def chapter_narrate_allowed(chapter: dict, trip: dict, scope: str) -> bool:
    chapters = trip.get("chapters") or []
    scope = normalize_scope(scope)
    if chapter_lead_allowed(chapter, chapters, scope):
        return True
    if captions_allowed(scope) and chapter_has_caption_slots(chapter, trip):
        return True
    return False


def assert_chapter_narrate_allowed(trip: dict, chapter_id: str, scope: str) -> None:
    chapters = trip.get("chapters") or []
    chapter = next((c for c in chapters if c.get("id") == chapter_id), None)
    if chapter is None:
        raise NarrateError("E_NARRATE_CHAPTER", f"unknown chapter {chapter_id!r}")
    if chapter_narrate_allowed(chapter, trip, scope):
        return
    scope_val = normalize_scope(scope)
    raise NarrateError(
        "E_NARRATE_SCOPE",
        f"chapter {chapter_id!r} has no narratable fields under scope {scope_val!r} "
        "(frame: meta hook/epilogue only; frame_chapters: first/last chapter leads + hook/epilogue)",
    )


def resolve_cover_show_title(trip: dict) -> bool:
    """
    Whether to overlay meta.title on the cover hero.

    frame / frame_chapters: hide (hook + trip-meta carry place/date).
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
    return False


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
