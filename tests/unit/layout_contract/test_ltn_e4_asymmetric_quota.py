"""LTN E4 · asymmetric dense quota (hard max, soft opportunity)."""

from __future__ import annotations

from travelogue.layout_contract.asymmetric_quota import (
    asymmetric_dense_snapshot,
    dense_opportunity_fill_rate,
    dense_opportunity_min_for,
)
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_engine.adapter import _apply_track_dense_cap
from travelogue.layout_engine.mosaic.ltn_weekly import compute_ltn_weekly_metrics


def test_opportunity_min_soft_by_track():
    assert dense_opportunity_min_for(dense_max=0, track="curated") == 0
    assert dense_opportunity_min_for(dense_max=2, track="curated") == 1
    assert dense_opportunity_min_for(dense_max=5, track="archive") == 2  # ceil(0.4*5)
    assert dense_opportunity_min_for(dense_max=2, track="quick_share") == 0


def test_force_emit_always_false_even_when_below_opportunity():
    st = ScreenLayoutPlannerState.from_trip_total(40)
    st.dense_collage_opportunity_min = 2
    st.dense_collage_used = 0
    assert st.needs_dense_opportunity() is True
    assert st.should_force_dense_emit() is False
    assert st.should_force_dense_emit() is False


def test_note_opportunity_and_snapshot():
    st = ScreenLayoutPlannerState.from_trip_total(120)
    st.dense_collage_max = 5
    st.dense_collage_opportunity_min = dense_opportunity_min_for(dense_max=5, track="archive")
    st.note_dense_opportunity()
    st.note_dense_opportunity()
    st.dense_collage_used = 1
    snap = st.asymmetric_dense_snapshot()
    assert snap["denseOpportunitySeen"] == 2
    assert snap["denseForcedEmit"] is False
    assert snap["asymmetricQuota"] is True
    assert snap["denseOpportunityFillRate"] == dense_opportunity_fill_rate(
        used=1, opportunity_min=snap["denseOpportunityMin"]
    )


def test_track_cap_refreshes_opportunity_min(monkeypatch):
    st = ScreenLayoutPlannerState.from_trip_total(120)
    assert st.dense_collage_max >= 3

    class _Cfg:
        track_dense_collage_cap = 2
        track_id = "curated"

    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.runtime.get_effective_mosaic_config",
        lambda: _Cfg(),
    )
    out = _apply_track_dense_cap(st)
    assert out.dense_collage_max == 2
    assert out.dense_collage_opportunity_min == 1  # curated soft floor


def test_weekly_metrics_include_asymmetric_fields():
    trip = {
        "intent": {"mode": "curated"},
        "assets": [{"id": f"a{i}"} for i in range(40)],
        "chapters": [
            {
                "screens": [
                    {
                        "patternId": "screen-mosaic-5-main-portrait-3land",
                        "slots": [{"assetId": "a1", "role": "main"}],
                    }
                ]
            }
        ],
        "curation": {
            "mosaicDecisionLog": [
                {
                    "isWinnerPlan": True,
                    "windowSize": 5,
                    "candidatesCount": 3,
                    "winnerPatternId": "screen-mosaic-5-main-portrait-3land",
                },
                {
                    "isWinnerPlan": True,
                    "windowSize": 5,
                    "candidatesCount": 0,
                    "fallbackUsed": True,
                    "fallbackReason": "no_candidates",
                },
            ]
        },
    }
    m = compute_ltn_weekly_metrics(trip)
    assert m["asymmetricQuota"] is True
    assert m["denseForcedEmit"] is False
    assert m["denseOpportunityMin"] == 1
    assert m["denseOpportunitySeen"] == 1
    assert m["denseOpportunityFillRate"] == 1.0
    assert asymmetric_dense_snapshot(
        dense_max=1, dense_used=1, opportunity_min=1, opportunity_seen=1
    )["denseQuotaUtilization"] == 1.0
