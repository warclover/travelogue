"""ADR-016 branch D · photo_grid_pack（真·朋友圈九宫格）.

Input: trip kept photo list. No Playwright / longshot HTML capture. No P1.
"""

from __future__ import annotations

import io
import json
import logging
from pathlib import Path
from typing import Any

from PIL import Image

from travelogue.export.longshot import (
    EXPORT_OUTPUT_DIRNAME,
    LongshotExportError,
    LongshotExportResult,
    LongshotOutput,
    ProgressFn,
    _slug_title,
    _trip_title,
)
from travelogue.export.output_recipe.config_loader import copy_text
from travelogue.export.output_recipe.kept_n import count_kept_n
from travelogue.export.platform_longshot import PlatformExportWriter
from travelogue.export.platform_profiles import file_prefix_for_platform, get_profile
from travelogue.export.slide_postprocess import _content_rect_letterbox
from travelogue.media.image_ops import load_image_normalized

_log = logging.getLogger(__name__)

DEFAULT_GRID_SIZE = 1080
MAX_GRID_PAGES = 9
CANVAS_BG = (24, 24, 24)


def list_kept_photo_paths(trip_dir: Path, *, limit: int | None = None) -> list[Path]:
    """Ordered kept image paths for grid export. Never pads to 9."""
    trip_dir = Path(trip_dir)
    trip = _load_trip(trip_dir)
    kept = count_kept_n(trip)
    n = min(MAX_GRID_PAGES, kept if limit is None else min(limit, kept))
    if n <= 0:
        return []

    assets_by_id = {
        str(a.get("id") or ""): a
        for a in (trip.get("assets") or [])
        if isinstance(a, dict) and str(a.get("id") or "").strip()
    }
    ordered_ids = _ordered_kept_ids(trip, assets_by_id)
    paths: list[Path] = []
    for aid in ordered_ids:
        if len(paths) >= n:
            break
        asset = assets_by_id.get(aid)
        if not asset or not _is_kept_image(asset):
            continue
        resolved = _resolve_asset_image_path(asset, trip_dir)
        if resolved is not None and resolved.is_file():
            paths.append(resolved)
    return paths


def compose_1x1_contain(
    path: Path,
    *,
    size: int = DEFAULT_GRID_SIZE,
    bg: tuple[int, int, int] = CANVAS_BG,
) -> bytes:
    """1:1 canvas · contain（竖/横均 letterbox，无三拼 · Phase B0）."""
    size = max(64, int(size))
    loaded = load_image_normalized(Path(path))
    src = loaded.image
    if src.mode != "RGB":
        src = src.convert("RGB")
    box = _content_rect_letterbox(src.width, src.height, size, size)
    tw = max(1, box[2] - box[0])
    th = max(1, box[3] - box[1])
    fg = src.resize((tw, th), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), bg)
    canvas.paste(fg, (box[0], box[1]))
    buf = io.BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def export_photo_grid_pack(
    trip_dir: Path,
    *,
    scale: int = 2,
    fmt: str = "png",
    progress: ProgressFn | None = None,
    platform: str = "moments_grid",
) -> LongshotExportResult:
    """Branch D export · N = min(9, kept_n), atomic write, no P1."""
    trip_dir = Path(trip_dir).resolve()
    if platform != "moments_grid":
        raise LongshotExportError(
            "E_LNG2_INVALID_PLATFORM",
            f"photo_grid_pack 仅支持 moments_grid，收到「{platform}」",
        )
    trip = _load_trip(trip_dir)
    kept = count_kept_n(trip)
    n = min(MAX_GRID_PAGES, kept)
    if n <= 0:
        raise LongshotExportError(
            "E_OR_GRID_EMPTY",
            "没有可导出的精选照片，请先完成策展",
        )

    paths = list_kept_photo_paths(trip_dir, limit=n)
    if not paths:
        raise LongshotExportError(
            "E_OR_GRID_EMPTY",
            "精选照片文件找不到，请检查相册资源",
        )
    # 禁止灌水：实际产物数 = 可读文件数，不超过 kept
    n = len(paths)

    title = _trip_title(trip_dir)
    prefix = file_prefix_for_platform(title, "moments_grid")
    canvas = DEFAULT_GRID_SIZE if int(scale or 2) <= 2 else int(DEFAULT_GRID_SIZE * 1.5)
    profile = get_profile("moments_grid")
    guide = (profile.publish_guide or copy_text("guide.moments_grid")).strip()

    out_ext = "jpg" if str(fmt).lower() in ("jpeg", "jpg") else "png"
    writer = PlatformExportWriter(
        trip_dir / EXPORT_OUTPUT_DIRNAME, prefix, ext=out_ext, single_file=False
    )
    outputs: list[LongshotOutput] = []

    try:
        with writer:
            for i, src_path in enumerate(paths, start=1):
                if progress:
                    progress(i - 1, n, f"九宫格 {i}/{n}")
                png_bytes = compose_1x1_contain(src_path, size=canvas)
                if out_ext == "jpg":
                    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=92)
                    data = buf.getvalue()
                else:
                    data = png_bytes
                writer.write(i, data)
            finals = writer.commit()
        for path in finals:
            outputs.append(LongshotOutput(path=path, capture_method="photo_grid"))
        if progress:
            progress(n, n, "九宫格完成")
    except LongshotExportError:
        writer.rollback()
        raise
    except Exception as exc:
        writer.rollback()
        _log.exception("moments_grid export failed")
        raise LongshotExportError(
            "E_OR_GRID_FAILED",
            f"九宫格导出失败: {exc}",
        ) from exc

    hint = copy_text("hint.grid_count")
    return LongshotExportResult(
        outputs=outputs,
        capture_method="photo_grid",
        title=_slug_title(title),
        segmented=len(outputs) > 1,
        segment_reason="photo_grid",
        user_hint=hint,
        platform="moments_grid",
        profile_label=profile.label,
        target_page_count=n,
        publish_guide=guide,
        page_count=len(outputs),
    )


