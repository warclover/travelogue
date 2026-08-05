"""GCS Track B · poster_bric Writer (TPC W4).

Single 3:4 Card export (PRD-EXPORT-CARD-COMPOSE-V1 §5.2 / ADR-021 v0.4).
Selects a "representative" photo pool via ``cover_scoring_v2.cover_score_v2``
(BLK-ECC-01), picks a poster template per §5.2 priority (prefer templates with
a ``main`` slot / low crop loss), and renders via CardRenderer. Does not write
trip.json screens[]. Requires
features.gcs_poster_bric / studio.gcs_poster_bric.enabled (default on).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from travelogue.curation.cover_scoring_v2 import cover_score_v2
from travelogue.export.card_grouper import plan_poster_card
from travelogue.export.card_renderer import CARD_CANVAS, render_card, scale_canvas
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

#: At least 1 non-collage kept photo — card-1-full-frame covers the
#: minimal case (a single big photo *is* a valid poster per §5.2).
MIN_N = 1
#: Safety cap on how many kept photos are considered for cover_score_v2
#: ranking (largest template only ever consumes 6; this just bounds scoring
#: cost on very large trips).
RANK_POOL_LIMIT = 24


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


def _poster_candidate_pairs(
    trip_dir: Path, *, limit: int
) -> list[tuple[Path, dict[str, Any]]]:
    """Kept image (path, asset) pairs excluding mediaClass=collage, capped at
    ``limit``, in the trip's existing kept-photo order."""
    trip_dir = Path(trip_dir)
    trip = _load_trip(trip_dir)
    assets_by_id = {
        str(a.get("id") or ""): a
        for a in (trip.get("assets") or [])
        if isinstance(a, dict) and str(a.get("id") or "").strip()
    }
    ordered_ids = _ordered_kept_ids(trip, assets_by_id)
    pairs: list[tuple[Path, dict[str, Any]]] = []
    for aid in ordered_ids:
        if len(pairs) >= limit:
            break
        asset = assets_by_id.get(aid)
        if not asset or not _is_kept_image(asset):
            continue
        if is_collage_asset(asset):
            continue
        resolved = _resolve_asset_image_path(asset, trip_dir)
        if resolved is not None and resolved.is_file():
            pairs.append((resolved, asset))
    return pairs


def list_poster_photo_paths(trip_dir: Path, *, limit: int = RANK_POOL_LIMIT) -> list[Path]:
    """Kept image paths excluding mediaClass=collage; n capped at ``limit``."""
    return [path for path, _ in _poster_candidate_pairs(trip_dir, limit=limit)]


def _rank_by_cover_score(pairs: list[tuple[Path, dict[str, Any]]]) -> list[Path]:
    """§5.2 「代表性精选」: rank candidates via ``cover_score_v2`` (best-first).

    BLK-ECC-01 (2026-08-05 评审): uses ``cover_scoring_v2.cover_score_v2``,
    *not* ``DEFAULT_FEATURED_WEIGHT`` (that constant is an in-screen hero
    selection weight, not a trip-wide representative-photo signal).
    ``export_layout="mobile"`` biases toward the trip's primary consumption
    surface; exact weight formula is deferred to OQ-ECC-01.
    """
    pool = [asset for _, asset in pairs]
    scored: list[tuple[float, Path]] = []
    for path, asset in pairs:
        try:
            score = cover_score_v2(asset, "mobile", pool=pool)
        except Exception:
            _log.debug("cover_score_v2 failed for %s", path, exc_info=True)
            score = 0.0
        scored.append((score, path))
    scored.sort(key=lambda item: -item[0])  # stable: ties keep original order
    return [path for _, path in scored]


def compose_poster_png(
    paths: list[Path],
    *,
    asset_lookup: Any | None = None,
    canvas_wh: tuple[int, int] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    """Pick a poster Card template for ``paths`` (best-first ranked) and
    render it via CardRenderer. ``paths`` beyond the chosen template's slot
    count are ignored (caller should already have ranked/truncated)."""
    if not paths:
        raise LongshotExportError(
            "E_GCS_POSTER_N",
            f"单屏海报至少需要 {MIN_N} 张精选照片，当前 0 张",
        )
    plan = plan_poster_card(paths)
    png_bytes, diag = render_card(
        list(plan.photos),
        plan.template,
        canvas_wh=canvas_wh or CARD_CANVAS,
        asset_lookup=asset_lookup,
    )
    diag = {
        **diag,
        "exportSurface": "poster_bric",
        "composer": "card_renderer_v1",
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

    pairs = _poster_candidate_pairs(trip_dir, limit=RANK_POOL_LIMIT)
    n = len(pairs)
    if n < MIN_N:
        raise LongshotExportError(
            "E_GCS_POSTER_N",
            f"单屏海报至少需要 {MIN_N} 张精选照片（已排除拼贴资产），当前 {n} 张",
        )

    if progress:
        progress(0, 1, "单屏海报选图")

    path_to_asset = dict(pairs)
    ranked_paths = _rank_by_cover_score(pairs)

    if progress:
        progress(0, 1, "单屏海报构图")

    canvas_wh = scale_canvas(CARD_CANVAS, scale)
    png_bytes, diag = compose_poster_png(
        ranked_paths, asset_lookup=path_to_asset.get, canvas_wh=canvas_wh
    )

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
        user_hint=f"单屏海报已生成（3:4 竖版拼贴卡片 · {diag.get('template', '')}）",
        platform="poster_bric",
        profile_label=profile.label,
        target_page_count=1,
        publish_guide=guide,
        page_count=len(outputs),
        output_format="png",
    )
