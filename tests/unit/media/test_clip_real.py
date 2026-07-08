"""Real CLIP integration (@pytest.mark.vision · optional torch)."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.config import AppConfig, ClusteringConfig, SceneClusterConfig, VisionConfig
from travelogue.curation.clustering import run_clustering_layer
from travelogue.vision.clip_encoder import ClipEncoder, clip_torch_available


def _sample_trip_with_images(tmp_path: Path, n: int = 6) -> tuple[dict, Path]:
    from PIL import Image

    trip_dir = tmp_path / "clip-trip"
    img_dir = trip_dir / "assets" / "web"
    img_dir.mkdir(parents=True, exist_ok=True)
    assets = []
    for i in range(n):
        aid = f"p{i:02d}"
        rel = f"assets/web/{aid}.jpg"
        Image.new("RGB", (224, 224), (30 + i * 30, 60, 90)).save(trip_dir / rel, quality=90)
        assets.append(
            {
                "id": aid,
                "type": "image",
                "path": rel,
                "width": 224,
                "height": 224,
                "sharpness": 0.55,
                "geo": {"lat": 35.6 + i * 0.01, "lon": 139.7},
            }
        )
    trip = {"assets": assets, "curation": {}, "chapters": []}
    return trip, trip_dir


@pytest.mark.vision
def test_clip_embed_real_images(tmp_path: Path) -> None:
    if not clip_torch_available():
        pytest.skip("torch/open_clip not installed")
    trip, trip_dir = _sample_trip_with_images(tmp_path)
    enc = ClipEncoder()
    result = enc.embed_assets(trip["assets"], trip_dir=trip_dir, deterministic=True)
    assert result.source == "clip"
    assert result.vectors.shape[0] == len(trip["assets"])
    assert result.vectors.shape[1] >= 128


@pytest.mark.vision
def test_clustering_full_path_with_clip(tmp_path: Path) -> None:
    if not clip_torch_available():
        pytest.skip("torch/open_clip not installed")
    trip, trip_dir = _sample_trip_with_images(tmp_path, n=12)
    cfg = AppConfig(
        clustering=ClusteringConfig(
            enabled="true",
            force_recluster=True,
            scene=SceneClusterConfig(cluster_min_samples=3, cluster_eps=0.15),
        ),
        vision=VisionConfig(enabled="true"),
    )
    run_clustering_layer(trip, trip_dir=trip_dir, cfg=cfg)
    clustering = (trip.get("curation") or {}).get("clustering") or {}
    assert clustering.get("clusters") is not None
    assert any(a.get("sceneClusterId") is not None for a in trip["assets"])
