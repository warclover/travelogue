"""Phase 23 · ingest writes assets[].exif from camera EXIF."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from travelogue.config import AppConfig, IngestConfig
from travelogue.media.ingest import ingest_into_trip
from travelogue.paths import ROOT
from travelogue.services.trip_factory import create_trip

pytestmark = pytest.mark.unit


def _write_jpeg_with_camera_exif(path: Path) -> None:
    try:
        import piexif
    except ImportError as exc:
        pytest.skip(f"piexif required: {exc}")

    img = Image.new("RGB", (1800, 1200), (90, 110, 140))
    zeroth_ifd = {
        piexif.ImageIFD.Make: b"Apple",
        piexif.ImageIFD.Model: b"iPhone 15 Pro",
        piexif.ImageIFD.Software: b"TravelogueTest",
    }
    exif_ifd = {
        piexif.ExifIFD.FNumber: (18, 10),
        piexif.ExifIFD.ExposureTime: (1, 120),
        piexif.ExifIFD.ISOSpeedRatings: 200,
        piexif.ExifIFD.FocalLength: (24, 1),
    }
    exif_bytes = piexif.dump({"0th": zeroth_ifd, "Exif": exif_ifd})
    img.save(path, "JPEG", quality=92, exif=exif_bytes)


def test_ingest_writes_exif_subobject(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("exif-ingest", trips)
    trip_dir = trips / "exif-ingest"
    album = tmp_path / "album"
    album.mkdir()
    _write_jpeg_with_camera_exif(album / "camera.jpg")
    for i in range(3):
        Image.new("RGB", (800, 600), (40 + i * 20, 60, 80)).save(album / f"fill-{i}.jpg", quality=90)

    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    cfg = AppConfig(ingest=IngestConfig(exif_camera=True))
    result = ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=False, app_cfg=cfg)
    assert result.added == 4

    with_exif = [
        a
        for a in trip.get("assets") or []
        if isinstance(a.get("exif"), dict) and a["exif"].get("model")
    ]
    assert with_exif
    exif = with_exif[0]["exif"]
    assert "iPhone" in str(exif.get("model") or "")
    assert exif.get("completeness") in ("full", "partial")


def test_golden_trip_moment_pool_size_formula() -> None:
    """AC-P23-23 · clamp(round(n×5%), 1, 5) when golden trip is present."""
    from travelogue.curation.moment_scoring import moment_pool_target_size
    from travelogue.config.moment import MomentConfig

    trip_json = ROOT / "trips" / "demo-d66fe642a9" / "trip.json"
    if not trip_json.is_file():
        pytest.skip("demo-d66fe642a9 not in workspace")

    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    pool = (trip.get("curation") or {}).get("momentPoolIds") or []
    if not pool:
        pytest.skip("golden trip has no moment pool (re-curate required)")

    layout_count = sum(1 for a in trip.get("assets") or [] if a.get("layoutEligible", True))
    expected = moment_pool_target_size(layout_count, MomentConfig())
    assert len(pool) == expected
