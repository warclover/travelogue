"""Trip-level CLIP embedding cache (Phase 3 · F-CLU-CACHE-* · P7 ABI + transactional writes)."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

_log = logging.getLogger(__name__)

CACHE_DIR_NAME = ".cluster-cache"
EMBEDDINGS_FILE = "embeddings.npz"
EMBEDDINGS_TMP = "embeddings.tmp.npz"
MANIFEST_FILE = "manifest.json"
MANIFEST_TMP = "manifest.tmp.json"

INCREMENTAL_MAX_CHANGE_RATIO = 0.10
FULL_RECLUSTER_MIN_RATIO = 0.30

CacheMode = Literal["full", "incremental", "prune", "reuse"]

_cache_write_lock = threading.Lock()
_trip_cache_locks: dict[str, threading.Lock] = {}
_trip_cache_locks_guard = threading.Lock()


def _cache_write_lock_for(trip_dir: Path) -> threading.Lock:
    """Per-trip write lock; falls back to global lock if path is unusable."""
    try:
        key = str(trip_dir.resolve())
    except OSError:
        return _cache_write_lock
    with _trip_cache_locks_guard:
        lock = _trip_cache_locks.get(key)
        if lock is None:
            lock = threading.Lock()
            _trip_cache_locks[key] = lock
        return lock


@dataclass
class EmbeddingCachePlan:
    mode: CacheMode
    current_ids: list[str]
    new_ids: list[str]
    removed_ids: list[str]
    change_ratio: float

    def cache_hit_ratio(self) -> float:
        total = len(self.current_ids)
        if total == 0:
            return 0.0
        if self.mode == "reuse":
            return 1.0
        if self.mode == "full":
            return 0.0
        return max(0.0, min(1.0, (total - len(self.new_ids)) / total))


def cache_dir_for_trip(trip_dir: Path) -> Path:
    return trip_dir / CACHE_DIR_NAME


def cache_path_for_trip(trip_dir: Path) -> Path:
    return cache_dir_for_trip(trip_dir) / EMBEDDINGS_FILE


def manifest_path_for_trip(trip_dir: Path) -> Path:
    return cache_dir_for_trip(trip_dir) / MANIFEST_FILE


def compute_cache_config_fingerprint(cfg: Any) -> str:
    """P7-G3 · stable fingerprint for cache invalidation."""
    vis = cfg.vision
    clu = cfg.clustering
    scene = clu.scene
    from travelogue.vision.clip_encoder import HEURISTIC_MODEL_V2

    payload = {
        "abi": clu.cache_abi_version,
        "model": vis.model,
        "pretrained": getattr(vis, "pretrained", "openai"),
        "batch_size": vis.batch_size,
        "prefer_web": vis.prefer_web_derivative,
        "web_cosine_max": getattr(vis, "web_derivative_cosine_max", 0.02),
        "scene_algorithm": scene.algorithm,
        "scene_eps": scene.cluster_eps,
        "scene_min_samples": scene.cluster_min_samples,
        "heuristic_model": HEURISTIC_MODEL_V2,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return digest[:16]


def resolve_cache_fingerprint(cfg: Any) -> str:
    fp = str(cfg.clustering.cache_config_fingerprint or "auto")
    if fp == "auto":
        return compute_cache_config_fingerprint(cfg)
    return fp


def embedding_cache_vector_stale(
    cached: dict[str, Any] | None,
    manifest: dict[str, Any] | None,
) -> bool:
    """True when cached heuristic vectors use pre-v2 schema (dim / model mismatch)."""
    if cached is None:
        return False
    vectors = cached.get("vectors")
    if vectors is None:
        return False
    try:
        dim = int(vectors.shape[1]) if getattr(vectors, "ndim", 0) == 2 else len(vectors[0])
    except (IndexError, TypeError, AttributeError):
        return True
    source = str(cached.get("source") or (manifest or {}).get("source") or "")
    model = str(cached.get("model") or (manifest or {}).get("model") or "")
    if source != "heuristic":
        return False
    from travelogue.vision.clip_encoder import HEURISTIC_MODEL_V2, HEURISTIC_V2_DIM

    if model and model != HEURISTIC_MODEL_V2:
        return True
    return dim != HEURISTIC_V2_DIM


def cache_abi_matches(manifest: dict[str, Any] | None, cfg: Any) -> bool:
    """Return False when manifest ABI/fingerprint drift requires rebuild (P7-G3)."""
    if manifest is None:
        return False
    expected_abi = str(cfg.clustering.cache_abi_version or "v1")
    manifest_abi = str(manifest.get("algoVersion") or manifest.get("cacheAbiVersion") or "")
    if manifest_abi and manifest_abi != expected_abi:
        return False
    expected_fp = resolve_cache_fingerprint(cfg)
    manifest_fp = str(manifest.get("configFingerprint") or "")
    if manifest_fp and manifest_fp != expected_fp:
        return False
    return True


def embedding_cache_is_corrupt(trip_dir: Path) -> bool:
    cache_path = cache_path_for_trip(trip_dir)
    manifest_path = manifest_path_for_trip(trip_dir)
    if cache_path.is_file() and load_embedding_cache(trip_dir) is None:
        return True
    if manifest_path.is_file() and load_cache_manifest(trip_dir) is None:
        return True
    return False


def image_asset_ids(assets: list[dict]) -> list[str]:
    return [
        str(a["id"])
        for a in assets
        if a.get("id") and a.get("type", "image") != "video"
    ]


def load_cache_manifest(trip_dir: Path) -> dict[str, Any] | None:
    path = manifest_path_for_trip(trip_dir)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else None
    except (OSError, json.JSONDecodeError) as exc:
        _log.warning("invalid cluster cache manifest %s: %s", path, exc)
        return None


def save_cache_manifest(
    trip_dir: Path,
    *,
    asset_ids: list[str],
    source: str,
    model: str | None,
    cfg: Any | None = None,
    version: int | None = None,
    recommended_batch_size: int | None = None,
) -> Path:
    out_dir = cache_dir_for_trip(trip_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    prev = load_cache_manifest(trip_dir) or {}
    next_version = (int(prev.get("version") or 0) + 1) if version is None else version
    payload: dict[str, Any] = {
        "version": next_version,
        "assetIds": asset_ids,
        "assetCount": len(asset_ids),
        "source": source,
        "model": model or "",
        "updatedAt": datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
    }
    if cfg is not None:
        payload["algoVersion"] = str(cfg.clustering.cache_abi_version or "v1")
        payload["configFingerprint"] = resolve_cache_fingerprint(cfg)
    if recommended_batch_size is not None:
        payload["recommendedBatchSize"] = int(recommended_batch_size)
    elif prev.get("recommendedBatchSize") is not None:
        payload["recommendedBatchSize"] = prev["recommendedBatchSize"]
    tmp_path = out_dir / MANIFEST_TMP
    final_path = out_dir / MANIFEST_FILE
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_path, final_path)
    return final_path


def _load_npz_embedding_cache(path: Path) -> dict[str, Any] | None:
    import numpy as np

    try:
        data = np.load(path, allow_pickle=False)
    except ValueError:
        data = np.load(path, allow_pickle=True)
    if "asset_ids" not in data or "vectors" not in data:
        return None
    raw_ids = data["asset_ids"]
    if raw_ids.dtype == object:
        ids = [str(x) for x in raw_ids.tolist()]
    else:
        ids = [str(x) for x in raw_ids.tolist()]
    vectors = data["vectors"]
    source = str(data.get("source") or "clip")
    model = str(data.get("model") or "")
    return {"asset_ids": ids, "vectors": vectors, "source": source, "model": model}


def load_embedding_cache(trip_dir: Path) -> dict[str, Any] | None:
    path = cache_path_for_trip(trip_dir)
    if not path.is_file():
        return None
    try:
        return _load_npz_embedding_cache(path)
    except Exception as exc:
        _log.warning("corrupt cluster cache %s: %s", path, exc)
        return None


def save_embedding_cache(
    trip_dir: Path,
    *,
    asset_ids: list[str],
    vectors: Any,
    source: str,
    model: str | None = None,
    cfg: Any | None = None,
    recommended_batch_size: int | None = None,
) -> Path:
    """P7-G4 · tmp + atomic rename under write lock."""
    from travelogue.vision.embed_cancel import embedding_cancelled

    if embedding_cancelled(trip_dir):
        _log.info("skip embedding cache write: trip embed cancelled")
        return cache_path_for_trip(trip_dir)
    import numpy as np

    with _cache_write_lock_for(trip_dir):
        out_dir = cache_dir_for_trip(trip_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = out_dir / EMBEDDINGS_TMP
        final_path = out_dir / EMBEDDINGS_FILE
        np.savez_compressed(
            tmp_path,
            asset_ids=np.asarray(asset_ids, dtype=str),
            vectors=vectors,
            source=np.array(source),
            model=np.array(model or ""),
        )
        os.replace(tmp_path, final_path)
        save_cache_manifest(
            trip_dir,
            asset_ids=asset_ids,
            source=source,
            model=model,
            cfg=cfg,
            recommended_batch_size=recommended_batch_size,
        )
        return final_path


def invalidate_embedding_cache(trip_dir: Path) -> None:
    clear_cluster_cache(trip_dir)


def clear_cluster_cache(trip_dir: Path) -> bool:
    cache_root = cache_dir_for_trip(trip_dir)
    if not cache_root.is_dir():
        return False
    import shutil

    with _cache_write_lock_for(trip_dir):
        shutil.rmtree(cache_root)
    try:
        key = str(trip_dir.resolve())
        with _trip_cache_locks_guard:
            _trip_cache_locks.pop(key, None)
    except OSError:
        pass
    return True


def list_pending_assets(trip: dict) -> list[str]:
    pending = (trip.get("pipeline") or {}).get("pendingAssets") or []
    if not isinstance(pending, list):
        return []
    return [str(x) for x in pending if x]


from travelogue.domain.pipeline import PIPELINE_LOCKED_STATUSES


def is_pipeline_locked(trip: dict) -> bool:
    pipe = trip.get("pipeline") or {}
    status = str(pipe.get("status") or "")
    if status in PIPELINE_LOCKED_STATUSES:
        return True
    locks = pipe.get("locks") or {}
    return bool(locks.get("structure"))


def append_pending_assets(trip: dict, asset_ids: list[str]) -> list[str]:
    pipe = trip.setdefault("pipeline", {})
    existing = pipe.get("pendingAssets")
    if not isinstance(existing, list):
        existing = []
    merged: list[str] = []
    seen: set[str] = set()
    for aid in (*existing, *asset_ids):
        s = str(aid).strip()
        if s and s not in seen:
            seen.add(s)
            merged.append(s)
    pipe["pendingAssets"] = merged
    return merged


def clear_pending_assets(trip: dict) -> list[str]:
    pipe = trip.setdefault("pipeline", {})
    previous = pipe.get("pendingAssets") or []
    pipe["pendingAssets"] = []
    return [str(x) for x in previous if x]


def compute_change_ratio(current_ids: list[str], cached_ids: list[str]) -> tuple[float, list[str], list[str]]:
    current_set = set(current_ids)
    cached_set = set(cached_ids)
    new_ids = [aid for aid in current_ids if aid not in cached_set]
    removed_ids = [aid for aid in cached_ids if aid not in current_set]
    delta = len(new_ids) + len(removed_ids)
    base = max(len(current_ids), len(cached_ids), 1)
    return delta / base, new_ids, removed_ids


def plan_embedding_refresh(
    trip_dir: Path,
    current_ids: list[str],
    *,
    force_recluster: bool = False,
    cfg: Any | None = None,
) -> EmbeddingCachePlan:
    if force_recluster:
        return EmbeddingCachePlan(
            mode="full",
            current_ids=current_ids,
            new_ids=list(current_ids),
            removed_ids=[],
            change_ratio=1.0,
        )

    cached = load_embedding_cache(trip_dir)
    manifest = load_cache_manifest(trip_dir)
    if cached is None or manifest is None:
        return EmbeddingCachePlan(
            mode="full",
            current_ids=current_ids,
            new_ids=list(current_ids),
            removed_ids=[],
            change_ratio=1.0 if current_ids else 0.0,
        )

    if cfg is not None and not cache_abi_matches(manifest, cfg):
        _log.info("cluster cache ABI mismatch; forcing full refresh")
        return EmbeddingCachePlan(
            mode="full",
            current_ids=current_ids,
            new_ids=list(current_ids),
            removed_ids=[],
            change_ratio=1.0,
        )

    if embedding_cache_vector_stale(cached, manifest):
        _log.info("heuristic embedding schema drift; forcing full refresh")
        return EmbeddingCachePlan(
            mode="full",
            current_ids=current_ids,
            new_ids=list(current_ids),
            removed_ids=[],
            change_ratio=1.0,
        )

    cached_ids = cached["asset_ids"]
    change_ratio, new_ids, removed_ids = compute_change_ratio(current_ids, cached_ids)

    if int(manifest.get("assetCount") or -1) != len(cached_ids):
        return EmbeddingCachePlan("full", current_ids, list(current_ids), removed_ids, 1.0)

    if change_ratio == 0.0:
        return EmbeddingCachePlan("reuse", current_ids, [], [], 0.0)

    if not new_ids and removed_ids:
        return EmbeddingCachePlan("prune", current_ids, [], removed_ids, change_ratio)

    if change_ratio >= FULL_RECLUSTER_MIN_RATIO:
        return EmbeddingCachePlan("full", current_ids, list(current_ids), removed_ids, change_ratio)

    new_only_ratio = len(new_ids) / max(len(current_ids), 1)
    if (
        change_ratio < INCREMENTAL_MAX_CHANGE_RATIO
        and new_only_ratio < INCREMENTAL_MAX_CHANGE_RATIO
    ):
        return EmbeddingCachePlan("incremental", current_ids, new_ids, removed_ids, change_ratio)

    return EmbeddingCachePlan("full", current_ids, list(current_ids), removed_ids, change_ratio)


def merge_embedding_vectors(
    cached: dict[str, Any],
    current_ids: list[str],
    new_ids: list[str],
    new_vectors: Any,
) -> Any:
    import numpy as np

    id_to_row = {aid: idx for idx, aid in enumerate(cached["asset_ids"])}
    new_map = {aid: idx for idx, aid in enumerate(new_ids)}
    rows: list[Any] = []
    for aid in current_ids:
        if aid in id_to_row:
            rows.append(cached["vectors"][id_to_row[aid]])
        elif aid in new_map:
            rows.append(new_vectors[new_map[aid]])
        else:
            raise KeyError(f"missing embedding for asset {aid}")
    return np.vstack(rows)


def prepare_scene_embeddings(
    trip_dir: Path,
    assets: list[dict],
    encoder: Any,
    *,
    force_recluster: bool = False,
    deterministic: bool = True,
    cfg: Any | None = None,
    apply_subject_class: bool = True,
) -> tuple[Any, EmbeddingCachePlan]:
    from travelogue.vision.clip_encoder import EmbedResult
    from travelogue.vision.embed_cancel import embedding_cancelled

    current_ids = image_asset_ids(assets)
    plan = plan_embedding_refresh(
        trip_dir, current_ids, force_recluster=force_recluster, cfg=cfg
    )

    def _save(embed: EmbedResult) -> None:
        if embedding_cancelled(trip_dir):
            return
        if embed.asset_ids:
            rec_batch = None
            if getattr(encoder, "last_embed_stats", None) is not None:
                stats = encoder.last_embed_stats
                rec_batch = stats.recommended_batch_size or stats.batch_size
            elif getattr(encoder, "_tuned_batch_size", None) is not None:
                rec_batch = encoder._tuned_batch_size
            save_embedding_cache(
                trip_dir,
                asset_ids=embed.asset_ids,
                vectors=embed.vectors,
                source=embed.source,
                model=embed.model,
                cfg=cfg,
                recommended_batch_size=rec_batch,
            )
            if rec_batch and cfg is not None:
                from travelogue.vision.clip_encoder import persist_recommended_batch_size

                persist_recommended_batch_size(
                    int(rec_batch),
                    trips_dir=cfg.trips_dir,
                    trip_dir=trip_dir,
                )

    if plan.mode == "full":
        clear_cluster_cache(trip_dir)
        embed = encoder.embed_assets(
            assets, trip_dir=trip_dir, deterministic=deterministic, apply_subject_class=apply_subject_class
        )
        _save(embed)
        return embed, plan

    if plan.mode == "reuse":
        cached = load_embedding_cache(trip_dir)
        if cached is None:
            embed = encoder.embed_assets(
                assets,
                trip_dir=trip_dir,
                deterministic=deterministic,
                apply_subject_class=apply_subject_class,
            )
            _save(embed)
            return embed, plan
        import numpy as np

        id_to_row = {aid: idx for idx, aid in enumerate(cached["asset_ids"])}
        order = [id_to_row[aid] for aid in current_ids]
        vectors = cached["vectors"][order]
        embed = EmbedResult(
            current_ids,
            vectors,
            str(cached.get("source") or "heuristic"),
            str(cached.get("model") or "") or None,
        )
        return embed, plan

    if plan.mode == "prune":
        cached = load_embedding_cache(trip_dir)
        if cached is None:
            embed = encoder.embed_assets(
                assets,
                trip_dir=trip_dir,
                deterministic=deterministic,
                apply_subject_class=apply_subject_class,
            )
            _save(embed)
            return embed, plan
        import numpy as np

        id_to_row = {aid: idx for idx, aid in enumerate(cached["asset_ids"])}
        rows = [cached["vectors"][id_to_row[aid]] for aid in current_ids if aid in id_to_row]
        if len(rows) != len(current_ids):
            _log.warning("prune missing rows; falling back to full refresh")
            clear_cluster_cache(trip_dir)
            embed = encoder.embed_assets(
                assets,
                trip_dir=trip_dir,
                deterministic=deterministic,
                apply_subject_class=apply_subject_class,
            )
            _save(embed)
            full_plan = EmbeddingCachePlan("full", current_ids, list(current_ids), plan.removed_ids, 1.0)
            return embed, full_plan
        vectors = np.vstack(rows)
        source = str(cached.get("source") or "heuristic")
        model = str(cached.get("model") or "") or None
        save_embedding_cache(
            trip_dir,
            asset_ids=current_ids,
            vectors=vectors,
            source=source,
            model=model,
            cfg=cfg,
        )
        embed = EmbedResult(current_ids, vectors, source, model)
        return embed, plan

    cached = load_embedding_cache(trip_dir)
    if cached is None:
        embed = encoder.embed_assets(
            assets, trip_dir=trip_dir, deterministic=deterministic, apply_subject_class=apply_subject_class
        )
        _save(embed)
        return embed, plan

    new_assets = [a for a in assets if str(a.get("id")) in set(plan.new_ids)]
    new_embed = encoder.embed_assets(
        new_assets,
        trip_dir=trip_dir,
        deterministic=deterministic,
        apply_subject_class=apply_subject_class,
    )
    if len(new_embed.asset_ids) != len(plan.new_ids):
        _log.warning("incremental embed count mismatch; falling back to full refresh")
        clear_cluster_cache(trip_dir)
        embed = encoder.embed_assets(
            assets, trip_dir=trip_dir, deterministic=deterministic, apply_subject_class=apply_subject_class
        )
        _save(embed)
        full_plan = EmbeddingCachePlan("full", current_ids, list(current_ids), plan.removed_ids, 1.0)
        return embed, full_plan

    if embedding_cache_vector_stale(cached, load_cache_manifest(trip_dir)):
        _log.warning("incremental merge blocked by vector schema drift; full refresh")
        clear_cluster_cache(trip_dir)
        embed = encoder.embed_assets(
            assets, trip_dir=trip_dir, deterministic=deterministic, apply_subject_class=apply_subject_class
        )
        _save(embed)
        full_plan = EmbeddingCachePlan("full", current_ids, list(current_ids), plan.removed_ids, 1.0)
        return embed, full_plan

    try:
        merged = merge_embedding_vectors(cached, current_ids, new_embed.asset_ids, new_embed.vectors)
    except ValueError:
        _log.warning("incremental vector dim mismatch; full refresh")
        clear_cluster_cache(trip_dir)
        embed = encoder.embed_assets(
            assets, trip_dir=trip_dir, deterministic=deterministic, apply_subject_class=apply_subject_class
        )
        _save(embed)
        full_plan = EmbeddingCachePlan("full", current_ids, list(current_ids), plan.removed_ids, 1.0)
        return embed, full_plan
    source = new_embed.source if plan.new_ids else str(cached.get("source") or "heuristic")
    model = new_embed.model or str(cached.get("model") or "") or None
    save_embedding_cache(
        trip_dir,
        asset_ids=current_ids,
        vectors=merged,
        source=source,
        model=model,
        cfg=cfg,
    )
    embed = EmbedResult(current_ids, merged, source, model)
    return embed, plan
