"""Unit tests for layout_search beam wrapper."""

from __future__ import annotations

from travelogue.curation.degradation import assess_degradation
from travelogue.curation.layout_scoring import PHASE2_WEIGHTS, ScoringWeights
from travelogue.curation.layout_search import maybe_replan_chapters

from tests._golden.helpers import build_portrait_heavy_trip, plan_legacy_screens


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
