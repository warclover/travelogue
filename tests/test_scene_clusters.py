"""Scene cluster DBSCAN tests (Phase 3 M13)."""

from __future__ import annotations

import numpy as np
import pytest

from travelogue.curation.scene_clusters import NOISE_CLUSTER_ID, assign_scene_cluster_fields, compute_scene_clusters


def test_compute_scene_clusters_groups_similar_vectors() -> None:
    ids = [f"a{i}" for i in range(12)]
    base_a = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    base_b = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    vectors = np.vstack([np.tile(base_a, (6, 1)), np.tile(base_b, (6, 1))])
    clusters = compute_scene_clusters(ids, vectors, eps=0.25, min_samples=3)
    assert len(clusters) == 2
    assert sum(len(c.asset_ids) for c in clusters) == 12


def test_assign_scene_cluster_fields_writes_trip() -> None:
    ids = ["x1", "x2", "x3", "x4"]
    vectors = np.array(
        [[1, 0, 0], [1, 0, 0], [0, 1, 0], [0, 1, 0]],
        dtype=np.float32,
    )
    clusters = compute_scene_clusters(ids, vectors, eps=0.2, min_samples=2)
    trip = {"assets": [{"id": i} for i in ids], "curation": {}}
    assign_scene_cluster_fields(trip, ids, vectors, clusters, cluster_source="heuristic")
    assert trip["curation"]["clustering"]["clusters"]
    assert trip["assets"][0].get("sceneClusterId") is not None
    assert trip["assets"][0].get("clusterSource") == "heuristic"


def test_noise_cluster_id_for_outliers() -> None:
    ids = ["o1"]
    vectors = np.array([[0.5, 0.5, 0.5]], dtype=np.float32)
    clusters = compute_scene_clusters(ids, vectors, eps=0.01, min_samples=5)
    assert clusters == []
    trip = {"assets": [{"id": "o1"}], "curation": {}}
    assign_scene_cluster_fields(trip, ids, vectors, clusters, cluster_source="heuristic")
    assert trip["assets"][0]["sceneClusterId"] == NOISE_CLUSTER_ID


@pytest.mark.vision
def test_clip_encoder_heuristic_without_torch() -> None:
    from travelogue.vision.clip_encoder import ClipEncoder

    assets = [{"id": "a1", "type": "image", "width": 1200, "height": 800, "sharpness": 0.7}]
    enc = ClipEncoder()
    result = enc.embed_assets(assets)
    assert result.source in ("heuristic", "clip")
    assert result.vectors.shape[0] == 1
