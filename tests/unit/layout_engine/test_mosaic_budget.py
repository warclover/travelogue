"""Budget exhausted continues with legacy_segment semantics."""

from __future__ import annotations

from tests._golden.helpers import build_portrait_heavy_trip, plan_legacy_screens
from travelogue.curation.degradation import assess_degradation
from travelogue.curation.layout_scoring import PHASE2_WEIGHTS
from travelogue.curation.search_budget import SearchBudget
from travelogue.layout_engine.planner.layout_search import maybe_replan_chapters


def test_search_budget_segment_cap():
    b = SearchBudget(max_evaluations_per_trip=100, max_evaluations_per_segment=1)
    b.begin_segment()
    assert b.can_evaluate()
    b.note_evaluation()
    assert not b.can_evaluate()
    b.begin_segment()
    assert b.can_evaluate()


def test_replan_continues_after_trip_budget_exhausted(monkeypatch) -> None:
    buckets, aspects, assets = build_portrait_heavy_trip()
    legacy = plan_legacy_screens(buckets, aspects, assets)
    calls: list[int] = []

    def _fake_candidates(*_args, **_kwargs):
        calls.append(1)
        return [("legacy", legacy[0].get("screens") or [])]

    monkeypatch.setattr(
        "travelogue.layout_engine.planner.layout_search.generate_day_bucket_candidates",
        _fake_candidates,
    )
    maybe_replan_chapters(
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
        max_evaluations_per_trip=1,
    )
    assert len(calls) >= len(buckets)
