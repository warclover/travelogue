"""Pillow preview.jpg (9:16) — MVP aligned with cover-share layout."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from travelogue.render.context import build_render_context
from travelogue.services.trip import TripService


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("msyh.ttc", "msyhbd.ttc", "simhei.ttf", "NotoSerifSC-Regular.otf"):
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_preview_jpg(
    trip_path: Path,
    out_path: Path | None = None,
    *,
    trip_root: Path | None = None,
) -> Path:
    trip_path = trip_path.resolve()
    trip_root = trip_root or trip_path.parent
    trip = TripService().load(trip_path)
    ctx = build_render_context(trip, export_mode="share", trip_root=trip_root)

    w, h = 1080, 1920
    img = Image.new("RGB", (w, h), (26, 25, 24))
    draw = ImageDraw.Draw(img)

    cover_rel = ctx["cover"]["src"]
    cover_path = trip_root / cover_rel
    if cover_path.is_file():
        cover = Image.open(cover_path).convert("RGB")
        cover = cover.resize((w, int(w * cover.height / cover.width)), Image.Resampling.LANCZOS)
        if cover.height < h:
            top = (h - cover.height) // 3
            img.paste(cover, (0, top))
        else:
            img.paste(cover.crop((0, cover.height - h, w, cover.height)), (0, 0))

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(h // 2, h):
        t = (y - h // 2) / (h // 2)
        od.line([(0, y), (w, y)], fill=(0, 0, 0, int(200 * t)))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    meta = trip.get("meta", {})
    place = (meta.get("places") or [""])[0]
    font_place = _load_font(28)
    font_date = _load_font(24)
    font_title = _load_font(72)
    font_hook = _load_font(32)

    y = h - 280
    draw.text((48, y), place.upper(), fill=(230, 230, 230), font=font_place)
    y += 40
    draw.text((48, y), ctx["tripMetaLine"].split("·")[0].strip(), fill=(180, 180, 180), font=font_date)
    y += 48
    draw.text((48, y), ctx["title"], fill=(255, 255, 255), font=font_title)
    y += 96
    if ctx.get("hasHook"):
        hook = ctx["hook"]
        draw.text((48, y), hook[:80], fill=(240, 240, 240), font=font_hook)

    out_path = out_path or trip_root / "preview.jpg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="JPEG", quality=88, optimize=True)
    return out_path
