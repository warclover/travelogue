"""Multi-portrait windows skip dense size≥6 and fall back to smaller mosaics."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import get_config
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
)
from travelogue.layout_engine.mosaic.hook import try_mosaic_window
from travelogue.layout_engine.planner.screen_planner_stages import build_chapter_plan_context


def _patch_cfg(monkeypatch):
    from travelogue.config.app import AppConfig

    base = AppConfig()
    mosaic = replace(
        base.mosaic,
        enabled=True,
        enabled_window_sizes=(4, 5, 6, 9),
        min_candidate_score=0.0,
        skip_dense_window_multi_portrait=True,
        prefer_five_slot_single_portrait=True,
        density_budget=replace(base.mosaic.density_budget, enabled=False),
    )
    app = replace(base, mosaic=mosaic)
    monkeypatch.setattr("travelogue.config.get_config", lambda: app)
    return mosaic


def test_two_portrait_six_window_skips_hero_and_uses_five_slot(monkeypatch):
    mosaic = _patch_cfg(monkeypatch)
    from travelogue.config.app import AppConfig
    from travelogue.config.runtime import config_override

    taken = "2024-06-01T12:00:00Z"
    assets = [
        {
            "id": f"l{i}",
            "width": 3000,
            "height": 1687,
            "takenAt": taken,
            "aspectKind": "landscape",
        }
        for i in range(4)
    ] + [
        {
            "id": "p1",
            "width": 1200,
            "height": 1800,
            "takenAt": taken,
            "aspectKind": "portrait",
        },
        {
            "id": "p2",
            "width": 1200,
            "height": 1800,
            "takenAt": taken,
            "aspectKind": "portrait",
        },
    ]
    aspects = {a["id"]: a["aspectKind"] for a in assets}
    assets_map = {a["id"]: a for a in assets}
    app = replace(AppConfig(), mosaic=mosaic)
    with config_override(app):
        ctx = build_chapter_plan_context(
            [a["id"] for a in assets],
            aspects,
            assets=assets_map,
            trip_photo_total=40,
            include_chapter_hero=False,
            layout_state=ScreenLayoutPlannerState.from_trip_total(40),
            app_config=app,
        )
        adv = try_mosaic_window(ctx, 0)
    assert adv == 5
    assert ctx.screens[0]["patternId"] == PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND
    assert ctx.screens[0]["patternId"] != PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5


def test_skip_dense_multi_portrait_can_be_disabled(monkeypatch):
    base = get_config()
    mosaic = replace(
        base.mosaic,
        enabled=True,
        enabled_window_sizes=(6,),
        min_candidate_score=0.0,
        skip_dense_window_multi_portrait=False,
        density_budget=replace(base.mosaic.density_budget, enabled=False),
    )
    monkeypatch.setattr("travelogue.config.get_config", lambda: replace(base, mosaic=mosaic))

    assets = [
        {
            "id": f"l{i}",
            "width": 3000,
            "height": 1687,
            "takenAt": f"2024-06-01T12:0{i}:00Z",
            "aspectKind": "landscape",
        }
        for i in range(4)
    ] + [
        {
            "id": "p1",
            "width": 1200,
            "height": 1800,
            "takenAt": "2024-06-01T12:05:00Z",
            "aspectKind": "portrait",
        },
        {
            "id": "p2",
            "width": 1200,
            "height": 1800,
            "takenAt": "2024-06-01T12:06:00Z",
            "aspectKind": "portrait",
        },
    ]
    aspects = {a["id"]: a["aspectKind"] for a in assets}
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
    assert adv is None


def test_single_portrait_six_window_prefers_main_portrait_3land(monkeypatch):
    _patch_cfg(monkeypatch)
    taken = "2024-06-01T12:00:00Z"
    assets = [
        {
            "id": "l0",
            "width": 3000,
            "height": 1687,
            "takenAt": taken,
            "aspectKind": "landscape",
        },
        {
            "id": "l1",
            "width": 3000,
            "height": 1687,
            "takenAt": taken,
            "aspectKind": "landscape",
        },
        {
            "id": "p1",
            "width": 1200,
            "height": 1800,
            "takenAt": taken,
            "aspectKind": "portrait",
        },
        {
            "id": "l2",
            "width": 3000,
            "height": 1687,
            "takenAt": taken,
            "aspectKind": "landscape",
        },
        {
            "id": "l3",
            "width": 3000,
            "height": 1687,
            "takenAt": taken,
            "aspectKind": "landscape",
        },
        {
            "id": "l4",
            "width": 3000,
            "height": 1687,
            "takenAt": taken,
            "aspectKind": "landscape",
        },
    ]
    aspects = {a["id"]: a["aspectKind"] for a in assets}
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
    assert adv == 5
    assert ctx.screens[0]["patternId"] == PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND


def test_single_portrait_trailing_skips_hero_six(monkeypatch):
    _patch_cfg(monkeypatch)
    taken = "2024-06-01T12:00:00Z"
    assets = [
        {
            "id": f"l{i}",
            "width": 3000,
            "height": 1687,
            "takenAt": taken,
            "aspectKind": "landscape",
        }
        for i in range(5)
    ] + [
        {
            "id": "p1",
            "width": 1200,
            "height": 1800,
            "takenAt": taken,
            "aspectKind": "portrait",
        },
    ]
    aspects = {a["id"]: a["aspectKind"] for a in assets}
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
    assert adv != 6
    assert ctx.screens[0]["patternId"] != PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
