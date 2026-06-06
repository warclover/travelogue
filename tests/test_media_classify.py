"""Media class heuristics."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from travelogue.curation.media_classify import (
    classify_media_class,
    cover_class_weight,
    date_confidence_for_source,
)


def test_date_confidence() -> None:
    assert date_confidence_for_source("exif") == "high"
    assert date_confidence_for_source("mtime") == "low"


def test_screenshot_wide_no_exif(tmp_path: Path) -> None:
    img = Image.new("RGB", (2400, 600), (10, 20, 30))
    p = tmp_path / "shot.png"
    img.save(p)
    assert (
        classify_media_class(path=p, img=img, date_source="mtime")
        == "screenshot"
    )


def test_cover_weight_screenshot_low() -> None:
    assert cover_class_weight("screenshot") < cover_class_weight("photo")


def test_small_source_with_upscaled_webp_metadata_stays_photo(tmp_path: Path) -> None:
    """Demo-album style: 900×1200 native, srcset max variant 2400×3200."""
    img = Image.new("RGB", (900, 1200), (30, 60, 90))
    p = tmp_path / "demo.jpg"
    img.save(p)
    asset = {
        "nativeWidth": 900,
        "nativeHeight": 1200,
        "width": 2400,
        "height": 3200,
    }
    assert (
        classify_media_class(path=p, img=img, date_source="exif", asset=asset)
        == "photo"
    )


def test_true_thumbnail_still_classified(tmp_path: Path) -> None:
    img = Image.new("RGB", (438, 640), (10, 20, 30))
    p = tmp_path / "thumb.jpg"
    img.save(p)
    assert (
        classify_media_class(path=p, img=img, date_source="exif")
        == "thumbnail"
    )
