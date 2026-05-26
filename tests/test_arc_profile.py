"""Phase 3a: adaptive arc profile."""

from __future__ import annotations

from travelogue.curation.arc_patterns import (
    ARC_CLOSE,
    ARC_MOMENT,
    ARC_OPEN,
    ARC_PEAK,
    arc_pattern_bonus,
    arc_segment_for_chapter,
    arc_segments_for_trip,
    infer_arc_profile,
)


def _asset(aid: str, *, sharp: float = 0.5, tags: list[str] | None = None) -> dict:
    return {
        "id": aid,
        "width": 2000,
        "height": 1200,
        "quality": {"sharpness": sharp},
        "tags": tags or [],
    }


def test_flat_profile_three_beat():
    segs = arc_segments_for_trip(4, "flat")
    assert segs == [ARC_OPEN, ARC_MOMENT, ARC_MOMENT, ARC_CLOSE]


def test_moderate_profile_has_single_peak():
    segs = arc_segments_for_trip(5, "moderate")
    assert segs.count(ARC_PEAK) == 1
    assert segs[0] == ARC_OPEN
    assert segs[-1] == ARC_CLOSE


def test_infer_flat_on_uniform_assets():
    assets = [_asset(f"a{i}", sharp=0.5, tags=["landscape"]) for i in range(8)]
    buckets = [ [a["id"] for a in assets[:4]], [a["id"] for a in assets[4:]] ]
    assert infer_arc_profile(assets, buckets, flat_threshold=0.08) == "flat"


def test_peak_pattern_neutral_on_flat_profile():
    bonus = arc_pattern_bonus(
        "screen-mosaic-5-main-portrait-3land",
        ARC_MOMENT,
        profile="flat",
    )
    assert bonus == 0.5


def test_dynamic_keeps_peak_bonus():
    bonus = arc_pattern_bonus(
        "screen-mosaic-5-main-portrait-3land",
        ARC_PEAK,
        profile="dynamic",
    )
    assert bonus == 1.0


def test_arc_segment_respects_profile():
    assert arc_segment_for_chapter(2, 4, profile="flat") == ARC_MOMENT
