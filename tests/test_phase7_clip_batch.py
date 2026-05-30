"""Phase 7 CLIP batch inference tests (M27-A-05)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest


def _make_asset(idx: int, rel: str) -> dict:
    return {
        "id": f"a{idx:02d}",
        "type": "image",
        "path": rel,
        "displayFile": rel,
        "width": 1200,
        "height": 1600,
        "sharpness": 0.6,
    }


def _write_jpeg(path: Path, color: tuple[int, int, int]) -> None:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 64), color).save(path, quality=85)


def _build_trip(tmp_path: Path, n: int = 4) -> tuple[list[dict], Path]:
    rels = []
    for i in range(n):
        rel = f"assets/web/img_{i}.jpg"
        _write_jpeg(tmp_path / rel, (30 + i * 10, 60, 90))
        rels.append(rel)
    assets = [_make_asset(i, rels[i]) for i in range(n)]
    return assets, tmp_path


torch = pytest.importorskip("torch")


def test_batch_and_single_subject_class_match(tmp_path: Path) -> None:
    pytest.importorskip("open_clip")
    from travelogue.vision.clip_encoder import ClipEncoder, reset_clip_encoder_singleton

    reset_clip_encoder_singleton()
    assets, trip_dir = _build_trip(tmp_path, n=3)

    batch_enc = ClipEncoder(batch_size=3, batch_auto_tune=False, prefetch=False)
    single_enc = ClipEncoder(batch_size=0, batch_auto_tune=False, prefetch=False)
    assert batch_enc._ensure_clip() and single_enc._ensure_clip()

    batch_assets = [dict(a) for a in assets]
    single_assets = [dict(a) for a in assets]

    batch_enc._embed_clip(batch_assets, trip_dir=trip_dir, deterministic=True)
    single_enc._embed_clip(single_assets, trip_dir=trip_dir, deterministic=True)

    for ba, sa in zip(batch_assets, single_assets):
        assert ba.get("subjectClass") == sa.get("subjectClass")


def test_heuristic_fallback_without_torch(tmp_path: Path, monkeypatch) -> None:
    from travelogue.vision import clip_encoder as mod

    monkeypatch.setattr(mod, "clip_torch_available", lambda: False)
    enc = mod.ClipEncoder()
    assets, _ = _build_trip(tmp_path, n=2)
    result = enc.embed_assets(assets, trip_dir=tmp_path)
    assert result.source == "heuristic"
    assert len(result.asset_ids) == 2
    assert result.vectors.shape[0] == 2


def test_clip_batch_no_heuristic_dim_mix(tmp_path: Path, monkeypatch) -> None:
    """Missing file in a batch must not produce 8d + 512d mixed vectors."""
    from travelogue.vision import clip_encoder as mod

    pytest.importorskip("open_clip")
    assets, trip_dir = _build_trip(tmp_path, n=2)
    assets[1] = dict(assets[1])
    assets[1]["path"] = "assets/web/missing.jpg"
    assets[1]["displayFile"] = "assets/web/missing.jpg"

    enc = mod.ClipEncoder(batch_size=2, batch_auto_tune=False, prefetch=False)
    assert enc._ensure_clip()
    result = enc._embed_clip(assets, trip_dir=trip_dir, deterministic=True)
    assert result.vectors.dtype == np.float32
    assert result.vectors.ndim == 2
    assert result.vectors.shape == (2, result.vectors.shape[1])
    assert result.vectors.shape[1] in (8, 512)
    assert len(result.asset_ids) == 2
    row_norms = np.linalg.norm(result.vectors, axis=1)
    assert np.all(row_norms > 0.9)


def test_embed_stats_recorded_heuristic(tmp_path: Path, monkeypatch) -> None:
    from travelogue.vision import clip_encoder as mod

    monkeypatch.setattr(mod, "clip_torch_available", lambda: False)
    enc = mod.ClipEncoder(batch_size=16)
    assets, trip_dir = _build_trip(tmp_path, n=2)
    enc.embed_assets(assets, trip_dir=trip_dir)
    assert enc.last_embed_stats is None


def test_embed_stats_recorded_clip(tmp_path: Path) -> None:
    pytest.importorskip("open_clip")
    from travelogue.vision.clip_encoder import ClipEncoder, reset_clip_encoder_singleton

    reset_clip_encoder_singleton()
    assets, trip_dir = _build_trip(tmp_path, n=3)
    enc = ClipEncoder(batch_size=3, batch_auto_tune=False, prefetch=False)
    assert enc._ensure_clip()
    enc.embed_assets(assets, trip_dir=trip_dir)
    stats = enc.last_embed_stats
    assert stats is not None
    payload = stats.to_dict()
    assert payload["batchSize"] == 3
    assert payload["batches"] >= 1
    assert payload["elapsedMs"] > 0
    assert "prefetchEnabled" in payload


def test_oom_split_preserves_tuned_batch_size(tmp_path: Path, monkeypatch) -> None:
    import torch

    pytest.importorskip("open_clip")
    from travelogue.vision.clip_encoder import ClipEncoder, reset_clip_encoder_singleton

    reset_clip_encoder_singleton()
    assets, trip_dir = _build_trip(tmp_path, n=4)
    enc = ClipEncoder(batch_size=4, batch_auto_tune=False, prefetch=False)
    assert enc._ensure_clip()
    enc._tuned_batch_size = 4

    calls = {"n": 0}
    real_encode = enc._model.encode_image

    def _flaky_encode(batch):
        calls["n"] += 1
        if batch.shape[0] > 1 and calls["n"] == 1:
            raise RuntimeError("CUDA out of memory")
        with torch.no_grad():
            return real_encode(batch)

    monkeypatch.setattr(enc._model, "encode_image", _flaky_encode)
    result = enc._embed_clip(assets, trip_dir=trip_dir, deterministic=True)
    assert len(result.asset_ids) == 4
    assert enc._tuned_batch_size == 4
    assert enc._oom_cap is None
    assert enc.last_embed_stats is not None
    assert enc.last_embed_stats.oom_halves >= 1
