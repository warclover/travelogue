"""M3 · D-QH-05：incomplete import purge + previewable predicate."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.web.studio_incomplete_purge import (
    PREVIEWABLE_PIPELINE_STATUSES,
    maybe_purge_incomplete_import_trip,
    trip_has_user_patches,
    trip_is_previewable,
)


def _write_trip(trip_dir: Path, *, status: str, locks: dict | None = None, revision: int = 0) -> None:
    trip_dir.mkdir(parents=True, exist_ok=True)
    trip = {
        "meta": {"title": "半成品", "revision": revision},
        "pipeline": {"status": status, "locks": locks or {"structure": False, "copy": False}},
    }
    (trip_dir / "trip.json").write_text(json.dumps(trip), encoding="utf-8")


def test_previewable_requires_index_and_status(tmp_path: Path) -> None:
    trip_dir = tmp_path / "t1"
    _write_trip(trip_dir, status="structure_draft")
    assert trip_is_previewable(trip_dir) is False
    (trip_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    assert trip_is_previewable(trip_dir) is True
    assert "structure_draft" in PREVIEWABLE_PIPELINE_STATUSES


def test_previewable_rejects_empty_pipeline(tmp_path: Path) -> None:
    trip_dir = tmp_path / "t2"
    _write_trip(trip_dir, status="")
    (trip_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    assert trip_is_previewable(trip_dir) is False


def test_purge_incomplete_shell(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_dir = trips / "half-done"
    _write_trip(trip_dir, status="")
    # no index.html → not previewable
    assert maybe_purge_incomplete_import_trip(trips, "half-done") is True
    assert not trip_dir.exists()


def test_purge_skips_previewable(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_dir = trips / "ready-trip"
    _write_trip(trip_dir, status="rendered")
    (trip_dir / "index.html").write_text("<html>ok</html>", encoding="utf-8")
    assert maybe_purge_incomplete_import_trip(trips, "ready-trip") is False
    assert trip_dir.is_dir()


def test_purge_skips_user_patches(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_dir = trips / "edited"
    _write_trip(trip_dir, status="", locks={"structure": True, "copy": False})
    trip = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    assert trip_has_user_patches(trip) is True
    assert maybe_purge_incomplete_import_trip(trips, "edited") is False
    assert trip_dir.is_dir()


def test_purge_skips_revision_bump(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_dir = trips / "rev2"
    _write_trip(trip_dir, status="", revision=2)
    assert maybe_purge_incomplete_import_trip(trips, "rev2") is False
