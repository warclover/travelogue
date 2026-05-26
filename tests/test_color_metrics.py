"""Color metrics for ingest and spread scoring."""

from __future__ import annotations

from PIL import Image

from travelogue.media.color_metrics import delta_e_cie76, dominant_tone_hex, mean_luma, triangular_score


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
