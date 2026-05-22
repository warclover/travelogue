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
