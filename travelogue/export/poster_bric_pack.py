"""GCS Track B · poster_bric Writer (TPC W4).

Single-canvas A4 collage export. Does not write trip.json screens[].
Requires features.gcs_poster_bric / studio.gcs_poster_bric.enabled (default on).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from travelogue.export.compose_canvas import A4_CANVAS, canvas_for_platform, compose_fixed_canvas
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
    _ordered_kept_ids,
    _resolve_asset_image_path,
)
from travelogue.export.platform_longshot import PlatformExportWriter
from travelogue.export.platform_profiles import file_prefix_for_platform, get_profile
from travelogue.media.media_classify import is_collage_asset

_log = logging.getLogger(__name__)

MIN_N = 3
MAX_N = 9
DEFAULT_WIDTH = A4_CANVAS[0]
BORDER = 16
SPACING = 8
CANVAS_BG = (245, 245, 243)


def gcs_poster_bric_enabled(cfg: Any | None = None) -> bool:
    if cfg is None:
        from travelogue.config import get_config

        cfg = get_config()
    studio = getattr(cfg, "studio", None)
    flag = getattr(studio, "gcs_poster_bric", None) if studio is not None else None
    # Default on when flag object missing ``enabled`` (GcsPosterBricConfig.enabled=True).
    return bool(getattr(flag, "enabled", True))


def _screens_fingerprint(trip: dict[str, Any]) -> str:
    screens: list[Any] = []
    for ch in trip.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        for s in ch.get("screens") or []:
            screens.append(s)
    return json.dumps(screens, ensure_ascii=False, sort_keys=True, default=str)


def list_poster_photo_paths(trip_dir: Path, *, limit: int = MAX_N) -> list[Path]:
    """Kept image paths excluding mediaClass=collage; n capped at ``limit``."""
    trip_dir = Path(trip_dir)
    trip = _load_trip(trip_dir)
    assets_by_id = {
        str(a.get("id") or ""): a
        for a in (trip.get("assets") or [])
        if isinstance(a, dict) and str(a.get("id") or "").strip()
    }
    ordered_ids = _ordered_kept_ids(trip, assets_by_id)
    paths: list[Path] = []
    for aid in ordered_ids:
        if len(paths) >= limit:
            break
        asset = assets_by_id.get(aid)
        if not asset or not _is_kept_image(asset):
            continue
        if is_collage_asset(asset):
            continue
        resolved = _resolve_asset_image_path(asset, trip_dir)
        if resolved is not None and resolved.is_file():
            paths.append(resolved)
    return paths


def compose_poster_png(
    paths: list[Path],
    *,
    canvas_wh: tuple[int, int] | None = None,
    width: int | None = None,
    border: int = BORDER,
    spacing: int = SPACING,
    bg: tuple[int, int, int] = CANVAS_BG,
) -> tuple[bytes, dict[str, Any]]:
    """Contain-paste photos onto fixed A4 (or ``canvas_wh``) via compose_fixed_canvas."""
    if not (MIN_N <= len(paths) <= MAX_N):
        raise LongshotExportError(
            "E_GCS_POSTER_N",
            f"单屏海报需要 {MIN_N}–{MAX_N} 张图，当前 {len(paths)} 张",
        )

    if canvas_wh is None:
        if width is not None:
            # Legacy width-only callers: keep A4 aspect, scale height to match width.
            w = max(64, int(width))
            h = max(64, int(round(w * A4_CANVAS[1] / A4_CANVAS[0])))
            canvas_wh = (w, h)
        else:
            canvas_wh = A4_CANVAS

    png_bytes, diag = compose_fixed_canvas(
        paths,
        canvas_wh=canvas_wh,
        border=border,
        spacing=spacing,
        bg=bg,
    )
    diag = {
        **diag,
        "exportSurface": "poster_bric",
        "composer": "shelf_packer_v1",
    }
    return png_bytes, diag


def export_poster_bric_pack(
    trip_dir: Path,
    *,
    scale: int = 2,
    fmt: str = "png",
    progress: ProgressFn | None = None,
    platform: str = "poster_bric",
    cfg: Any | None = None,
) -> LongshotExportResult:
    if platform != "poster_bric":
        raise LongshotExportError(
            "E_LNG2_INVALID_PLATFORM",
            f"poster_bric 仅支持 platform=poster_bric，收到「{platform}」",
        )
    if not gcs_poster_bric_enabled(cfg):
        raise LongshotExportError(
            "E_GCS_POSTER_DISABLED",
            "单屏海报未开启（features.gcs_poster_bric.enabled=false）",
        )

    trip_dir = Path(trip_dir).resolve()
    trip = _load_trip(trip_dir)
    screens_before = _screens_fingerprint(trip)

    paths = list_poster_photo_paths(trip_dir, limit=MAX_N)
    n = len(paths)
    if n < MIN_N:
        raise LongshotExportError(
            "E_GCS_POSTER_N",
            f"单屏海报至少需要 {MIN_N} 张精选照片（已排除拼贴资产），当前 {n} 张",
        )

    if progress:
        progress(0, 1, "单屏海报构图")

    canvas_wh = canvas_for_platform("poster_bric", scale=scale)
    png_bytes, diag = compose_poster_png(paths, canvas_wh=canvas_wh)

    title = _trip_title(trip_dir)
    prefix = file_prefix_for_platform(title, "poster_bric")
    profile = get_profile("poster_bric")
    # BE-DFX-21 · poster always PNG (ignore job jpeg default / capacity fallback)
    _ = fmt
    out_ext = "png"
    writer = PlatformExportWriter(trip_dir, prefix, ext=out_ext, single_file=True)

    try:
        with writer:
            data = png_bytes
            writer.write(1, data)
            finals = writer.commit()
        if progress:
            progress(1, 1, "单屏海报完成")
    except LongshotExportError:
        writer.rollback()
        raise
    except Exception as exc:
        writer.rollback()
        _log.exception("poster_bric export failed")
        raise LongshotExportError(
            "E_GCS_POSTER_FAILED",
            f"单屏海报导出失败: {exc}",
        ) from exc

    # Sidecar diagnostic (not screens[])
    try:
        runs = trip_dir / "runs"
        runs.mkdir(parents=True, exist_ok=True)
        (runs / "gcs-poster-bric.json").write_text(
            json.dumps(diag, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        _log.debug("poster_bric sidecar write skipped", exc_info=True)

    trip_after = _load_trip(trip_dir)
    if screens_before != _screens_fingerprint(trip_after):
        raise LongshotExportError(
            "E_GCS_POSTER_SCREENS",
            "单屏海报不得改写 screens[]（检测到 trip 屏结构变化）",
        )

    guide = (profile.publish_guide or "").strip()
    outputs = [
        LongshotOutput(path=path, capture_method="poster_bric") for path in finals
    ]
    return LongshotExportResult(
        outputs=outputs,
        capture_method="poster_bric",
        title=_slug_title(title),
        segmented=False,
        segment_reason="poster_bric",
        user_hint="A4 单屏海报已生成（一张竖版拼贴画布）",
        platform="poster_bric",
        profile_label=profile.label,
        target_page_count=1,
        publish_guide=guide,
        page_count=len(outputs),
        output_format="png",
    )
