"""Export strips GPS/EXIF from raster assets (AC-06)."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from travelogue.export.exif import strip_image_to_bytes, write_asset_to_zip
from travelogue.export.packager import export_trip
from travelogue.paths import ROOT
from travelogue.render.engine import render_trip

FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"


def _has_gps_exif(data: bytes) -> bool:
    img = Image.open(io.BytesIO(data))
    exif = img.getexif()
    if not exif:
        return False
    try:
        return bool(exif.get_ifd(0x8825))
    except (KeyError, OSError):
        return False


def _write_jpeg_with_gps(path: Path) -> None:
    try:
        import piexif
    except ImportError as exc:
        pytest.skip(f"piexif required for GPS fixture: {exc}")

    img = Image.new("RGB", (400, 300), (120, 80, 60))
    gps_ifd = {
        piexif.GPSIFD.GPSVersionID: (2, 2, 0, 0),
        piexif.GPSIFD.GPSLatitudeRef: b"N",
        piexif.GPSIFD.GPSLatitude: ((35, 1), (0, 1), (0, 1)),
        piexif.GPSIFD.GPSLongitudeRef: b"E",
        piexif.GPSIFD.GPSLongitude: ((135, 1), (45, 1), (0, 1)),
    }
    exif_bytes = piexif.dump({"GPS": gps_ifd})
    img.save(path, "JPEG", quality=92, exif=exif_bytes)
    raw = path.read_bytes()
    assert _has_gps_exif(raw), "fixture JPEG should contain GPS EXIF"


def test_strip_image_to_bytes_removes_gps(tmp_path: Path) -> None:
    src = tmp_path / "gps.jpg"
    _write_jpeg_with_gps(src)
    stripped = strip_image_to_bytes(src)
    assert not _has_gps_exif(stripped)


def test_export_zip_assets_have_no_gps(tmp_path: Path) -> None:
    import shutil

    from travelogue.paths import TEMPLATE_VISUAL_JOURNAL

    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ws = tmp_path / "trips" / "exif-strip-test"
    ws.mkdir(parents=True)
    shutil.copytree(TEMPLATE_VISUAL_JOURNAL / "assets", ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")

    gps_jpg = ws / "assets" / "demo" / "gps-test.jpg"
    _write_jpeg_with_gps(gps_jpg)
    assert _has_gps_exif(gps_jpg.read_bytes())

    trip["assets"][0]["displayFile"] = "assets/demo/gps-test.jpg"
    trip["assets"][0]["srcset"] = [{"file": "assets/demo/gps-test.jpg", "width": 400}]
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")

    render_trip(ws / "trip.json", validate=False)
    zip_path = export_trip(
        ws / "trip.json",
        confirm_privacy=True,
        validate=False,
    )

    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if not name.lower().endswith((".webp", ".jpg", ".jpeg", ".png")):
                continue
            data = zf.read(name)
            assert not _has_gps_exif(data), f"GPS still present in exported {name}"


def test_write_asset_to_zip_strips_when_enabled(tmp_path: Path) -> None:
    import zipfile

    src = tmp_path / "gps.jpg"
    _write_jpeg_with_gps(src)
    out = tmp_path / "out.zip"
    with zipfile.ZipFile(out, "w") as zf:
        write_asset_to_zip(zf, "assets/gps.jpg", src, strip_exif=True)
    with zipfile.ZipFile(out) as zf:
        data = zf.read("assets/gps.jpg")
    assert not _has_gps_exif(data)
