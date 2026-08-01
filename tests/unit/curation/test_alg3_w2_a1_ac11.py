"""ALG-V3 W2-A1 · cluster_selection_epsilon honesty + AC-11 fingerprint / noise gate."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from travelogue.config import AppConfig, ClusteringConfig, SceneClusterConfig
from travelogue.curation.scene_clusters import (
    NOISE_CLUSTER_ID,
    cluster_noise_ratio,
    compute_scene_clusters,
)
from travelogue.vision.cache import compute_cache_config_fingerprint

_BASELINE = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "acceptance-records"
    / "alg3-ac11-noise-baseline.json"
)


def _synthetic_corpus(
    *,
    seed: int,
    centers: int,
    per_center: int,
    outliers: int,
    dim: int,
) -> tuple[list[str], np.ndarray]:
    rng = np.random.default_rng(seed)
    base = np.eye(centers, dtype=np.float32)
    vecs: list[np.ndarray] = []
    for c in range(centers):
        for _ in range(per_center):
            v = np.zeros(dim, dtype=np.float32)
            v[:centers] = base[c]
            v += rng.normal(0, 0.02, size=dim).astype(np.float32)
            vecs.append(v)
    for _ in range(outliers):
        vecs.append(rng.normal(0, 1, size=dim).astype(np.float32))
    mat = np.stack(vecs).astype(np.float32)
    ids = [f"a{i:02d}" for i in range(mat.shape[0])]
    return ids, mat


def _labels_for_result(asset_ids: list[str], result) -> list[int]:
    aid_to_c: dict[str, int] = {}
    for cl in result.clusters:
        for aid in cl.asset_ids:
            aid_to_c[aid] = cl.id
    return [aid_to_c.get(aid, NOISE_CLUSTER_ID) for aid in asset_ids]


def test_a1_selection_epsilon_parses_and_defaults() -> None:
    assert SceneClusterConfig().cluster_selection_epsilon == 0.0
    from travelogue.config.clustering import scene_cluster_from_dict

    cfg = scene_cluster_from_dict({"clusterSelectionEpsilon": 0.15})
    assert cfg.cluster_selection_epsilon == pytest.approx(0.15)


def test_ac11_fingerprint_tracks_hdbscan_consumed_knobs() -> None:
    base = AppConfig()
    assert base.clustering.scene.algorithm == "hdbscan"
    fp0 = compute_cache_config_fingerprint(base)

    # Dead knob under HDBSCAN: must NOT invalidate cache (A1 · no silent remap).
    dead = replace(
        base,
        clustering=replace(
            base.clustering,
            scene=replace(base.clustering.scene, cluster_eps=0.99),
        ),
    )
    assert compute_cache_config_fingerprint(dead) == fp0

    # Consumed HDBSCAN knob: fingerprint MUST change.
    live = replace(
        base,
        clustering=replace(
            base.clustering,
            scene=replace(base.clustering.scene, cluster_selection_epsilon=0.12),
        ),
    )
    assert compute_cache_config_fingerprint(live) != fp0

    # min_samples still consumed → fingerprint change.
    ms = replace(
        base,
        clustering=replace(
            base.clustering,
            scene=replace(base.clustering.scene, cluster_min_samples=3),
        ),
    )
    assert compute_cache_config_fingerprint(ms) != fp0


def test_ac11_fingerprint_tracks_dbscan_eps() -> None:
    base = AppConfig(
        clustering=ClusteringConfig(
            scene=SceneClusterConfig(algorithm="dbscan", cluster_eps=0.07)
        )
    )
    fp0 = compute_cache_config_fingerprint(base)
    # selection_epsilon unused on DBSCAN path → no fingerprint change.
    unused = replace(
        base,
        clustering=replace(
            base.clustering,
            scene=replace(base.clustering.scene, cluster_selection_epsilon=0.5),
        ),
    )
    assert compute_cache_config_fingerprint(unused) == fp0

    eps = replace(
        base,
        clustering=replace(
            base.clustering,
            scene=replace(base.clustering.scene, cluster_eps=0.2),
        ),
    )
    assert compute_cache_config_fingerprint(eps) != fp0


def test_ac11_fixture_noise_within_baseline() -> None:
    data = json.loads(_BASELINE.read_text(encoding="utf-8"))
    fx = data["fixture"]
    ids, mat = _synthetic_corpus(
        seed=int(fx["seed"]),
        centers=int(fx["centers"]),
        per_center=int(fx["per_center"]),
        outliers=int(fx["outliers"]),
        dim=int(fx["dim"]),
    )
    result = compute_scene_clusters(
        ids,
        mat,
        min_samples=int(fx["min_samples"]),
        algorithm=fx["algorithm"],
        cluster_selection_epsilon=float(fx["cluster_selection_epsilon"]),
    )
    assert result.algorithm_used == "hdbscan"
    labels = _labels_for_result(ids, result)
    ratio = cluster_noise_ratio(ids, labels)
    ceiling = float(data["baseline_noise_ratio"]) + float(data["tolerance"])
    assert ratio <= ceiling + 1e-9, (ratio, ceiling, data["baseline_noise_ratio"])
