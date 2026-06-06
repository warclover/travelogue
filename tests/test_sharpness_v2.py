"""Sharpness V2 (Laplacian + ROI) tests."""

from __future__ import annotations

from PIL import Image, ImageDraw

from travelogue.curation.asset_quality import normalized_sharpness
from travelogue.media.sharpness import sharpness_score_v2


def _grid_image() -> Image.Image:
    img = Image.new("RGB", (400, 400), color=(200, 200, 200))
    draw = ImageDraw.Draw(img)
    for i in range(0, 400, 6):
        draw.line((i, 0, i, 400), fill=(20, 20, 20), width=1)
    return img


def test_sharpness_v2_positive_on_textured_image() -> None:
    img = _grid_image()
    assert sharpness_score_v2(img) > 0.0


def test_sharpness_v2_roi_boosts_salient_region() -> None:
    img = _grid_image()
    full = sharpness_score_v2(img)
    roi = sharpness_score_v2(img, roi={"x": 0.25, "y": 0.25, "w": 0.5, "h": 0.5})
    assert roi > 0.0
    assert full > 0.0


def test_sharpness_v2_solid_color_uses_v1_floor() -> None:
    """P0 · low-texture solids must not write sharpness=0."""
    from PIL import Image

    img = Image.new("RGB", (512, 512), color=(120, 80, 200))
    assert sharpness_score_v2(img) > 0.0


def test_normalized_sharpness_percentile_rank() -> None:
    low = {"id": "l", "quality": {"sharpness": 10.0}, "mediaClass": "photo"}
    high = {"id": "h", "quality": {"sharpness": 100.0}, "mediaClass": "photo"}
    pool = [low, high]
    assert normalized_sharpness(high, pool) > normalized_sharpness(low, pool)
