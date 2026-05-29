"""P5-I4 · ingest checkpoint for resume after crash."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CHECKPOINT_NAME = ".ingest-checkpoint.json"
CHECKPOINT_VERSION = 1


def checkpoint_path(trip_dir: Path) -> Path:
    return trip_dir / CHECKPOINT_NAME


def source_key(photo: Path, album_root: Path) -> str:
    root = album_root.resolve()
    try:
        return photo.resolve().relative_to(root).as_posix()
    except ValueError:
        return photo.name


def load_ingest_checkpoint(trip_dir: Path) -> dict[str, Any] | None:
    path = checkpoint_path(trip_dir)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def save_ingest_checkpoint(
    trip_dir: Path,
    *,
    source_root: str,
    processed_rel_paths: list[str],
    total: int,
) -> None:
    trip_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": CHECKPOINT_VERSION,
        "sourceRoot": source_root,
        "processedRelPaths": sorted(set(processed_rel_paths)),
        "total": total,
        "updatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    checkpoint_path(trip_dir).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def clear_ingest_checkpoint(trip_dir: Path) -> None:
    path = checkpoint_path(trip_dir)
    if path.is_file():
        path.unlink(missing_ok=True)
