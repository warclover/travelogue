"""ClipEncoder concurrency / prefetch safety (T5)."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")


def _write_trip(tmp_path: Path, n: int) -> tuple[list[dict], Path]:
    from PIL import Image

    assets = []
    for i in range(n):
        rel = f"assets/web/img_{i}.jpg"
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (48, 48), (40 + i * 15, 70, 100)).save(path, quality=85)
        assets.append(
            {
                "id": f"a{i:02d}",
                "type": "image",
                "path": rel,
                "displayFile": rel,
                "width": 48,
                "height": 48,
                "sharpness": 0.5,
            }
        )
    return assets, tmp_path


def test_prefetch_embed_completes_with_stats(tmp_path: Path) -> None:
    pytest.importorskip("open_clip")
    from travelogue.vision.clip_encoder import ClipEncoder, reset_clip_encoder_singleton

    reset_clip_encoder_singleton()
    assets, trip_dir = _write_trip(tmp_path, 6)
    enc = ClipEncoder(batch_size=2, batch_auto_tune=False, prefetch=True)
    assert enc._ensure_clip()
    result = enc.embed_assets(assets, trip_dir=trip_dir, deterministic=True)
    assert len(result.asset_ids) == 6
    stats = enc.last_embed_stats
    assert stats is not None
    assert stats.prefetch_enabled is True
    assert stats.batches >= 3


def test_parallel_embed_clip_sessions_serialize_on_lock(tmp_path: Path) -> None:
    """Two threads sharing one encoder should not raise CUDA/prefetch races."""
    pytest.importorskip("open_clip")
    from travelogue.vision.clip_encoder import ClipEncoder, reset_clip_encoder_singleton

    reset_clip_encoder_singleton()
    assets, trip_dir = _write_trip(tmp_path, 4)
    enc = ClipEncoder(batch_size=2, batch_auto_tune=False, prefetch=True)
    assert enc._ensure_clip()

    errors: list[BaseException] = []
    barrier = threading.Barrier(2)

    def _run() -> None:
        try:
            barrier.wait(timeout=5)
            enc.embed_assets(
                [dict(a) for a in assets],
                trip_dir=trip_dir,
                deterministic=True,
            )
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=_run) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    assert not errors
