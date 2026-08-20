"""PFM ISO-04 · 作品集 × 微信群换种分享。

Explicit ``wechat_chat`` still exports a vertical strip, but the strip is
built from the kept photo pool (same source as ECC collage). It must not
flatten ``screens[].patternId`` / 5+ slot ``page-*`` geometry.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

from travelogue.export.longshot import (
    EXPORT_OUTPUT_DIRNAME,
    LongshotExportError,
    LongshotExportResult,
    LongshotOutput,
    ProgressFn,
    default_longshot_output_name,
)
from travelogue.export.poster_bric_pack import list_poster_photo_paths
from travelogue.media.image_ops import load_image_normalized

WECHAT_STACK_WIDTH = 1080
MAX_STACK_PHOTOS = 24
MAX_PHOTO_HEIGHT = 1440
STACK_GAP = 16
STACK_BG = (24, 24, 24)


def list_portfolio_wechat_photo_paths(trip_dir: Path) -> list[Path]:
    """Kept-pool paths only. Callers must not pass ``screens`` / ``patternId``."""
    return list_poster_photo_paths(Path(trip_dir), limit=MAX_STACK_PHOTOS)


def _fit_width(path: Path, *, width: int) -> Image.Image:
    loaded = load_image_normalized(path)
    src = loaded.image.convert("RGB")
    if src.width <= 0 or src.height <= 0:
        return Image.new("RGB", (width, width // 2), STACK_BG)
    new_h = max(1, round(src.height * (width / src.width)))
    if new_h > MAX_PHOTO_HEIGHT:
        new_h = MAX_PHOTO_HEIGHT
        new_w = max(1, round(src.width * (MAX_PHOTO_HEIGHT / src.height)))
        fitted = src.resize((new_w, new_h), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (width, new_h), STACK_BG)
        canvas.paste(fitted, ((width - new_w) // 2, 0))
        return canvas
    return src.resize((width, new_h), Image.Resampling.LANCZOS)


def export_portfolio_wechat_from_kept(
    trip_dir: Path,
    *,
    scale: int = 2,
    fmt: str = "png",
    progress: ProgressFn | None = None,
) -> LongshotExportResult:
    """Pillow vertical stack from kept photos. No Playwright / page-* HTML."""
    del scale  # kept-stack is 1080 CSS px; scale is a Playwright capture knob
    trip_dir = Path(trip_dir)
    paths = list_portfolio_wechat_photo_paths(trip_dir)
    if not paths:
        raise LongshotExportError(
            "E_PORTFOLIO_WECHAT_EMPTY",
            "没有可导出的照片",
        )
    if progress:
        progress(0, 1, "正在用同一批照片出社交图…")

    tiles = [_fit_width(path, width=WECHAT_STACK_WIDTH) for path in paths]
    total_h = sum(im.height for im in tiles) + STACK_GAP * max(0, len(tiles) - 1)
    canvas = Image.new("RGB", (WECHAT_STACK_WIDTH, max(1, total_h)), STACK_BG)
    y = 0
    for im in tiles:
        canvas.paste(im, (0, y))
        y += im.height + STACK_GAP

    fmt_norm = "jpeg" if str(fmt).lower() in ("jpeg", "jpg") else "png"
    name = default_longshot_output_name(trip_dir, fmt=fmt_norm)
    out_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / name
    buf = BytesIO()
    if fmt_norm == "jpeg":
        canvas.save(buf, format="JPEG", quality=90)
    else:
        canvas.save(buf, format="PNG")
    dest.write_bytes(buf.getvalue())
    if progress:
        progress(1, 1, "社交图已就绪")
    return LongshotExportResult(
        outputs=[LongshotOutput(path=dest, capture_method="kept_stack")],
        capture_method="kept_stack",
        title=dest.stem,
        segmented=False,
        segment_reason="",
        user_hint="社交图仍按现网拼贴，不是这一本作品集的页。",
        platform="wechat_chat",
        profile_label="微信群",
        target_page_count=None,
        publish_guide="",
        page_count=1,
        output_format=fmt_norm,
    )


def trip_is_portfolio(trip_dir: Path) -> bool:
    import json

    from travelogue.config.edition import is_portfolio_trip

    trip_json = Path(trip_dir) / "trip.json"
    if not trip_json.is_file():
        return False
    try:
        data: dict[str, Any] = json.loads(trip_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return False
    return is_portfolio_trip(data)
