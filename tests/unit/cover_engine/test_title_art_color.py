"""Unit tests · title_art color contrast + recolor (PRD §6.1 · D-CAL-13/17)."""

from __future__ import annotations

import pytest
from PIL import Image

from travelogue.cover_engine.title_art.color import (
    DARK,
    MIN_CONTRAST_RATIO,
    WHITE,
    ContrastPick,
    contrast_ratio,
    pick_readable_color,
    recolor_ink_on_white,
    roi_average_color,
)

pytestmark = pytest.mark.unit


def test_contrast_ratio_white_on_black_is_max() -> None:
    ratio = contrast_ratio(WHITE, (0, 0, 0))
    assert ratio == pytest.approx(21.0, abs=0.1)


def test_contrast_ratio_symmetric() -> None:
    a = contrast_ratio(WHITE, (100, 100, 100))
    b = contrast_ratio((100, 100, 100), WHITE)
    assert a == pytest.approx(b)


def test_pick_readable_color_dark_background_prefers_white() -> None:
    pick = pick_readable_color((10, 10, 10))
    assert pick.color_rgb == WHITE
    assert pick.ok is True


def test_pick_readable_color_light_background_prefers_dark() -> None:
    pick = pick_readable_color((245, 245, 245))
    assert pick.color_rgb == DARK
    assert pick.ok is True


def test_pick_readable_color_mid_gray_falls_back_to_white_when_neither_hits_threshold() -> None:
    # 中性灰背景：白/深都可能不达标时，用户口径 (3) 要求默认回落白色。
    pick = pick_readable_color((128, 128, 128))
    assert isinstance(pick, ContrastPick)
    if not pick.ok:
        assert pick.color_rgb == WHITE


def test_pick_readable_color_hex_matches_rgb() -> None:
    pick = pick_readable_color((0, 0, 0))
    assert pick.color_hex == "#ffffff"


def test_min_contrast_ratio_is_positive() -> None:
    assert MIN_CONTRAST_RATIO > 1.0


def test_roi_average_color_solid_fill() -> None:
    img = Image.new("RGB", (100, 100), (10, 20, 30))
    avg = roi_average_color(img, (10, 10, 50, 50))
    assert avg == (10, 20, 30)


def test_roi_average_color_out_of_bounds_returns_neutral_gray() -> None:
    img = Image.new("RGB", (10, 10), (0, 0, 0))
    avg = roi_average_color(img, (100, 100, 50, 50))
    assert avg == (128, 128, 128)


def test_recolor_ink_on_white_background_becomes_transparent() -> None:
    img = Image.new("RGB", (20, 20), (255, 255, 255))
    out = recolor_ink_on_white(img, (255, 0, 0))
    assert out.mode == "RGBA"
    r, g, b, a = out.getpixel((5, 5))
    assert a == 0


def test_recolor_ink_on_white_black_ink_becomes_target_color_opaque() -> None:
    img = Image.new("RGB", (20, 20), (255, 255, 255))
    for x in range(5, 15):
        for y in range(5, 15):
            img.putpixel((x, y), (0, 0, 0))
    out = recolor_ink_on_white(img, (10, 20, 200))
    r, g, b, a = out.getpixel((10, 10))
    assert (r, g, b) == (10, 20, 200)
    assert a > 200
