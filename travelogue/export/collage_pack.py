"""Multi-page collage export · xiaohongshu (3:4) + album_spread (2.8:1)."""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any

from travelogue.export.compose_canvas import (
    canvas_for_platform,
    compose_fixed_canvas,
    pack_photo_pages,
)
from travelogue.export.longshot import (
    LongshotExportError,
    LongshotExportResult,
    LongshotOutput,
    ProgressFn,
    _slug_title,
    _trip_title,
)
from travelogue.export.photo_grid_pack import (
    _is_kept_image,
    _load_trip,
    _resolve_asset_image_path,
)
from travelogue.export.poster_bric_pack import list_poster_photo_paths
from travelogue.export.platform_longshot import PlatformExportWriter
from travelogue.export.platform_profiles import (
    file_prefix_for_platform,
    get_profile,
    resolve_xhs_slide_count,
)
from travelogue.media.media_classify import is_collage_asset

_log = logging.getLogger(__name__)

_COLLAGE_PHOTO_LIMIT = 72
_XHS_PER_PAGE_MIN = 3
_XHS_PER_PAGE_MAX = 6
_ALBUM_PER_PAGE = 6
_ALBUM_MAX_PAGES = 30
_ALBUM_MERGE_BELOW = 2  # 章内图过少时尝试与上一 spread 合并


def list_collage_photo_paths(trip_dir: Path, *, limit: int = _COLLAGE_PHOTO_LIMIT) -> list[Path]:
    """Kept image paths excluding collage assets (alias of list_poster_photo_paths)."""
    return list_poster_photo_paths(trip_dir, limit=limit)


def _xhs_page_count(
    n_photos: int,
    *,
    slide_count: int | None,
    profile: Any,
) -> tuple[int, str]:
    """Resolve N pages for xiaohongshu collage (soft band 3–9 like estimate)."""
    n, hint = resolve_xhs_slide_count(
        photo_count=n_photos,
        slide_count=slide_count,
        profile=profile,
    )
    return n, hint


def _xhs_per_page(n_photos: int, n_pages: int) -> int:
    n_pages = max(1, int(n_pages))
    raw = max(1, int(math.ceil(n_photos / n_pages)))
    return max(_XHS_PER_PAGE_MIN, min(_XHS_PER_PAGE_MAX, raw)) if n_photos >= 3 else raw


def _chapter_photo_paths(
    trip: dict[str, Any],
    trip_dir: Path,
    *,
    limit: int,
) -> list[list[Path]]:
    """Per-chapter ordered kept photo paths (exclude collage assets)."""
    assets_by_id = {
        str(a.get("id") or ""): a
        for a in (trip.get("assets") or [])
        if isinstance(a, dict) and str(a.get("id") or "").strip()
    }
    seen: set[str] = set()
    chapters_out: list[list[Path]] = []
    total = 0
    for ch in trip.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        batch: list[Path] = []
        for screen in ch.get("screens") or []:
            if not isinstance(screen, dict):
                continue
            for raw_id in screen.get("assetIds") or []:
                aid = str(raw_id or "").strip()
                if not aid or aid in seen:
                    continue
                asset = assets_by_id.get(aid)
                if not asset or not _is_kept_image(asset):
                    continue
                if is_collage_asset(asset):
                    continue
                resolved = _resolve_asset_image_path(asset, trip_dir)
                if resolved is None or not resolved.is_file():
                    continue
                seen.add(aid)
                batch.append(resolved)
                total += 1
                if total >= limit:
                    if batch:
                        chapters_out.append(batch)
                    return chapters_out
        if batch:
            chapters_out.append(batch)
    return chapters_out


