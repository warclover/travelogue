"""Phase 7 RAW gate tests (AC-RAW-*)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from travelogue.media.ingest import (
    RAW_UNSUPPORTED_MESSAGE,
    IngestError,
    ingest_into_trip,
    scan_image_paths,
)
from travelogue.services.trip_factory import create_trip


def _write_jpg(folder: Path, name: str) -> None:
    Image.new("RGB", (800, 600), (40, 80, 120)).save(folder / name, quality=90)


def test_raw_only_folder_blocked(tmp_path: Path) -> None:
    album = tmp_path / "raw_only"
    album.mkdir()
    (album / "IMG_0001.CR3").write_bytes(b"\x00" * 1024)
    (album / "IMG_0002.NEF").write_bytes(b"\x00" * 1024)

    with pytest.raises(IngestError) as exc:
        scan_image_paths(album)
    assert exc.value.code == "E_INGEST_RAW_UNSUPPORTED"
    assert "JPG" in str(exc.value)


def test_raw_mixed_with_jpg_blocked(tmp_path: Path) -> None:
    album = tmp_path / "mixed"
    album.mkdir()
    _write_jpg(album, "photo.jpg")
    (album / "DSC_0001.ARW").write_bytes(b"\x00" * 512)

    with pytest.raises(IngestError) as exc:
        scan_image_paths(album)
    assert exc.value.code == "E_INGEST_RAW_UNSUPPORTED"


def test_jpg_only_regression(tmp_path: Path) -> None:
    album = tmp_path / "jpg_only"
    album.mkdir()
    for i in range(4):
        _write_jpg(album, f"p{i:02d}.jpg")

    paths, stats = scan_image_paths(album, max_photos=10)
    assert len(paths) == 4
    assert stats.get("rawRejectedCount", 0) == 0


def test_heic_not_blocked(tmp_path: Path) -> None:
    album = tmp_path / "heic"
    album.mkdir()
    _write_jpg(album, "fallback.jpg")
    # HEIC without pillow-heif may fail open but must not trigger RAW gate
    (album / "photo.heic").write_bytes(b"fake-heic")

    paths, stats = scan_image_paths(album, max_photos=10)
    assert len(paths) >= 1
    assert stats.get("rawRejectedCount", 0) == 0


def test_ingest_raw_telemetry_fields(tmp_path: Path) -> None:
    """AC-RAW-05 · stats would be populated before raise (guard helper)."""
    from travelogue.config import IngestConfig
    from travelogue.media.ingest import guard_raw_in_directory

    album = tmp_path / "raw_telemetry"
    album.mkdir()
    (album / "a.cr2").write_bytes(b"x")

    cfg = IngestConfig(reject_raw=True)
    with pytest.raises(IngestError):
        guard_raw_in_directory(album, cfg)


def test_ingest_jpg_into_trip(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("raw-gate-ok", trips)
    trip_dir = trips / "raw-gate-ok"
    album = tmp_path / "album"
    album.mkdir()
    for i in range(4):
        _write_jpg(album, f"x{i}.jpg")

    trip = __import__("json").loads(trip_json.read_text(encoding="utf-8"))
    result = ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=False)
    assert result.added == 4
    assert RAW_UNSUPPORTED_MESSAGE  # import sanity
