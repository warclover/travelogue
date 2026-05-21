"""Person-aware screen planning and landscape aspect buckets."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from travelogue.curation.aspect_buckets import landscape_aspect_bucket, prefix_same_bucket
from travelogue.curation.screen_planner import (
    PATTERN_PORTRAIT_1_LANDSCAPE_2,
    plan_screens_for_chapter,
)


def _assets_with_tags(ids: list[str], tag_map: dict[str, list[str]]) -> dict[str, dict]:
    return {
        i: {
            "id": i,
            "tags": tag_map.get(i, []),
            "nativeWidth": 1200,
            "nativeHeight": 1800,
        }
        for i in ids
    }


def test_three_portraits_with_person_triple_row():
    ids = ["p1", "p2", "p3"]
    aspects = {x: "portrait" for x in ids}
    assets = _assets_with_tags(ids, {x: ["person", "face"] for x in ids})
    screens = plan_screens_for_chapter(
        ids, aspects, chapter_id="ch-p", assets=assets
    )
    assert len(screens) == 1
    assert screens[0]["patternId"] == "screen-portrait-3"
    assert screens[0]["layoutHint"] == "person-triple"
    assert len(screens[0]["slots"]) == 3
    assert all(s["fit"] == "contain" for s in screens[0]["slots"])


def test_one_person_portrait_uses_cover_single_screen():
    ids = ["p1"]
    aspects = {"p1": "portrait"}
    assets = _assets_with_tags(ids, {"p1": ["person", "face"]})
    screens = plan_screens_for_chapter(ids, aspects, chapter_id="ch-1p", assets=assets)
    assert len(screens) == 1
    assert screens[0]["patternId"] == "screen-portrait-1"
    assert "layoutHint" not in screens[0]
    assert screens[0]["slots"][0]["fit"] == "cover"


def test_two_person_portraits_one_pair_screen():
    ids = ["p1", "p2"]
    aspects = {x: "portrait" for x in ids}
    assets = _assets_with_tags(ids, {x: ["person", "face"] for x in ids})
    screens = plan_screens_for_chapter(ids, aspects, chapter_id="ch-2p", assets=assets)
    assert len(screens) == 1
    assert screens[0]["patternId"] == "screen-portrait-2"
    assert screens[0]["layoutHint"] == "person-pair"


def test_three_portraits_without_person_stays_triple():
    ids = ["p1", "p2", "p3"]
    aspects = {x: "portrait" for x in ids}
    screens = plan_screens_for_chapter(ids, aspects, chapter_id="ch-s")
    assert len(screens) == 1
    assert screens[0]["patternId"] == "screen-portrait-3"


def test_mixed_p1_l2_blocked_when_portrait_has_person():
    base = datetime(2025, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
    assets = {
        "p1": {
            "id": "p1",
            "tags": ["person", "face"],
            "takenAt": base.isoformat().replace("+00:00", "Z"),
            "nativeWidth": 900,
            "nativeHeight": 1400,
        },
        "l1": {
            "id": "l1",
            "takenAt": (base + timedelta(seconds=2)).isoformat().replace("+00:00", "Z"),
            "nativeWidth": 1920,
            "nativeHeight": 1080,
        },
        "l2": {
            "id": "l2",
            "takenAt": (base + timedelta(seconds=3)).isoformat().replace("+00:00", "Z"),
            "nativeWidth": 1920,
            "nativeHeight": 1080,
        },
    }
    ids = ["p1", "l1", "l2"]
    aspects = {"p1": "portrait", "l1": "landscape", "l2": "landscape"}
    screens = plan_screens_for_chapter(
        ids, aspects, assets=assets, burst_seconds=12.0, chapter_id="ch-m"
    )
    assert not any(sc["patternId"] == PATTERN_PORTRAIT_1_LANDSCAPE_2 for sc in screens)
    assert screens[0]["patternId"] == "screen-portrait-1"
    assert "layoutHint" not in screens[0]
    assert screens[0]["slots"][0]["fit"] == "cover"


def test_landscape_bucket_prefix_splits_ratios():
    assets = {
        "a": {"nativeWidth": 1920, "nativeHeight": 1080},
        "b": {"nativeWidth": 1920, "nativeHeight": 1080},
        "c": {"nativeWidth": 2000, "nativeHeight": 800},
    }
    assert landscape_aspect_bucket(assets["a"]) == "standard"
    assert landscape_aspect_bucket(assets["c"]) == "wide"
    prefix = prefix_same_bucket(["a", "b", "c"], assets)
    assert prefix == ["a", "b"]


def test_landscape_four_mixed_buckets_yields_two_singles_via_planner():
    ids = [f"l{i}" for i in range(4)]
    aspects = {x: "landscape" for x in ids}
    assets = {
        "l0": {"nativeWidth": 1920, "nativeHeight": 1080},
        "l1": {"nativeWidth": 1920, "nativeHeight": 1080},
        "l2": {"nativeWidth": 2000, "nativeHeight": 800},
        "l3": {"nativeWidth": 2000, "nativeHeight": 800},
    }
    screens = plan_screens_for_chapter(ids, aspects, assets=assets, chapter_id="ch-l")
    patterns = [sc["patternId"] for sc in screens]
    assert patterns.count("screen-landscape-1") >= 2
