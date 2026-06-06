"""NR-P3-01 · clustering off documented equivalent to Phase 2 curate path."""

from __future__ import annotations

import copy

from travelogue.config import AppConfig, ClusteringConfig
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.curate import run_curate


def _sample_trip() -> dict:
    assets = []
    for i in range(12):
        day = 10 + (i // 4)
        assets.append(
            {
                "id": f"a{i:02d}",
                "type": "image",
                "takenAt": f"2025-04-{day:02d}T{8 + i % 4:02d}:00:00Z",
                "width": 1200,
                "height": 1600,
                "sharpness": 0.5 + i * 0.01,
            }
        )
    return {
        "schemaVersion": "0.2",
        "exportLayout": "auto",
        "meta": {"title": "测试", "places": ["旅途"]},
        "assets": assets,
        "curation": {},
        "chapters": [],
    }


def _chapter_asset_sets(trip: dict) -> list[frozenset[str]]:
    return [frozenset(ch.get("assetIds") or []) for ch in trip.get("chapters") or []]


def test_clustering_disabled_matches_baseline_curate(tmp_path) -> None:
    trip_dir = tmp_path / "trip"
    trip_dir.mkdir()
    cfg_off = AppConfig(clustering=ClusteringConfig(enabled="false"))

    baseline = _sample_trip()
    run_curate(baseline, apply_layout=True, trip_dir=trip_dir, cfg=cfg_off)

    candidate = _sample_trip()
    run_clustering_layer(candidate, trip_dir=trip_dir, cfg=cfg_off)
    run_curate(candidate, apply_layout=True, trip_dir=trip_dir, cfg=cfg_off)

    assert _chapter_asset_sets(baseline) == _chapter_asset_sets(candidate)


def test_date_fallback_ignores_geo_segments(tmp_path) -> None:
    trip_dir = tmp_path / "trip2"
    trip_dir.mkdir()
    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="true", segment_curate_mode="date_fallback")
    )

    trip = _sample_trip()
    for i, a in enumerate(trip["assets"]):
        a["geo"] = {"lat": 35.0 + i * 0.5, "lon": 139.0}

    baseline = copy.deepcopy(trip)
    run_curate(baseline, apply_layout=True, trip_dir=trip_dir, cfg=cfg)

    enriched = copy.deepcopy(trip)
    run_clustering_layer(enriched, trip_dir=trip_dir, cfg=cfg)
    run_curate(enriched, apply_layout=True, trip_dir=trip_dir, cfg=cfg)

    assert _chapter_asset_sets(baseline) == _chapter_asset_sets(enriched)
