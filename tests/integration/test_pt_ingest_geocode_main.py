"""AC-PT-11 · geocode only on main process (workers must not call Nominatim)."""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path

import pytest
from PIL import Image

from travelogue.config import AppConfig, GeocodeConfig, IngestConfig, PipelineConfig
from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[2]
WORKER_PATH = ROOT / "travelogue" / "media" / "ingest_worker.py"


def _write_jpeg_with_gps(path: Path) -> None:
    try:
        import piexif
    except ImportError as exc:
        pytest.skip(f"piexif required: {exc}")
    gps_ifd = {
        piexif.GPSIFD.GPSVersionID: (2, 2, 0, 0),
        piexif.GPSIFD.GPSLatitudeRef: b"N",
        piexif.GPSIFD.GPSLatitude: ((35, 1), (0, 1), (0, 1)),
        piexif.GPSIFD.GPSLongitudeRef: b"E",
        piexif.GPSIFD.GPSLongitude: ((135, 1), (45, 1), (0, 1)),
    }
    exif_bytes = piexif.dump({"GPS": gps_ifd})
    Image.new("RGB", (800, 1000), (90, 40, 20)).save(path, quality=90, exif=exif_bytes)


def test_ingest_worker_module_has_no_geocode_import() -> None:
    tree = ast.parse(WORKER_PATH.read_text(encoding="utf-8"), filename=str(WORKER_PATH))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "geocode" not in alias.name, alias.name
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert "geocode" not in mod, mod
            for alias in node.names:
                assert alias.name != "reverse_geocode_city"


def test_parallel_ingest_geocode_only_on_main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    album = tmp_path / "album"
    album.mkdir()
    base_t = 1_700_000_000.0
    for i in range(3):
        path = album / f"g{i}.jpg"
        _write_jpeg_with_gps(path)
        os.utime(path, (base_t + i * 120, base_t + i * 120))

    calls: list[tuple[float, float]] = []

    def fake_reverse(lat: float, lon: float, *, cache_path=None, enabled=True):
        calls.append((float(lat), float(lon)))
        return "京都"

    monkeypatch.setattr(
        "travelogue.media.geocode.reverse_geocode_city",
        fake_reverse,
    )

    trips = tmp_path / "trips"
    trip_json = create_trip("pt-geo", trips, title="geo")
    trip_dir = trip_json.parent
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    cfg = AppConfig(
        pipeline=PipelineConfig(
            parallel_ingest=True,
            parallel_ingest_min_photos=2,
            parallel_ingest_workers=2,
        ),
        ingest=IngestConfig(webp_widths=(640,), generate_crops=False, detect_faces=False),
        geocode=GeocodeConfig(enabled=True),
    )
    ingest_into_trip(
        trip,
        trip_dir,
        from_dir=album,
        dedupe=False,
        app_cfg=cfg,
        resume_ingest=False,
        min_assets=1,
    )
    assert len(calls) >= 1, "main process should geocode GPS assets"
    # All geocode calls happen in-process (monkeypatch only affects main + forked
    # children that re-import; worker must not import geocode at all — covered above).
    places = [a.get("place", {}).get("city") for a in trip["assets"] if a.get("place")]
    assert "京都" in places
