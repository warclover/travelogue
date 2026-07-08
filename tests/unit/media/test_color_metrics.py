"""Color metrics for ingest and spread scoring."""

from __future__ import annotations

from PIL import Image

from travelogue.media.color_metrics import (
    color_harmony_score,
    delta_e_cie76,
    dominant_colors,
    dominant_tone_hex,
    mean_luma,
    triangular_score,
)


def test_mean_luma_dark_vs_bright():
    dark = Image.new("RGB", (64, 64), (10, 10, 12))
    bright = Image.new("RGB", (64, 64), (240, 235, 220))
    assert mean_luma(dark) < mean_luma(bright)


def test_dominant_tone_hex_format():
    img = Image.new("RGB", (32, 32), (200, 100, 50))
    assert dominant_tone_hex(img).lower() == "#c86432"


def test_delta_e_same_color_zero():
    assert delta_e_cie76("#808080", "#808080") == 0.0


def test_triangular_score_peak():
    assert triangular_score(25.0, low=10.0, peak=25.0, high=40.0) == 1.0
    assert triangular_score(5.0, low=10.0, peak=25.0, high=40.0) == 0.0


def _mosaic(colors: list[tuple[int, int, int]], *, tile: int = 8) -> Image.Image:
    """Tile distinct colours into one image (deterministic palette)."""
    n = len(colors)
    img = Image.new("RGB", (tile * n, tile))
    px = img.load()
    for i, color in enumerate(colors):
        for x in range(i * tile, (i + 1) * tile):
            for y in range(tile):
                px[x, y] = color
    return img


def test_dominant_colors_solid_is_monochrome():
    colors = dominant_colors(Image.new("RGB", (32, 32), (200, 40, 40)))
    assert len(colors) == 1
    assert colors[0][0] == 1.0


def test_color_harmony_solid_high():
    assert color_harmony_score(Image.new("RGB", (32, 32), (40, 120, 200))) >= 0.85


def test_color_harmony_messy_low():
    messy = _mosaic(
        [
            (220, 20, 20),
            (20, 200, 20),
            (20, 20, 220),
            (220, 220, 20),
            (220, 20, 220),
            (20, 220, 220),
        ]
    )
    assert color_harmony_score(messy) <= 0.6


def test_color_harmony_two_tone_beats_messy():
    two_tone = _mosaic([(0, 64, 255), (0, 192, 255)])  # analogous blues
    messy = _mosaic(
        [
            (220, 20, 20),
            (20, 200, 20),
            (20, 20, 220),
            (220, 220, 20),
            (220, 20, 220),
        ]
    )
    assert color_harmony_score(two_tone) > color_harmony_score(messy)
