"""Regression: scene-clustering timeout must not block the surrounding pipeline.

Covers P1 fix from the Phase 3 code review (ThreadPoolExecutor's context manager
called `shutdown(wait=True)` on exit, so `future.result(timeout=...)` raising a
TimeoutError did NOT actually free the pipeline — the with-block would still
block until CLIP finished). After the fix the layer must return within roughly
the configured timeout, regardless of how long the encoder would have taken.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from travelogue.config import AppConfig, ClusteringConfig, SceneClusterConfig, VisionConfig
from travelogue.curation import clustering as clustering_mod
from travelogue.curation.clustering import ClusteringLayer


def _gps_assets(count: int = 12) -> list[dict]:
    assets: list[dict] = []
    for i in range(count):
        day = 1 + (i // 4)
        assets.append(
            {
                "id": f"t{i:02d}",
                "type": "image",
                "takenAt": f"2025-04-{day:02d}T0{i % 9}:00:00Z",
                "geo": {"lat": 35.0 + 0.01 * (i // 4), "lon": 139.0 + 0.01 * (i % 4)},
                "width": 1200,
                "height": 1600,
                "sharpness": 0.6,
            }
        )
    return assets


class _SleepyEncoder:
    """Mimics ClipEncoder but blocks longer than the configured timeout."""

    model_name = "ViT-B-32"

    def __init__(self, *, sleep_sec: float) -> None:
        self._sleep_sec = sleep_sec
        self.called = False

    def embed_assets(self, assets, *, trip_dir=None, deterministic=True):  # noqa: D401, ANN001
        self.called = True
        time.sleep(self._sleep_sec)
        raise AssertionError("Sleepy encoder should have been cut off by timeout")


def test_scene_clustering_timeout_returns_before_clip_finishes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assets = _gps_assets(20)
    trip = {"assets": [dict(a) for a in assets], "curation": {}, "chapters": []}

    # Shrink the timeout floor so the test stays under ~3s while still
    # exercising the real ThreadPoolExecutor + future.result(timeout=...) path.
    monkeypatch.setattr(clustering_mod, "_MIN_SCENE_TIMEOUT_SEC", 1)

    cfg = AppConfig(
        clustering=ClusteringConfig(
            enabled="true",
            scene=SceneClusterConfig(timeout_sec=1),
        ),
        vision=VisionConfig(enabled="true"),
    )

    monkeypatch.setattr(clustering_mod, "vision_stack_available", lambda: True)
    monkeypatch.setattr(
        clustering_mod, "clip_torch_available", lambda **_: False
    )
    monkeypatch.setattr(
        clustering_mod, "embedding_cache_is_corrupt", lambda _trip_dir: False
    )
    sleepy = _SleepyEncoder(sleep_sec=30)
    monkeypatch.setattr(clustering_mod, "ClipEncoder", lambda **_: sleepy)

    started = time.perf_counter()
    result = ClusteringLayer().run(trip, trip_dir=tmp_path, cfg=cfg)
    elapsed = time.perf_counter() - started

    assert sleepy.called, "expected sleepy encoder to have been submitted to pool"
    assert elapsed < 4.0, (
        f"layer blocked on sleepy encoder for {elapsed:.1f}s; "
        "shutdown(wait=False) is not honored"
    )
    assert result.scene_cluster_count == 0
    assert result.mode in {"lite", "off"}
