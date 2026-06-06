"""Scene cluster assignment via embedding clustering (Phase 3 M13 · Phase 6 HDBSCAN)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

_log = logging.getLogger(__name__)

NOISE_CLUSTER_ID = -1
ClusterAlgorithm = Literal["hdbscan", "dbscan"]


@dataclass
class SceneCluster:
    id: int
    label: str
    asset_ids: list[str]
    medoid_asset_id: str | None
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": self.id,
            "label": self.label,
            "assetIds": list(self.asset_ids),
        }
        if self.medoid_asset_id:
            out["medoidAssetId"] = self.medoid_asset_id
        if self.confidence is not None:
            out["confidence"] = round(self.confidence, 4)
        return out


def _pick_medoid(asset_ids: list[str], vectors_by_id: dict[str, Any]) -> str | None:
    if not asset_ids:
        return None
    import numpy as np

    vecs = []
    kept: list[str] = []
    for aid in asset_ids:
        v = vectors_by_id.get(aid)
        if v is None:
            continue
        vecs.append(np.asarray(v, dtype=np.float32))
        kept.append(aid)
    if not kept:
        return asset_ids[0]
    mat = np.stack(vecs)
    centroid = mat.mean(axis=0)
    dists = np.linalg.norm(mat - centroid, axis=1)
    return kept[int(dists.argmin())]


def _normalize_embedding_matrix(mat: Any) -> Any:
    import numpy as np

    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms = np.where(norms < 1e-8, 1.0, norms)
    return mat / norms


def _cluster_labels(
    mat: Any,
    *,
    algorithm: ClusterAlgorithm,
    eps: float,
    min_samples_eff: int,
) -> tuple[Any, Any | None, ClusterAlgorithm]:
    """Return (labels, probabilities_, effective_algorithm)."""
    if algorithm == "hdbscan":
        try:
            from sklearn.cluster import HDBSCAN

            clusterer = HDBSCAN(
                min_cluster_size=min_samples_eff,
                min_samples=max(2, min_samples_eff // 2),
                metric="cosine",
                cluster_selection_method="eom",
                copy=True,
            )
            labels = clusterer.fit_predict(mat)
            probs = getattr(clusterer, "probabilities_", None)
            return labels, probs, "hdbscan"
        except Exception as exc:
            _log.warning("HDBSCAN failed, falling back to DBSCAN: %s", exc)

    try:
        from sklearn.cluster import DBSCAN

        db = DBSCAN(eps=eps, min_samples=min_samples_eff, metric="cosine")
        labels = db.fit_predict(mat)
        return labels, None, "dbscan"
    except Exception as exc:
        _log.warning("DBSCAN failed, assigning noise labels: %s", exc)
        import numpy as np

        return np.full(mat.shape[0], -1, dtype=int), None, "dbscan"


@dataclass
class SceneClusterResult:
    clusters: list[SceneCluster]
    probabilities_by_id: dict[str, float]
    algorithm_used: ClusterAlgorithm = "dbscan"


def compute_scene_clusters(
    asset_ids: list[str],
    embeddings: Any,
    *,
    eps: float = 0.07,
    min_samples: int = 10,
    algorithm: ClusterAlgorithm = "hdbscan",
    deterministic: bool = True,  # reserved; stable output via re-numbering below
) -> SceneClusterResult:
    """Cluster L2-normalized embeddings; default HDBSCAN (Phase 6).

    Raw cluster labels reflect discovery order and can shift between runs.
    We re-number clusters deterministically (member count desc, then first asset_id).
    The ``deterministic`` flag is accepted for API compatibility with clustering cfg.
    """
    _ = deterministic
    import numpy as np

    if len(asset_ids) == 0:
        return SceneClusterResult(clusters=[], probabilities_by_id={}, algorithm_used=algorithm)
    mat = np.asarray(embeddings, dtype=np.float32)
    if mat.shape[0] != len(asset_ids):
        raise ValueError("embeddings row count must match asset_ids")

    mat = _normalize_embedding_matrix(mat)
    min_samples_eff = min(min_samples, max(2, len(asset_ids) // 5))
    labels, probabilities, algorithm_used = _cluster_labels(
        mat,
        algorithm=algorithm,
        eps=eps,
        min_samples_eff=min_samples_eff,
    )

    vectors_by_id = {aid: mat[i] for i, aid in enumerate(asset_ids)}
    prob_by_id: dict[str, float] = {}
    if probabilities is not None:
        for i, aid in enumerate(asset_ids):
            prob_by_id[aid] = float(probabilities[i])

    raw_groups: dict[int, list[str]] = {}
    for i, lab in enumerate(labels):
        cid = int(lab)
        if cid == NOISE_CLUSTER_ID:
            continue
        raw_groups.setdefault(cid, []).append(asset_ids[i])
    raw_groups = {k: v for k, v in raw_groups.items() if v}

    ordered = sorted(
        raw_groups.items(),
        key=lambda kv: (-len(kv[1]), kv[1][0]),
    )

    clusters: list[SceneCluster] = []
    for new_id, (_raw_id, members) in enumerate(ordered):
        medoid = _pick_medoid(members, vectors_by_id)
        member_probs = [prob_by_id[aid] for aid in members if aid in prob_by_id]
        avg_conf = float(np.mean(member_probs)) if member_probs else None
        clusters.append(
            SceneCluster(
                id=new_id,
                label=f"场景{new_id + 1}",
                asset_ids=members,
                medoid_asset_id=medoid,
                confidence=avg_conf,
            )
        )
    return SceneClusterResult(
        clusters=clusters,
        probabilities_by_id=prob_by_id,
        algorithm_used=algorithm_used,
    )


def cluster_noise_ratio(asset_ids: list[str], labels: Any) -> float:
    """Fraction of assets labeled as noise (-1)."""
    if not asset_ids:
        return 0.0
    import numpy as np

    labs = np.asarray(labels)
    if labs.shape[0] != len(asset_ids):
        raise ValueError("labels length must match asset_ids")
    noise = int((labs == NOISE_CLUSTER_ID).sum())
    return noise / len(asset_ids)


def assign_scene_cluster_fields(
    trip: dict,
    asset_ids: list[str],
    embeddings: Any,
    clusters: list[SceneCluster],
    *,
    cluster_source: str,
    model: str | None = None,
    algorithm: ClusterAlgorithm | None = None,
    probabilities_by_id: dict[str, float] | None = None,
) -> None:
    """Write asset.sceneClusterId, confidence, and curation.clustering.clusters."""
    by_id = {a["id"]: a for a in trip.get("assets") or []}
    id_to_label: dict[str, int] = {}
    for cluster in clusters:
        for aid in cluster.asset_ids:
            id_to_label[aid] = cluster.id

    prob_map = probabilities_by_id or {}

    for aid in asset_ids:
        asset = by_id.get(aid)
        if asset is None:
            continue
        asset["clusterSource"] = cluster_source
        asset["sceneClusterId"] = id_to_label.get(aid, NOISE_CLUSTER_ID)
        if aid in prob_map:
            asset["sceneClusterConfidence"] = round(prob_map[aid], 4)

    curation = trip.setdefault("curation", {})
    clustering = curation.setdefault("clustering", {})
    clustering["clusters"] = [c.to_dict() for c in clusters]
    if algorithm:
        clustering["sceneAlgorithm"] = algorithm
    clustering["vision"] = {
        "source": cluster_source,
        "model": model or clustering.get("visionModel") or "",
    }
    if cluster_source == "clip":
        clustering["visionModel"] = clustering.get("visionModel") or "ViT-B-32"
