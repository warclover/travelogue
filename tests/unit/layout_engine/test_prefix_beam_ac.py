"""AC-AAD-21/22/23 · PrefixBeam budget fallback + IncrementalScoreState probe."""

from __future__ import annotations

from dataclasses import replace

import pytest

from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_contract.scoring import IncrementalScoreState, ScoringWeights
from travelogue.layout_contract.search_budget import SearchBudget
from travelogue.layout_engine.mosaic.prefix_beam import prefix_beam_plan_bucket

pytestmark = pytest.mark.unit


def test_prefix_beam_budget_exhausted_returns_fallback() -> None:
    budget = SearchBudget(
        max_candidates_per_bucket=1,
        max_evaluations_per_trip=0,
        max_evaluations_per_segment=0,
        search_timeout_ms=1,
    )
    screens, reason = prefix_beam_plan_bucket(
        ["a", "b", "c"],
        {"a": "landscape", "b": "landscape", "c": "landscape"},
        assets_by_id={
            "a": {"id": "a", "takenAt": "2024-01-01T10:00:00Z"},
            "b": {"id": "b", "takenAt": "2024-01-01T10:01:00Z"},
            "c": {"id": "c", "takenAt": "2024-01-01T10:02:00Z"},
        },
        orientation_summary=None,
        skip_screen_asset_ids=None,
        mixed_proximity_seconds=30.0,
        trip_photo_total=3,
        preferred_hero_id=None,
        layout_state=ScreenLayoutPlannerState.from_trip_total(3),
        enable_food_grid=False,
        mundane_grid_buckets=(),
        beam_width=2,
        budget=budget,
        weights=ScoringWeights(),
        subject_run_tolerance=1,
        enable_gravity_balance=False,
        late_kwargs={},
    )
    assert screens == []
    assert reason == "BUDGET_EXHAUSTED"


def test_prefix_beam_uses_incremental_score_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-AAD-23: expansion loop must pass IncrementalScoreState into score_screen_plan."""
    seen: list[object] = []

    def _fake_score(screens, **kwargs):
        seen.append(kwargs.get("incremental_state"))
        assert kwargs.get("incremental") is True
        from travelogue.layout_contract.scoring import ScoreBreakdown

        return ScoreBreakdown(total=0.5, utility=0.5)

    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.prefix_beam.score_screen_plan",
        _fake_score,
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.prefix_beam.generate_day_bucket_candidates",
        lambda remaining, aspects, **kw: [
            (
                "v0",
                [
                    {
                        "patternId": "screen-landscape-1",
                        "slots": [{"assetId": remaining[0], "slot": 0}],
                    }
                ]
                + (
                    [
                        {
                            "patternId": "screen-landscape-1",
                            "slots": [{"assetId": remaining[1], "slot": 0}],
                        }
                    ]
                    if len(remaining) > 1
                    else []
                ),
            )
        ]
        if remaining
        else [],
    )
    shared = IncrementalScoreState()
    budget = SearchBudget(
        max_candidates_per_bucket=8,
        max_evaluations_per_trip=50,
        max_evaluations_per_segment=50,
        search_timeout_ms=10_000,
    )
    aspects: dict[str, AspectKind] = {
        "a": "landscape",
        "b": "landscape",
    }
    assets = {
        "a": {"id": "a", "takenAt": "2024-01-01T10:00:00Z"},
        "b": {"id": "b", "takenAt": "2024-01-01T10:01:00Z"},
    }
    screens, reason = prefix_beam_plan_bucket(
        ["a", "b"],
        aspects,
        assets_by_id=assets,
        orientation_summary=None,
        skip_screen_asset_ids=None,
        mixed_proximity_seconds=30.0,
        trip_photo_total=2,
        preferred_hero_id=None,
        layout_state=ScreenLayoutPlannerState.from_trip_total(2),
        enable_food_grid=False,
        mundane_grid_buckets=(),
        beam_width=2,
        budget=budget,
        weights=ScoringWeights(),
        subject_run_tolerance=1,
        enable_gravity_balance=False,
        late_kwargs={},
        incremental_state=shared,
    )
    assert reason is None
    assert screens
    assert seen
    assert all(s is shared for s in seen)


def test_beam_score_exposes_utility() -> None:
    from travelogue.layout_engine.planner.beam_scoring import score_screen_plan

    screens = [
        {
            "patternId": "screen-landscape-1",
            "slots": [{"assetId": "a", "slot": 0}],
        }
    ]
    bd = score_screen_plan(
        screens,
        aspects={"a": "landscape"},
        assets_by_id={"a": {"id": "a", "sharpness": 0.8}},
        weights=ScoringWeights(),
    )
    assert bd.utility == pytest.approx(bd.total, abs=1e-9)
    d = bd.to_dict()
    assert "utility" in d
