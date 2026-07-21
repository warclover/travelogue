"""Compact chapter items (shim + render resolver)."""

from travelogue.layout_contract.chapter_items import *  # noqa: F403,F405


def resolve_chapter_items_for_render(
    chapter: dict,
    *,
    export_layout: str,
    layout_engine: str,
    is_longshot: bool,
    aspects: dict[str, str],
    assets_map: dict[str, dict],
    trip_photo_total: int,
    compact_longshot: bool = False,
) -> list[dict]:
    """
    Pick items[] for HTML render.

    - longshot: ADR-020 / LTN B2 · respect preserveGroup (stack / badge / flatten)
    - mobile + screens trip: re-run mobile layout planner (trip.json items may be schema stub)
    - otherwise: stored items[]
    """
    if is_longshot and chapter.get("screens"):
        return screens_to_longshot_items(chapter, compact=compact_longshot)

    from travelogue.curation.layout_planner import (
        _apply_gallery_layout,
        plan_chapter_items,
    )
    from travelogue.curation.mobile_layout_state import (
        MobilePuzzlePlannerState,
        mobile_puzzle_enabled,
    )
    from travelogue.layout_contract.engines import LAYOUT_ENGINE_LEGACY

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
