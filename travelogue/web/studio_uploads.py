"""Studio browser upload staging and cleanup."""

from __future__ import annotations

import shutil
import time
from pathlib import Path


def uploads_root(trips_dir: Path) -> Path:
    root = trips_dir / "_uploads"
    root.mkdir(parents=True, exist_ok=True)
    return root


def upload_dir_for_job(trips_dir: Path, job_id: str) -> Path:
    path = uploads_root(trips_dir) / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def delete_upload_dir(path: Path, *, trips_dir: Path | None = None) -> None:
    path = path.resolve()
    if trips_dir is not None:
        uploads_root_dir = uploads_root(trips_dir).resolve()
        try:
            path.relative_to(uploads_root_dir)
        except ValueError:
            return
    elif "_uploads" not in path.parts:
        return
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def save_upload_files(upload_dir: Path, files: list[tuple[str, bytes]]) -> int:
    saved = 0
    for relpath, content in files:
        clean = relpath.replace("\\", "/").lstrip("/")
        if not clean or ".." in clean.split("/"):
            continue
        dest = upload_dir / clean
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        saved += 1
    return saved


def sweep_stale_uploads(trips_dir: Path, *, max_age_hours: float = 24.0) -> int:
    root = uploads_root(trips_dir)
    if not root.is_dir():
        return 0
    cutoff = time.time() - max_age_hours * 3600
    removed = 0
    for child in root.iterdir():
        if not child.is_dir():
            continue
        try:
            if child.stat().st_mtime < cutoff:
                shutil.rmtree(child, ignore_errors=True)
                removed += 1
        except OSError:
            continue
    return removed
