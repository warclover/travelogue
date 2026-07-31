"""Legacy fallbacks when MCS pick defers to prior planner rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from travelogue.layout_contract.orientations import AspectKind

if TYPE_CHECKING:
    from travelogue.layout_engine.planner.screen_planner_stages import ChapterPlanContext


def build_legacy_screen(
    window: list[str],
    size: int,
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    burst_seconds: float = 12.0,
    median_sharp: float | None = None,
    trip_total: int = 0,
    app_cfg=None,
    atom_policy=None,
) -> dict | None:
    """Build one legacy planner screen for a fixed asset window (no chapter mutation).

    PLAN P1 · multi-slot legacy screens must pass the same Scene Atom gate.
    """
    from travelogue.config.shot_grouping import resolve_shot_group_mosaic_policy
    from travelogue.layout_engine.planner.scene_atoms import window_violates_atom
    from travelogue.layout_engine.planner.screen_planner import (
        MIN_TRIP_PHOTOS_FOR_MOSAIC,
        _can_mixed_p1_l2,
        _can_mosaic_5_main_portrait_3land,
        _can_portrait_grid8_window,
        _is_landscape_id,
        _is_std_portrait_id,
        _make_mixed_portrait_landscape_screen,
        _make_mosaic_5_main_portrait_3land_screen,
        _make_portrait_grid8_screen,
        _make_screen,
    )

    if len(window) >= 2:
        policy = atom_policy
        if policy is None:
            policy = resolve_shot_group_mosaic_policy(app_cfg).atom
        if window_violates_atom(list(window), assets_map, policy):
            return None

    burst = burst_seconds

    def _blocked(pattern_id: str) -> bool:
        # MTSO S-06 · refuse deprecated/disabled at construct time (not only append).
        from travelogue.layout_engine.mosaic.lifecycle import lifecycle_admit

        return not lifecycle_admit(pattern_id).ok

    if size == 5:
        from travelogue.layout_engine.mosaic.runtime import (
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
        if _blocked("screen-portrait-grid-8"):
            return None
        if _can_portrait_grid8_window(
            window, aspects, assets_map, burst_seconds=burst
        ):
            return _make_portrait_grid8_screen(window, assets_map=assets_map)
        return None

    if size == 9 and len(window) == 9:
        if all(_is_std_portrait_id(x, aspects) for x in window):
            if _blocked("screen-portrait-9"):
                return None
            return _make_screen(
                "screen-portrait-9",
                window,
                screen_id="",
                aspects=aspects,
                assets_map=assets_map,
            )
        if all(_is_landscape_id(x, aspects) for x in window):
            if _blocked("screen-landscape-9"):
                return None
            return _make_screen(
                "screen-landscape-9",
                window,
                screen_id="",
                aspects=aspects,
                assets_map=assets_map,
            )
        return None

    if size == 6 and len(window) == 6:
        from travelogue.layout_engine.mosaic.runtime import (
            get_effective_mosaic_config,
            mosaic_window_size_enabled,
        )

        if not mosaic_window_size_enabled(6, get_effective_mosaic_config()):
            return None
        if all(_is_std_portrait_id(x, aspects) for x in window):
            if _blocked("screen-portrait-6"):
                return None
            return _make_screen(
                "screen-portrait-6",
                window,
                screen_id="",
                aspects=aspects,
                assets_map=assets_map,
            )
        if all(_is_landscape_id(x, aspects) for x in window):
            if _blocked("screen-landscape-6"):
                return None
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
    from travelogue.layout_engine.planner.screen_planner_stages import append_screen

    screen = build_legacy_screen(
        window,
        size,
        ctx.aspects,
        ctx.assets_map,
        burst_seconds=ctx.mix_gap,
        median_sharp=ctx.med_sharp,
        trip_total=ctx.trip_total,
        app_cfg=ctx.app_config,
    )
    if not screen:
        return False
    from travelogue.layout_contract.usage_context import build_window_context
    from travelogue.layout_engine.usage_rules.evaluator import evaluate_reject

    window_ctx = build_window_context(
        window,
        ctx.aspects,
        ctx.assets_map,
        layout_state=ctx.layout_state,
        median_sharp=ctx.med_sharp,
        featured_weight=ctx.featured_weight,
    )
    pid = str(screen.get("patternId") or "")
    reject, _rule_id, _detail = evaluate_reject(pid, window_ctx, screen=screen)
    if reject:
        return False
    from travelogue.layout_engine.mosaic.lifecycle import trip_id_from_trip
    from travelogue.layout_engine.mosaic.lte_adapter import mosaic_pattern_disabled
    from travelogue.layout_engine.mosaic.runtime import get_effective_mosaic_config
    from travelogue.layout_engine.mosaic.slot_geometry import screen_slots_geometry_ok

    if pid and mosaic_pattern_disabled(
        pid,
        cfg=get_effective_mosaic_config(),
        trip_id=trip_id_from_trip(getattr(ctx, "trip", None)),
    ):
        return False
    # Legacy size==4 emits portrait-4 (2×2) for all-portrait windows, which on the
    # 16:9 web stage puts portraits into wide cells. Reject so planning falls back
    # to portrait column grids (portrait-3 + portrait-1).
    if not screen_slots_geometry_ok(screen, ctx.aspects):
        return False
    # Legacy fallback emits raw screen_planner screens that never pass through
    # ``_finalize_mosaic_screen``; solidify so they carry LTE geometry + role-aware
    # fit like the MCS candidate path (no-op for non-LTE pattern ids).
    from travelogue.layout_engine.mosaic.lte_adapter import read_templates_from_lte

    if read_templates_from_lte():
        from travelogue.layout_templates.geometry_solidify import (
            solidify_screen_geometry,
        )

        solidify_screen_geometry(screen, pid, assets_map=ctx.assets_map)
    append_screen(ctx, screen)
    return True
