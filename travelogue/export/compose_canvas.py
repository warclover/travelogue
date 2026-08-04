"""Shared fixed-canvas collage composition (A4 / XHS 3:4 / album 2.8:1)."""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any

from PIL import Image

from travelogue.export.bric_compose import bric_compose
from travelogue.media.image_ops import load_image_normalized

_log = logging.getLogger(__name__)

A4_CANVAS = (1748, 2480)  # ~150dpi A4 portrait
XHS_CANVAS = (1080, 1440)  # 3:4 portrait
ALBUM_CANVAS = (2800, 1000)  # 2.8:1 spread

DEFAULT_BORDER = 16
DEFAULT_SPACING = 8
DEFAULT_BG = (245, 245, 243)

_MAX_N = 12


def canvas_for_platform(platform: str, *, scale: int = 2) -> tuple[int, int]:
    """Return fixed canvas (w, h) for a compose platform."""
    pid = str(platform or "").strip()
    scale = int(scale or 2)
    if pid == "poster_bric":
        w, h = A4_CANVAS
        if scale > 2:
            return int(1.25 * w), int(1.25 * h)
        return w, h
    if pid == "xiaohongshu":
        w, h = XHS_CANVAS
        if scale > 2:
            return int(1.25 * w), int(1.25 * h)
        return w, h
    if pid == "album_spread":
        return ALBUM_CANVAS
    raise ValueError(f"unsupported compose platform: {pid}")


def pack_photo_pages(
    paths: list[Path],
    *,
    per_page: int,
    max_pages: int,
) -> list[list[Path]]:
    """Chunk ordered paths into pages; avoid singleton last page when possible."""
    if not paths:
        return []
    per_page = max(1, int(per_page))
    max_pages = max(1, int(max_pages))

    pages: list[list[Path]] = []
    for i in range(0, len(paths), per_page):
        pages.append(list(paths[i : i + per_page]))

    if len(pages) > max_pages:
        head = pages[: max_pages - 1]
        tail: list[Path] = []
        for chunk in pages[max_pages - 1 :]:
            tail.extend(chunk)
        # Absorb overflow on last page (allow up to ~per_page*2; keep remainder).
        cap = per_page * 2
        if len(tail) > cap and head:
            # Prefer keeping remainder on last page rather than dropping photos.
            pages = head + [tail]
        else:
            pages = head + [tail]

    if len(pages) >= 2 and len(pages[-1]) == 1 and len(pages[-2]) > 2:
        stolen = pages[-2].pop()
        pages[-1].insert(0, stolen)

    return pages


def _contain_paste_cell(
    img: Image.Image,
    *,
    tw: int,
    th: int,
    bg: tuple[int, int, int],
) -> Image.Image:
    """Contain-paste photo into a cell (letterbox inside allocated box)."""
    tw, th = max(1, int(tw)), max(1, int(th))
    ar_src = img.width / max(1, img.height)
    ar_box = tw / th
    if ar_src > ar_box:
        nw, nh = tw, max(1, int(round(tw / ar_src)))
    else:
        nh, nw = th, max(1, int(round(th * ar_src)))
    fg = img.resize((nw, nh), Image.Resampling.LANCZOS)
    cell = Image.new("RGB", (tw, th), bg)
    cell.paste(fg, ((tw - nw) // 2, (th - nh) // 2))
    fg.close()
    return cell


def compose_fixed_canvas(
    paths: list[Path],
    *,
    canvas_wh: tuple[int, int],
    border: int = DEFAULT_BORDER,
    spacing: int = DEFAULT_SPACING,
    bg: tuple[int, int, int] = DEFAULT_BG,
) -> tuple[bytes, dict[str, Any]]:
    """Compose photos onto a fixed canvas via bric layout + contain paste.

    Allows n in 1–12 (callers enforce product-specific bands).
    """
    n = len(paths)
    if not (1 <= n <= _MAX_N):
        raise ValueError(f"compose_fixed_canvas expects 1–{_MAX_N} photos, got {n}")

    canvas_w, canvas_h = int(canvas_wh[0]), int(canvas_wh[1])
    canvas_w = max(64, canvas_w)
    canvas_h = max(64, canvas_h)
    border = max(0, int(border))
    spacing = max(0, int(spacing))

    natives: list[tuple[float, float]] = []
    images: list[Image.Image] = []
    collage: Image.Image | None = None
    out: Image.Image | None = None
    scaled: Image.Image | None = None

    try:
        for p in paths:
            loaded = load_image_normalized(Path(p))
            img = loaded.image
            if img.mode != "RGB":
                img = img.convert("RGB")
            natives.append((float(img.width), float(img.height)))
            images.append(img)

        fitted, positions, natural_size = bric_compose(
            natives,
            width=canvas_w,
            border=border,
            spacing=spacing,
            round_result=True,
        )
        nw, nh = int(natural_size[0]), int(max(1, natural_size[1]))
        collage = Image.new("RGB", (nw, nh), bg)

        for img, (fw, fh), (x, y) in zip(images, fitted, positions, strict=True):
            cell = _contain_paste_cell(img, tw=int(fw), th=int(fh), bg=bg)
            collage.paste(cell, (int(x), int(y)))
            cell.close()

        place_scale = 1.0
        if nh <= canvas_h and nw <= canvas_w:
            out = Image.new("RGB", (canvas_w, canvas_h), bg)
            ox = (canvas_w - nw) // 2
            oy = (canvas_h - nh) // 2
            out.paste(collage, (ox, oy))
        else:
            place_scale = min(canvas_w / max(1, nw), canvas_h / max(1, nh))
            new_w = max(1, int(round(nw * place_scale)))
            new_h = max(1, int(round(nh * place_scale)))
            scaled = collage.resize((new_w, new_h), Image.Resampling.LANCZOS)
            out = Image.new("RGB", (canvas_w, canvas_h), bg)
            out.paste(scaled, ((canvas_w - new_w) // 2, (canvas_h - new_h) // 2))

        assert out is not None
        buf = io.BytesIO()
        out.save(buf, format="PNG", optimize=True)
        diag: dict[str, Any] = {
            "canvas": [canvas_w, canvas_h],
            "n": n,
            "border": border,
            "spacing": spacing,
            "naturalCanvas": [nw, nh],
            "scale": float(place_scale),
        }
        return buf.getvalue(), diag
    finally:
        for img in images:
            try:
                img.close()
            except Exception:
                pass
        for im in (collage, scaled, out):
            if im is not None:
                try:
                    im.close()
                except Exception:
                    pass
