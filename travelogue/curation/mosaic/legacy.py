"""Legacy fallbacks when MCS pick defers to prior planner rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from travelogue.curation.layout_planner import AspectKind

if TYPE_CHECKING:
    from travelogue.curation.screen_planner_stages import ChapterPlanContext


def build_legacy_screen(
    window: list[str],
    size: int,
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    burst_seconds: float = 12.0,
    median_sharp: float | None = None,
    trip_total: int = 0,
) -> dict | None:
    """Build one legacy planner screen for a fixed asset window (no chapter mutation)."""
    from travelogue.curation.screen_planner import (
        MIN_TRIP_PHOTOS_FOR_MOSAIC,
        _can_mosaic_5_main_portrait_3land,
        _can_mixed_p1_l2,
        _can_portrait_grid8_window,
        _is_landscape_id,
        _is_std_portrait_id,
        _make_mixed_portrait_landscape_screen,
        _make_mosaic_5_main_portrait_3land_screen,
        _make_portrait_grid8_screen,
        _make_screen,
    )

    burst = burst_seconds

    if size == 5:
        from travelogue.curation.mosaic.runtime import (
            five_slot_mosaic_enabled,
            get_effective_mosaic_config,
        )

        mosaic_cfg = get_effective_mosaic_config()
        if not five_slot_mosaic_enabled(mosaic_cfg):
            return None
        mosaic_on = mosaic_cfg.enabled
        if not mosaic_on and trip_total < MIN_TRIP_PHOTOS_FOR_MOSAIC:
            return None
        ordered = _can_mosaic_5_main_portrait_3land(
            window, aspects, assets_map, burst_seconds=burst, median_sharp=median_sharp
        )
        if not ordered:
            return None
        return _make_mosaic_5_main_portrait_3land_screen(ordered, assets_map=assets_map)

    if size == 3 and len(window) == 3:
        a, b, c = window
        trials = [
            (a, [b, c]),
            (b, [a, c]),
            (c, [a, b]),
            (a, [c, b]),
            (c, [b, a]),
        ]
        for p_id, lands in trials:
            if _can_mixed_p1_l2(p_id, lands, aspects, assets_map, burst_seconds=burst):
                return _make_mixed_portrait_landscape_screen(
                    p_id, lands, assets_map=assets_map
                )
        if all(_is_std_portrait_id(x, aspects) for x in window):
            return _make_screen(
                "screen-portrait-3",
                window,
                screen_id="",
                aspects=aspects,
                assets_map=assets_map,
            )
        if all(_is_landscape_id(x, aspects) for x in window):
            return _make_screen(
                "screen-landscape-3",
                window,
                screen_id="",
                aspects=aspects,
                assets_map=assets_map,
            )
        return None

    if size == 4 and len(window) == 4:
        if all(_is_std_portrait_id(x, aspects) for x in window):
            return _make_screen(
                "screen-portrait-4",
                window,
                screen_id="",
                aspects=aspects,
                assets_map=assets_map,
            )
        if all(_is_landscape_id(x, aspects) for x in window):
            return _make_screen(
                "screen-landscape-4",
                window,
                screen_id="",
                aspects=aspects,
                assets_map=assets_map,
            )
        return None

    if size == 8 and len(window) == 8:
        if _can_portrait_grid8_window(
            window, aspects, assets_map, burst_seconds=burst
        ):
            return _make_portrait_grid8_screen(window, assets_map=assets_map)
        return None

    if size == 9 and len(window) == 9:
        if all(_is_std_portrait_id(x, aspects) for x in window):
            return _make_screen(
                "screen-portrait-9",
                window,
                screen_id="",
                aspects=aspects,
                assets_map=assets_map,
            )
        if all(_is_landscape_id(x, aspects) for x in window):
            return _make_screen(
                "screen-landscape-9",
                window,
                screen_id="",
                aspects=aspects,
                assets_map=assets_map,
            )
        return None

    if size == 6 and len(window) == 6:
        from travelogue.curation.mosaic.runtime import (
            get_effective_mosaic_config,
            mosaic_window_size_enabled,
        )

        if not mosaic_window_size_enabled(6, get_effective_mosaic_config()):
            return None
        if all(_is_std_portrait_id(x, aspects) for x in window):
            return _make_screen(
                "screen-portrait-6",
                window,
                screen_id="",
                aspects=aspects,
                assets_map=assets_map,
            )
        if all(_is_landscape_id(x, aspects) for x in window):
            return _make_screen(
                "screen-landscape-6",
                window,
                screen_id="",
                aspects=aspects,
                assets_map=assets_map,
            )
        return None

    return None


def append_legacy_window(
    ctx: ChapterPlanContext,
    window: list[str],
    size: int,
) -> bool:
    from travelogue.curation.screen_planner_stages import append_screen

    screen = build_legacy_screen(
        window,
        size,
        ctx.aspects,
        ctx.assets_map,
        burst_seconds=ctx.mix_gap,
        median_sharp=ctx.med_sharp,
        trip_total=ctx.trip_total,
    )
    if not screen:
        return False
    from travelogue.curation.mosaic.pattern_policy import mosaic_pattern_disabled
    from travelogue.curation.mosaic.runtime import get_effective_mosaic_config
    from travelogue.curation.mosaic.slot_geometry import screen_slots_geometry_ok

    pid = str(screen.get("patternId") or "")
    if pid and mosaic_pattern_disabled(pid, cfg=get_effective_mosaic_config()):
        return False
    # Legacy size==4 emits portrait-4 (2×2) for all-portrait windows, which on the
    # 16:9 web stage puts portraits into wide cells. Reject so planning falls back
    # to portrait column grids (portrait-3 + portrait-1).
    if not screen_slots_geometry_ok(screen, ctx.aspects):
        return False
    append_screen(ctx, screen)
    return True
