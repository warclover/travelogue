"""Album export bookends — Pillow cover / closing cards (PRD-ALBUM-EXPORT-BOOKENDS-V1).

Visual technique mirrors ``travelogue.render.preview.render_preview_jpg``
(gradient veil + CJK font stack) but lives entirely in the export layer —
no import of ``travelogue.render.*`` (NG-ABE-01).
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from travelogue.media.image_ops import crop_aspect_focal, load_image_normalized

_log = logging.getLogger(__name__)

_FONT_CANDIDATES = (
    "msyh.ttc",
    "msyhbd.ttc",
    "simhei.ttf",
    "NotoSerifSC-Regular.otf",
)


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """CJK-first font stack with Pillow default as last-resort safety net."""
    for name in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _cover_crop_to_canvas(photo_path: Path, canvas_wh: tuple[int, int]) -> Image.Image:
    width, height = canvas_wh
    loaded = load_image_normalized(photo_path)
    img = loaded.image
    if img.mode != "RGB":
        img = img.convert("RGB")
    cropped = crop_aspect_focal(img, width / height, focal=(0.5, 0.45))
    img.close()
    if cropped.size != (width, height):
        cropped = cropped.resize((width, height), Image.Resampling.LANCZOS)
    return cropped


def _bottom_gradient_veil(canvas: Image.Image) -> Image.Image:
    """Black alpha ramp from mid-canvas to bottom (preview.py technique)."""
    w, h = canvas.size
    base = canvas.convert("RGBA")
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    mid = h // 2
    for y in range(mid, h):
        t = (y - mid) / max(1, h - mid)
        od.line([(0, y), (w, y)], fill=(0, 0, 0, int(200 * t)))
    return Image.alpha_composite(base, overlay).convert("RGB")


def _draw_dashed_edge(
    draw: ImageDraw.ImageDraw,
    *,
    width: int,
    height: int,
    y: int | None = None,
    dash: int = 10,
    gap: int = 8,
    color: tuple[int, int, int, int] = (255, 255, 255, 160),
) -> None:
    """Evenly spaced short segments simulating a ticket tear edge (v1)."""
    y_line = height - max(24, height // 28) if y is None else y
    x = 16
    while x < width - 16:
        x2 = min(x + dash, width - 16)
        draw.line([(x, y_line), (x2, y_line)], fill=color, width=2)
        x = x2 + gap


def _to_png_bytes(canvas: Image.Image) -> bytes:
    buf = io.BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def render_cover_card(
    photo_path: Path,
    *,
    title: str,
    subtitle: str = "",
    canvas_wh: tuple[int, int],
) -> bytes | None:
    """Full-bleed cover photo + bottom veil + title / subtitle. ``None`` on failure."""
    try:
        width, height = canvas_wh
        if width <= 0 or height <= 0:
            return None
        canvas = _cover_crop_to_canvas(Path(photo_path), canvas_wh)
        canvas = _bottom_gradient_veil(canvas)
        draw = ImageDraw.Draw(canvas)

        title_text = str(title or "").strip() or "旅行"
        sub_text = str(subtitle or "").strip()

        # Scale typography with canvas (base CARD_CANVAS = 1080×1440).
        scale = width / 1080.0
        font_title = _load_font(max(28, int(round(64 * scale))))
        font_sub = _load_font(max(16, int(round(28 * scale))))
        margin_x = max(24, int(round(48 * scale)))
        y = height - max(120, int(round(220 * scale)))

        draw.text((margin_x, y), title_text[:40], fill=(255, 255, 255), font=font_title)
        if sub_text:
            y += max(48, int(round(72 * scale)))
            draw.text(
                (margin_x, y),
                sub_text[:60],
                fill=(230, 230, 230),
                font=font_sub,
            )
        return _to_png_bytes(canvas)
    except Exception:
        _log.exception("album cover card render failed (%s)", photo_path)
        return None


def render_closing_card(
    photo_path: Path,
    *,
    title: str,
    canvas_wh: tuple[int, int],
) -> bytes | None:
    """Full-bleed closing photo + minimal colophon (no day/place/count stats).

    Ticket-stub cue: translucent footer strip + dashed tear line + "THE END".
    ``None`` on failure.
    """
    try:
        width, height = canvas_wh
        if width <= 0 or height <= 0:
            return None
        canvas = _cover_crop_to_canvas(Path(photo_path), canvas_wh).convert("RGBA")
        scale = width / 1080.0
        strip_h = max(72, int(round(140 * scale)))
        strip_y = height - strip_h

        strip = Image.new("RGBA", (width, strip_h), (20, 18, 16, 150))
        canvas.paste(strip, (0, strip_y), strip)

        draw = ImageDraw.Draw(canvas)
        _draw_dashed_edge(draw, width=width, height=height, y=strip_y + 10)

        title_text = str(title or "").strip()
        font_title = _load_font(max(14, int(round(22 * scale))))
        font_end = _load_font(max(12, int(round(18 * scale))))
        margin_x = max(24, int(round(40 * scale)))
        text_y = strip_y + max(28, int(round(40 * scale)))

        if title_text:
            draw.text(
                (margin_x, text_y),
                title_text[:48],
                fill=(235, 235, 230, 220),
                font=font_title,
            )
            text_y += max(28, int(round(36 * scale)))
        draw.text(
            (margin_x, text_y),
            "THE END",
            fill=(200, 200, 195, 180),
            font=font_end,
        )

        return _to_png_bytes(canvas.convert("RGB"))
    except Exception:
        _log.exception("album closing card render failed (%s)", photo_path)
        return None