def pack_album_pages_by_chapter(
    trip_dir: Path,
    *,
    per_page: int = _ALBUM_PER_PAGE,
    max_pages: int = _ALBUM_MAX_PAGES,
    limit: int = _COLLAGE_PHOTO_LIMIT,
) -> list[list[Path]]:
    """Chapter-first album packing: one chapter → one+ spreads; merge tiny tails."""
    trip_dir = Path(trip_dir)
    trip = _load_trip(trip_dir)
    chapter_batches = _chapter_photo_paths(trip, trip_dir, limit=limit)

    if not chapter_batches:
        flat = list_collage_photo_paths(trip_dir, limit=limit)
        return pack_photo_pages(flat, per_page=per_page, max_pages=max_pages)

    pages: list[list[Path]] = []
    for batch in chapter_batches:
        if len(batch) <= per_page:
            pages.append(list(batch))
        else:
            pages.extend(
                pack_photo_pages(batch, per_page=per_page, max_pages=max_pages)
            )

    # Merge tiny chapters into previous spread when it still fits.
    merged: list[list[Path]] = []
    for batch in pages:
        if (
            merged
            and len(batch) < _ALBUM_MERGE_BELOW
            and len(merged[-1]) + len(batch) <= per_page
        ):
            merged[-1].extend(batch)
        else:
            merged.append(batch)

    if len(merged) > max_pages:
        head = merged[: max_pages - 1]
        tail: list[Path] = []
        for chunk in merged[max_pages - 1 :]:
            tail.extend(chunk)
        return head + [tail]
    return merged


def export_collage_pack(
    trip_dir: Path,
    *,
    platform: str,
    scale: int = 2,
    fmt: str = "png",
    progress: ProgressFn | None = None,
    slide_count: int | None = None,
    cfg: Any | None = None,
) -> LongshotExportResult:
    """Compose multi-page fixed-canvas collages (no Playwright / gcs flag)."""
    _ = cfg
    pid = str(platform or "").strip()
    if pid not in ("xiaohongshu", "album_spread"):
        raise LongshotExportError(
            "E_LNG2_INVALID_PLATFORM",
            f"collage_pack 仅支持 xiaohongshu / album_spread，收到「{pid}」",
        )

    trip_dir = Path(trip_dir).resolve()
    profile = get_profile(pid)
    title = _trip_title(trip_dir)
    prefix = file_prefix_for_platform(title, pid)
    canvas_wh = canvas_for_platform(pid, scale=scale)
    _ = fmt  # collage pages always PNG
    out_ext = "png"

    if pid == "xiaohongshu":
        paths = list_collage_photo_paths(trip_dir, limit=_COLLAGE_PHOTO_LIMIT)
        if not paths:
            raise LongshotExportError(
                "E_COLLAGE_N",
                "没有可导出的精选照片，请先完成策展",
            )
        n_pages, _auto_hint = _xhs_page_count(
            len(paths), slide_count=slide_count, profile=profile
        )
        per_page = _xhs_per_page(len(paths), n_pages)
        pages = pack_photo_pages(paths, per_page=per_page, max_pages=n_pages)
        user_hint = (
            f"已生成 {len(pages)} 张竖版拼贴海报（3:4）· 更多细节可写在笔记正文"
        )
        segment_reason = "collage_pages"
    else:
        pages = pack_album_pages_by_chapter(trip_dir)
        if not pages:
            raise LongshotExportError(
                "E_COLLAGE_N",
                "没有可导出的精选照片，请先完成策展",
            )
        user_hint = f"已生成 {len(pages)} 张画册跨页拼贴（2.8:1 · 按章分页）"
        segment_reason = "collage_pages"

    writer = PlatformExportWriter(trip_dir, prefix, ext=out_ext, single_file=False)
    outputs: list[LongshotOutput] = []
    total = len(pages)

    try:
        with writer:
            for i, page_paths in enumerate(pages, start=1):
                if progress:
                    progress(i - 1, total, f"拼贴页 {i}/{total}")
                png_bytes, _diag = compose_fixed_canvas(
                    page_paths, canvas_wh=canvas_wh
                )
                writer.write(i, png_bytes)
            finals = writer.commit()
        for path in finals:
            outputs.append(
                LongshotOutput(path=path, capture_method="collage_pages")
            )
        if progress:
            progress(total, total, "拼贴导出完成")
    except LongshotExportError:
        writer.rollback()
        raise
    except Exception as exc:
        writer.rollback()
        _log.exception("collage_pack export failed (%s)", pid)
        raise LongshotExportError(
            "E_COLLAGE_FAILED",
            f"拼贴导出失败: {exc}",
        ) from exc

    guide = (profile.publish_guide or "").strip()
    return LongshotExportResult(
        outputs=outputs,
        capture_method="collage_pages",
        title=_slug_title(title),
        segmented=len(outputs) > 1,
        segment_reason=segment_reason,
        user_hint=user_hint,
        platform=pid,
        profile_label=profile.label,
        target_page_count=len(outputs),
        publish_guide=guide,
        page_count=len(outputs),
        output_format="png",
    )
