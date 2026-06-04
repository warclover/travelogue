"""Golden layout baselines: legacy planner output frozen for regression (ADR-002)."""

from __future__ import annotations

from copy import deepcopy

from travelogue.curation.degradation import DegradationAssessment
from travelogue.curation.layout_scoring import ScoringWeights
from travelogue.curation.layout_search import maybe_replan_chapters

from travelogue.curation.mosaic.metrics import mosaic5_exposure_rate

from tests._golden.helpers import (
    build_mixed_aspects_trip,
    build_mosaic_eligible_trip,
    build_portrait_heavy_trip,
    layout_snapshot,
    load_golden,
    plan_legacy_screens,
    plan_mosaic_screens,
)


def test_golden_portrait_heavy_matches_legacy():
    buckets, aspects, assets = build_portrait_heavy_trip()
    chapters = plan_legacy_screens(buckets, aspects, assets)
    expected = load_golden("portrait-heavy")
    assert layout_snapshot(chapters) == expected


def test_golden_mixed_aspects_matches_legacy():
    buckets, aspects, assets = build_mixed_aspects_trip()
    chapters = plan_legacy_screens(buckets, aspects, assets)
    expected = load_golden("mixed-aspects")
    assert layout_snapshot(chapters) == expected


def test_scoring_aspect_only_equivalent_to_legacy():
    """Phase-1 equivalence: aspect_match=1.0 only must not change screen signatures."""
    buckets, aspects, assets = build_mixed_aspects_trip()
    legacy = plan_legacy_screens(buckets, aspects, assets)
    weights = ScoringWeights(aspect_match=1.0)
    replanned, meta = maybe_replan_chapters(
        deepcopy(legacy),
        buckets=buckets,
        aspects=aspects,  # type: ignore[arg-type]
        assets=assets,
        scoring_enabled=True,
        weights=weights,
        beam_width=3,
        degradation=DegradationAssessment(force_legacy=False),
    )
    assert layout_snapshot(replanned) == layout_snapshot(legacy)
    assert meta.get("equivalentToLegacy") is True


def test_mosaic5_exposure_ab_fixture():
    """P15-4f · mosaic on raises mosaic-5 exposure vs off on synthetic fixture."""
    buckets, aspects, assets = build_mosaic_eligible_trip()
    off = plan_legacy_screens(buckets, aspects, assets, mosaic_enabled=False)
    on = plan_mosaic_screens(buckets, aspects, assets)
    assert mosaic5_exposure_rate(on) > mosaic5_exposure_rate(off)


def test_scoring_disabled_skips_replan():
    buckets, aspects, assets = build_portrait_heavy_trip()
    legacy = plan_legacy_screens(buckets, aspects, assets)
    replanned, meta = maybe_replan_chapters(
        deepcopy(legacy),
        buckets=buckets,
        aspects=aspects,  # type: ignore[arg-type]
        assets=assets,
        scoring_enabled=False,
        weights=ScoringWeights(aspect_match=1.0),
        beam_width=3,
        degradation=DegradationAssessment(force_legacy=False),
    )
    assert layout_snapshot(replanned) == layout_snapshot(legacy)
    assert meta.get("skipReason") == "scoring_disabled"
