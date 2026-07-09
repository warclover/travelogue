"""Slide post-process for Longshot 2.0.

Phase A: ``draw_page_footer``.
Phase B: ``fit_aspect`` letterbox / smart_crop → 1080×1440 + safe-area warn.
"""

from __future__ import annotations

import logging
from io import BytesIO

from PIL import Image, ImageFilter

_log = logging.getLogger(__name__)

XHS_WIDTH = 1080
XHS_HEIGHT = 1440
XHS_ASPECT = XHS_WIDTH / XHS_HEIGHT  # 0.75

# D-LNG2-30 · reference safe area (warn only)
SAFE_LEFT = 72
SAFE_RIGHT = 72
SAFE_TOP = 72
SAFE_BOTTOM = 80


def draw_page_footer(data: bytes, page: int, total: int, *, fmt: str = "png") -> bytes:
    """Pillow footer watermark ``{i}/{n}`` (orientation, not decoration)."""
    if page < 1 or total < 1 or page > total:
        return data

    from travelogue.export.longshot import apply_chapter_watermark

    if total < 2:
        return _draw_footer_always(data, page, total, fmt=fmt)
    return apply_chapter_watermark(data, page=page, total=total, fmt=fmt)


def _draw_footer_always(data: bytes, page: int, total: int, *, fmt: str) -> bytes:
    from PIL import ImageDraw

    from travelogue.export.longshot import _watermark_font

    img = Image.open(BytesIO(data)).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    label = f"{page}/{total}"
    font_size = max(14, img.width // 22)
    font = _watermark_font(font_size)
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    pad = max(10, img.width // 40)
    x = (img.width - text_w) // 2
    y = img.height - text_h - pad * 2
    pill = [x - pad, y - pad // 2, x + text_w + pad, y + text_h + pad // 2]
    draw.rounded_rectangle(pill, radius=pad, fill=(0, 0, 0, 120))
    draw.text((x, y), label, fill=(255, 255, 255, 210), font=font)
    composed = Image.alpha_composite(img, overlay)
    buf = BytesIO()
    if fmt == "jpeg":
        composed.convert("RGB").save(buf, format="JPEG", quality=92)
    else:
        composed.save(buf, format="PNG")
    return buf.getvalue()


def _encode(img: Image.Image, *, fmt: str) -> bytes:
    buf = BytesIO()
    if fmt == "jpeg":
        img.convert("RGB").save(buf, format="JPEG", quality=92)
    else:
        img.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()


def _content_rect_letterbox(src_w: int, src_h: int, canvas_w: int, canvas_h: int) -> tuple[int, int, int, int]:
    """Return (x0, y0, x1, y1) of fitted content on canvas."""
    scale = min(canvas_w / max(src_w, 1), canvas_h / max(src_h, 1))
    tw = max(1, int(round(src_w * scale)))
    th = max(1, int(round(src_h * scale)))
    x0 = (canvas_w - tw) // 2
    y0 = (canvas_h - th) // 2
    return x0, y0, x0 + tw, y0 + th


def warn_safe_area(
    content_box: tuple[int, int, int, int],
    *,
    canvas_w: int = XHS_WIDTH,
    canvas_h: int = XHS_HEIGHT,
) -> bool:
    """Return True and log warn if content touches outside reference safe area."""
    x0, y0, x1, y1 = content_box
    ok_left = x0 >= SAFE_LEFT
    ok_right = (canvas_w - x1) >= SAFE_RIGHT
    ok_top = y0 >= SAFE_TOP
    ok_bottom = (canvas_h - y1) >= SAFE_BOTTOM
    if ok_left and ok_right and ok_top and ok_bottom:
        return False
    _log.warning(
        "xhs safe-area warn: content_box=%s margins L=%s R=%s T=%s B=%s "
        "(ref L/R≥%s T≥%s B≥%s)",
        content_box,
        x0,
        canvas_w - x1,
        y0,
        canvas_h - y1,
        SAFE_LEFT,
        SAFE_TOP,
        SAFE_BOTTOM,
    )
    return True


def fit_aspect_letterbox(
    data: bytes,
    *,
    width: int = XHS_WIDTH,
    height: int = XHS_HEIGHT,
    fmt: str = "png",
    blur_radius: float = 28.0,
) -> tuple[bytes, tuple[int, int, int, int]]:
    """Blurred background + contain-fit foreground (D-LNG2-06 default)."""
    src = Image.open(BytesIO(data)).convert("RGB")
    canvas = Image.new("RGB", (width, height), (20, 20, 20))

    # Background: cover-scale + blur
    bg_scale = max(width / max(src.width, 1), height / max(src.height, 1))
    bg_w = max(width, int(round(src.width * bg_scale)))
    bg_h = max(height, int(round(src.height * bg_scale)))
    bg = src.resize((bg_w, bg_h), Image.Resampling.LANCZOS)
    bx = (bg_w - width) // 2
    by = (bg_h - height) // 2
    bg = bg.crop((bx, by, bx + width, by + height))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    # Slight darken so foreground pops
    bg = Image.blend(bg, Image.new("RGB", bg.size, (0, 0, 0)), 0.25)
    canvas.paste(bg, (0, 0))

    box = _content_rect_letterbox(src.width, src.height, width, height)
    x0, y0, x1, y1 = box
    fg = src.resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS)
    canvas.paste(fg, (x0, y0))
    warn_safe_area(box, canvas_w=width, canvas_h=height)
    return _encode(canvas, fmt=fmt), box


def fit_aspect_smart_crop(
    data: bytes,
    *,
    width: int = XHS_WIDTH,
    height: int = XHS_HEIGHT,
    fmt: str = "png",
) -> tuple[bytes, tuple[int, int, int, int]]:
    """Center-crop to 3:4 then scale to canvas (experimental)."""
    src = Image.open(BytesIO(data)).convert("RGB")
    target_ar = width / height
    src_ar = src.width / max(src.height, 1)
    if src_ar > target_ar:
        # too wide → crop sides
        new_w = max(1, int(round(src.height * target_ar)))
        left = (src.width - new_w) // 2
        cropped = src.crop((left, 0, left + new_w, src.height))
    else:
        new_h = max(1, int(round(src.width / target_ar)))
        top = (src.height - new_h) // 2
        cropped = src.crop((0, top, src.width, top + new_h))
    out = cropped.resize((width, height), Image.Resampling.LANCZOS)
    # Full-bleed: content fills canvas → always outside side safe margins → warn
    box = (0, 0, width, height)
    warn_safe_area(box, canvas_w=width, canvas_h=height)
    return _encode(out, fmt=fmt), box


def fit_aspect(
    data: bytes,
    *,
    pad_mode: str = "letterbox",
    width: int = XHS_WIDTH,
    height: int = XHS_HEIGHT,
    fmt: str = "png",
) -> bytes:
    """Fit slice to platform aspect. Returns encoded image bytes."""
    mode = (pad_mode or "letterbox").strip().lower()
    if mode == "smart_crop":
        out, _ = fit_aspect_smart_crop(data, width=width, height=height, fmt=fmt)
        return out
    out, _ = fit_aspect_letterbox(data, width=width, height=height, fmt=fmt)
    return out
