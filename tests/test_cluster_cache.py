"""F-CLU-CACHE-01～05 · incremental embedding cache."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from travelogue.config import AppConfig, ClusteringConfig, VisionConfig
from travelogue.curation.clustering import run_clustering_layer
from travelogue.vision.cache import (
    FULL_RECLUSTER_MIN_RATIO,
    INCREMENTAL_MAX_CHANGE_RATIO,
    clear_cluster_cache,
    compute_change_ratio,
    load_embedding_cache,
    plan_embedding_refresh,
    prepare_scene_embeddings,
    save_embedding_cache,
)
from travelogue.vision.clip_encoder import ClipEncoder


def _assets(n: int, *, prefix: str = "a") -> list[dict]:
    return [
        {
            "id": f"{prefix}{i:02d}",
            "type": "image",
            "width": 1200,
            "height": 800,
            "sharpness": 0.5 + i * 0.01,
            "subjectBucket": "landscape" if i % 2 == 0 else "food",
        }
        for i in range(n)
    ]


def test_plan_full_when_no_cache(tmp_path: Path) -> None:
    ids = [a["id"] for a in _assets(10)]
    plan = plan_embedding_refresh(tmp_path, ids)
    assert plan.mode == "full"


def test_plan_reuse_when_unchanged(tmp_path: Path) -> None:
    assets = _assets(12)
    ids = [a["id"] for a in assets]
    vectors = np.random.RandomState(0).rand(len(ids), 8).astype(np.float32)
    save_embedding_cache(tmp_path, asset_ids=ids, vectors=vectors, source="heuristic", model="h1")
    plan = plan_embedding_refresh(tmp_path, ids)
    assert plan.mode == "reuse"
    assert plan.change_ratio == 0.0


def test_plan_incremental_under_10_percent(tmp_path: Path) -> None:
    base = _assets(100)
    ids = [a["id"] for a in base]
    vectors = np.random.RandomState(1).rand(len(ids), 8).astype(np.float32)
    save_embedding_cache(tmp_path, asset_ids=ids, vectors=vectors, source="heuristic", model="h1")
    new_assets = base + _assets(5, prefix="n")
    new_ids = [a["id"] for a in new_assets]
    plan = plan_embedding_refresh(tmp_path, new_ids)
    assert plan.mode == "incremental"
    assert len(plan.new_ids) == 5
    assert plan.change_ratio < INCREMENTAL_MAX_CHANGE_RATIO


def test_plan_full_at_30_percent_change(tmp_path: Path) -> None:
    base = _assets(100)
    ids = [a["id"] for a in base]
    vectors = np.random.RandomState(2).rand(len(ids), 8).astype(np.float32)
    save_embedding_cache(tmp_path, asset_ids=ids, vectors=vectors, source="heuristic", model="h1")
    kept = base[:70]
    added = _assets(30, prefix="x")
    new_ids = [a["id"] for a in kept + added]
    ratio, _, _ = compute_change_ratio(new_ids, ids)
    assert ratio >= FULL_RECLUSTER_MIN_RATIO
    plan = plan_embedding_refresh(tmp_path, new_ids)
    assert plan.mode == "full"


def test_prepare_scene_embeddings_incremental_skips_reembed(tmp_path: Path) -> None:
    base = _assets(20)
    ids = [a["id"] for a in base]
    vectors = np.random.RandomState(3).rand(len(ids), 8).astype(np.float32)
    save_embedding_cache(tmp_path, asset_ids=ids, vectors=vectors, source="heuristic", model="h1")
    enc = ClipEncoder()
    extended = base + _assets(1, prefix="n")
    embed, plan = prepare_scene_embeddings(tmp_path, extended, enc, deterministic=True)
    assert plan.mode == "incremental"
    assert embed.asset_ids == [a["id"] for a in extended]
    cached = load_embedding_cache(tmp_path)
    assert cached is not None
    assert len(cached["asset_ids"]) == 21


def test_corrupt_cache_triggers_full_refresh(tmp_path: Path) -> None:
    cache_dir = tmp_path / ".cluster-cache"
    cache_dir.mkdir()
    (cache_dir / "embeddings.npz").write_bytes(b"not-npz")
    (cache_dir / "manifest.json").write_text("{}", encoding="utf-8")
    assets = _assets(8)
    enc = ClipEncoder()
    embed, plan = prepare_scene_embeddings(tmp_path, assets, enc)
    assert plan.mode == "full"
    assert len(embed.asset_ids) == 8


def test_clustering_layer_logs_cache_plan(tmp_path: Path) -> None:
    trip_dir = tmp_path / "trip"
    trip_dir.mkdir()
    assets = _assets(15)
    trip = {"assets": assets, "curation": {}, "chapters": []}
    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="true"),
        vision=VisionConfig(enabled="true"),
    )
    run_clustering_layer(trip, trip_dir=trip_dir, cfg=cfg)
    log = json.loads((trip_dir / "decision_log.json").read_text(encoding="utf-8"))
    kinds = [e.get("kind") for e in log.get("entries") or []]
    assert "cache_plan" in kinds
    assert load_embedding_cache(trip_dir) is not None

    trip2 = {"assets": assets + _assets(1, prefix="n"), "curation": {}, "chapters": []}
    run_clustering_layer(trip2, trip_dir=trip_dir, cfg=cfg)
    log2 = json.loads((trip_dir / "decision_log.json").read_text(encoding="utf-8"))
    cache_entries = [e for e in log2.get("entries") or [] if e.get("kind") == "cache_plan"]
    assert cache_entries
    assert "incremental" in cache_entries[-1].get("detail", "")


def test_force_recluster_clears_cache(tmp_path: Path) -> None:
    assets = _assets(10)
    ids = [a["id"] for a in assets]
    vectors = np.random.RandomState(4).rand(len(ids), 8).astype(np.float32)
    save_embedding_cache(tmp_path, asset_ids=ids, vectors=vectors, source="heuristic", model="h1")
    enc = ClipEncoder()
    _, plan = prepare_scene_embeddings(tmp_path, assets, enc, force_recluster=True)
    assert plan.mode == "full"
