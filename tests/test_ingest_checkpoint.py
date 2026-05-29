"""P5-I4 · ingest checkpoint resume tests."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from travelogue.media.ingest import ingest_into_trip
from travelogue.media.ingest_checkpoint import (
    checkpoint_path,
    load_ingest_checkpoint,
    save_ingest_checkpoint,
    source_key,
)
from travelogue.services.trip_factory import create_trip


def _album(tmp_path: Path, n: int = 6) -> Path:
    album = tmp_path / "album"
    album.mkdir()
    for i in range(n):
        Image.new("RGB", (1200, 1600), (30 + i * 17, 50 + i * 11, 70 + i * 13)).save(
            album / f"p{i:02d}.jpg", quality=95
        )
    return album


def test_source_key_relative(tmp_path: Path) -> None:
    album = _album(tmp_path, 4)
    assert source_key(album / "p00.jpg", album) == "p00.jpg"


def test_checkpoint_save_load(tmp_path: Path) -> None:
    trip_dir = tmp_path / "trip"
    trip_dir.mkdir()
    save_ingest_checkpoint(
        trip_dir,
        source_root=str(tmp_path / "album"),
        processed_rel_paths=["p01.jpg", "p02.jpg"],
        total=4,
    )
    row = load_ingest_checkpoint(trip_dir)
    assert row is not None
    assert row["processedRelPaths"] == ["p01.jpg", "p02.jpg"]


def test_ingest_resumes_from_checkpoint(tmp_path: Path) -> None:
    import shutil

    album = _album(tmp_path, 6)
    trips = tmp_path / "trips"
    trip_json = create_trip("resume-demo", trips, title="Resume", place="测试")
    trip_dir = trip_json.parent
    trip = json.loads(trip_json.read_text(encoding="utf-8"))

    partial = tmp_path / "partial"
    partial.mkdir()
    for name in ("p00.jpg", "p01.jpg", "p02.jpg", "p03.jpg"):
        shutil.copy(album / name, partial / name)
    ingest_into_trip(
        trip,
        trip_dir,
        from_dir=partial,
        dedupe=False,
        generate_crops=False,
        resume_ingest=False,
        min_assets=0,
    )
    assert len(trip.get("assets") or []) == 4

    save_ingest_checkpoint(
        trip_dir,
        source_root=str(album.resolve()),
        processed_rel_paths=["p00.jpg", "p01.jpg", "p02.jpg", "p03.jpg"],
        total=6,
    )

    persist_calls = 0

    def on_persist() -> None:
        nonlocal persist_calls
        persist_calls += 1

    result = ingest_into_trip(
        trip,
        trip_dir,
        from_dir=album,
        dedupe=False,
        generate_crops=False,
        on_persist=on_persist,
        resume_ingest=True,
    )

    assert result.stats.get("ingestSkippedCheckpoint") == 4
    assert len(trip.get("assets") or []) == 6
    assert not checkpoint_path(trip_dir).is_file()
    assert persist_calls >= 1
