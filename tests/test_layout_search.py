"""Unit tests for layout_search beam wrapper."""

from __future__ import annotations

from travelogue.curation.degradation import assess_degradation
from travelogue.curation.layout_scoring import PHASE2_WEIGHTS, ScoringWeights
from travelogue.curation.layout_search import maybe_replan_chapters

from tests._golden.helpers import build_portrait_heavy_trip, plan_legacy_screens


def _screen(pid: str, aid: str) -> dict:
    return {"patternId": pid, "slots": [{"assetId": aid}]}


def test_consecutive_pattern_filter_accepts_candidate_tuples(monkeypatch) -> None:
    """Regression: candidates are (variant_name, screen_plan) tuples, not bare plans."""
    buckets, aspects, assets = build_portrait_heavy_trip()
    legacy = plan_legacy_screens(buckets, aspects, assets)
    violating = [
        _screen("screen-portrait-1", "a1"),
        _screen("screen-portrait-1", "a2"),
        _screen("screen-portrait-1", "a3"),
    ]
    ok = [
        _screen("screen-portrait-1", "a1"),
        _screen("screen-portrait-2", "a2"),
        _screen("screen-portrait-3", "a3"),
    ]

    def _fake_candidates(*_args, **_kwargs):
        return [("violating", violating), ("ok", ok)]

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
    assert meta.get("replanApplied") is True


def test_degradation_insufficient_assets():
    assets = [{"id": "a1", "width": 900, "height": 1600, "curation": {"layoutEligible": True}}]
    aspects = {"a1": "portrait"}
    d = assess_degradation(assets, aspects, min_layout_eligible=3)
    assert d.force_legacy
    assert d.reason == "insufficient_layout_eligible"


def test_aspect_only_skips_replan():
    buckets, aspects, assets = build_portrait_heavy_trip()
    legacy = plan_legacy_screens(buckets, aspects, assets)
    replanned, meta = maybe_replan_chapters(
        legacy,
        buckets=buckets,
        aspects=aspects,  # type: ignore[arg-type]
        assets=assets,
        scoring_enabled=True,
        weights=ScoringWeights(aspect_match=1.0),
        beam_width=3,
        degradation=assess_degradation(assets, aspects, min_layout_eligible=3),
        orientation_summary={"portrait": 6, "landscape": 0},
        trip_photo_total=len(assets),
    )
    assert meta.get("skipReason") == "aspect_only_preserve_legacy"
    assert meta.get("equivalentToLegacy") is True


def test_phase2_beam_runs_without_error():
    buckets, aspects, assets = build_portrait_heavy_trip()
    legacy = plan_legacy_screens(buckets, aspects, assets)
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
    )
    assert replanned
    assert meta.get("decisionLogs")
