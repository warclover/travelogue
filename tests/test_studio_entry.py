"""Phase 4 M16 · F-P4-PRV-06: preview entry deep-link resolver tests."""

from __future__ import annotations

from travelogue.web.studio_entry import (
    build_chapter_summaries,
    build_entry,
    build_intent_summary,
    resolve_peak_screen_id,
)


def _screen(screen_id: str, asset_ids: list[str], *, arc_segment: str | None = None) -> dict:
    screen = {
        "screenId": screen_id,
        "patternId": "screen-portrait-1",
        "slots": [{"assetId": a} for a in asset_ids],
    }
    if arc_segment:
        screen["arcSegment"] = arc_segment
    return screen


def _trip_with_screens(*chapters_screens: list[dict]) -> dict:
    return {
        "chapters": [{"screens": screens} for screens in chapters_screens],
    }


def test_peak_prefers_best_scored_peak_screen():
    trip = _trip_with_screens(
        [
            _screen("s1", ["a1"], arc_segment="peak"),
            _screen("grid-peak", ["a2", "a3"], arc_segment="peak"),
            _screen("hero-peak", ["a4"], arc_segment="peak"),
        ],
    )
    assert resolve_peak_screen_id(trip) == "hero-peak"


def test_peak_prefers_arc_segment_over_scene_cluster():
    trip = _trip_with_screens(
        [_screen("s1", ["a1"]), _screen("peak", ["a2"], arc_segment="peak")],
        [_screen("s3", ["a9"])],
    )
    trip["curation"] = {
        "clustering": {
            "clusters": [
                {"assetIds": ["a9", "a10", "a11"]},
            ]
        }
    }
    assert resolve_peak_screen_id(trip) == "peak"


def test_peak_prefers_largest_scene_cluster_screen():
    trip = _trip_with_screens(
        [_screen("s1", ["a1", "a2"]), _screen("s2", ["a3"])],
        [_screen("s3", ["a9"])],
    )
    trip["curation"] = {
        "clustering": {
            "clusters": [
                {"assetIds": ["a3"]},
                {"assetIds": ["a9", "a10", "a11"]},  # largest
            ]
        }
    }
    # Largest cluster contains a9 -> screen s3.
    assert resolve_peak_screen_id(trip) == "s3"


def test_peak_falls_back_to_first_content_screen():
    trip = _trip_with_screens(
        [_screen("cover", []), _screen("s2", ["a1"])],
    )
    assert resolve_peak_screen_id(trip) == "s2"


def test_peak_falls_back_to_first_screen_when_no_assets():
    trip = _trip_with_screens([_screen("cover", []), _screen("s2", [])])
    assert resolve_peak_screen_id(trip) == "cover"


def test_peak_none_for_no_screens():
    assert resolve_peak_screen_id({"chapters": []}) is None
    assert resolve_peak_screen_id({}) is None


def test_build_entry_appends_fragment_when_peak_exists():
    trip = _trip_with_screens([_screen("s1", ["a1"])])
    entry = build_entry(trip, "demo-trip")
    assert entry["peakScreenId"] == "s1"
    assert entry["previewUrl"] == "/demo-trip/index.html#screen-s1"
    assert entry["scrollShareUrl"] == "/demo-trip/index.html?share=1#screen-s1"


def test_build_entry_no_fragment_when_no_peak():
    entry = build_entry({"chapters": []}, "demo-trip")
    assert entry["peakScreenId"] is None
    assert entry["previewUrl"] == "/demo-trip/index.html"
    assert entry["scrollShareUrl"] == "/demo-trip/index.html?share=1"


def test_intent_summary_reads_intent_then_meta():
    trip = {
        "intent": {"title": "京都之秋", "userNotes": "想表达静谧"},
        "meta": {"title": "fallback"},
        "assets": [
            {"userTier": "featured"},
            {"userTier": "featured"},
            {"userTier": "normal"},
        ],
        "curation": {"clustering": {"segments": [{}, {}, {}]}},
    }
    summary = build_intent_summary(trip)
    assert summary["title"] == "京都之秋"
    assert summary["featuredCount"] == 2
    assert summary["segmentCount"] == 3
    assert summary["hasUserNotes"] is True


def test_build_entry_includes_pipeline_and_chapters():
    trip = {
        "pipeline": {"status": "structure_draft"},
        "chapters": [{
            "id": "ch-01",
            "title": "京都",
            "screens": [_screen("s1", ["a1"])],
            "curation": {"memoryAnchors": ["寺", "雨"]},
        }],
    }
    entry = build_entry(trip, "demo-trip")
    assert entry["pipelineStatus"] == "structure_draft"
    assert entry["g1Pending"] is True
    assert entry["chapters"][0]["memoryAnchors"] == ["寺", "雨"]
    assert entry["aesthetic"]["enabled"] is True


def test_chapter_summaries_empty_without_chapters():
    assert build_chapter_summaries({}) == []
    summary = build_intent_summary({})
    assert summary["title"] == "我的旅途"
    assert summary["featuredCount"] == 0
    assert summary["segmentCount"] == 0
    assert summary["hasUserNotes"] is False
    assert summary["userNotes"] == ""
