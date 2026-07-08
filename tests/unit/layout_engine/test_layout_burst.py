"""Layout burst utils and stub items tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from travelogue.curation.burst_utils import (
    burst_group_map,
    shared_ingest_burst_group,
    time_near_sequential,
)
from travelogue.curation.chapter_items import items_from_screens


def test_shared_ingest_burst_group():
    assets = {
        "a1": {"burstGroupId": "burst-001"},
        "a2": {"burstGroupId": "burst-001"},
        "a3": {"burstGroupId": "burst-002"},
    }
    assert shared_ingest_burst_group(["a1", "a2"], assets) == "burst-001"
    assert shared_ingest_burst_group(["a1", "a3"], assets) is None


def test_time_near_sequential_uses_burst_group_id():
    assets = {
        "a1": {"burstGroupId": "burst-001", "takenAt": "2020-01-01T00:00:00Z"},
        "a2": {"burstGroupId": "burst-001", "takenAt": "2025-06-01T00:00:00Z"},
    }
    assert time_near_sequential(["a1", "a2"], assets, burst_seconds=3.0) is True


def test_burst_group_map_honors_ingest_ids():
    base = datetime(2025, 5, 1, 12, 0, 0, tzinfo=UTC)
    assets = {}
    ids = ["a1", "a2", "b1"]
    for i, aid in enumerate(["a1", "a2"]):
        assets[aid] = {
            "burstGroupId": "burst-001",
            "takenAt": (base + timedelta(hours=i)).isoformat().replace("+00:00", "Z"),
        }
    assets["b1"] = {
        "takenAt": (base + timedelta(days=1)).isoformat().replace("+00:00", "Z"),
    }
    aspects = {x: "landscape" for x in ids}
    groups = burst_group_map(ids, assets, aspects, burst_seconds=3.0)
    assert groups["a1"] == groups["a2"]
    assert groups["b1"] != groups["a1"]


def test_items_from_screens_one_block_per_screen():
    chapter = {
        "screens": [
            {"patternId": "screen-landscape-4", "slots": [{"assetId": f"a{i}"} for i in range(4)]},
            {"patternId": "screen-portrait-1", "slots": [{"assetId": "p1"}]},
        ]
    }
    items = items_from_screens(chapter)
    assert len(items) == 2
    assert items[0]["type"] == "media-row"
    assert items[1]["type"] == "media-card"


def test_preferred_hero_for_day_bucket():
    from travelogue.curation.screen_planner_attach import _preferred_hero_for_bucket

    bucket = ["h1", "a2", "a3"]
    asset_to_ch = {"h1": "ch-01", "a2": "ch-01", "a3": "ch-02"}
    hero_by_ch = {"ch-01": "h1", "ch-02": "a3"}
    assets = {
        "h1": {"id": "h1", "width": 2400, "height": 1350, "aspectKind": "landscape"},
        "a2": {"id": "a2", "width": 1200, "height": 800, "aspectKind": "landscape"},
        "a3": {"id": "a3", "width": 900, "height": 1600, "aspectKind": "portrait"},
    }
    assert _preferred_hero_for_bucket(bucket, asset_to_ch, hero_by_ch, assets) == "h1"
