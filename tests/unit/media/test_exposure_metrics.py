"""PA-T02 / PA-T03 · exposure + lighting metric unit tests."""

from __future__ import annotations

from PIL import Image

from travelogue.media.exposure_metrics import (
    histogram_stats,
    lighting_stats,
    quadrant_balance,
    subject_contrast_score,
)


def _gradient(width: int = 64, height: int = 64) -> Image.Image:
    img = Image.new("L", (width, height))
    px = img.load()
    for x in range(width):
        v = int(round(255 * x / (width - 1)))
        for y in range(height):
            px[x, y] = v
    return img.convert("RGB")


def _split_lr(width: int = 64, height: int = 64) -> Image.Image:
    img = Image.new("RGB", (width, height), (0, 0, 0))
    px = img.load()
    for x in range(width // 2, width):
        for y in range(height):
            px[x, y] = (255, 255, 255)
    return img


def test_histogram_pure_black():
    stats = histogram_stats(Image.new("RGB", (32, 32), (0, 0, 0)))
    assert stats["clipLowRatio"] == 1.0
    assert stats["clipHighRatio"] == 0.0
    assert stats["dynamicRange"] == 0.0
    assert stats["midtoneCenter"] == 0.0


def test_histogram_pure_white():
    stats = histogram_stats(Image.new("RGB", (32, 32), (255, 255, 255)))
    assert stats["clipHighRatio"] == 1.0
    assert stats["clipLowRatio"] == 0.0
    assert stats["midtoneCenter"] == 0.0


def test_histogram_midgray_centered():
    stats = histogram_stats(Image.new("RGB", (32, 32), (128, 128, 128)))
    assert stats["midtoneCenter"] > 0.98
    assert stats["clipHighRatio"] == 0.0
    assert stats["clipLowRatio"] == 0.0


def test_histogram_gradient_high_dynamic_range():
    stats = histogram_stats(_gradient())
    assert stats["dynamicRange"] > 0.8


def test_histogram_mean_luma_override():
    # An explicit meanLuma drives midtoneCenter regardless of pixels.
    stats = histogram_stats(Image.new("RGB", (32, 32), (0, 0, 0)), mean_luma=0.5)
    assert stats["midtoneCenter"] == 1.0


def test_lighting_flat_is_low():
    stats = lighting_stats(Image.new("RGB", (32, 32), (120, 120, 120)))
    assert stats["lumaGradient"] == 0.0
    assert stats["contrast"] == 0.0


def test_lighting_gradient_has_direction():
    flat = lighting_stats(Image.new("RGB", (32, 32), (120, 120, 120)))
    grad = lighting_stats(_gradient())
    assert grad["lumaGradient"] > flat["lumaGradient"]
    assert grad["contrast"] > flat["contrast"]


def test_lighting_split_high_contrast():
    stats = lighting_stats(_split_lr())
    assert stats["contrast"] > 0.9


def test_quadrant_balance_flat_is_balanced():
    assert quadrant_balance(Image.new("RGB", (32, 32), (120, 120, 120))) == 1.0


def test_quadrant_balance_one_sided_is_low():
    assert quadrant_balance(_split_lr()) < 0.2


def test_subject_contrast_none_without_box():
    assert subject_contrast_score(_gradient(), None) is None
    assert subject_contrast_score(_gradient(), {"x": 0, "y": 0, "w": 0.0, "h": 0.0}) is None


def test_subject_contrast_in_range():
    img = _split_lr()
    score = subject_contrast_score(img, {"x": 0.4, "y": 0.0, "w": 0.2, "h": 1.0})
    assert score is not None
    assert 0.0 <= score <= 1.0
