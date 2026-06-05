"""Heuristic embedding cache schema invalidation (C-B)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from travelogue.vision.cache import embedding_cache_vector_stale, plan_embedding_refresh
from travelogue.vision.clip_encoder import HEURISTIC_MODEL_V2, HEURISTIC_V2_DIM


def test_legacy_8d_heuristic_cache_is_stale(tmp_path: Path) -> None:
    vectors = np.zeros((3, 8), dtype=np.float32)
    cached = {"vectors": vectors, "source": "heuristic", "model": "heuristic-v1-quality-bucket"}
    assert embedding_cache_vector_stale(cached, None) is True


def test_heuristic_v2_cache_not_stale(tmp_path: Path) -> None:
    vectors = np.zeros((3, HEURISTIC_V2_DIM), dtype=np.float32)
    cached = {"vectors": vectors, "source": "heuristic", "model": HEURISTIC_MODEL_V2}
    assert embedding_cache_vector_stale(cached, None) is False


def test_plan_refresh_full_on_legacy_heuristic(tmp_path: Path) -> None:
    from travelogue.vision.cache import save_embedding_cache

    ids = ["a1", "a2"]
    vectors = np.zeros((2, 8), dtype=np.float32)
    save_embedding_cache(tmp_path, asset_ids=ids, vectors=vectors, source="heuristic", model="h1")
    plan = plan_embedding_refresh(tmp_path, ids + ["a3"])
    assert plan.mode == "full"
