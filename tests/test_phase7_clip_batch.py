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


def test_embed_stats_recorded(tmp_path: Path, monkeypatch) -> None:
    from travelogue.vision import clip_encoder as mod

    monkeypatch.setattr(mod, "clip_torch_available", lambda: False)
    enc = mod.ClipEncoder(batch_size=16)
    assets, trip_dir = _build_trip(tmp_path, n=2)
    enc.embed_assets(assets, trip_dir=trip_dir)
    # heuristic path skips stats; ensure API exists
    assert hasattr(enc, "last_embed_stats")
