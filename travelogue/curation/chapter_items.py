"""Compact chapter items (shim + render resolver)."""

from travelogue.layout_contract.chapter_items import *  # noqa: F403

def resolve_chapter_items_for_render(
    chapter: dict,
    *,
    export_layout: str,
    layout_engine: str,
    is_longshot: bool,
    aspects: dict[str, str],
    assets_map: dict[str, dict],
    trip_photo_total: int,
) -> list[dict]:
    """
    Pick items[] for HTML render.

    - longshot: one card per screen slot (vertical stack)
    - mobile + screens trip: re-run mobile layout planner (trip.json items may be schema stub)
    - otherwise: stored items[]
    """
    if is_longshot and chapter.get("screens"):
        return flatten_screens_to_items(chapter)

    from travelogue.curation.layout_planner import (
        _apply_gallery_layout,
        plan_chapter_items,
    )
    from travelogue.curation.mobile_layout_state import (
        MobilePuzzlePlannerState,
        mobile_puzzle_enabled,
    )
    from travelogue.curation.screen_planner import LAYOUT_ENGINE_LEGACY

    is_mobile = export_layout == "mobile"
    is_stub = bool((chapter.get("curation") or {}).get("layoutStub"))
    if not (
        layout_engine == LAYOUT_ENGINE_LEGACY
        and is_mobile
        and chapter.get("screens")
        and is_stub
    ):
        return list(chapter.get("items") or [])

    asset_ids = collect_screen_asset_ids(chapter)
    if not asset_ids:
        return list(chapter.get("items") or [])

    puzzle_state = None
    if mobile_puzzle_enabled(trip_photo_total):
        puzzle_state = MobilePuzzlePlannerState.from_trip_total(trip_photo_total)
        puzzle_state.begin_chapter()

    items = plan_chapter_items(
        asset_ids,
        aspects,
        export_layout="mobile",
        assets=assets_map,
        trip_photo_total=trip_photo_total,
        puzzle_state=puzzle_state,
    )
    if chapter.get("patternId") == "gallery":
        if chapter.get("screens"):
            return flatten_screens_to_items(chapter)
        items = _apply_gallery_layout(items, export_layout="mobile")
    return items


def compact_chapter_items_for_screens(chapters: list[dict]) -> None:
    """
    When layoutEngine=screens, items[] is a legacy/mobile stub (≤8 blocks).

    Web render reads screens[]; compact items keeps trip.json schema-valid.
    """
    for ch in chapters:
        if not ch.get("screens"):
            continue
        stub_items = items_from_screens(ch)
        if stub_items:
            ch["items"] = stub_items
            ch_cur = ch.setdefault("curation", {})
            ch_cur["layoutStub"] = True
        elif len(ch.get("items") or []) > MAX_CHAPTER_ITEMS:
            flat: list[str] = []
            for it in ch.get("items") or []:
                for aid in item_asset_ids(it):
                    if aid not in flat:
                        flat.append(aid)
            ch["items"] = items_from_asset_ids(flat)
            ch.setdefault("curation", {})["layoutStub"] = True


def collect_displayed_asset_ids(
    chapters: list[dict],
    *,
    extra_asset_ids: list[str] | None = None,
) -> list[str]:
    """Ordered unique ids on screens plus optional cover/extra heroes (Phase 15 · D-MCS-09)."""
    seen: set[str] = set()
    out: list[str] = []
    for aid in extra_asset_ids or []:
        if aid and aid not in seen:
            seen.add(aid)
            out.append(aid)
    for ch in chapters:
        for aid in collect_screen_asset_ids(ch):
            if aid not in seen:
                seen.add(aid)
                out.append(aid)
    return out


def summarize_screen_patterns(chapters: list[dict]) -> dict[str, int]:
    """Count screen patternId usage across chapters (layout observability)."""
    counts: dict[str, int] = {}
    for ch in chapters:
        for sc in ch.get("screens") or []:
            pid = str(sc.get("patternId") or "unknown")
            counts[pid] = counts.get(pid, 0) + 1
    return counts
