"""Trip-level CLIP embedding cache (Phase 3 · F-CLU-CACHE-*)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

_log = logging.getLogger(__name__)

CACHE_DIR_NAME = ".cluster-cache"
EMBEDDINGS_FILE = "embeddings.npz"
MANIFEST_FILE = "manifest.json"

# F-CLU-CACHE-02 / 03 thresholds (PRD §7.4)
INCREMENTAL_MAX_CHANGE_RATIO = 0.10
FULL_RECLUSTER_MIN_RATIO = 0.30

CacheMode = Literal["full", "incremental", "reuse"]


@dataclass
class EmbeddingCachePlan:
    mode: CacheMode
    current_ids: list[str]
    new_ids: list[str]
    removed_ids: list[str]
    change_ratio: float


def cache_dir_for_trip(trip_dir: Path) -> Path:
    return trip_dir / CACHE_DIR_NAME


def embedding_cache_is_corrupt(trip_dir: Path) -> bool:
    """True when cache files exist but cannot be loaded (F-CLU-CACHE-05)."""
    cache_path = cache_path_for_trip(trip_dir)
    manifest_path = manifest_path_for_trip(trip_dir)
    if cache_path.is_file() and load_embedding_cache(trip_dir) is None:
        return True
    if manifest_path.is_file() and load_cache_manifest(trip_dir) is None:
        return True
    return False


def cache_path_for_trip(trip_dir: Path) -> Path:
    return cache_dir_for_trip(trip_dir) / EMBEDDINGS_FILE


def manifest_path_for_trip(trip_dir: Path) -> Path:
    return cache_dir_for_trip(trip_dir) / MANIFEST_FILE


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
) -> Path:
    out_dir = cache_dir_for_trip(trip_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / MANIFEST_FILE
    payload = {
        "version": 1,
        "assetIds": asset_ids,
        "assetCount": len(asset_ids),
        "source": source,
        "model": model or "",
        "updatedAt": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_embedding_cache(trip_dir: Path) -> dict[str, Any] | None:
    path = cache_path_for_trip(trip_dir)
    if not path.is_file():
        return None
    try:
        import numpy as np

        data = np.load(path, allow_pickle=True)
        ids = [str(x) for x in data["asset_ids"].tolist()]
        vectors = data["vectors"]
        source = str(data.get("source") or "clip")
        model = str(data.get("model") or "")
        return {"asset_ids": ids, "vectors": vectors, "source": source, "model": model}
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
) -> Path:
    import numpy as np

    out_dir = cache_dir_for_trip(trip_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / EMBEDDINGS_FILE
    np.savez_compressed(
        path,
        asset_ids=np.array(asset_ids, dtype=object),
        vectors=vectors,
        source=np.array(source),
        model=np.array(model or ""),
    )
    save_cache_manifest(trip_dir, asset_ids=asset_ids, source=source, model=model)
    return path


def invalidate_embedding_cache(trip_dir: Path) -> None:
    clear_cluster_cache(trip_dir)


def clear_cluster_cache(trip_dir: Path) -> bool:
    """Remove entire `.cluster-cache` directory. Returns True if anything removed."""
    cache_root = cache_dir_for_trip(trip_dir)
    if not cache_root.is_dir():
        return False
    import shutil

    shutil.rmtree(cache_root)
    return True


def list_pending_assets(trip: dict) -> list[str]:
    """Assets listed in pipeline.pendingAssets (F-CLU-CACHE-04 · structure_locked append)."""
    pending = (trip.get("pipeline") or {}).get("pendingAssets") or []
    if not isinstance(pending, list):
        return []
    return [str(x) for x in pending if x]


# F-CLU-CACHE-04 · post-lock statuses where new assets must NOT auto-update chapters
PIPELINE_LOCKED_STATUSES: frozenset[str] = frozenset(
    {"structure_locked", "copy_draft", "copy_locked", "rendered", "exported"}
)


def is_pipeline_locked(trip: dict) -> bool:
    """True when ingest must defer asset ids to pendingAssets (F-CLU-CACHE-04)."""
    pipe = trip.get("pipeline") or {}
    status = str(pipe.get("status") or "")
    if status in PIPELINE_LOCKED_STATUSES:
        return True
    locks = pipe.get("locks") or {}
    return bool(locks.get("structure"))


def append_pending_assets(trip: dict, asset_ids: list[str]) -> list[str]:
    """Merge ``asset_ids`` into ``pipeline.pendingAssets`` preserving insertion order.

    Returns the updated pendingAssets list. No-op for empty input.
    """
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
    """Empty ``pipeline.pendingAssets`` and return the previous list."""
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
) -> EmbeddingCachePlan:
    """F-CLU-CACHE-01～03 · decide full vs incremental vs reuse."""
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

    cached_ids = cached["asset_ids"]
    change_ratio, new_ids, removed_ids = compute_change_ratio(current_ids, cached_ids)

    # F-CLU-CACHE-01 · manifest asset count drift
    if int(manifest.get("assetCount") or -1) != len(cached_ids):
        return EmbeddingCachePlan("full", current_ids, list(current_ids), removed_ids, 1.0)

    if change_ratio == 0.0:
        return EmbeddingCachePlan("reuse", current_ids, [], [], 0.0)

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
    """Merge cached vectors with newly embedded rows in current_ids order."""
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
) -> tuple[Any, EmbeddingCachePlan]:
    """Load / incrementally refresh embeddings per cache plan; always returns full-trip matrix."""
    from travelogue.vision.clip_encoder import EmbedResult

    current_ids = image_asset_ids(assets)
    plan = plan_embedding_refresh(trip_dir, current_ids, force_recluster=force_recluster)

    if plan.mode == "full":
        clear_cluster_cache(trip_dir)
        embed = encoder.embed_assets(assets, trip_dir=trip_dir, deterministic=deterministic)
        if embed.asset_ids:
            save_embedding_cache(
                trip_dir,
                asset_ids=embed.asset_ids,
                vectors=embed.vectors,
                source=embed.source,
                model=embed.model,
            )
        return embed, plan

    if plan.mode == "reuse":
        cached = load_embedding_cache(trip_dir)
        if cached is None:
            embed = encoder.embed_assets(assets, trip_dir=trip_dir, deterministic=deterministic)
            if embed.asset_ids:
                save_embedding_cache(
                    trip_dir,
                    asset_ids=embed.asset_ids,
                    vectors=embed.vectors,
                    source=embed.source,
                    model=embed.model,
                )
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

    # incremental · F-CLU-CACHE-02
    cached = load_embedding_cache(trip_dir)
    if cached is None:
        embed = encoder.embed_assets(assets, trip_dir=trip_dir, deterministic=deterministic)
        if embed.asset_ids:
            save_embedding_cache(
                trip_dir,
                asset_ids=embed.asset_ids,
                vectors=embed.vectors,
                source=embed.source,
                model=embed.model,
            )
        return embed, plan

    new_assets = [a for a in assets if str(a.get("id")) in set(plan.new_ids)]
    new_embed = encoder.embed_assets(new_assets, trip_dir=trip_dir, deterministic=deterministic)
    if len(new_embed.asset_ids) != len(plan.new_ids):
        _log.warning("incremental embed count mismatch; falling back to full refresh")
        clear_cluster_cache(trip_dir)
        embed = encoder.embed_assets(assets, trip_dir=trip_dir, deterministic=deterministic)
        if embed.asset_ids:
            save_embedding_cache(
                trip_dir,
                asset_ids=embed.asset_ids,
                vectors=embed.vectors,
                source=embed.source,
                model=embed.model,
            )
        full_plan = EmbeddingCachePlan("full", current_ids, list(current_ids), plan.removed_ids, 1.0)
        return embed, full_plan

    merged = merge_embedding_vectors(cached, current_ids, new_embed.asset_ids, new_embed.vectors)
    source = new_embed.source if plan.new_ids else str(cached.get("source") or "heuristic")
    model = new_embed.model or str(cached.get("model") or "") or None
    save_embedding_cache(
        trip_dir,
        asset_ids=current_ids,
        vectors=merged,
        source=source,
        model=model,
    )
    embed = EmbedResult(current_ids, merged, source, model)
    return embed, plan
