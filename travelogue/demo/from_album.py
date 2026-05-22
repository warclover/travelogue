"""Demo entrypoints — thin wrappers over ``demo.build`` (official pipeline)."""

from __future__ import annotations

from pathlib import Path

from travelogue.demo.build import (
    DemoError,
    DemoResult,
    run_demo_from_album,
)
from travelogue.media.ingest import IngestError, scan_image_paths

__all__ = [
    "DemoError",
    "DemoResult",
    "demo_from_album",
    "run_demo_from_album",
    "scan_album",
]


def scan_album(
    directory: Path,
    *,
    max_photos: int = 250,
    recursive: bool = True,
    min_edge_px: int = 320,
) -> tuple[list[Path], dict]:
    """Scan album folder (tests / preflight). Maps ingest errors to DemoError."""
    try:
        files, stats = scan_image_paths(
            directory,
            max_photos=max_photos,
            recursive=recursive,
            min_edge_px=min_edge_px,
        )
    except IngestError as exc:
        if exc.code in ("E_INGEST_TOO_FEW", "E_INGEST_EMPTY"):
            raise DemoError("E_DEMO_TOO_FEW", str(exc)) from exc
        raise DemoError(exc.code, str(exc)) from exc
    if len(files) < 4:
        raise DemoError(
            "E_DEMO_TOO_FEW",
            f"need at least 4 usable photos (>= {min_edge_px}px), got {len(files)}",
        )
    return files, stats


def demo_from_album(
    album_dir: Path,
    *,
    trips_dir: Path | None = None,
    trip_id: str | None = None,
    title: str = "我的旅途",
    place: str = "旅途",
    hook: str = "",
    max_photos: int = 250,
    recursive: bool = True,
    render: bool = True,
    export_layout: str = "mobile",
    force: bool = False,
    dedupe: bool = True,
    config: Path | None = None,
) -> DemoResult:
    """Backward-compatible alias for :func:`run_demo_from_album`."""
    return run_demo_from_album(
        album_dir,
        trips_dir=trips_dir,
        trip_id=trip_id,
        title=title,
        place=place,
        hook=hook,
        max_photos=max_photos,
        recursive=recursive,
        render=render,
        export_layout=export_layout,
        force=force,
        dedupe=dedupe,
        config=config,
    )
