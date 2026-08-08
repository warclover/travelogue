"""Route B · clean font-compositing pipeline (PRD §5.1/5.2 · D-CAL-02/03).

干净管线：字体直出主字 → 可选副标 → 导出 PNG-RGBA。
明确不做：飞白、墨点、随机旋转、骨架盖章、任何笔锋做旧（D-CAL-02 红线）。
默认 ``TEMPLATE_PLAIN`` 不再画印章（W3：红圈「旅」字属画蛇添足）；旧印章
模板仍可显式传入（D-CAL-12 矢量印章逻辑保留）。

衬底：仅 ``veil-footer`` 烧柔光垫底（呼应原生 text-shadow）。``band-cut`` /
``contact-stamp`` / ``folio-overlap`` 出纯字，落在原生标题位，由封面样式自身
的纸签 / 暗雾 / 纸面栏承托（W3：去掉双层衬底与印章）。
"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFilter

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

#: band-cut 左对齐纸签模型下主字收得更紧——真实候选矩形宽高比≈3.9:1
#: （whitelist.py band-cut rect w:0.55/h:0.14），沿用通用 0.86 会让纸签向
#: 右延展的"淡出尾巴"没有画布余量可用，见 ``_band_cut_backdrop``。
#: contact-stamp 同理收紧——卡片会在文字四周各加 16% 内边距再旋转 -2°，沿用
#: 通用 0.86 会让卡片宽度超出 1200px 工作画布、被硬裁出一条直边（旋转卡片
#: 却带直边缺口，一看就是穿帮），实测见 D-CAL-23 记录。
_MAIN_TEXT_MAX_WIDTH_RATIO_BY_STYLE: dict[str, float] = {
    "band-cut": 0.62,
    "contact-stamp": 0.62,
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

#: 跟 journal.css ``--cover-band-paper: rgba(246, 243, 236, 0.97)`` 呼应
#: （band-cut 原生纸签面板底色）。
_BAND_CUT_PAPER_RGB = (246, 243, 236)
_BAND_CUT_PAPER_ALPHA = 240
#: 纸签实色部分之后再延展多少比例作为淡出尾巴（呼应原生
#: ``linear-gradient(90deg, paper 0 88%, transparent 100%)``，这里额外留
#: 一点淡出空间让边缘不那么硬）。
_BAND_CUT_FADE_TAIL_RATIO = 0.32
_BAND_CUT_SHADOW_OFFSET = 10
_BAND_CUT_SHADOW_BLUR = 14
_BAND_CUT_SHADOW_ALPHA = 95

#: 呼应 veil-footer 原生 ``text-shadow: 0 3px 34px rgba(0,0,0,0.45)``——
#: 用模糊的暖色柔光代替纯黑投影，跟该风格暮光暖调更贴（D-CAL-23）。
#: 色调按主字明暗自适应（而不是固定暗色）：主字若是深墨色，深色柔光在浅色
#: 天空区域能补足对比度，但落在同样深色的树影区域时深底+深字近乎同色，
#: 反而看不清；主字若是浅色，暗色柔光才是经典 text-shadow 那套逻辑。两种
#: 主字明暗各配一套跟自己反向的柔光基调，保证无论落在画面哪块背景上都比
#: "裸字直接盖上去"多一层保底对比度（2026-08-08 用 veil-footer 真实素材
#: 走查发现固定暖暗色调在浅色天空区域几乎看不出光晕，才改成自适应）。
_VEIL_FOOTER_GLOW_DARK_TEXT_RGB = (250, 238, 218)  # 深墨主字 → 暖白柔光垫底
_VEIL_FOOTER_GLOW_LIGHT_TEXT_RGB = (32, 22, 12)  # 浅色主字 → 暖黑柔光垫底
#: 贴纸已钉在底部浓黑区；过大 pad/blur 会在雾带中段形成「浮块」，看起来像没进色块。
_VEIL_FOOTER_GLOW_ALPHA = 110
_VEIL_FOOTER_GLOW_PAD_RATIO = 0.12
_VEIL_FOOTER_GLOW_BLUR = 14

#: contact-stamp 呼应现网日戳徽标（``rotate(-9deg)`` 圆形描边卡）的"手工
#: 贴卡片"语言，但改用矩形——多字标题用圆形装不下。全幅已有暗渐罩
#: （``assume_dark_veil``），这里的卡片主要给文字一个"落脚点"边界，不用
#: 再叠一层强对比背景。
_CONTACT_STAMP_CARD_RGB = (8, 8, 8)
_CONTACT_STAMP_CARD_ALPHA = 120
_CONTACT_STAMP_BORDER_RGBA = (255, 255, 255, 90)
_CONTACT_STAMP_PAD_RATIO = 0.16
_CONTACT_STAMP_ROTATION_DEG = -2.0
_CONTACT_STAMP_RADIUS_RATIO = 0.12


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


def _horizontal_fade_alpha(width: int, height: int, start_alpha: int) -> Image.Image:
    """1px 高的从 ``start_alpha`` 线性降到 0 的水平渐变，resize 到目标尺寸。

    ``width``/``height`` 通常很小（纸签淡出尾巴，量级几百像素），纯 Python
    循环足够快，不引入 numpy 依赖。
    """
    if width <= 0 or height <= 0:
        return Image.new("L", (max(1, width), max(1, height)), 0)
    row = Image.new("L", (width, 1))
    for x in range(width):
        row.putpixel((x, 0), int(round(start_alpha * (1 - x / max(1, width - 1)))))
    return row.resize((width, height), Image.Resampling.BILINEAR)


def _band_cut_backdrop(
    canvas: Image.Image, content_box: tuple[float, float, float, float]
) -> None:
    """左对齐纸签面板：实色区 + 向右淡出尾巴 + 柔和投影（就地写入 ``canvas``）。

    ``content_box`` = 该风格所有可见元素（主字+副标+印章）的并集像素坐标
    ``(left, top, right, bottom)``——纸签必须完整覆盖它们，否则文字会露出
    画布之外，看起来仍像"贴纸盖住了纸签边缘"而不是"纸签托着文字"。
    """
    left, top, right, bottom = content_box
    width, _height = canvas.size
    pad_x = int(width * 0.03)
    pad_y = int((bottom - top) * 0.22)

    card_left = 0  # 贴齐画布左边——呼应原生 panel `left: 0`（纸签挂在断带线左端）
    card_top = max(0, int(top - pad_y))
    card_bottom = min(canvas.height, int(bottom + pad_y))
    solid_right = min(width, int(right + pad_x))
    fade_w = max(0, min(width - solid_right, int((solid_right - card_left) * _BAND_CUT_FADE_TAIL_RATIO)))
    card_h = card_bottom - card_top
    if card_h <= 0 or solid_right <= card_left:
        return

    # 投影先画（比纸签本体往下/右偏一点 + 模糊），再画纸签盖住投影上半部分，
    # 让纸签边缘看起来"浮"在照片上而不是贴死。
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle(
        [card_left, card_top + _BAND_CUT_SHADOW_OFFSET, solid_right, card_bottom + _BAND_CUT_SHADOW_OFFSET],
        fill=(0, 0, 0, _BAND_CUT_SHADOW_ALPHA),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=_BAND_CUT_SHADOW_BLUR))
    canvas.alpha_composite(shadow)

    card = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    solid = Image.new(
        "RGBA", (solid_right - card_left, card_h), (*_BAND_CUT_PAPER_RGB, _BAND_CUT_PAPER_ALPHA)
    )
    card.alpha_composite(solid, (card_left, card_top))
    if fade_w > 0:
        fade_alpha = _horizontal_fade_alpha(fade_w, card_h, _BAND_CUT_PAPER_ALPHA)
        fade_rgba = Image.new("RGBA", (fade_w, card_h), (*_BAND_CUT_PAPER_RGB, 0))
        fade_rgba.putalpha(fade_alpha)
        card.alpha_composite(fade_rgba, (solid_right, card_top))
    canvas.alpha_composite(card)


def _veil_footer_backdrop(
    canvas: Image.Image,
    content_box: tuple[float, float, float, float],
    main_color: tuple[int, int, int] = (255, 255, 255),
) -> None:
    """柔光垫底：呼应原生 ``text-shadow`` 的柔焦阴影，给文字一层"落地"的雾感。

    色调按 ``main_color`` 明暗自适应，见上方常量注释。
    """
    left, top, right, bottom = content_box
    w = right - left
    h = bottom - top
    if w <= 0 or h <= 0:
        return
    # ITU-R BT.601 亮度近似，够用于二分深浅，不需要更严谨的色彩空间转换。
    luma = 0.299 * main_color[0] + 0.587 * main_color[1] + 0.114 * main_color[2]
    glow_rgb = _VEIL_FOOTER_GLOW_LIGHT_TEXT_RGB if luma >= 128 else _VEIL_FOOTER_GLOW_DARK_TEXT_RGB
    pad_x = w * _VEIL_FOOTER_GLOW_PAD_RATIO
    pad_y = h * _VEIL_FOOTER_GLOW_PAD_RATIO
    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse(
        [left - pad_x, top - pad_y, right + pad_x, bottom + pad_y],
        fill=(*glow_rgb, _VEIL_FOOTER_GLOW_ALPHA),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=_VEIL_FOOTER_GLOW_BLUR))
    canvas.alpha_composite(glow)


def _contact_stamp_backdrop(
    canvas: Image.Image, content_box: tuple[float, float, float, float]
) -> None:
    """微旋转说明卡片：呼应现网日戳徽标"手工贴卡"的语言，给文字一个落脚边界。"""
    left, top, right, bottom = content_box
    pad_x = (right - left) * _CONTACT_STAMP_PAD_RATIO
    pad_y = (bottom - top) * _CONTACT_STAMP_PAD_RATIO
    card_w = int((right - left) + pad_x * 2)
    card_h = int((bottom - top) + pad_y * 2)
    if card_w <= 0 or card_h <= 0:
        return
    radius = max(4, int(min(card_w, card_h) * _CONTACT_STAMP_RADIUS_RATIO))
    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle(
        [0, 0, card_w - 1, card_h - 1],
        radius=radius,
        fill=(*_CONTACT_STAMP_CARD_RGB, _CONTACT_STAMP_CARD_ALPHA),
        outline=_CONTACT_STAMP_BORDER_RGBA,
        width=2,
    )
    rotated = card.rotate(_CONTACT_STAMP_ROTATION_DEG, resample=Image.Resampling.BICUBIC, expand=True)
    center_x = (left + right) / 2
    center_y = (top + bottom) / 2
    paste_x = int(center_x - rotated.width / 2)
    paste_y = int(center_y - rotated.height / 2)
    canvas.alpha_composite(rotated, (paste_x, paste_y))


#: veil-footer 需要额外的 ``main_color`` 参数（柔光色调自适应），单独在
#: ``render_title_art`` 里特判调用。band-cut / contact-stamp 不再烧独立衬底——
#: 产品反馈印章与双层卡片属画蛇添足，字应落在各风格原生文字位、借原生纸签/
#: 暗雾本身承托（W3 盲评后）。
_BACKDROP_RENDERERS: dict[str, object] = {}


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
    纸面栏承托。``_veil_footer_backdrop`` 仍保留备用；veil 现走 panel 流式位，
    不再烧柔光垫底。旧印章模板仍可显式传入。
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

    content_left = main_x + main_bbox[0]
    content_top = main_y + main_bbox[1]
    content_right = main_x + main_bbox[0] + main_w
    content_bottom = main_y + main_bbox[1] + main_h

    sub_x = sub_y = sub_font = sub_bbox = sub_w = sub_h = None
    seal_pos: tuple[int, int] | None = None

    if template == TEMPLATE_SEAL_CORNER and want_seal:
        seal_pos = (width - seal_d - 24, 24)
        content_right = max(content_right, seal_pos[0] + seal_d)
        content_top = min(content_top, seal_pos[1])
        if sub:
            sub_font = load_truetype(font_candidate, size=int(height * 0.1))
            sub_w, sub_h, sub_bbox = _text_size(draw, sub, sub_font)
            sub_x = (width - sub_w) / 2 - sub_bbox[0]
            sub_y = baseline_y - sub_bbox[1]
            content_left = min(content_left, sub_x + sub_bbox[0])
            content_right = max(content_right, sub_x + sub_bbox[0] + sub_w)
            content_bottom = max(content_bottom, sub_y + sub_bbox[1] + sub_h)
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
                content_left = min(content_left, sub_x + sub_bbox[0])
                content_right = max(content_right, seal_pos[0] + seal_d)
                content_bottom = max(content_bottom, sub_y + sub_bbox[1] + sub_h)
                content_bottom = max(content_bottom, seal_pos[1] + seal_d)
            else:
                sub_x = (width * 0.045 if left_align else (width - sub_w) / 2) - sub_bbox[0]
                sub_y = baseline_y - sub_bbox[1]
                content_left = min(content_left, sub_x + sub_bbox[0])
                content_right = max(content_right, sub_x + sub_bbox[0] + sub_w)
                content_bottom = max(content_bottom, sub_y + sub_bbox[1] + sub_h)
        elif want_seal:
            seal_x = width * 0.045 if left_align else (width - seal_d) / 2
            seal_pos = (int(seal_x), int(baseline_y))
            content_left = min(content_left, seal_pos[0])
            content_right = max(content_right, seal_pos[0] + seal_d)
            content_bottom = max(content_bottom, seal_pos[1] + seal_d)

    # veil-footer 走 panel 流式位、落在底部浓黑区，不再烧柔光浮块。
    # ``_veil_footer_backdrop`` 保留备用（D-CAL-23）。

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
