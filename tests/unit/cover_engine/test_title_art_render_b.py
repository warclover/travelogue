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
    # 出稿已裁到内容 bbox（见 _crop_to_content）——不再是固定工作画布尺寸；
    # 只断言不超过工作画布、且确实裁小了（否则 §6.2 居中定位会把字顶到锚点
    # 上方，见该函数 docstring 里记录的真实 bug）。
    assert img.width <= CANVAS_SIZE[0]
    assert img.height <= CANVAS_SIZE[1]
    assert img.height < CANVAS_SIZE[1] * 0.9


def test_render_title_art_transparent_background_outside_glyphs() -> None:
    rendered = render_title_art("拾光")
    img = _decode(rendered.png_bytes)
    # 裁剪后画布四角仍留有 pad_ratio 呼吸边，应保持全透明。
    assert img.getpixel((0, 0))[3] == 0


def test_render_title_art_with_subtitle_and_seal_inline_wide() -> None:
    rendered = render_title_art("拾光", subtitle="贵州暑假游", template=TEMPLATE_INLINE_SEAL_WIDE)
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


def test_render_title_art_content_fills_most_of_cropped_frame() -> None:
    """Regression guard for the "顶到锚点上方" bug (2026-08-07 视觉验收发现)：

    未裁剪时字形只占 1200×720 工作画布的一小块，CSS 用 ``translate(-50%,
    -50%)`` 按整张图居中，字形视觉中心就会明显偏离 §6.2 算出的锚点。裁剪后
    字形 bbox 应几乎填满裁剪结果（只留 pad_ratio 呼吸边），锚点才对得上。
    """
    rendered = render_title_art("夏睿彤贵州暑假游")
    img = _decode(rendered.png_bytes)
    bbox = img.getbbox()
    assert bbox is not None
    left, top, right, bottom = bbox
    # 呼吸边（pad_ratio=0.06）之外应几乎无多余空白——bbox 应覆盖裁剪结果
    # 至少 ~85% 的面积，而不是原始画布里那一小块。
    assert (right - left) >= img.width * 0.85
    assert (bottom - top) >= img.height * 0.85
