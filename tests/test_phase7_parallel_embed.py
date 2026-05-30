"""Phase 7 parallel embed integration tests (M28-A-06)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from travelogue.config import AppConfig, ClusteringConfig, PipelineConfig, VisionConfig
from travelogue.vision.cache import load_embedding_cache
from travelogue.vision.parallel_embed import ParallelEmbedCoordinator


def _write_asset_files(trip_dir: Path, asset_id: str) -> dict:
    web = trip_dir / "assets" / "web"
    web.mkdir(parents=True, exist_ok=True)
    rel = f"assets/web/{asset_id}.jpg"
    Image.new("RGB", (64, 64), (50, 80, 110)).save(trip_dir / rel, quality=85)
    return {
        "id": asset_id,
        "type": "image",
        "path": rel,
        "displayFile": rel,
        "width": 64,
        "height": 64,
        "sharpness": 0.5,
    }


def test_parallel_embed_coordinator_writes_cache(tmp_path: Path, monkeypatch) -> None:
    from travelogue.vision import clip_encoder as enc_mod

    monkeypatch.setattr(enc_mod, "clip_torch_available", lambda: False)

    cfg = AppConfig(
        vision=VisionConfig(enabled="false", batch_size=8),
        clustering=ClusteringConfig(deterministic=True),
        pipeline=PipelineConfig(parallel_embed=True, parallel_embed_chunk=2),
    )
    assets = [_write_asset_files(tmp_path, f"a{i:02d}") for i in range(4)]
    coord = ParallelEmbedCoordinator(tmp_path, cfg=cfg, chunk_size=2)
    for a in assets:
        coord.offer(a)
    coord.finish()

    cached = load_embedding_cache(tmp_path)
    assert cached is not None
    assert len(cached["asset_ids"]) == 4


def test_parallel_embed_no_corrupt_manifest(tmp_path: Path, monkeypatch) -> None:
    from travelogue.vision import clip_encoder as enc_mod

    monkeypatch.setattr(enc_mod, "clip_torch_available", lambda: False)
    cfg = AppConfig(pipeline=PipelineConfig(parallel_embed_chunk=1))
    coord = ParallelEmbedCoordinator(tmp_path, cfg=cfg, chunk_size=1)
    for i in range(3):
        coord.offer(_write_asset_files(tmp_path, f"b{i:02d}"))
    coord.finish()

    cached = load_embedding_cache(tmp_path)
    assert cached is not None
    vectors = cached["vectors"]
    assert vectors.shape[0] == 3
    norms = np.linalg.norm(vectors, axis=1)
    assert np.all(norms > 0.9)
