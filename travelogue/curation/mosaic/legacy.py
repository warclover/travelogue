"""Legacy fallbacks when MCS pick defers to prior planner rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from travelogue.curation.layout_planner import AspectKind

if TYPE_CHECKING:
    from travelogue.curation.screen_planner_stages import ChapterPlanContext


def append_legacy_window(
    ctx: ChapterPlanContext,
    window: list[str],
    size: int,
) -> bool:
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
    from travelogue.curation.screen_planner_stages import append_screen

    aspects = ctx.aspects
    assets_map = ctx.assets_map
    burst = ctx.mix_gap

    if size == 5:
        from travelogue.curation.mosaic.runtime import get_effective_mosaic_config

        mosaic_on = get_effective_mosaic_config().enabled
        if not mosaic_on and ctx.trip_total < MIN_TRIP_PHOTOS_FOR_MOSAIC:
            return False
        ordered = _can_mosaic_5_main_portrait_3land(
            window, aspects, assets_map, burst_seconds=burst, median_sharp=ctx.med_sharp
        )
        if not ordered:
            return False
        append_screen(
            ctx,
            _make_mosaic_5_main_portrait_3land_screen(ordered, assets_map=assets_map),
        )
        return True

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
                append_screen(
                    ctx,
                    _make_mixed_portrait_landscape_screen(
                        p_id, lands, assets_map=assets_map
                    ),
                )
                return True
        if all(_is_std_portrait_id(x, aspects) for x in window):
            append_screen(
                ctx,
                _make_screen(
                    "screen-portrait-3",
                    window,
                    aspects=aspects,
                    assets_map=assets_map,
                ),
            )
            return True
        if all(_is_landscape_id(x, aspects) for x in window):
            append_screen(
                ctx,
                _make_screen(
                    "screen-landscape-3",
                    window,
                    aspects=aspects,
                    assets_map=assets_map,
                ),
            )
            return True
        return False

    if size == 4 and len(window) == 4:
        if all(_is_std_portrait_id(x, aspects) for x in window):
            append_screen(
                ctx,
                _make_screen(
                    "screen-portrait-4",
                    window,
                    aspects=aspects,
                    assets_map=assets_map,
                ),
            )
            return True
        if all(_is_landscape_id(x, aspects) for x in window):
            append_screen(
                ctx,
                _make_screen(
                    "screen-landscape-4",
                    window,
                    aspects=aspects,
                    assets_map=assets_map,
                ),
            )
            return True
        return False

    if size == 8 and len(window) == 8:
        if _can_portrait_grid8_window(
            window, aspects, assets_map, burst_seconds=burst
        ):
            append_screen(
                ctx,
                _make_portrait_grid8_screen(window, assets_map=assets_map),
            )
            return True
        return False

    if size == 9 and len(window) == 9:
        if all(_is_std_portrait_id(x, aspects) for x in window):
            append_screen(
                ctx,
                _make_screen(
                    "screen-portrait-9",
                    window,
                    aspects=aspects,
                    assets_map=assets_map,
                ),
            )
            return True
        if all(_is_landscape_id(x, aspects) for x in window):
            append_screen(
                ctx,
                _make_screen(
                    "screen-landscape-9",
                    window,
                    aspects=aspects,
                    assets_map=assets_map,
                ),
            )
            return True
        return False

    if size == 6 and len(window) == 6:
        if all(_is_std_portrait_id(x, aspects) for x in window):
            append_screen(
                ctx,
                _make_screen(
                    "screen-portrait-6",
                    window,
                    aspects=aspects,
                    assets_map=assets_map,
                ),
            )
            return True
        if all(_is_landscape_id(x, aspects) for x in window):
            append_screen(
                ctx,
                _make_screen(
                    "screen-landscape-6",
                    window,
                    aspects=aspects,
                    assets_map=assets_map,
                ),
            )
            return True
        return False

    return False
