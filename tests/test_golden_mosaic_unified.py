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
from travelogue.curation.mosaic.constants import (
    PATTERN_LANDSCAPE_6,
    PATTERN_MOSAIC_5_HERO_3_2_PLUS_4,
    PATTERN_PORTRAIT_3,
    PATTERN_PORTRAIT_4,
)
from travelogue.curation.mosaic.metrics import mcs_unified_exposure_rate


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
    buckets, aspects, assets = build_mosaic_landscape6_trip()
    chapters = plan_mosaic_screens(buckets, aspects, assets)
    assert layout_snapshot(chapters) == load_golden("mosaic-landscape-6")
    patterns = [s["patternId"] for s in chapters[0]["screens"]]
    # Flat 6-grid is still avoided; the hero-3-2 weighted track is now also
    # off-limits for an all-landscape window — its tall main slot (displayAspect
    # ~0.89) crops landscapes badly (Plate 63 guard, commit 1dedb8d).
    assert PATTERN_LANDSCAPE_6 not in patterns
    assert PATTERN_MOSAIC_5_HERO_3_2_PLUS_4 not in patterns


def test_mosaic_landscape_6_ab_unified_vs_legacy():
    """6 横图：MCS 不再合并为 hero-3-2（Plate 63 高槽裁切 guard），拆为更小的横图屏。"""
    buckets, aspects, assets = build_mosaic_landscape6_trip()
    off = plan_legacy_screens(buckets, aspects, assets, mosaic_enabled=False)
    on = plan_mosaic_screens(buckets, aspects, assets)
    assert len(off[0]["screens"]) == 3
    on_patterns = [s["patternId"] for s in on[0]["screens"]]
    assert PATTERN_MOSAIC_5_HERO_3_2_PLUS_4 not in on_patterns


def test_golden_mosaic_portrait_8_grid():
    buckets, aspects, assets = build_mosaic_portrait8_trip()
    chapters = plan_mosaic_screens(
        buckets,
        aspects,
        assets,
        trip_photo_total=60,
        orientation_summary={"portrait": 8, "landscape": 0},
    )
    assert layout_snapshot(chapters) == load_golden("mosaic-portrait-8")


def test_golden_mosaic_landscape_9():
    buckets, aspects, assets = build_mosaic_landscape9_trip()
    chapters = plan_mosaic_screens(
        buckets,
        aspects,
        assets,
        trip_photo_total=60,
    )
    assert layout_snapshot(chapters) == load_golden("mosaic-landscape-9")


def test_mosaic_portrait_3_ab_exposure():
    buckets, aspects, assets = build_mosaic_portrait3_trip()
    off = plan_legacy_screens(buckets, aspects, assets, mosaic_enabled=False)
    on = plan_mosaic_screens(buckets, aspects, assets)
    assert on[0]["screens"][0]["patternId"] == PATTERN_PORTRAIT_3
    assert mcs_unified_exposure_rate(on) >= mcs_unified_exposure_rate(off)
