"""Golden baselines for Phase 15 S2 · 3/4/6 unified MCS windows."""

from __future__ import annotations

from travelogue.curation.mosaic.constants import (
    PATTERN_LANDSCAPE_4,
    PATTERN_LANDSCAPE_6,
    PATTERN_PORTRAIT_3,
    PATTERN_PORTRAIT_4,
)
from travelogue.curation.mosaic.metrics import mcs_unified_exposure_rate

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


def test_golden_mosaic_portrait_3_matches_mcs():
    buckets, aspects, assets = build_mosaic_portrait3_trip()
    chapters = plan_mosaic_screens(buckets, aspects, assets)
    assert layout_snapshot(chapters) == load_golden("mosaic-portrait-3")
    assert mcs_unified_exposure_rate(chapters) == 1.0


def test_golden_mosaic_portrait_4_matches_mcs():
    """4 portraits use portrait-stage screen-portrait-4 (not legacy wide 2×2)."""
    buckets, aspects, assets = build_mosaic_portrait4_trip()
    chapters = plan_mosaic_screens(buckets, aspects, assets)
    assert layout_snapshot(chapters) == load_golden("mosaic-portrait-4")
    screens = chapters[0]["screens"]
    assert screens[0]["patternId"] == PATTERN_PORTRAIT_4


def test_golden_mosaic_landscape_6_matches_mcs():
    buckets, aspects, assets = build_mosaic_landscape6_trip()
    chapters = plan_mosaic_screens(buckets, aspects, assets)
    assert layout_snapshot(chapters) == load_golden("mosaic-landscape-6")
    patterns = [s["patternId"] for s in chapters[0]["screens"]]
    assert PATTERN_LANDSCAPE_6 not in patterns
    assert PATTERN_LANDSCAPE_4 in patterns


def test_mosaic_landscape_6_ab_unified_vs_legacy():
    """6 横图：MCS 与 legacy 在当前阈值下拆屏策略一致。"""
    buckets, aspects, assets = build_mosaic_landscape6_trip()
    off = plan_legacy_screens(buckets, aspects, assets, mosaic_enabled=False)
    on = plan_mosaic_screens(buckets, aspects, assets)
    assert layout_snapshot(off) == layout_snapshot(on)
    assert len(on[0]["screens"]) >= 2


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
