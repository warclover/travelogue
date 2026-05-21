"""Image crop / EXIF helpers."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from PIL import Image

from travelogue.media.image_ops import (
    center_crop_aspect,
    classify_aspect,
    crop_for_aspect_kind,
    detect_orientation,
    export_webp_variants,
    filter_trip_dates,
    parse_datetime_from_filename,
    resize_to_width,
)


def test_detect_orientation():
    assert detect_orientation(1600, 2400) == "portrait"
    assert detect_orientation(1600, 900) == "landscape"
    assert detect_orientation(1000, 1000) == "square"


def test_classify_aspect_kinds():
    assert classify_aspect(2400, 800) == "panorama"
    assert classify_aspect(1600, 900) == "landscape"
    assert classify_aspect(1080, 1080) == "square"
    assert classify_aspect(900, 1350) == "portrait"
    assert classify_aspect(600, 2000) == "tall"


def test_crop_for_aspect_kind_panorama():
    img = __import__("PIL.Image").Image.new("RGB", (2400, 600), (0, 0, 0))
    out = crop_for_aspect_kind(img, "panorama")
    assert abs(out.width / out.height - 2.0) < 0.05


def test_center_crop_portrait_aspect():
    img = Image.new("RGB", (2000, 1000), (255, 0, 0))
    out = center_crop_aspect(img, 9 / 16)
    assert abs(out.width / out.height - 9 / 16) < 0.02


def test_parse_datetime_from_filename():
    assert parse_datetime_from_filename(Path("2024-03-15_sunset.jpg")) == datetime(
        2024, 3, 15, 12, 0, 0
    )
    assert parse_datetime_from_filename(Path("IMG_20250301_001.jpg")) == datetime(
        2025, 3, 1, 12, 0, 0
    )
    assert parse_datetime_from_filename(Path("random.jpg")) is None


def test_filter_trip_dates_drops_outliers():
    dates = [
        date(2024, 6, 1),
        date(2024, 6, 2),
        date(2005, 1, 1),
        date(2024, 6, 3),
    ]
    sources = ["exif", "exif", "exif", "exif"]
    filtered = filter_trip_dates(dates, sources=sources)
    assert date(2005, 1, 1) not in filtered
    assert len(filtered) == 3


def test_filter_trip_dates_prefers_trusted_when_mostly_mtime():
    dates = [
        date(2024, 1, 1),
        date(2024, 1, 2),
        date(2099, 12, 31),
        date(2024, 1, 3),
        date(2024, 1, 4),
    ]
    sources = ["mtime", "mtime", "mtime", "exif", "filename"]
    filtered = filter_trip_dates(dates, sources=sources)
    assert date(2099, 12, 31) not in filtered


def test_export_upscales_small_image(tmp_path):
    img = Image.new("RGB", (400, 600), (0, 128, 255))
    cropped = center_crop_aspect(img, 9 / 16)
    display, srcset, w, h, crop_m, crop_w = export_webp_variants(
        cropped, tmp_path, "t1", widths=(800, 1600), generate_crops=True
    )
    assert w == 1600
    assert display.endswith("-w1600.webp")
    assert len(srcset) == 2
    assert crop_m and crop_m.endswith("-m.webp")
    assert crop_w and crop_w.endswith("-w.webp")


def test_export_preserves_aspect_without_crop(tmp_path):
    img = Image.new("RGB", (1200, 1600), (80, 90, 100))
    display, srcset, w, h, crop_m, crop_w = export_webp_variants(
        img, tmp_path, "t2", widths=(800, 1600), generate_crops=False
    )
    assert w < h
    assert crop_m is None
    assert crop_w is None
    assert display.endswith("-w1600.webp")
    with Image.open(tmp_path / "t2-w1600.webp") as out:
        assert out.width < out.height
