"""Unit tests for arc_patterns and layout_metrics."""

from __future__ import annotations

from tests._golden.helpers import build_portrait_heavy_trip, plan_legacy_screens
from travelogue.curation.arc_patterns import arc_pattern_bonus, arc_segment_for_chapter
from travelogue.curation.layout_metrics import compute_layout_metrics, pattern_diversity


def test_arc_segment_five_chapters():
    assert arc_segment_for_chapter(1, 5) == "open"
    assert arc_segment_for_chapter(3, 5) == "peak"
    assert arc_segment_for_chapter(5, 5) == "close"


def test_arc_pattern_bonus_prefers_open_patterns():
    assert arc_pattern_bonus("screen-portrait-1", "open") == 1.0
    assert arc_pattern_bonus("screen-unknown", "open") == 0.3


def test_layout_metrics_from_chapters():
    buckets, aspects, assets = build_portrait_heavy_trip()
    chapters = plan_legacy_screens(buckets, aspects, assets)
    m = compute_layout_metrics(chapters)
    assert m["screenCount"] >= 2
    assert 0.0 < pattern_diversity(chapters) <= 1.0
