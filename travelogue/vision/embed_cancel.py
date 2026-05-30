"""Trip-scoped cancellation for in-flight CLIP / cache writes (cluster timeout)."""

from __future__ import annotations

from pathlib import Path

_cancelled: set[str] = set()


def _key(trip_dir: Path) -> str:
    return str(trip_dir.resolve())


def clear_embedding_cancelled(trip_dir: Path) -> None:
    _cancelled.discard(_key(trip_dir))


def set_embedding_cancelled(trip_dir: Path) -> None:
    _cancelled.add(_key(trip_dir))


def embedding_cancelled(trip_dir: Path) -> bool:
    return _key(trip_dir) in _cancelled
