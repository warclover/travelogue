"""Phase 6 layout rhythm tests (M25-B)."""

from __future__ import annotations

from travelogue.curation.layout_constraints import (
    check_max_consecutive_same_pattern,
    plan_violates_consecutive_pattern,
)
from travelogue.curation.layout_metrics import max_pattern_repeat_streak
from travelogue.curation.layout_scoring import (
    PHASE6_WEIGHTS,
    score_gravity_balance,
    score_screen_plan,
    ScoringWeights,
)
from travelogue.curation.longshot_filter import select_longshot_screens


def _screen(pid: str, aid: str, *, arc: str | None = None) -> dict:
    sc = {"patternId": pid, "slots": [{"assetId": aid}]}
    if arc:
        sc["arcSegment"] = arc
    return sc


def test_gravity_balance_rewards_smooth_focal_flow() -> None:
    assets = {
        "a1": {"id": "a1", "focalPoint": {"x": 0.33, "y": 0.33}},
        "a2": {"id": "a2", "focalPoint": {"x": 0.35, "y": 0.34}},
        "a3": {"id": "a3", "focalPoint": {"x": 0.36, "y": 0.35}},
    }
    smooth = [
        _screen("screen-portrait-1", "a1"),
        _screen("screen-portrait-1", "a2"),
        _screen("screen-portrait-1", "a3"),
    ]
    jumpy = [
        _screen("screen-portrait-1", "a1"),
        _screen("screen-portrait-1", "a2"),
        {"patternId": "screen-portrait-1", "slots": [{"assetId": "a3"}],},
    ]
    jumpy_assets = dict(assets)
    jumpy_assets["a3"] = {"id": "a3", "focalPoint": {"x": 0.9, "y": 0.1}}
    assert score_gravity_balance(smooth, assets) > score_gravity_balance(jumpy, jumpy_assets)


def test_phase6_weights_include_gravity_balance() -> None:
    assert PHASE6_WEIGHTS.gravity_balance > 0


def test_score_screen_plan_writes_gravity_balance() -> None:
    assets = {
        "a1": {"id": "a1", "focalPoint": {"x": 0.4, "y": 0.4}},
        "a2": {"id": "a2", "focalPoint": {"x": 0.42, "y": 0.41}},
    }
    bd = score_screen_plan(
        [_screen("screen-portrait-1", "a1"), _screen("screen-portrait-1", "a2")],
        aspects={"a1": "portrait", "a2": "portrait"},
        assets_by_id=assets,
        weights=PHASE6_WEIGHTS,
        enable_gravity_balance=True,
    )
    assert bd.gravity_balance > 0.5
    assert "gravity_balance" in bd.to_dict()


def test_consecutive_pattern_violation_detected() -> None:
    screens = [
        _screen("screen-portrait-1", "a1"),
        _screen("screen-portrait-1", "a2"),
        _screen("screen-portrait-1", "a3"),
    ]
    assert plan_violates_consecutive_pattern(screens, max_streak=2)
    violations = check_max_consecutive_same_pattern([{"id": "ch1", "screens": screens}], max_streak=2)
    assert violations
    assert violations[0].code == "consecutive_same_pattern"


def test_max_pattern_repeat_streak_metric() -> None:
    chapters = [{"id": "ch1", "screens": [_screen("p", f"a{i}") for i in range(4)]}]
    assert max_pattern_repeat_streak(chapters) == 4


def test_longshot_mmr_prefers_diverse_patterns() -> None:
    assets_by_id = {
        "a0": {"id": "a0", "dominantTone": "#112233"},
        "a1": {"id": "a1", "dominantTone": "#112233"},
        "a2": {"id": "a2", "dominantTone": "#445566"},
        "a3": {"id": "a3", "dominantTone": "#778899"},
        "a4": {"id": "a4", "dominantTone": "#aabbcc"},
    }
    screens = [
        _screen("screen-portrait-1", "a0"),
        _screen("screen-portrait-1", "a1"),
        _screen("screen-portrait-2", "a2"),
        _screen("screen-portrait-3", "a3"),
        _screen("screen-portrait-4", "a4"),
    ]
    picked = select_longshot_screens(
        screens,
        max_screens=3,
        assets_by_id=assets_by_id,
        enable_mmr=True,
        max_consecutive_same_pattern=2,
    )
    pids = [sc["patternId"] for sc in picked]
    assert len(pids) == 3
    assert len(set(pids)) >= 2
