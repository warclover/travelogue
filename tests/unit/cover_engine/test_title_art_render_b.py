"""Unit tests · title_art Route B clean-compositing pipeline (PRD §5.1/5.2)."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from travelogue.cover_engine.title_art.render_b import (
    CANVAS_SIZE,
    TEMPLATE_INLINE_SEAL,
    TEMPLATE_INLINE_SEAL_WIDE,
    TEMPLATE_PLAIN,
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
    assert img.width <= CANVAS_SIZE[0]
    assert img.height <= CANVAS_SIZE[1]
    assert img.height < CANVAS_SIZE[1] * 0.9
    assert rendered.template == TEMPLATE_PLAIN


def test_render_title_art_transparent_background_outside_glyphs() -> None:
    rendered = render_title_art("拾光")
    img = _decode(rendered.png_bytes)
    assert img.getpixel((0, 0))[3] == 0


def test_render_title_art_default_has_no_seal_pixels() -> None:
    """默认 plain：不应出现印章红圈（产品判定画蛇添足）。"""
    rendered = render_title_art("拾光")
    img = _decode(rendered.png_bytes).convert("RGBA")
    redish = 0
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = img.getpixel((x, y))
            if a > 200 and r > 140 and g < 90 and b < 90:
                redish += 1
    assert redish < 30


def test_render_title_art_with_subtitle_and_seal_inline_wide() -> None:
    rendered = render_title_art(
        "拾光", subtitle="贵州暑假游", template=TEMPLATE_INLINE_SEAL_WIDE
    )
    img = _decode(rendered.png_bytes)
    assert img.width <= CANVAS_SIZE[0]
    assert img.height <= CANVAS_SIZE[1]
    assert rendered.template == TEMPLATE_INLINE_SEAL_WIDE


def test_render_title_art_seal_corner_template() -> None:
    rendered = render_title_art("拾光", subtitle="贵州", template=TEMPLATE_SEAL_CORNER)
    assert rendered.template == TEMPLATE_SEAL_CORNER
    img = _decode(rendered.png_bytes)
    assert img.width <= CANVAS_SIZE[0]
    assert img.height <= CANVAS_SIZE[1]


def test_render_title_art_without_subtitle_still_renders() -> None:
    rendered = render_title_art("拾光", template=TEMPLATE_INLINE_SEAL)
    img = _decode(rendered.png_bytes)
    assert img.mode == "RGBA"


def test_render_title_art_records_font_name() -> None:
    rendered = render_title_art("拾光")
    assert isinstance(rendered.font_name, str)
    assert rendered.font_name


def test_render_title_art_veil_footer_no_baked_glow_plaque() -> None:
    """veil-footer 不再烧柔光浮块；画布应与纯字接近（左对齐导致左右裁切可不同）。"""
    plain = render_title_art("拾光", opening_style_id=None)
    styled = render_title_art("拾光", opening_style_id="veil-footer")
    styled_img = _decode(styled.png_bytes)
    # 四角保持透明——没有大面积柔光垫底
    assert styled_img.getpixel((0, 0))[3] == 0
    assert plain.template == TEMPLATE_PLAIN


@pytest.mark.parametrize("style_id", ["band-cut", "contact-stamp", "folio-overlap"])
def test_render_title_art_no_baked_card_for_paper_or_stamp_styles(style_id: str) -> None:
    """band-cut/contact-stamp 不再烧独立纸签/卡片——纯字贴原生文字位。"""
    plain = render_title_art("拾光", opening_style_id=None)
    styled = render_title_art("拾光", opening_style_id=style_id)
    # folio/band/contact 走左对齐，字节不必相等；但不该比「纯字+印章」时代更大很多
    # （无衬底）。这里只断言四角仍透明。
    styled_img = _decode(styled.png_bytes)
    assert styled_img.getpixel((0, 0))[3] == 0
    assert plain.template == TEMPLATE_PLAIN


def test_render_title_art_band_cut_left_aligns_main_text() -> None:
    left_aligned = render_title_art("拾光贵州行", opening_style_id="band-cut")
    centered = render_title_art("拾光贵州行", opening_style_id=None)
    left_img = _decode(left_aligned.png_bytes)
    centered_img = _decode(centered.png_bytes)
    left_bbox = left_img.getbbox()
    centered_bbox = centered_img.getbbox()
    assert left_bbox is not None
    assert centered_bbox is not None
    # 左对齐主字更靠左（呼吸边内）；居中版本左右对称，左边界更大
    assert left_bbox[0] <= centered_bbox[0]


def test_render_title_art_content_fills_most_of_cropped_frame() -> None:
    rendered = render_title_art("夏睿彤贵州暑假游")
    img = _decode(rendered.png_bytes)
    bbox = img.getbbox()
    assert bbox is not None
    left, top, right, bottom = bbox
    assert (right - left) >= img.width * 0.85
    assert (bottom - top) >= img.height * 0.85
