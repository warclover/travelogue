"""Scene cluster assignment via embedding DBSCAN (Phase 3 M13)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import logging

_log = logging.getLogger(__name__)

NOISE_CLUSTER_ID = -1


@dataclass
class SceneCluster:
    id: int
    label: str
    asset_ids: list[str]
    medoid_asset_id: str | None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": self.id,
            "label": self.label,
            "assetIds": list(self.asset_ids),
        }
        if self.medoid_asset_id:
            out["medoidAssetId"] = self.medoid_asset_id
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


def compute_scene_clusters(
    asset_ids: list[str],
    embeddings: Any,
    *,
    eps: float = 0.07,
    min_samples: int = 10,
    deterministic: bool = True,
) -> list[SceneCluster]:
    """DBSCAN on L2-normalized embedding matrix aligned to asset_ids.

    The DBSCAN raw labels reflect discovery order and can shift between runs on
    slightly different input. We therefore re-number clusters deterministically
    (by member count desc, then first asset_id) so that ``sceneClusterId`` and
    user-facing labels stay stable across reruns.
    """
    import numpy as np
    from sklearn.cluster import DBSCAN

    if len(asset_ids) == 0:
        return []
    mat = np.asarray(embeddings, dtype=np.float32)
    if mat.shape[0] != len(asset_ids):
        raise ValueError("embeddings row count must match asset_ids")

    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms = np.where(norms < 1e-8, 1.0, norms)
    mat = mat / norms

    min_samples_eff = min(min_samples, max(2, len(asset_ids) // 5))
    db = DBSCAN(eps=eps, min_samples=min_samples_eff, metric="cosine")
    labels = db.fit_predict(mat)

    vectors_by_id = {aid: mat[i] for i, aid in enumerate(asset_ids)}
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
        clusters.append(
            SceneCluster(
                id=new_id,
                label=f"场景{new_id + 1}",
                asset_ids=members,
                medoid_asset_id=medoid,
            )
        )
    return clusters


def assign_scene_cluster_fields(
    trip: dict,
    asset_ids: list[str],
    embeddings: Any,
    clusters: list[SceneCluster],
    *,
    cluster_source: str,
    model: str | None = None,
) -> None:
    """Write asset.sceneClusterId and curation.clustering.clusters."""
    by_id = {a["id"]: a for a in trip.get("assets") or []}
    id_to_label: dict[str, int] = {}
    for cluster in clusters:
        for aid in cluster.asset_ids:
            id_to_label[aid] = cluster.id

    for aid in asset_ids:
        asset = by_id.get(aid)
        if asset is None:
            continue
        asset["clusterSource"] = cluster_source
        asset["sceneClusterId"] = id_to_label.get(aid, NOISE_CLUSTER_ID)

    curation = trip.setdefault("curation", {})
    clustering = curation.setdefault("clustering", {})
    clustering["clusters"] = [c.to_dict() for c in clusters]
    clustering["vision"] = {
        "source": cluster_source,
        "model": model or clustering.get("visionModel") or "",
    }
    if cluster_source == "clip":
        clustering["visionModel"] = clustering.get("visionModel") or "ViT-B-32"
