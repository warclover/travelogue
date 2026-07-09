"""Phase B · Xiaohongshu postprocess + slideCount (AC-LNG2-03/04)."""

from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from travelogue.export.platform_profiles import resolve_xhs_slide_count
from travelogue.export.slide_postprocess import (
    XHS_HEIGHT,
    XHS_WIDTH,
    fit_aspect,
    fit_aspect_letterbox,
    fit_aspect_smart_crop,
    warn_safe_area,
)

pytestmark = pytest.mark.unit


def _png(w: int, h: int, color=(200, 100, 50)) -> bytes:
    img = Image.new("RGB", (w, h), color)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_resolve_xhs_slide_count_auto_regular() -> None:
    """AC-LNG2-04 · conventional trip → 5–9."""
    n, hint = resolve_xhs_slide_count(photo_count=24)
    assert 5 <= n <= 9
    assert "笔记正文" in hint


def test_resolve_xhs_slide_count_short_trip() -> None:
    n, _ = resolve_xhs_slide_count(photo_count=8)
    assert 3 <= n <= 6


def test_resolve_xhs_slide_count_long_trip_cap_10() -> None:
    n, _ = resolve_xhs_slide_count(photo_count=60)
    assert n <= 10


def test_resolve_xhs_slide_count_explicit() -> None:
    n, hint = resolve_xhs_slide_count(photo_count=40, slide_count=6)
    assert n == 6
    assert "3:4" in hint


def test_fit_aspect_letterbox_1080x1440() -> None:
    """AC-LNG2-03b · default letterbox → exact canvas."""
    raw = _png(428, 900)
    out = fit_aspect(raw, pad_mode="letterbox")
    im = Image.open(BytesIO(out))
    assert im.size == (XHS_WIDTH, XHS_HEIGHT)


def test_fit_aspect_smart_crop_1080x1440() -> None:
    raw = _png(800, 600)
    out, box = fit_aspect_smart_crop(raw)
    im = Image.open(BytesIO(out))
    assert im.size == (XHS_WIDTH, XHS_HEIGHT)
    assert box == (0, 0, XHS_WIDTH, XHS_HEIGHT)


def test_letterbox_returns_content_box_and_may_warn() -> None:
    raw = _png(428, 2000)  # very tall → narrow on canvas
    out, box = fit_aspect_letterbox(raw)
    im = Image.open(BytesIO(out))
    assert im.size == (XHS_WIDTH, XHS_HEIGHT)
    x0, y0, x1, y1 = box
    assert 0 <= x0 < x1 <= XHS_WIDTH
    assert 0 <= y0 < y1 <= XHS_HEIGHT


def test_warn_safe_area_full_bleed() -> None:
    assert warn_safe_area((0, 0, XHS_WIDTH, XHS_HEIGHT)) is True


def test_warn_safe_area_inset_ok() -> None:
    assert warn_safe_area((80, 80, XHS_WIDTH - 80, XHS_HEIGHT - 90)) is False
