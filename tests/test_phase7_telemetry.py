"""P7 telemetry: timings breakdown and cacheHitRatio."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip
from travelogue.vision.cache import EmbeddingCachePlan, save_embedding_cache


def _album(tmp_path: Path, n: int = 4) -> Path:
    album = tmp_path / "album"
    album.mkdir()
    for i in range(n):
        Image.new("RGB", (800, 600), (i * 40, 80, 120)).save(album / f"p{i}.jpg")
    return album


def test_ingest_elapsed_ms_breakdown(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("tel-ingest", trips, title="telemetry")
    trip_dir = trips / "tel-ingest"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    result = ingest_into_trip(trip, trip_dir, from_dir=_album(tmp_path), dedupe=False)
    elapsed = (result.stats or {}).get("elapsedMs") or {}
    assert "total" in elapsed
    assert elapsed["total"] >= 0
    assert "decode" in elapsed
    assert "webp" in elapsed
    assert elapsed["decode"] >= 0
    assert elapsed["webp"] >= 0


def test_embedding_cache_plan_hit_ratio() -> None:
    plan = EmbeddingCachePlan("reuse", ["a", "b", "c"], [], [], 0.0)
    assert plan.cache_hit_ratio() == 1.0
    plan_inc = EmbeddingCachePlan("incremental", ["a", "b", "c", "d"], ["d"], [], 0.25)
    assert plan_inc.cache_hit_ratio() == 0.75


def test_persist_recommended_batch_size(tmp_path: Path) -> None:
    from travelogue.vision.clip_encoder import load_persisted_batch_size, persist_recommended_batch_size

    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    persist_recommended_batch_size(8, trips_dir=trips_dir)
    assert load_persisted_batch_size(trips_dir=trips_dir) == 8

    trip_dir = trips_dir / "demo"
    trip_dir.mkdir()
    import numpy as np

    save_embedding_cache(
        trip_dir,
        asset_ids=["a1"],
        vectors=np.zeros((1, 8), dtype=np.float32),
        source="heuristic",
        recommended_batch_size=12,
    )
    assert load_persisted_batch_size(trip_dir=trip_dir, trips_dir=trips_dir) == 12
