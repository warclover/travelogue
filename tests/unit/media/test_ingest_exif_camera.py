"""Phase 23 · camera EXIF ingest helpers."""

from __future__ import annotations

from io import BytesIO

from PIL import Image

from travelogue.media.exif_camera import read_camera_exif
from travelogue.render.moment_exif import format_moment_exif_line


def test_read_camera_exif_returns_none_for_blank_image() -> None:
    buf = BytesIO()
    Image.new("RGB", (64, 64), (10, 20, 30)).save(buf, format="JPEG")
    buf.seek(0)
    img = Image.open(buf)
    assert read_camera_exif(buf, img) is None
    img.close()


def test_format_moment_exif_line_requires_two_segments() -> None:
    asset = {
        "takenAt": "2024-06-14T18:30:00+08:00",
        "place": {"city": "林芝"},
        "exif": {
            "model": "iPhone 15 Pro",
            "focalLengthMm": 24,
            "aperture": 1.8,
            "shutter": "1/120",
            "iso": 100,
        },
    }
    line = format_moment_exif_line(asset)
    assert line
    assert "林芝" in line
    # BE-FST-04 · 读者面不含相机 Model / 曝光串
    assert "iPhone 15 Pro" not in line
    assert "24mm" not in line
    assert "NIKON" not in line.upper()


def test_format_moment_exif_line_single_segment_returns_none() -> None:
    asset = {"exif": {"model": "Sony A7"}}
    assert format_moment_exif_line(asset) is None


def test_format_moment_exif_line_no_camera_model() -> None:
    asset = {
        "takenAt": "2024-06-14T10:00:00+08:00",
        "place": {"city": "京都"},
        "exif": {"make": "NIKON CORPORATION", "model": "NIKON Z 6"},
    }
    line = format_moment_exif_line(asset)
    assert line
    assert "京都" in line
    assert "NIKON" not in line.upper()
