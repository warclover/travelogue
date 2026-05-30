"""Phase 7 cache ABI tests (M28-B-03)."""

from __future__ import annotations

import numpy as np

from travelogue.config import AppConfig, ClusteringConfig, VisionConfig
from travelogue.vision.cache import (
    cache_abi_matches,
    compute_cache_config_fingerprint,
    plan_embedding_refresh,
    save_embedding_cache,
)


def test_abi_mismatch_triggers_full_refresh(tmp_path) -> None:
    cfg = AppConfig(
        clustering=ClusteringConfig(cache_abi_version="v1"),
        vision=VisionConfig(model="ViT-B/32"),
    )
    ids = ["a1", "a2"]
    vecs = np.random.randn(2, 8).astype(np.float32)
    save_embedding_cache(tmp_path, asset_ids=ids, vectors=vecs, source="clip", model="m", cfg=cfg)

    cfg2 = AppConfig(
        clustering=ClusteringConfig(cache_abi_version="v2"),
        vision=VisionConfig(model="ViT-B/32"),
    )
    plan = plan_embedding_refresh(tmp_path, ids, cfg=cfg2)
    assert plan.mode == "full"


def test_fingerprint_auto_stable() -> None:
    cfg = AppConfig()
    fp1 = compute_cache_config_fingerprint(cfg)
    fp2 = compute_cache_config_fingerprint(cfg)
    assert fp1 == fp2
    assert cache_abi_matches({"configFingerprint": fp1, "algoVersion": "v1"}, cfg)
