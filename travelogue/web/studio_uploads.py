"""Studio browser upload staging and cleanup."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

_WIN_DEVICES = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
)


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


def safe_upload_basename(relpath: str) -> str | None:
    raw = (relpath or "").replace("\\", "/").strip()
    if not raw or raw.startswith("/") or raw.endswith("/"):
        return None
    if ":" in raw:
        return None
    if any(part in {".", ".."} for part in raw.split("/")):
        return None
    name = raw.rsplit("/", 1)[-1]
    if not name or name in {".", ".."}:
        return None
    stem = name.split(".")[0]
    if stem.upper() in _WIN_DEVICES:
        return None
    if any(char in name for char in '<>"|?*'):
        return None
    return name


def unique_upload_dest(upload_root: Path, name: str) -> Path:
    dest = upload_root / name
    if not dest.exists():
        return dest
    stem = Path(name).stem
    suffix = Path(name).suffix
    index = 2
    while True:
        candidate = upload_root / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def save_upload_files(upload_dir: Path, files: list[tuple[str, bytes]]) -> int:
    upload_root = upload_dir.resolve()
    saved = 0
    for relpath, content in files:
        name = safe_upload_basename(relpath)
        if name is None:
            continue
        dest = unique_upload_dest(upload_root, name).resolve()
        try:
            dest.relative_to(upload_root)
        except ValueError:
            continue
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
