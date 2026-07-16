"""Safe / deep cleanup for trip media storage (PRD-MEDIA-REFERENCE-STORAGE-V1)."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from travelogue.media.source_resolve import compute_storage_mode, source_ref_path

# W1 whitelist — migrate to CacheRegistry when Phase22 lands (BLK-06).
SAFE_CLEANUP_REL_DIRS: tuple[str, ...] = (
    ".cluster-cache",
    "cache",
    ".cache/narrate",
    ".cache",
)


@dataclass
class CleanupItemResult:
    path: str
    bytes_freed: int = 0
    status: str = "ok"  # ok | skipped | failed
    detail: str = ""


@dataclass
class CleanupResult:
    bytes_freed: int = 0
    items: list[CleanupItemResult] = field(default_factory=list)
    cluster_cache_cleared: bool = False
    storage_mode: str | None = None


def _dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total = 0
    try:
        for p in path.rglob("*"):
            if p.is_file():
                try:
                    total += p.stat().st_size
                except OSError:
                    continue
    except OSError:
        return total
    return total


def estimate_trips_usage(trips_dir: Path) -> dict[str, Any]:
    """Approximate workspace disk usage (source + assets + known caches)."""
    trips_dir = trips_dir.resolve()
    source_bytes = 0
    assets_bytes = 0
    cache_bytes = 0
    trip_count = 0
    if not trips_dir.is_dir():
        return {
            "tripsDir": str(trips_dir),
            "tripCount": 0,
            "bytesTotal": 0,
            "bytesSource": 0,
            "bytesAssets": 0,
            "bytesCache": 0,
            "approx": True,
        }
    for child in trips_dir.iterdir():
        if not child.is_dir() or child.name.startswith(("_", ".")):
            continue
        if not (child / "trip.json").is_file():
            continue
        trip_count += 1
        source_bytes += _dir_size(child / "source")
        assets_bytes += _dir_size(child / "assets")
        for rel in SAFE_CLEANUP_REL_DIRS:
            cache_bytes += _dir_size(child / rel)
    uploads = trips_dir / "_uploads"
    cache_bytes += _dir_size(uploads)
    total = source_bytes + assets_bytes + cache_bytes
    return {
        "tripsDir": str(trips_dir),
        "tripCount": trip_count,
        "bytesTotal": total,
        "bytesSource": source_bytes,
        "bytesAssets": assets_bytes,
        "bytesCache": cache_bytes,
        "approx": True,
        "warnThresholdBytes": 5 * 1024**3,
        "overThreshold": total >= 5 * 1024**3,
    }


def estimate_safe_cleanup(trip_dir: Path) -> int:
    total = 0
    for rel in SAFE_CLEANUP_REL_DIRS:
        total += _dir_size(trip_dir / rel)
    return total


def safe_cleanup_trip(
    trip_dir: Path,
    *,
    cancel_check: Callable[[], bool] | None = None,
) -> CleanupResult:
    """Delete regenerable caches under a trip. Does not touch source/ or assets/."""
    result = CleanupResult()
    for rel in SAFE_CLEANUP_REL_DIRS:
        if cancel_check and cancel_check():
            result.items.append(
                CleanupItemResult(path=rel, status="skipped", detail="cancelled")
            )
            break
        target = trip_dir / rel
        if not target.exists():
            continue
        freed = _dir_size(target)
        try:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            result.bytes_freed += freed
            result.items.append(CleanupItemResult(path=str(target), bytes_freed=freed))
            if rel == ".cluster-cache":
                result.cluster_cache_cleared = True
        except OSError as exc:
            result.items.append(
                CleanupItemResult(
                    path=str(target), status="failed", detail=str(exc)
                )
            )
    return result


def deep_cleanup_source(
    trip: dict[str, Any],
    trip_dir: Path,
    *,
    accept_derivatives_only: bool = False,
    cancel_check: Callable[[], bool] | None = None,
) -> CleanupResult:
    """Delete materialized source/ files per D-MRS-06 (asset-level)."""
    result = CleanupResult()
    assets = trip.get("assets") or []
    for asset in assets:
        if cancel_check and cancel_check():
            result.items.append(
                CleanupItemResult(path="source/", status="skipped", detail="cancelled")
            )
            break
        if not isinstance(asset, dict) or asset.get("type") not in (None, "image"):
            continue
        source_rel = asset.get("sourceFile")
        if not isinstance(source_rel, str) or not source_rel.strip():
            continue
        source_path = trip_dir / source_rel.lstrip("/\\")
        if not source_path.is_file():
            continue
        has_ref = source_ref_path(asset) is not None
        if not has_ref and not accept_derivatives_only:
            result.items.append(
                CleanupItemResult(
                    path=str(source_path),
                    status="skipped",
                    detail="E_MEDIA_CLEANUP_REFUSED",
                )
            )
            continue
        try:
            freed = source_path.stat().st_size
            source_path.unlink()
            result.bytes_freed += freed
            result.items.append(
                CleanupItemResult(path=str(source_path), bytes_freed=freed)
            )
            # Clear sourceFile when file gone (keep sourceRef if any)
            asset.pop("sourceFile", None)
        except OSError as exc:
            result.items.append(
                CleanupItemResult(
                    path=str(source_path), status="failed", detail=str(exc)
                )
            )
    media = trip.setdefault("media", {})
    if not isinstance(media, dict):
        media = {}
        trip["media"] = media
    media["storageMode"] = compute_storage_mode(trip, trip_dir)
    result.storage_mode = media["storageMode"]
    return result


def list_dev_scratch_dirs(repo_root: Path) -> list[Path]:
    """Known development benchmark scratch under .cache/."""
    cache = repo_root / ".cache"
    if not cache.is_dir():
        return []
    out: list[Path] = []
    for child in cache.iterdir():
        if child.is_dir() and child.name.startswith("pt-bench"):
            out.append(child)
    return out


def safe_cleanup_dev_scratch(repo_root: Path) -> CleanupResult:
    result = CleanupResult()
    for path in list_dev_scratch_dirs(repo_root):
        freed = _dir_size(path)
        try:
            shutil.rmtree(path)
            result.bytes_freed += freed
            result.items.append(CleanupItemResult(path=str(path), bytes_freed=freed))
        except OSError as exc:
            result.items.append(
                CleanupItemResult(path=str(path), status="failed", detail=str(exc))
            )
    return result
