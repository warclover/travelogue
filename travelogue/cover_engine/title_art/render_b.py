"""Route B · clean font-compositing pipeline (PRD §5.1/5.2 · D-CAL-02/03).

干净管线：字体直出主字 → 可选副标 → 可选印章 → 导出 PNG-RGBA。
明确不做：飞白、墨点、随机旋转、骨架盖章、任何笔锋做旧（D-CAL-02 红线）。
印章为自制矢量描边圆 + 居中字（D-CAL-12：V1 不移植 wanx 印章批次）。
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

TEMPLATE_INLINE_SEAL = "inline_seal"
TEMPLATE_INLINE_SEAL_WIDE = "inline_seal_wide"
TEMPLATE_SEAL_CORNER = "seal_corner"


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
    template: str = TEMPLATE_INLINE_SEAL_WIDE,
    main_color: tuple[int, int, int] = (255, 255, 255),
    seal_color: tuple[int, int, int] = DEFAULT_SEAL,
    seal_char: str = "旅",
    font: FontCandidate | None = None,
) -> RenderedTitleArt:
    font_candidate = font or pick_default_font()
    width, height = CANVAS_SIZE
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    main = str(main_text or "").strip()
    max_w = width * _MAIN_TEXT_MAX_WIDTH_RATIO
    size = int(height * 0.42)
    min_size = max(1, int(height * _MAIN_TEXT_MIN_SIZE_RATIO))
    main_font, main_font_name = load_truetype_named(font_candidate, size=size)
    main_w, main_h, main_bbox = _text_size(draw, main, main_font)
    # 长标题/回落到较宽的通用 CJK 字体时自适应收缩，避免超出画布（§5.1 长度门槛
    # 之外的二次防线：8 字上限仍可能因字体宽度差异溢出）。
    while main_w > max_w and size > min_size:
        size = max(min_size, int(size * (max_w / main_w) * 0.96))
        main_font, main_font_name = load_truetype_named(font_candidate, size=size)
        main_w, main_h, main_bbox = _text_size(draw, main, main_font)
    main_x = (width - main_w) / 2 - main_bbox[0]
    main_y = (height * 0.32) - main_h / 2 - main_bbox[1]
    draw.text((main_x, main_y), main, font=main_font, fill=(*main_color, 255))

    sub = str(subtitle or "").strip()
    seal_d = int(height * 0.22)
    baseline_y = main_y + main_h + int(height * 0.06)

    if template == TEMPLATE_SEAL_CORNER:
        seal = _seal_image(seal_d, seal_char, seal_color)
        canvas.alpha_composite(seal, (width - seal_d - 24, 24))
        if sub:
            sub_font = load_truetype(font_candidate, size=int(height * 0.1))
            sub_w, sub_h, sub_bbox = _text_size(draw, sub, sub_font)
            sub_x = (width - sub_w) / 2 - sub_bbox[0]
            draw.text(
                (sub_x, baseline_y - sub_bbox[1]),
                sub,
                font=sub_font,
                fill=(*main_color, 230),
            )
    else:
        # inline_seal / inline_seal_wide：主字居中 → 副标+印章同行
        if sub:
            sub_size = int(height * (0.12 if template == TEMPLATE_INLINE_SEAL_WIDE else 0.1))
            sub_font = load_truetype(font_candidate, size=sub_size)
            sub_w, sub_h, sub_bbox = _text_size(draw, sub, sub_font)
            seal_gap = int(width * 0.02)
            total_w = sub_w + seal_gap + seal_d
            start_x = (width - total_w) / 2
            draw.text(
                (start_x - sub_bbox[0], baseline_y - sub_bbox[1]),
                sub,
                font=sub_font,
                fill=(*main_color, 230),
            )
            seal = _seal_image(seal_d, seal_char, seal_color)
            canvas.alpha_composite(
                seal, (int(start_x + sub_w + seal_gap), int(baseline_y - seal_d * 0.15))
            )
        else:
            # 无副标：印章独立居中下方，避免版式空荡
            seal = _seal_image(seal_d, seal_char, seal_color)
            canvas.alpha_composite(seal, (int((width - seal_d) / 2), int(baseline_y)))

    return RenderedTitleArt(
        png_bytes=image_to_png_bytes(canvas),
        font_name=main_font_name,
        template=template,
    )
