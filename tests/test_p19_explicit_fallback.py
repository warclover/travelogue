"""P19 R-304 · explicit single-image fallback when dense layouts are infeasible."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from tests._golden.helpers import _asset, build_portrait_heavy_trip, plan_legacy_screens
from travelogue.curation.layout_search import maybe_replan_chapters
from travelogue.curation.mosaic.explicit_fallback import build_explicit_single_screen_plan
from travelogue.curation.mosaic.hook import try_mosaic_window_mcs
from travelogue.curation.mosaic.log import MosaicWindowLog
from travelogue.curation.mosaic.compose import WindowPickResult
from travelogue.curation.screen_planner_stages import build_chapter_plan_context


def _screen(pid: str, aid: str) -> dict:
    return {"patternId": pid, "slots": [{"assetId": aid}]}


def test_build_explicit_single_screen_plan_mixed_orientations() -> None:
    assets = [_asset("p1", 900, 1600), _asset("l1", 2000, 1200)]
    aspects = {a["id"]: a["aspectKind"] for a in assets}
    assets_map = {a["id"]: a for a in assets}
    plan = build_explicit_single_screen_plan(
        [a["id"] for a in assets],
        aspects,
        assets_map=assets_map,
    )
    assert len(plan) == 2
    assert plan[0]["patternId"] == "screen-portrait-1"
    assert plan[1]["patternId"] == "screen-landscape-1"


def test_try_mosaic_window_mcs_explicit_single_when_legacy_rejects() -> None:
    ctx = build_chapter_plan_context(
        ["a1", "a2", "a3"],
        {"a1": "portrait", "a2": "portrait", "a3": "portrait"},
        chapter_id="ch-test",
        assets={
            "a1": _asset("a1", 900, 1600),
            "a2": _asset("a2", 900, 1600),
            "a3": _asset("a3", 900, 1600),
        },
        enable_mosaic=True,
    )
    pick = WindowPickResult(
        screen=None,
        log=MosaicWindowLog(fallback_reason="no_candidates", fallback_used=True),
        used_legacy=True,
    )
    from travelogue.curation.mosaic.runtime import get_effective_mosaic_config

    cfg = get_effective_mosaic_config()

    with patch(
        "travelogue.curation.mosaic.hook.pick_best_window",
        return_value=pick,
    ), patch(
        "travelogue.curation.mosaic.hook.append_legacy_window",
        return_value=False,
    ):
        ok = try_mosaic_window_mcs(ctx, 0, 3, cfg)
    assert ok
    assert len(ctx.screens) == 3
    assert all(s.get("patternId") == "screen-portrait-1" for s in ctx.screens)


def test_replan_explicit_single_when_rhythm_filters_all_plans(monkeypatch) -> None:
    from travelogue.curation.degradation import assess_degradation
    from travelogue.curation.layout_scoring import PHASE2_WEIGHTS

    buckets, aspects, assets = build_portrait_heavy_trip()
    legacy = plan_legacy_screens(buckets, aspects, assets)
    violating = [
        _screen("screen-portrait-1", "a1"),
        _screen("screen-portrait-1", "a2"),
        _screen("screen-portrait-1", "a3"),
    ]

    def _fake_candidates(*_args, **_kwargs):
        return [("violating", violating)]

    monkeypatch.setattr(
        "travelogue.curation.layout_search.generate_day_bucket_candidates",
        _fake_candidates,
    )
    replanned, meta = maybe_replan_chapters(
        legacy,
        buckets=buckets,
        aspects=aspects,  # type: ignore[arg-type]
        assets=assets,
        scoring_enabled=True,
        weights=PHASE2_WEIGHTS,
        beam_width=3,
        degradation=assess_degradation(assets, aspects, min_layout_eligible=3),
        orientation_summary={"portrait": 6, "landscape": 0},
        trip_photo_total=len(assets),
        max_consecutive_same_pattern=2,
    )
    assert replanned
    logs = meta.get("decisionLogs") or []
    assert any(
        ev.get("plannerPath") == "explicit_single"
        for log in logs
        for ev in log.get("events") or []
    )