def _load_trip(trip_dir: Path) -> dict[str, Any]:
    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        raise LongshotExportError("E_TRIP_NOT_FOUND", "缺少 trip.json")
    try:
        data = json.loads(trip_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LongshotExportError("E_TRIP_NOT_FOUND", "trip.json 无法读取") from exc
    return data if isinstance(data, dict) else {}


def _ordered_kept_ids(trip: dict[str, Any], assets_by_id: dict[str, dict]) -> list[str]:
    displayed = trip.get("curation", {}).get("displayedAssetIds") if isinstance(
        trip.get("curation"), dict
    ) else None
    if isinstance(displayed, list) and displayed:
        return [str(x) for x in displayed if str(x).strip()]

    chapters = trip.get("chapters") or []
    if chapters:
        try:
            from travelogue.layout_contract.chapter_items import collect_displayed_asset_ids

            ids = collect_displayed_asset_ids(chapters)
            if ids:
                return ids
        except Exception:
            pass

    # fallback：assets 顺序，优先 layoutEligible
    eligible: list[str] = []
    rest: list[str] = []
    for aid, asset in assets_by_id.items():
        if not _is_kept_image(asset):
            continue
        if asset.get("layoutEligible") is False:
            continue
        if asset.get("layoutEligible") is True:
            eligible.append(aid)
        else:
            rest.append(aid)
    return eligible + rest


def _is_kept_image(asset: dict[str, Any]) -> bool:
    t = str(asset.get("type") or "image").lower()
    if t in ("video", "audio"):
        return False
    if asset.get("culled") is True or asset.get("excluded") is True:
        return False
    if str(asset.get("tier") or "").lower() in ("reject", "culled", "drop"):
        return False
    if asset.get("layoutEligible") is False:
        return False
    return True


def _resolve_asset_image_path(asset: dict[str, Any], trip_dir: Path) -> Path | None:
    for key in ("sourceFile", "displayFile", "path", "file", "src"):
        raw = asset.get(key)
        if not raw:
            continue
        p = Path(str(raw))
        if not p.is_absolute():
            p = trip_dir / p
        if p.is_file():
            return p
    aid = str(asset.get("id") or "").strip()
    if aid:
        for cand in (
            trip_dir / "source" / f"{aid}.jpg",
            trip_dir / "source" / f"{aid}.jpeg",
            trip_dir / "source" / f"{aid}.png",
            trip_dir / "assets" / f"{aid}.jpg",
            trip_dir / "assets" / f"{aid}.png",
        ):
            if cand.is_file():
                return cand
    return None
