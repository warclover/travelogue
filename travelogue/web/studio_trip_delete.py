"""PDG · trip delete: tombstone rename, async rmtree, startup sweep."""

from __future__ import annotations

import logging
import os
import re
import secrets
import shutil
import threading
import time
from pathlib import Path

_log = logging.getLogger(__name__)

_REPLACE_BUSY_BACKOFF_S: tuple[float, ...] = (0.05, 0.1, 0.2, 0.4, 0.8, 1.2)
_TOMBSTONE_RE = re.compile(r"^_deleting-.+")
_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _is_replace_busy_error(exc: BaseException) -> bool:
    if isinstance(exc, PermissionError):
        return True
    if os.name == "nt" and isinstance(exc, OSError):
        return getattr(exc, "winerror", None) in (5, 32)
    return False


def sanitize_trip_id_for_tombstone(trip_id: str) -> str:
    cleaned = _SAFE_ID_RE.sub("_", str(trip_id or "").strip())
    return cleaned or "trip"


def tombstone_name(trip_id: str, *, nonce: str | None = None) -> str:
    token = nonce or secrets.token_hex(4)
    return f"_deleting-{sanitize_trip_id_for_tombstone(trip_id)}-{token}"


def rename_trip_to_tombstone(trip_dir: Path) -> Path:
    """Rename ``trip_dir`` to a sibling ``_deleting-*`` tombstone with busy retries."""
    trip_dir = trip_dir.resolve()
    parent = trip_dir.parent
    disk_id = trip_dir.name
    last_exc: OSError | None = None
    for attempt, delay in enumerate(_REPLACE_BUSY_BACKOFF_S):
        dest = parent / tombstone_name(disk_id)
        if dest.exists():
            continue
        try:
            trip_dir.rename(dest)
            return dest
        except OSError as exc:
            last_exc = exc
            if not _is_replace_busy_error(exc):
                raise
            if attempt + 1 < len(_REPLACE_BUSY_BACKOFF_S):
                time.sleep(delay)
    if last_exc is not None:
        raise last_exc
    raise OSError(f"failed to rename trip dir to tombstone: {trip_dir}")


def rmtree_tombstone(tombstone: Path, *, attempts: int = 4) -> None:
    """Best-effort physical delete of a tombstone directory."""
    path = Path(tombstone)
    for attempt in range(max(1, attempts)):
        if not path.exists():
            return
        try:
            shutil.rmtree(path)
            return
        except OSError as exc:
            _log.warning(
                "rmtree tombstone failed attempt=%s path=%s err=%s",
                attempt + 1,
                path,
                exc,
            )
            if attempt + 1 < attempts:
                time.sleep(_REPLACE_BUSY_BACKOFF_S[min(attempt, len(_REPLACE_BUSY_BACKOFF_S) - 1)])
    _log.error("rmtree tombstone exhausted retries: %s", path)


def spawn_async_rmtree(tombstone: Path) -> None:
    threading.Thread(
        target=rmtree_tombstone,
        args=(tombstone,),
        name="trip-delete-rmtree",
        daemon=True,
    ).start()


def sweep_deleting_tombstones(trips_dir: Path) -> int:
    """Startup: remove leftover ``_deleting-*`` directories. Returns count attempted."""
    root = Path(trips_dir)
    if not root.is_dir():
        return 0
    count = 0
    try:
        children = list(root.iterdir())
    except OSError:
        _log.exception("sweep_deleting_tombstones list failed for %s", root)
        return 0
    for child in children:
        try:
            if not child.is_dir() or not _TOMBSTONE_RE.match(child.name):
                continue
        except OSError:
            continue
        count += 1
        rmtree_tombstone(child)
    if count:
        _log.info("sweep_deleting_tombstones cleared=%s root=%s", count, root)
    return count
