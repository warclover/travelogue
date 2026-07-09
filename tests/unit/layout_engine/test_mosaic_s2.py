"""Phase 15 S2/S2+ · 3/4/6/8/9 window candidates and planning."""

from __future__ import annotations

from dataclasses import replace

from tests._golden.helpers import (
    build_mosaic_eligible_trip,
    build_mosaic_landscape9_trip,
    build_mosaic_portrait8_trip,
)
from travelogue.config import get_config
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_engine.mosaic.candidates import generate_window_candidates
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_LANDSCAPE_9,
    PATTERN_PORTRAIT_GRID_8,
)
from travelogue.layout_engine.mosaic.hook import drain_mosaic_logs, try_mosaic_window
from travelogue.layout_engine.planner.screen_planner_stages import (
    build_chapter_plan_context,
    run_planning_loop,
)


def _s2_cfg(*, max_mosaic_slots: int = 9):
    base = get_config()
    layout = replace(base.layout, template_engine=replace(base.layout.template_engine, max_mosaic_slots=max_mosaic_slots))
    return replace(base, layout=layout), replace(
        base.mosaic,
        enabled=True,
        enabled_window_sizes=(3, 4, 5, 6, 8, 9),
        min_candidate_score=0.0,
        density_budget=replace(
            base.mosaic.density_budget,
            enabled=False,
        ),
    )


def _patch_s2_cfg(monkeypatch, *, max_mosaic_slots: int = 9):
    app, mosaic = _s2_cfg(max_mosaic_slots=max_mosaic_slots)
    monkeypatch.setattr("travelogue.config.get_config", lambda: replace(app, mosaic=mosaic))
    return mosaic


def test_generate_candidates_size_3_4_6():
    _app, cfg = _s2_cfg()
    _, aspects, assets = build_mosaic_eligible_trip()
    assets_map = {a["id"]: a for a in assets}
    portrait_ids = [a["id"] for a in assets if aspects[a["id"]] == "portrait"][:3]
    c3 = generate_window_candidates(portrait_ids, aspects, assets_map, cfg=cfg, burst_seconds=3600)
    assert any(c.pattern_id == "screen-portrait-3" for c in c3)

    land_ids = [a["id"] for a in assets if aspects[a["id"]] == "landscape"][:6]
    c6 = generate_window_candidates(land_ids, aspects, assets_map, cfg=cfg, burst_seconds=3600)
    assert any(c.pattern_id == "screen-landscape-6" for c in c6)


def test_generate_candidates_size_8_9():
    _app, cfg = _s2_cfg()
    _, aspects, assets = build_mosaic_portrait8_trip()
    assets_map = {a["id"]: a for a in assets}
    c8 = generate_window_candidates(
        [a["id"] for a in assets],
        aspects,
        assets_map,
        cfg=cfg,
        burst_seconds=3600,
    )
    assert any(c.pattern_id == PATTERN_PORTRAIT_GRID_8 for c in c8)

    _, aspects9, assets9 = build_mosaic_landscape9_trip()
    assets_map9 = {a["id"]: a for a in assets9}
    c9 = generate_window_candidates(
        [a["id"] for a in assets9],
        aspects9,
        assets_map9,
        cfg=cfg,
        burst_seconds=3600,
    )
    assert any(c.pattern_id == PATTERN_LANDSCAPE_9 for c in c9)


def test_planning_loop_uses_portrait_3_for_three_portraits(monkeypatch):
    _patch_s2_cfg(monkeypatch)
    assets = [
        {
            "id": f"p{i}",
            "width": 900,
            "height": 1600,
            "takenAt": "2024-06-01T10:00:00Z",
            "aspectKind": "portrait",
        }
        for i in range(3)
    ]
    aspects = {a["id"]: "portrait" for a in assets}
    assets_map = {a["id"]: a for a in assets}
    ctx = build_chapter_plan_context(
        [a["id"] for a in assets],
        aspects,
        assets=assets_map,
        trip_photo_total=40,
        include_chapter_hero=False,
        layout_state=ScreenLayoutPlannerState.from_trip_total(40),
    )
    run_planning_loop(ctx)
    assert len(ctx.screens) == 1
    assert ctx.screens[0]["patternId"] == "screen-portrait-3"


def test_try_mosaic_window_six_landscapes(monkeypatch):
    _patch_s2_cfg(monkeypatch)
    assets = [
        {
            "id": f"l{i}",
            "width": 2000,
            "height": 1200,
            "takenAt": "2024-06-01T10:00:00Z",
            "aspectKind": "landscape",
        }
        for i in range(6)
    ]
    aspects = {a["id"]: "landscape" for a in assets}
    assets_map = {a["id"]: a for a in assets}
    ctx = build_chapter_plan_context(
        [a["id"] for a in assets],
        aspects,
        assets=assets_map,
        trip_photo_total=40,
        include_chapter_hero=False,
        layout_state=ScreenLayoutPlannerState.from_trip_total(40),
    )
    adv = try_mosaic_window(ctx, 0)
    assert adv == 6
    assert ctx.screens[0]["patternId"] == "screen-landscape-6"


def test_try_mosaic_window_nine_landscapes(monkeypatch):
    _patch_s2_cfg(monkeypatch, max_mosaic_slots=9)
    _, aspects, assets = build_mosaic_landscape9_trip()
    assets_map = {a["id"]: a for a in assets}
    ctx = build_chapter_plan_context(
        [a["id"] for a in assets],
        aspects,
        assets=assets_map,
        trip_photo_total=60,
        include_chapter_hero=False,
        layout_state=ScreenLayoutPlannerState.from_trip_total(60),
    )
    drain_mosaic_logs()
    adv = try_mosaic_window(ctx, 0)
    assert adv == 9
    assert ctx.screens[0]["patternId"] == PATTERN_LANDSCAPE_9

