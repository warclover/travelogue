"""Phase 4 M16 · F-P4-PRV-06: preview entry deep-link resolver tests."""

from __future__ import annotations

from travelogue.web.studio_entry import (
    build_entry,
    build_intent_summary,
    resolve_peak_screen_id,
)


def _screen(screen_id: str, asset_ids: list[str]) -> dict:
    return {
        "screenId": screen_id,
        "patternId": "screen-portrait-1",
        "slots": [{"assetId": a} for a in asset_ids],
    }


def _trip_with_screens(*chapters_screens: list[dict]) -> dict:
    return {
        "chapters": [{"screens": screens} for screens in chapters_screens],
    }


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


def test_build_entry_no_fragment_when_no_peak():
    entry = build_entry({"chapters": []}, "demo-trip")
    assert entry["peakScreenId"] is None
    assert entry["previewUrl"] == "/demo-trip/index.html"


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


def test_intent_summary_defaults():
    summary = build_intent_summary({})
    assert summary["title"] == "我的旅途"
    assert summary["featuredCount"] == 0
    assert summary["segmentCount"] == 0
    assert summary["hasUserNotes"] is False
