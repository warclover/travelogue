"""Curate consumption of curation.clustering segments (Phase 3 M12)."""

from __future__ import annotations

import pytest

from travelogue.config import AppConfig, ClusteringConfig, VisionConfig
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.clustering_buckets import cap_geo_segments, merge_small_geo_events
from travelogue.curation.curate import run_curate


def _gps_trip() -> dict:
    assets = []
    # Tokyo stay
    for i in range(5):
        assets.append(
            {
                "id": f"t{i}",
                "type": "image",
                "takenAt": f"2025-06-01T{9 + i}:00:00Z",
                "geo": {"lat": 35.681 + i * 0.001, "lon": 139.767},
                "place": {"city": "东京"},
                "width": 1200,
                "height": 1600,
                "sharpness": 0.6,
            }
        )
    # Kyoto stay
    for i in range(5):
        assets.append(
            {
                "id": f"k{i}",
                "type": "image",
                "takenAt": f"2025-06-01T{14 + i}:00:00Z",
                "geo": {"lat": 35.011 + i * 0.001, "lon": 135.768},
                "place": {"city": "京都"},
                "width": 1200,
                "height": 1600,
                "sharpness": 0.6,
            }
        )
    return {
        "schemaVersion": "0.2",
        "exportLayout": "auto",
        "meta": {"title": "关东关西", "places": ["日本"]},
        "assets": assets,
        "curation": {},
        "chapters": [],
    }


def test_cap_geo_segments_limits_to_five() -> None:
    segments = [
        {"id": f"e{i}", "startDate": "2025-06-01", "endDate": "2025-06-01", "assetIds": [f"a{i}"]}
        for i in range(8)
    ]
    capped = cap_geo_segments(segments, min_chapters=3, max_chapters=5)
    assert 3 <= len(capped) <= 5


def test_geo_clustering_produces_chapters(tmp_path) -> None:
    trip_dir = tmp_path / "gps-trip"
    trip_dir.mkdir()
    cfg = AppConfig(clustering=ClusteringConfig(enabled="true"))
    trip = _gps_trip()
    run_clustering_layer(trip, trip_dir=trip_dir, cfg=cfg)
    clustering = trip["curation"]["clustering"]
    assert clustering["segmentMode"] == "geo_event"
    assert len(clustering["segments"]) >= 2

    result = run_curate(trip, apply_layout=True, trip_dir=trip_dir, cfg=cfg)
    assert 3 <= result.chapter_count <= 5


def test_merge_small_geo_events_combines_neighbors() -> None:
    segments = [
        {
            "id": "e1",
            "startDate": "2025-06-01",
            "endDate": "2025-06-01",
            "assetIds": ["a1", "a2"],
        },
        {
            "id": "e2",
            "startDate": "2025-06-01",
            "endDate": "2025-06-01",
            "assetIds": ["a3", "a4"],
        },
    ]
    merged = merge_small_geo_events(segments, min_photos=15)
    assert len(merged) == 1
    assert len(merged[0]["assetIds"]) == 4


def test_vision_clustering_writes_scene_fields(tmp_path) -> None:
    pytest.importorskip("sklearn")
    from PIL import Image

    trip_dir = tmp_path / "vision-trip"
    trip_dir.mkdir()
    (trip_dir / "assets").mkdir()
    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="true"),
        vision=VisionConfig(enabled="true"),
    )
    trip = _gps_trip()
    for idx, asset in enumerate(trip["assets"]):
        rel = f"assets/{asset['id']}.webp"
        path = trip_dir / rel
        Image.new("RGB", (120, 120), color=(idx * 17 % 255, 80, 120)).save(path)
        asset["displayFile"] = rel
        asset["sourceFile"] = rel
    result = run_clustering_layer(trip, trip_dir=trip_dir, cfg=cfg)
    assert result.mode == "full"
    assert trip["curation"]["clustering"].get("clusters") is not None
    assert any(a.get("sceneClusterId") is not None for a in trip["assets"])
