"""Route B · clean font-compositing pipeline (PRD §5.1/5.2 · D-CAL-02/03).

干净管线：字体直出主字 → 可选副标 → 导出 PNG-RGBA。
明确不做：飞白、墨点、随机旋转、骨架盖章、任何笔锋做旧（D-CAL-02 红线）。
默认 ``TEMPLATE_PLAIN`` 不再画印章（W3：红圈「旅」字属画蛇添足）；旧印章
模板仍可显式传入（D-CAL-12 矢量印章逻辑保留）。

各白名单风格出纯字，落在原生标题位，由封面样式自身的纸签 / 暗雾 / 纸面栏
承托（W3 后不再烧独立衬底；D-CAL-23 曾实现的 backdrop 已删除）。
"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw

from travelogue.cover_engine.title_art.color import DEFAULT_SEAL, image_to_png_bytes
from travelogue.cover_engine.title_art.fonts import (
    FontCandidate,
    load_truetype,
    load_truetype_named,
    pick_default_font,
)

#: 透明画布尺寸；消费方（Opening 渲染）按 placement 位置缩放叠加。
CANVAS_SIZE: tuple[int, int] = (1200, 720)

#: 主字最多占画布宽度的比例（留白边距，避免长标题贴边/溢出画布）。
_MAIN_TEXT_MAX_WIDTH_RATIO = 0.86
_MAIN_TEXT_MIN_SIZE_RATIO = 0.14  # 收缩下限，避免过度缩小到不可读

#: band-cut / contact-stamp 收紧宽度比：原生候选矩形偏扁，沿用通用 0.86
#: 会让贴纸超出目标区域。veil-footer 放宽到 0.94——W3 盲评 b06 长标题字号
#: 偏小，少收一档收缩循环（详见 veil-footer long-title tuning 决策记录）。
_MAIN_TEXT_MAX_WIDTH_RATIO_BY_STYLE: dict[str, float] = {
    "band-cut": 0.62,
    "contact-stamp": 0.62,
    "veil-footer": 0.94,
}

TEMPLATE_PLAIN = "plain"
TEMPLATE_INLINE_SEAL = "inline_seal"
TEMPLATE_INLINE_SEAL_WIDE = "inline_seal_wide"
TEMPLATE_SEAL_CORNER = "seal_corner"
SEAL_TEMPLATES = frozenset(
    {TEMPLATE_INLINE_SEAL, TEMPLATE_INLINE_SEAL_WIDE, TEMPLATE_SEAL_CORNER}
)
_SEAL_TEMPLATES = SEAL_TEMPLATES  # 兼容旧引用

#: 主字起始字号相对画布高度——贴近各风格原生 ``font-size`` 量级（band-cut 最小、
#: veil/folio 最大）。最终展示尺寸还受 journal.css ``max-width/max-height`` 约束。
_MAIN_TEXT_SIZE_RATIO_BY_STYLE: dict[str, float] = {
    "band-cut": 0.28,
    "contact-stamp": 0.36,
    "veil-footer": 0.52,
    "folio-overlap": 0.38,
}
_MAIN_TEXT_SIZE_RATIO_DEFAULT = 0.42

#: 画布内左对齐（呼应原生标题左起排版）；居中锚点风格不进此集合。
_LEFT_ALIGN_STYLES = frozenset({"band-cut", "contact-stamp", "folio-overlap", "veil-footer"})


@dataclass(frozen=True)
class RenderedTitleArt:
    png_bytes: bytes
    font_name: str
    template: str


def _text_size(
    draw: ImageDraw.ImageDraw, text: str, font
) -> tuple[float, float, tuple[float, float, float, float]]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1], bbox


def _seal_image(diameter: int, char: str, color: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = max(2, diameter // 24)
    draw.ellipse(
        (pad, pad, diameter - pad, diameter - pad),
        outline=(*color, 255),
        width=max(2, diameter // 30),
    )
    if char:
        font = load_truetype(pick_default_font(), size=int(diameter * 0.42))
        tw, th, bbox = _text_size(draw, char, font)
        draw.text(
            ((diameter - tw) / 2 - bbox[0], (diameter - th) / 2 - bbox[1]),
            char,
            font=font,
            fill=(*color, 255),
        )
    return img


def render_title_art(
    main_text: str,
    *,
    subtitle: str | None = None,
    template: str = TEMPLATE_PLAIN,
    main_color: tuple[int, int, int] = (255, 255, 255),
    seal_color: tuple[int, int, int] = DEFAULT_SEAL,
    seal_char: str = "旅",
    font: FontCandidate | None = None,
    opening_style_id: str | None = None,
) -> RenderedTitleArt:
    """默认 ``TEMPLATE_PLAIN``：只出主字（+可选副标），不画印章。

    各白名单风格均出纯字，落点对齐原生标题位，由封面自身的纸签 / 暗雾 /
    纸面栏承托。旧印章模板仍可显式传入。
    """
    font_candidate = font or pick_default_font()
    width, height = CANVAS_SIZE
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    left_align = opening_style_id in _LEFT_ALIGN_STYLES
    max_w = width * _MAIN_TEXT_MAX_WIDTH_RATIO_BY_STYLE.get(
        opening_style_id or "", _MAIN_TEXT_MAX_WIDTH_RATIO
    )

    main = str(main_text or "").strip()
    size_ratio = _MAIN_TEXT_SIZE_RATIO_BY_STYLE.get(
        opening_style_id or "", _MAIN_TEXT_SIZE_RATIO_DEFAULT
    )
    size = int(height * size_ratio)
    min_size = max(1, int(height * _MAIN_TEXT_MIN_SIZE_RATIO))
    main_font, main_font_name = load_truetype_named(font_candidate, size=size)
    main_w, main_h, main_bbox = _text_size(draw, main, main_font)
    while main_w > max_w and size > min_size:
        size = max(min_size, int(size * (max_w / main_w) * 0.96))
        main_font, main_font_name = load_truetype_named(font_candidate, size=size)
        main_w, main_h, main_bbox = _text_size(draw, main, main_font)
    if left_align:
        main_x = width * 0.045 - main_bbox[0]
    else:
        main_x = (width - main_w) / 2 - main_bbox[0]
    main_y = (height * 0.32) - main_h / 2 - main_bbox[1]

    sub = str(subtitle or "").strip()
    seal_d = int(height * 0.22)
    baseline_y = main_y + main_h + int(height * 0.06)
    want_seal = template in _SEAL_TEMPLATES

    sub_x = sub_y = sub_font = sub_bbox = sub_w = sub_h = None
    seal_pos: tuple[int, int] | None = None

    if template == TEMPLATE_SEAL_CORNER and want_seal:
        seal_pos = (width - seal_d - 24, 24)
        if sub:
            sub_font = load_truetype(font_candidate, size=int(height * 0.1))
            sub_w, sub_h, sub_bbox = _text_size(draw, sub, sub_font)
            sub_x = (width - sub_w) / 2 - sub_bbox[0]
            sub_y = baseline_y - sub_bbox[1]
    else:
        if sub:
            sub_size = int(height * (0.12 if template == TEMPLATE_INLINE_SEAL_WIDE else 0.1))
            sub_font = load_truetype(font_candidate, size=sub_size)
            sub_w, sub_h, sub_bbox = _text_size(draw, sub, sub_font)
            if want_seal:
                seal_gap = int(width * 0.02)
                total_w = sub_w + seal_gap + seal_d
                start_x = width * 0.045 if left_align else (width - total_w) / 2
                sub_x = start_x
                sub_y = baseline_y - sub_bbox[1]
                seal_pos = (int(start_x + sub_w + seal_gap), int(baseline_y - seal_d * 0.15))
            else:
                sub_x = (width * 0.045 if left_align else (width - sub_w) / 2) - sub_bbox[0]
                sub_y = baseline_y - sub_bbox[1]
        elif want_seal:
            seal_x = width * 0.045 if left_align else (width - seal_d) / 2
            seal_pos = (int(seal_x), int(baseline_y))

    draw.text((main_x, main_y), main, font=main_font, fill=(*main_color, 255))
    if sub and sub_x is not None:
        draw.text((sub_x - sub_bbox[0], sub_y), sub, font=sub_font, fill=(*main_color, 230))
    if seal_pos is not None:
        seal = _seal_image(seal_d, seal_char, seal_color)
        canvas.alpha_composite(seal, seal_pos)

    canvas = _crop_to_content(canvas)

    return RenderedTitleArt(
        png_bytes=image_to_png_bytes(canvas),
        font_name=main_font_name,
        template=template,
    )


def _crop_to_content(canvas: Image.Image, *, pad_ratio: float = 0.06) -> Image.Image:
    """Crop the fixed 1200×720 working canvas down to its actual ink bbox.

    ``CANVAS_SIZE`` is a generous fixed working area so every template/length
    combination has room; most of it stays fully transparent. Shipping the
    padded canvas as-is breaks §6.2 placement: consumers (``cover-opening.hbs``
    + ``journal.css``) center the sticker via ``transform: translate(-50%,
    -50%)`` at the placement rect's *visual* center — but that transform
    centers on the *box*, so an untrimmed canvas puts the empty lower half of
    the 720px-tall working area below the anchor point, shoving the actual
    glyphs well above the intended rect (observed: title clipped by the
    viewport's top edge on a real cover). Cropping to the non-transparent
    bbox (plus a little breathing-room padding) makes the shipped PNG's own
    center coincide with the glyphs' visual center, so the CSS anchor lines
    up with what's actually drawn.
    """
    bbox = canvas.getbbox()
    if bbox is None:
        return canvas
    left, top, right, bottom = bbox
    pad_x = max(4, int((right - left) * pad_ratio))
    pad_y = max(4, int((bottom - top) * pad_ratio))
    left = max(0, left - pad_x)
    top = max(0, top - pad_y)
    right = min(canvas.width, right + pad_x)
    bottom = min(canvas.height, bottom + pad_y)
    return canvas.crop((left, top, right, bottom))
