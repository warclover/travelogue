"""Media class heuristics."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from travelogue.curation.media_classify import (
    classify_media_class,
    cover_class_weight,
    date_confidence_for_source,
    detect_collage_asset,
)


def _grid_collage_image(w: int, h: int, *, panels: tuple[int, int] = (2, 2)) -> Image.Image:
    img = Image.new("RGB", (w, h), color=(40, 40, 40))
    px = img.load()
    if panels == (2, 1):
        mid = w // 2
        for x in range(w):
            for y in range(h):
                panel = 0 if x < mid - 3 else 1
                base = (180, 120, 90) if panel == 0 else (90, 140, 180)
                px[x, y] = (240, 240, 240) if abs(x - mid) < 4 else base
    else:
        for x in range(w):
            for y in range(h):
                panel_x = 0 if x < w // 2 - 5 else 1
                panel_y = 0 if y < h // 2 - 5 else 1
                base = (180, 120, 90) if (panel_x + panel_y) % 2 == 0 else (90, 140, 180)
                if abs(x - w // 2) < 4 or abs(y - h // 2) < 4:
                    px[x, y] = (240, 240, 240)
                else:
                    px[x, y] = base
    return img


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


def test_wide_collage_not_misclassified_as_screenshot(tmp_path: Path) -> None:
    """Three-panel horizontal collages exceed 2.4 AR but must stay collage, not screenshot."""
    img = _grid_collage_image(2400, 600, panels=(2, 1))
    p = tmp_path / "wide-collage.jpg"
    img.save(p)
    assert detect_collage_asset(path=p, img=img) is True
    assert (
        classify_media_class(path=p, img=img, date_source="mtime")
        == "collage"
    )


def test_filename_hint_classifies_collage(tmp_path: Path) -> None:
    img = Image.new("RGB", (1200, 1200), (100, 110, 120))
    p = tmp_path / "云南拼图01.jpg"
    img.save(p)
    assert classify_media_class(path=p, img=img, date_source="exif") == "collage"


def test_travel_landscape_not_false_positive_collage(tmp_path: Path) -> None:
    """Scene edges must not trigger collage when gutters are not grid-aligned."""
    img = Image.new("RGB", (6331, 3561), (90, 100, 110))
    px = img.load()
    for x in range(img.width):
        for y in range(img.height):
            if x % 900 < 3:
                px[x, y] = (200, 200, 200)
    p = tmp_path / "travel-landscape.jpg"
    img.save(p, quality=85)
    assert detect_collage_asset(path=p, img=img) is False
    assert classify_media_class(path=p, img=img, date_source="exif") == "photo"


def test_demo_style_panorama_not_false_positive_collage() -> None:
    """Natural wide travel frames (center luminance seam) must stay photo."""
    root = Path(__file__).resolve().parents[1]
    for name in ("asset-058.jpg", "asset-059.jpg"):
        p = root / "trips" / "demo-2025-4" / "source" / name
        if not p.is_file():
            pytest.skip(f"missing {p}")
        img = Image.open(p)
        assert detect_collage_asset(path=p, img=img) is False
        assert classify_media_class(path=p, img=img, date_source="exif") == "photo"


def test_exif_software_hint_classifies_collage(tmp_path: Path) -> None:
    img = Image.new("RGB", (1200, 1200), (128, 128, 128))
    exif = img.getexif()
    from PIL.ExifTags import Base

    exif[Base.Software] = "CapCut"
    buf = BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    buf.seek(0)
    loaded = Image.open(buf)
    p = tmp_path / "x.jpg"
    assert classify_media_class(path=p, img=loaded, date_source="exif") == "collage"
