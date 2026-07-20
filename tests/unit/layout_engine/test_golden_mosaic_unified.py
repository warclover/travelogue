"""Golden baselines for Phase 15 S2 · 3/4/6 unified MCS windows."""

from __future__ import annotations

from tests._golden.helpers import (
    build_mosaic_landscape6_trip,
    build_mosaic_landscape9_trip,
    build_mosaic_portrait3_trip,
    build_mosaic_portrait4_trip,
    build_mosaic_portrait8_trip,
    layout_snapshot,
    load_golden,
    plan_legacy_screens,
    plan_mosaic_screens,
)
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_LANDSCAPE_6,
    PATTERN_MOSAIC_5_HERO_3_2_PLUS_4,
    PATTERN_PORTRAIT_3,
    PATTERN_PORTRAIT_4,
)
from travelogue.layout_engine.mosaic.metrics import mcs_unified_exposure_rate


def test_golden_mosaic_portrait_3_matches_mcs():
    buckets, aspects, assets = build_mosaic_portrait3_trip()
    chapters = plan_mosaic_screens(buckets, aspects, assets)
    assert layout_snapshot(chapters) == load_golden("mosaic-portrait-3")
    assert mcs_unified_exposure_rate(chapters) == 1.0


def test_golden_mosaic_portrait_4_matches_mcs():
    """Pair-first priority: 4 portraits tile into two portrait-2 pairs.

    Two-column pairs outrank the dense portrait-4 (2×2) grid, so a run of four
    standard portraits never collapses into a single quad screen.
    """
    buckets, aspects, assets = build_mosaic_portrait4_trip()
    chapters = plan_mosaic_screens(buckets, aspects, assets)
    assert layout_snapshot(chapters) == load_golden("mosaic-portrait-4")
    patterns = [s["patternId"] for s in chapters[0]["screens"]]
    assert patterns == ["screen-portrait-2", "screen-portrait-2"]
    assert PATTERN_PORTRAIT_4 not in patterns


def test_golden_mosaic_landscape_6_matches_mcs():
    """LTN C3 · landscape-6 pruned; 6L splits into smaller landscape screens."""
    buckets, aspects, assets = build_mosaic_landscape6_trip()
    chapters = plan_mosaic_screens(buckets, aspects, assets)
    patterns = [s["patternId"] for s in chapters[0]["screens"]]
    assert PATTERN_LANDSCAPE_6 not in patterns
    assert PATTERN_MOSAIC_5_HERO_3_2_PLUS_4 not in patterns
    assert "screen-landscape-4" in patterns or "screen-landscape-1" in patterns


def test_mosaic_landscape_6_ab_unified_vs_legacy():
    """6 横图：MCS 不再合并为 hero-3-2（Plate 63）；flat-6 已剪除。"""
    buckets, aspects, assets = build_mosaic_landscape6_trip()
    off = plan_legacy_screens(buckets, aspects, assets, mosaic_enabled=False)
    on = plan_mosaic_screens(buckets, aspects, assets)
    assert len(off[0]["screens"]) == 3
    on_patterns = [s["patternId"] for s in on[0]["screens"]]
    assert PATTERN_MOSAIC_5_HERO_3_2_PLUS_4 not in on_patterns
    assert PATTERN_LANDSCAPE_6 not in on_patterns


def test_golden_mosaic_portrait_8_pair_first_after_grid8_prune():
    """LTN C3 · grid-8 pruned; eight portraits fall to pair-first tiler."""
    buckets, aspects, assets = build_mosaic_portrait8_trip()
    chapters = plan_mosaic_screens(
        buckets,
        aspects,
        assets,
        trip_photo_total=60,
        orientation_summary={"portrait": 8, "landscape": 0},
    )
    patterns = [s["patternId"] for s in chapters[0]["screens"]]
    assert "screen-portrait-grid-8" not in patterns
    assert patterns.count("screen-portrait-2") >= 2


def test_golden_mosaic_landscape_9_after_prune():
    """LTN C3 · landscape-9 pruned from MCS active set."""
    buckets, aspects, assets = build_mosaic_landscape9_trip()
    chapters = plan_mosaic_screens(
        buckets,
        aspects,
        assets,
        trip_photo_total=60,
    )
    patterns = [s["patternId"] for s in chapters[0]["screens"]]
    assert "screen-landscape-9" not in patterns
    assert any(p.startswith("screen-landscape-") for p in patterns)


def test_mosaic_portrait_3_ab_exposure():
    buckets, aspects, assets = build_mosaic_portrait3_trip()
    off = plan_legacy_screens(buckets, aspects, assets, mosaic_enabled=False)
    on = plan_mosaic_screens(buckets, aspects, assets)
    assert on[0]["screens"][0]["patternId"] == PATTERN_PORTRAIT_3
    assert mcs_unified_exposure_rate(on) >= mcs_unified_exposure_rate(off)
