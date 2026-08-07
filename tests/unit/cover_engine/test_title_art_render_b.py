"""Unit tests · title_art Route B clean-compositing pipeline (PRD §5.1/5.2)."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from travelogue.cover_engine.title_art.render_b import (
    CANVAS_SIZE,
    TEMPLATE_INLINE_SEAL,
    TEMPLATE_INLINE_SEAL_WIDE,
    TEMPLATE_SEAL_CORNER,
    render_title_art,
)

pytestmark = pytest.mark.unit


def _decode(png_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(png_bytes))


def test_render_title_art_produces_valid_rgba_png() -> None:
    rendered = render_title_art("拾光")
    img = _decode(rendered.png_bytes)
    assert img.mode == "RGBA"
    assert img.size == CANVAS_SIZE


def test_render_title_art_transparent_background_outside_glyphs() -> None:
    rendered = render_title_art("拾光")
    img = _decode(rendered.png_bytes)
    # 画布四角必然落在字形之外，应保持全透明。
    assert img.getpixel((0, 0))[3] == 0


def test_render_title_art_with_subtitle_and_seal_inline_wide() -> None:
    rendered = render_title_art("拾光", subtitle="贵州暑假游", template=TEMPLATE_INLINE_SEAL_WIDE)
    img = _decode(rendered.png_bytes)
    assert img.size == CANVAS_SIZE
    assert rendered.template == TEMPLATE_INLINE_SEAL_WIDE


def test_render_title_art_seal_corner_template() -> None:
    rendered = render_title_art("拾光", subtitle="贵州", template=TEMPLATE_SEAL_CORNER)
    assert rendered.template == TEMPLATE_SEAL_CORNER
    img = _decode(rendered.png_bytes)
    assert img.size == CANVAS_SIZE


def test_render_title_art_without_subtitle_still_renders() -> None:
    rendered = render_title_art("拾光", template=TEMPLATE_INLINE_SEAL)
    img = _decode(rendered.png_bytes)
    assert img.mode == "RGBA"


def test_render_title_art_records_font_name() -> None:
    rendered = render_title_art("拾光")
    assert isinstance(rendered.font_name, str)
    assert rendered.font_name
