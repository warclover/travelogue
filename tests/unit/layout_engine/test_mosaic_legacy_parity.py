"""mosaic.enabled=false matches legacy mosaic-five behavior."""

from __future__ import annotations

from dataclasses import replace

from tests._golden.helpers import build_mosaic_eligible_trip
from travelogue.config import get_config
from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState
from travelogue.layout_engine.mosaic.hook import try_mosaic_window
from travelogue.layout_engine.planner.screen_planner_stages import (
    build_chapter_plan_context,
    run_planning_loop,
)


def test_try_mosaic_window_none_when_disabled(monkeypatch):
    cfg = replace(get_config().mosaic, enabled=False)
    monkeypatch.setattr(
        "travelogue.config.get_config",
        lambda: replace(get_config(), mosaic=cfg),
    )
    buckets, aspects, assets = build_mosaic_eligible_trip()
    assets_map = {a["id"]: a for a in assets}
    ctx = build_chapter_plan_context(
        buckets[0],
        aspects,
        assets=assets_map,
        trip_photo_total=40,
        include_chapter_hero=False,
        layout_state=ScreenLayoutPlannerState.from_trip_total(40),
    )
    assert try_mosaic_window(ctx, 0) is None


def test_planning_loop_off_uses_legacy_patterns(monkeypatch):
    cfg = replace(get_config().mosaic, enabled=False)
    monkeypatch.setattr(
        "travelogue.config.get_config",
        lambda: replace(get_config(), mosaic=cfg),
    )
    buckets, aspects, assets = build_mosaic_eligible_trip()
    assets_map = {a["id"]: a for a in assets}
    ctx = build_chapter_plan_context(
        buckets[0],
        aspects,
        assets=assets_map,
        trip_photo_total=40,
        include_chapter_hero=False,
        layout_state=ScreenLayoutPlannerState.from_trip_total(40),
    )
    run_planning_loop(ctx)
    pids = [s["patternId"] for s in ctx.screens]
    assert all("mosaic-5" not in pid for pid in pids)
