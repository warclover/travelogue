"""Studio import pipeline: album → preview (Phase 2 M8)."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from travelogue.config import AppConfig, app_config_scope, get_config
from travelogue.curation.curate import CurateError
from travelogue.demo.build import DemoError
from travelogue.media.ingest import (
    RAW_UNSUPPORTED_MESSAGE,
    IngestError,
    scan_image_paths,
)
from travelogue.orchestrator.run import run_trip
from travelogue.orchestrator.studio_hooks import StudioHooks
from travelogue.orchestrator.studio_profile import StudioProfile
from travelogue.runtime import AppContext
from travelogue.services.copy_subject import is_generic_place
from travelogue.services.trip import TripService, apply_intent, mark_render_bundle_current
from travelogue.services.trip_factory import create_trip
from travelogue.util.trip_slug import demo_trip_id_from_album
from travelogue.web.studio_config import resolve_studio_config
from travelogue.web.studio_jobs import ProgressCallback

_log = logging.getLogger(__name__)


@dataclass
class StudioPipelineResult:
    trip_id: str
    trip_dir: Path
    trip_json: Path
    preview_url: str
    photo_count: int
    cluster_notice: str = ""
    title: str = ""
    intent_line: str = ""
    featured_count: int = 0
    segment_count: int = 0
    g1_pending: bool = False
    sparse_g1_suppressed: bool = False
    tier_mode: str = "single"
    cull_user_line: str = ""
    cull_warn: str = ""
    template_feedback_kind: str = ""
    template_feedback_message: str = ""
    resolved_template_id: str = "visual-journal"
    import_mode: str = "quick_share"
    layout_density: str = "balanced"
    layout_density_effect: str = "ignored_quick"
    date_range_warn: str = ""
    photo_cull_enabled: bool = True
    layout_eligible_count: int = 0
    keep_near_duplicates: bool = False
    photo_keep_mode: str = "recommended"
    assets_written: int = 0
    media_warn: str = ""
    title_noise_fallback: bool = False
    # FirstSuccess 顶栏用真实封面图（非竖版 preview.jpg 封面卡）
    shelf_cover_rel_path: str = ""


def _parse_iso_date(raw: object) -> date | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _build_date_range_weak_hint(
    *,
    user_date_range: dict | None,
    inferred_start: str | None,
    inferred_end: str | None,
) -> str:
    if not isinstance(user_date_range, dict):
        return ""
    u_start = _parse_iso_date(user_date_range.get("start"))
    u_end = _parse_iso_date(user_date_range.get("end"))
    i_start = _parse_iso_date(inferred_start)
    i_end = _parse_iso_date(inferred_end)
    deltas: list[int] = []
    if u_start and i_start:
        deltas.append(abs((u_start - i_start).days))
    if u_end and i_end:
        deltas.append(abs((u_end - i_end).days))
    if not deltas:
        return ""
    if max(deltas) <= 365:
        return ""
    return "你填写的日期与照片时间差异较大，仍将按你填写的日期生成"


def _resolve_tier_mode(ingest_stats: dict) -> str:
    mode = ingest_stats.get("tier_mode") or ingest_stats.get("mode")
    return str(mode) if mode else "single"


def _apply_featured_detected_intent(trip: dict, ingest_stats: dict) -> str:
    tier_mode = _resolve_tier_mode(ingest_stats)
    featured_detected = tier_mode in ("auto", "explicit", "dual") or ingest_stats.get("mode") == "dual"
    existing_folders = dict((trip.get("intent") or {}).get("folders") or {})
    existing_folders["featuredDetected"] = bool(featured_detected)
    apply_intent(trip, folders=existing_folders)
    return tier_mode


def _path_within_album(raw: str, album_dir: Path) -> Path:
    """Resolve ``raw`` under ``album_dir``; reject absolute escape / ``..`` traversal."""
    album_root = album_dir.resolve()
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = album_root / candidate
    try:
        resolved = candidate.resolve()
        resolved.relative_to(album_root)
    except (OSError, ValueError) as exc:
        raise DemoError(
            "E_STUDIO_ALBUM_DENIED",
            f"E_STUDIO_ALBUM_DENIED: path outside album: {raw}",
        ) from exc
    return resolved


def _resolve_ingest_folder_paths(
    album_dir: Path,
    folder_overrides: dict[str, str],
) -> tuple[Path | None, Path | None]:
    featured_path: Path | None = None
    material_path: Path | None = None
    if folder_overrides.get("featuredDir"):
        featured_path = _path_within_album(folder_overrides["featuredDir"], album_dir)
    if folder_overrides.get("materialDir"):
        material_path = _path_within_album(folder_overrides["materialDir"], album_dir)
    return featured_path, material_path


def _sync_trip_from_disk(trip: dict, svc: TripService, trip_json: Path) -> None:
    loaded = svc.load(trip_json)
    trip.clear()
    trip.update(loaded)


def _raise_demo_from_ingest(exc: IngestError) -> None:
    """Map ingest failures onto Studio/DemoError while preserving user-facing codes.

    ``E_INGEST_TOO_FEW`` / ``E_INGEST_EMPTY`` must stay as-is for regular album
    imports so the homepage failure hint does not claim this was a demo album.
    Demo-only entry points (``demo/from_album``, ``demo/build``) still remap to
    ``E_DEMO_TOO_FEW`` themselves.
    """
    if exc.code == "E_INGEST_RAW_UNSUPPORTED":
        raise DemoError(exc.code, RAW_UNSUPPORTED_MESSAGE) from exc
    raise DemoError(exc.code, str(exc)) from exc


def _studio_post_curate(
    *,
    svc: TripService,
    app_ctx: AppContext,
    trip: dict,
    trip_json: Path,
    trip_root: Path,
    cfg: AppConfig,
    slug: str,
    host: str,
    port: int,
    title: str,
    photo_count: int,
    cluster_notice: str,
    tier_mode: str,
    date_payload: dict | None,
    import_mode: str,
    pipeline_timings: dict[str, float],
    report: ProgressCallback | Callable[[str, int, str | None], None],
    persist_trip_state: Callable[[], None],
    flush_pipeline_timings: Callable[[dict[str, float] | None], None],
    hooks: StudioHooks,
    force_stub: bool = False,
    media_warn: str = "",
) -> StudioPipelineResult:
    from travelogue.domain.sparse_g1 import resolve_g1_pending
    from travelogue.export.output_recipe.kept_n import count_kept_n

    # SFC W1 · D-SFC-07 · Sparse 快速分享默认不打断 G1
    kept_n = count_kept_n(trip)
    g1_pending, sparse_g1_suppressed = resolve_g1_pending(
        import_mode=import_mode,
        kept_n=kept_n,
        g1_confirm_structure=bool(cfg.studio.g1_confirm_structure),
    )
    if g1_pending:
        from travelogue.render.engine import render_trip_surfaces
        from travelogue.render.preview import render_preview_jpg
        from travelogue.services.pipeline_state import trip_status

        render_t0 = time.monotonic()
        render_trip_surfaces(
            trip_json,
            trip_root,
            export_mode="draft",
            validate=False,
            update_pipeline=False,
            cfg=cfg,
        )
        # Shelf / reveal still need preview.jpg while structure confirmation waits.
        render_preview_jpg(trip_json, trip_root=trip_root)
        pipeline_timings["renderMs"] = round((time.monotonic() - render_t0) * 1000.0, 2)
        flush_pipeline_timings()
        from travelogue.domain.stage_hints import LAYOUT_PREVIEW_READY, stage_hint_text

        trip.setdefault("pipeline", {})["derivativesStatus"] = "preview"
        mark_render_bundle_current(trip)
        persist_trip_state()
        report("render", 4, stage_hint_text(LAYOUT_PREVIEW_READY))
        trip_final = svc.load(trip_json)
        if trip_status(trip_final) != "structure_draft":
            g1_pending = False
        return _finalize_pipeline_result(
            svc=svc,
            trip_json=trip_json,
            trip_root=trip_root,
            slug=slug,
            host=host,
            port=port,
            title=title,
            photo_count=photo_count,
            cluster_notice=cluster_notice,
            tier_mode=tier_mode,
            user_date_range=date_payload,
            import_mode=import_mode,
            g1_pending=g1_pending,
            sparse_g1_suppressed=False,
            media_warn=media_warn,
        )

    from travelogue.web.studio_narrate import resolve_studio_narrate_provider

    narrate_provider = resolve_studio_narrate_provider(
        cfg=cfg, force_stub=bool(force_stub)
    )
    # BE-FST-01 · 进入文案/排版前显式推进 stage（产品四段）
    report("narrate", 3)
    try:
        # Single run_trip slice (align with continue_after_g1_confirm): lock → narrate → render.
        run_trip(
            trip_json,
            from_stage="lock_structure",
            until="rendered",
            skip_locked=True,
            narrate_provider=narrate_provider,
            validate=False,
            cfg=cfg,
            studio_hooks=hooks,
        )
        from travelogue.domain.stage_hints import EXPORT_READY, stage_hint_text
        from travelogue.render.preview import render_preview_jpg

        render_preview_jpg(trip_json, trip_root=trip_root)
        _sync_trip_from_disk(trip, svc, trip_json)
        trip.setdefault("pipeline", {})["derivativesStatus"] = "ready"
        flush_pipeline_timings()
        # Metadata-only persist after a fresh render must re-stamp the watermark;
        # otherwise revision > renderedRevision and preview false-flags「产物已过期」.
        mark_render_bundle_current(trip)
        persist_trip_state()
        report("render", 4, stage_hint_text(EXPORT_READY))
    except Exception as exc:
        code = getattr(exc, "code", "E_STUDIO_PIPELINE")
        # BE-03: never leave users in an auth dead-end; degrade once to stub.
        if code == "E_LLM_AUTH" and narrate_provider != "stub":
            _log.warning(
                "studio import narrate hit E_LLM_AUTH with provider=%s; degrading to stub",
                narrate_provider,
            )
            try:
                run_trip(
                    trip_json,
                    from_stage="narrate",
                    until="rendered",
                    skip_locked=True,
                    narrate_provider="stub",
                    validate=False,
                    cfg=cfg,
                    studio_hooks=hooks,
                )
                from travelogue.render.preview import render_preview_jpg

                render_preview_jpg(trip_json, trip_root=trip_root)
                _sync_trip_from_disk(trip, svc, trip_json)
                flush_pipeline_timings()
                mark_render_bundle_current(trip)
                persist_trip_state()
            except Exception as stub_exc:
                stub_code = getattr(stub_exc, "code", "E_STUDIO_PIPELINE")
                raise DemoError(stub_code, str(stub_exc)) from stub_exc
        else:
            raise DemoError(code, str(exc)) from exc

    return _finalize_pipeline_result(
        svc=app_ctx.trip_service(),
        trip_json=trip_json,
        trip_root=trip_root,
        slug=slug,
        host=host,
        port=port,
        title=title,
        photo_count=photo_count,
        cluster_notice=cluster_notice,
        tier_mode=tier_mode,
        user_date_range=date_payload,
        import_mode=import_mode,
        g1_pending=False,
        sparse_g1_suppressed=sparse_g1_suppressed,
        media_warn=media_warn,
    )


def _finalize_pipeline_result(
    *,
    svc: TripService,
    trip_json: Path,
    trip_root: Path,
    slug: str,
    host: str,
    port: int,
    title: str,
    photo_count: int,
    cluster_notice: str,
    tier_mode: str,
    user_date_range: dict | None = None,
    import_mode: str = "quick_share",
    layout_density: str = "balanced",
    g1_pending: bool = False,
    sparse_g1_suppressed: bool = False,
    media_warn: str = "",
) -> StudioPipelineResult:
    from travelogue.web.studio_intent_telemetry import write_studio_intent_telemetry

    trip_final = svc.load(trip_json)
    meta_final = trip_final.get("meta") or {}
    date_range_warn = _build_date_range_weak_hint(
        user_date_range=user_date_range,
        inferred_start=meta_final.get("dateStart"),
        inferred_end=meta_final.get("dateEnd"),
    )
    from travelogue.domain.share_face_purity import migrate_share_face_purity_on_open
    from travelogue.domain.title_humanize import (
        is_folder_title_noise,
        resolve_display_title,
    )

    # SFP D-SFP-12 · pipeline 收尾静默 migrate（脏 displayTitle / 序号腔章名）
    # BE-FST-06 · 目录名噪音 → 展示名（FirstSuccess / 书架 / 封面同源）
    raw_meta_title = str(meta_final.get("title") or title).strip()
    display_title = resolve_display_title(meta_final, raw_title=raw_meta_title)
    title_noise_fallback = is_folder_title_noise(raw_meta_title)
    from travelogue.curation.chapter_titles import is_ordinal_face_title
    from travelogue.domain.copy_origin import is_user_protected

    display_needs = str(meta_final.get("displayTitle") or "").strip() != display_title
    ordinal_needs = any(
        isinstance(ch, dict)
        and not (ch.get("curation") or {}).get("isAppendix")
        and is_ordinal_face_title(str(ch.get("title") or ""))
        and not is_user_protected(ch, "titleOrigin")
        for ch in (trip_final.get("chapters") or [])
    )
    # Probe full SFP migrate (incl. cross-year year prefix) without writing.
    from copy import deepcopy

    _sfp_probe = migrate_share_face_purity_on_open(deepcopy(trip_final))
    sfp_needs = bool(display_needs or ordinal_needs or _sfp_probe.get("changed"))
    if sfp_needs:

        def _sfp_pipeline_migrate(trip: dict) -> bool:
            result = migrate_share_face_purity_on_open(trip)
            meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
            resolved = resolve_display_title(
                meta, raw_title=str(meta.get("title") or title).strip()
            )
            if resolved and str(meta.get("displayTitle") or "").strip() != resolved:
                meta["displayTitle"] = resolved[:32]
                trip["meta"] = meta
            # Always re-stamp: TripService.update bumps revision; without a
            # watermark sync FirstSuccess false-flags「预览需更新」.
            mark_render_bundle_current(trip)
            return True

        svc.update(trip_json, _sfp_pipeline_migrate, touch_updated=False)
        trip_final = svc.load(trip_json)
        meta_final = trip_final.get("meta") or {}
        display_title = resolve_display_title(
            meta_final, raw_title=str(meta_final.get("title") or title).strip()
        )
    featured_n, segment_n = _trip_import_stats(trip_final)
    intent_line = _format_intent_line(display_title, featured_n, segment_n)
    curation = trip_final.get("curation") or {}
    cull_user_line = str(curation.get("cullUserLine") or "")
    cull_summary = curation.get("cullSummary") or {}
    cull_warn = str(cull_summary.get("warnMessage") or "") if cull_summary.get("maxPhotosExceeded") else ""
    intent = trip_final.get("intent") or {}
    from travelogue.domain.photo_keep_mode import resolve_photo_keep_prefs

    keep_resolved = resolve_photo_keep_prefs(
        photo_keep_mode=intent.get("photoKeepMode"),
        photo_cull_enabled=bool(intent.get("photoCullEnabled", True)),
        keep_near_duplicates=bool(intent.get("keepNearDuplicates", False)),
    )
    photo_cull_enabled = keep_resolved.photo_cull_enabled
    keep_near_duplicates = keep_resolved.keep_near_duplicates
    photo_keep_mode = keep_resolved.mode
    assets_written = len(trip_final.get("assets") or [])
    layout_eligible_count = int(
        cull_summary.get("finalLayoutEligibleCount")
        or cull_summary.get("layoutEligibleCount")
        or photo_count
    )
    from travelogue.templating.router import template_user_feedback

    sel = trip_final.get("templateSelection") or {}
    tfb = template_user_feedback(sel)
    layout_density = _resolve_stored_layout_density(trip_final, import_mode=import_mode)
    from travelogue.curation.layout_density import layout_density_effect as _layout_effect

    density_effect = _layout_effect(
        photo_count,
        layout_density,
        import_mode=import_mode,
    )
    write_studio_intent_telemetry(
        trip_final,
        trip_root,
        tier_mode=tier_mode,
        g1_pending=g1_pending,
        g1_confirmed=not g1_pending and (trip_final.get("pipeline") or {}).get("status")
        not in (None, "structure_draft"),
        import_mode=import_mode,
        layout_density=layout_density,
    )
    preview_url = f"http://{host}:{port}/{slug}/index.html"
    from travelogue.web.studio_trips import _pick_shelf_cover_rel

    shelf_cover_rel = _pick_shelf_cover_rel(trip_root, trip_final) or ""
    # FirstSuccess 只要照片本身；竖版 preview.jpg 封面卡（含标题）不进顶栏
    if shelf_cover_rel.replace("\\", "/").rsplit("/", 1)[-1] == "preview.jpg":
        shelf_cover_rel = ""
    return StudioPipelineResult(
        trip_id=slug,
        trip_dir=trip_root,
        trip_json=trip_json,
        preview_url=preview_url,
        photo_count=photo_count,
        cluster_notice=cluster_notice,
        title=display_title,
        intent_line=intent_line,
        featured_count=featured_n,
        segment_count=segment_n,
        g1_pending=g1_pending,
        sparse_g1_suppressed=sparse_g1_suppressed,
        tier_mode=tier_mode,
        cull_user_line=cull_user_line,
        cull_warn=cull_warn,
        template_feedback_kind=tfb.get("kind", ""),
        template_feedback_message=tfb.get("message", ""),
        resolved_template_id=str(sel.get("resolvedTemplateId") or "visual-journal"),
        import_mode=import_mode,
        layout_density=layout_density,
        layout_density_effect=density_effect,
        date_range_warn=date_range_warn,
        photo_cull_enabled=photo_cull_enabled,
        layout_eligible_count=layout_eligible_count,
        keep_near_duplicates=keep_near_duplicates,
        photo_keep_mode=photo_keep_mode,
        assets_written=assets_written,
        media_warn=media_warn or "",
        title_noise_fallback=title_noise_fallback,
        shelf_cover_rel_path=shelf_cover_rel,
    )


def _resolve_stored_layout_density(trip: dict, *, import_mode: str) -> str:
    from travelogue.curation.layout_density import normalize_layout_density

    if str(import_mode or "quick_share").strip().lower() != "fine_craft":
        return "balanced"
    intent = trip.get("intent") or {}
    return normalize_layout_density(intent.get("layoutDensity"))


def _trip_import_stats(trip: dict) -> tuple[int, int]:
    assets = trip.get("assets") or []
    featured = sum(1 for a in assets if a.get("userTier") == "featured")
    clustering = (trip.get("curation") or {}).get("clustering") or {}
    segments = clustering.get("segments") or []
    return featured, len(segments)


def _format_intent_line(title: str, featured: int, segments: int) -> str:
    label = (title or "我的旅途").strip()[:20] or "我的旅途"
    parts = [f"《{label}》"]
    if featured > 0:
        parts.append(f"精选 {featured} 张")
    if segments > 0:
        parts.append(f"行程 {segments} 段")
    return " · ".join(parts)


def count_album_photos(album_dir: Path, *, max_photos: int = 250) -> int:
    paths, _ = scan_image_paths(album_dir, max_photos=max_photos)
    return len(paths)


def _even_sample_indices(total: int, count: int) -> list[int]:
    if total <= 0:
        return []
    if total <= count:
        return list(range(total))
    if count <= 1:
        return [0]
    step = (total - 1) / (count - 1)
    return [min(total - 1, round(i * step)) for i in range(count)]


# PRD-IMPORT-SHEET-v3-WIZARD §7 BE-02 · 超过此候选文件数时，验货预览跳过精确
# EXIF 排序扫描（成本随候选数线性增长），改为降级：只做轻量计数 + 文件名序抽样，
# 避免大相册（>2000 张）阻塞 Step 2 一屏渲染。真实导入 pipeline 不受影响。
ALBUM_PREVIEW_FAST_DEGRADE_THRESHOLD = 800
MAX_ALBUM_PREVIEW_THUMBS = 6


def _fast_candidate_paths(album_dir: Path) -> list[Path]:
    """Extension-only scan，不打开图片，仅用于预估候选数量与降级抽样。"""
    from travelogue.media.ingest import HEIC_SUFFIXES, IMAGE_SUFFIXES

    candidates: list[Path] = []
    for path in album_dir.rglob("*"):
        if not path.is_file():
            continue
        suf = path.suffix.lower()
        if suf in IMAGE_SUFFIXES or suf in HEIC_SUFFIXES:
            candidates.append(path)
    return candidates


def list_album_preview_candidates(album_dir: Path) -> list[Path]:
    """Shared candidate list for thumbs + date-range preview (one rglob)."""
    try:
        return _fast_candidate_paths(album_dir)
    except OSError:
        return []


def _render_thumb_data_url(path: Path, thumb_px: int) -> str | None:
    import base64
    from io import BytesIO

    from travelogue.media.image_ops import load_image_normalized

    try:
        loaded = load_image_normalized(path)
        img = loaded.image
        img.thumbnail((thumb_px, thumb_px))
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=78)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        return None


def _peek_photo_datetime(path: Path):
    """Lightweight taken-at for preview prefill (EXIF/filename/mtime; no RGB decode)."""
    from datetime import datetime

    from PIL import Image

    from travelogue.media.image_ops import resolve_photo_datetime

    try:
        with Image.open(path) as img:
            taken_at, _source = resolve_photo_datetime(path, img)
            return taken_at
    except Exception:
        try:
            return datetime.fromtimestamp(path.stat().st_mtime)
        except OSError:
            return None


def _mtime_sample_paths(candidates: list[Path]) -> list[Path]:
    """Pick earliest / latest / mid by mtime without a full sort copy when large."""
    if not candidates:
        return []
    if len(candidates) <= 64:
        try:
            by_mtime = sorted(candidates, key=lambda p: p.stat().st_mtime)
        except OSError:
            return candidates[:1]
        sample = [by_mtime[0]]
        if len(by_mtime) > 1:
            sample.append(by_mtime[-1])
        if len(by_mtime) > 4:
            mid = by_mtime[len(by_mtime) // 2]
            if mid not in sample:
                sample.append(mid)
        return sample

    earliest = latest = None
    earliest_t = latest_t = None
    mid = candidates[len(candidates) // 2]
    for path in candidates:
        try:
            t = path.stat().st_mtime
        except OSError:
            continue
        if earliest is None or t < earliest_t:
            earliest, earliest_t = path, t
        if latest is None or t > latest_t:
            latest, latest_t = path, t
    sample: list[Path] = []
    if earliest is not None:
        sample.append(earliest)
    if latest is not None and latest not in sample:
        sample.append(latest)
    if mid not in sample:
        sample.append(mid)
    return sample


def infer_album_preview_date_range(
    album_dir: Path,
    *,
    budget_s: float = 1.0,
    candidates: list[Path] | None = None,
) -> tuple[str | None, str | None]:
    """Best-effort ISO date range for Wizard 2b prefill (A1-07).

    Budget-capped and decode-light: peek EXIF/filename/mtime on a few extremes.
    Pass ``candidates`` from a shared scan to avoid a second ``rglob``.
    On timeout/failure returns ``(None, None)``.
    """
    from datetime import datetime

    started = time.monotonic()
    if candidates is None:
        try:
            candidates = _fast_candidate_paths(album_dir)
        except OSError:
            return None, None
    if not candidates:
        return None, None

    sample = _mtime_sample_paths(candidates)
    if not sample:
        return None, None

    taken: list[datetime] = []
    for path in sample:
        if time.monotonic() - started > budget_s:
            break
        peeked = _peek_photo_datetime(path)
        if peeked is not None:
            taken.append(peeked)

    if not taken:
        try:
            times = []
            for path in sample[:2]:
                times.append(datetime.fromtimestamp(path.stat().st_mtime))
            taken = times
        except OSError:
            return None, None

    if not taken:
        return None, None
    start_d = min(taken).date().isoformat()
    end_d = max(taken).date().isoformat()
    return start_d, end_d


def sample_album_preview_thumbs(
    album_dir: Path,
    *,
    count: int = 4,
    thumb_px: int = 112,
    max_photos: int = 250,
    candidates: list[Path] | None = None,
) -> tuple[list[str], int, list[str]]:
    """Return JPEG data-URL thumbs evenly sampled from *album_dir*.

    大相册降级（BE-02）：候选文件数超过 `ALBUM_PREVIEW_FAST_DEGRADE_THRESHOLD` 时，
    跳过逐张打开做 EXIF 排序的精确扫描，改为按文件名序抽样，photo_count 为快速
    候选计数（近似值，仅用于验货文案，不影响真实导入的精确统计口径）。

    Pass ``candidates`` from a shared scan to avoid a second ``rglob``.

    Returns ``(thumbs, photo_count, thumb_names)``.
    """
    count = max(1, min(int(count or count), MAX_ALBUM_PREVIEW_THUMBS))

    if candidates is None:
        try:
            fast_candidates = _fast_candidate_paths(album_dir)
        except OSError:
            return [], 0, []
    else:
        fast_candidates = list(candidates)

    if not fast_candidates:
        return [], 0, []

    if len(fast_candidates) > ALBUM_PREVIEW_FAST_DEGRADE_THRESHOLD:
        fast_candidates.sort(key=lambda p: str(p).lower())
        photo_count = len(fast_candidates)
        thumbs: list[str] = []
        names: list[str] = []
        for idx in _even_sample_indices(photo_count, count):
            path = fast_candidates[idx]
            url = _render_thumb_data_url(path, thumb_px)
            if url:
                thumbs.append(url)
                names.append(path.name)
        return thumbs, photo_count, names

    try:
        paths, _stats = scan_image_paths(album_dir, max_photos=max_photos)
    except IngestError:
        return [], 0, []

    photo_count = len(paths)
    if not paths:
        return [], 0, []

    thumbs = []
    names = []
    for idx in _even_sample_indices(len(paths), count):
        path = paths[idx]
        url = _render_thumb_data_url(path, thumb_px)
        if url:
            thumbs.append(url)
            names.append(path.name)
    return thumbs, photo_count, names

def resolve_studio_trip_dir(
    album_dir: Path,
    *,
    trips_dir: Path,
    title: str = "我的旅途",
    place: str = "旅途",
    trip_id: str | None = None,
) -> tuple[str, Path]:
    slug = demo_trip_id_from_album(
        album_dir, title=title, place=place, explicit=trip_id
    )
    return slug, trips_dir / slug


def assert_album_importable(
    album_dir: Path,
    *,
    trips_dir: Path,
    title: str = "我的旅途",
    place: str = "旅途",
    trip_id: str | None = None,
    force: bool = False,
) -> str:
    album_dir = album_dir.resolve()
    if not album_dir.is_dir():
        raise DemoError("E_DEMO_NOT_DIR", f"not a directory: {album_dir}")
    slug, trip_dir = resolve_studio_trip_dir(
        album_dir,
        trips_dir=trips_dir,
        title=title,
        place=place,
        trip_id=trip_id,
    )
    if trip_dir.exists() and any(trip_dir.iterdir()) and not force:
        raise DemoError(
            "E_DEMO_EXISTS",
            f"trip already exists: {trip_dir} (use force to replace)",
        )
    return slug


def run_studio_pipeline(
    album_dir: Path,
    *,
    trips_dir: Path | None = None,
    trip_id: str | None = None,
    title: str = "我的旅途",
    place: str = "旅途",
    place_user_set: bool | None = None,
    force: bool = False,
    dedupe: bool = True,
    host: str = "127.0.0.1",
    port: int = 8766,
    config: Path | None = None,
    app_config: AppConfig | None = None,
    progress: ProgressCallback | None = None,
    mode: str = "quick_share",
    user_notes: str | None = None,
    travel_notes: str | None = None,
    date_range: dict | None = None,
    plan_bytes: bytes | None = None,
    plan_text: str | None = None,
    plan_filename: str = "plan.txt",
    template_mode: str = "smart",
    template_id: str | None = None,
    featured_dir: str | Path | None = None,
    material_dir: str | Path | None = None,
    layout_density: str | None = None,
    photo_cull_enabled: bool = True,
    keep_near_duplicates: bool = False,
    photo_keep_mode: str | None = None,
    stop_after: str = "full",
    force_stub: bool = False,
) -> StudioPipelineResult:
    from travelogue.domain.photo_keep_mode import resolve_photo_keep_prefs

    keep_prefs = resolve_photo_keep_prefs(
        photo_keep_mode=photo_keep_mode,
        photo_cull_enabled=photo_cull_enabled,
        keep_near_duplicates=keep_near_duplicates,
    )
    photo_cull_enabled = keep_prefs.photo_cull_enabled
    keep_near_duplicates = keep_prefs.keep_near_duplicates
    # 仅显式 mode 落盘 keep_all；兼容路径不写 keep_all
    resolved_photo_keep_mode = (
        keep_prefs.mode if photo_keep_mode else None
    )

    album_dir = album_dir.resolve()
    cfg_path = resolve_studio_config(config)
    if cfg_path:
        get_config(reload=True, path=cfg_path)
    cfg = app_config or get_config()
    trips_root = trips_dir or cfg.trips_dir

    slug = assert_album_importable(
        album_dir,
        trips_dir=trips_root,
        title=title,
        place=place,
        trip_id=trip_id,
        force=force,
    )
    trip_dir = trips_root / slug

    if force and trip_dir.exists():
        # CQA I-CQA-08 · tombstone path (HTTP force pre-clears; CLI uses same helper)
        from travelogue.web.studio_trip_delete import clear_trip_dir_via_tombstone

        clear_trip_dir_via_tombstone(trip_dir)

    try:
        photo_count = count_album_photos(album_dir, max_photos=cfg.ingest.max_photos)
    except IngestError as exc:
        # The early photo precheck shares the RAW gate with full ingest, so it can
        # surface E_INGEST_RAW_UNSUPPORTED before the ingest stage's handler below.
        # Translate here too, otherwise it leaks as a generic E_STUDIO_PIPELINE
        # ("导入失败，请重试") instead of the actionable RAW / too-few guidance.
        # Keep E_INGEST_TOO_FEW / E_INGEST_EMPTY codes (do not remap to E_DEMO_*).
        _raise_demo_from_ingest(exc)

    if cfg.vision.preload_on_folder_pick and cfg.vision.enabled != "false":
        if progress:
            from travelogue.domain.stage_hints import (
                VISION_WARMUP,
                maybe_sleep_vision_warmup_inject,
                stage_hint_text,
            )

            # SFC W0 · D-SFC-04 · 识图准备为一等阶段（禁双空）
            progress("vision_warmup", 0, stage_hint_text(VISION_WARMUP))
            # AC-SFC-04 / BLK-06 · 测试可注入延长，保证 UI 能看见主句
            maybe_sleep_vision_warmup_inject()
        from travelogue.vision.clip_encoder import preload_clip_encoder

        preload_clip_encoder(cfg)

    from travelogue.orchestrator.throughput_precheck import emit_throughput_precheck_warnings

    for warn in emit_throughput_precheck_warnings(cfg):
        if progress:
            progress("ingest", 0, warn)

    pipeline_timings: dict[str, float] = {}
    pipeline_t0 = time.monotonic()

    def _flush_pipeline_timings(extra: dict[str, float] | None = None) -> None:
        if extra:
            pipeline_timings.update(extra)
        from travelogue.domain.pipeline_view import (
            absorb_pipeline_timing_keys,
            set_pipeline_timings,
        )

        # PRD-PIPELINE-PERF-V1 · MF-07: same merge as orchestrator.run.flush_timings.
        absorb_pipeline_timing_keys(trip, pipeline_timings)
        pipeline_timings["totalMs"] = round((time.monotonic() - pipeline_t0) * 1000.0, 2)
        set_pipeline_timings(trip, pipeline_timings)

    def report(stage: str, index: int, hint: str | None = None) -> None:
        if progress:
            progress(stage, index, hint or "")
        time.sleep(0)

    from travelogue.curation.photo_cull import format_ingest_progress_hint

    def ingest_progress(cur: int, total: int) -> None:
        report(
            "ingest",
            1,
            format_ingest_progress_hint(
                cur,
                total,
                cull_enabled=photo_cull_enabled,
            ),
        )

    def cull_progress_hint(hint: str) -> None:
        report("ingest", 1, hint)

    with app_config_scope(cfg):
        from travelogue.domain.stage_hints import PROCESSING_PHOTOS, stage_hint_text

        report("ingest", 1, stage_hint_text(PROCESSING_PHOTOS))
        cluster_notice = ""
        import_mode = str(mode or "quick_share").strip().lower()
        if import_mode not in ("quick_share", "fine_craft"):
            import_mode = "quick_share"
        mode = "manual" if str(template_mode).strip().lower() == "manual" else "smart"
        trip_json = create_trip(
            slug,
            trips_root,
            title=title,
            place=place,
            export_layout="auto",
            template_mode=mode,  # type: ignore[arg-type]
            template_id=template_id,
            cfg=cfg,
        )
        trip_root = trip_json.parent
        app_ctx = AppContext(cfg=cfg, trips_root=trips_root.resolve())
        svc = app_ctx.trip_service()
        trip = svc.load(trip_json)

        def _persist_trip_state() -> None:
            """Incremental pipeline persist — never full-trip overwrite (ADR-008 §9)."""
            from travelogue.media.ingest_persist import make_pipeline_persist_mutator

            svc.update(trip_json, make_pipeline_persist_mutator(trip))

        trip_rollout_id = str(trip.get("tripId") or slug).strip()
        if trip_rollout_id:
            from travelogue.curation.phase6_rollout import resolve_app_config_for_trip

            cfg = resolve_app_config_for_trip(cfg, trip_rollout_id)
            from travelogue.layout_engine.rollout import resolve_lse_config_for_trip

            cfg = resolve_lse_config_for_trip(cfg, trip_rollout_id)
        # PRD-P9-F2: keep near-duplicates → skip ingest burst/pHash dedupe for this
        # trip only (MD5 exact dedupe unaffected). Override the resolved ingest config
        # after rollout resolution so it is not clobbered; global config untouched.
        if keep_near_duplicates:
            from dataclasses import replace

            cfg = replace(
                cfg,
                ingest=replace(cfg.ingest, dedupe_burst=False, dedupe_phash=False),
            )
        # F-P4 M15: single-writer intent — mirrors meta.title/places + trip.userNotes
        # (never meta.userNotes, which is not in schema).
        place_raw = str(place or "").strip()
        resolved_place_user_set = (
            bool(place_user_set)
            if place_user_set is not None
            else bool(place_raw) and not is_generic_place(place_raw)
        )
        folder_overrides: dict[str, str] = {}
        if featured_dir:
            raw = str(featured_dir).strip()
            if raw:
                folder_overrides["featuredDir"] = raw
        if material_dir:
            raw = str(material_dir).strip()
            if raw:
                folder_overrides["materialDir"] = raw
        date_payload = date_range if isinstance(date_range, dict) else None
        intent_kwargs: dict = {
            "title": title,
            "places": [place_raw] if resolved_place_user_set else [],
            "places_user_set": resolved_place_user_set,
            "user_notes": user_notes,
            "travel_notes": travel_notes,
            "date_range": date_payload,
            "folders": folder_overrides if folder_overrides else None,
        }
        from travelogue.curation.layout_density import resolve_import_layout_density

        intent_kwargs["layout_density"] = resolve_import_layout_density(
            layout_density,
            import_mode=import_mode,
            app_cfg=cfg,
        )
        intent_kwargs["photo_cull_enabled"] = bool(photo_cull_enabled)
        intent_kwargs["keep_near_duplicates"] = bool(keep_near_duplicates)
        if resolved_photo_keep_mode:
            intent_kwargs["photo_keep_mode"] = resolved_photo_keep_mode
        apply_intent(trip, **intent_kwargs)
        # Flush intent before ingest so mid-ingest merge never needs to push it,
        # and concurrent HTTP PATCH can CAS against a real disk revision.
        from travelogue.media.ingest_persist import make_intent_flush_mutator

        svc.update(trip_json, make_intent_flush_mutator(trip))

        if plan_bytes is not None or plan_text:
            from travelogue.services.intent_plan import ingest_travel_plan

            ingest_travel_plan(
                trip,
                trip_root,
                raw_bytes=plan_bytes,
                raw_text=plan_text,
                filename=plan_filename,
            )
            # Persist travelPlan / planCities before ingest sync-from-disk.
            svc.update(trip_json, make_intent_flush_mutator(trip))

        featured_path, material_path = _resolve_ingest_folder_paths(album_dir, folder_overrides)

        def persist_partial_ingest() -> None:
            """Incremental merge during ingest (D-PT-03 / ADR-008 §9)."""
            from travelogue.media.ingest_persist import make_ingest_merge_mutator

            svc.update(
                trip_json,
                make_ingest_merge_mutator(trip),
                bump_revision=False,
            )

        post_curate_kwargs = {
            "svc": svc,
            "app_ctx": app_ctx,
            "trip": trip,
            "trip_json": trip_json,
            "trip_root": trip_root,
            "cfg": cfg,
            "slug": slug,
            "host": host,
            "port": port,
            "title": title,
            "photo_count": photo_count,
            "date_payload": date_payload,
            "import_mode": import_mode,
            "pipeline_timings": pipeline_timings,
            "report": report,
            "persist_trip_state": _persist_trip_state,
            "flush_pipeline_timings": _flush_pipeline_timings,
            "force_stub": bool(force_stub),
        }

        ingest_stats_holder: dict = {}
        cluster_notice = ""
        media_warn = ""

        def capture_ingest_stats(stats: dict) -> None:
            nonlocal media_warn
            ingest_stats_holder.update(stats)
            code = str(stats.get("errorCode") or stats.get("error") or "")
            if code == "E_MEDIA_INCREMENTAL_SOURCE":
                from travelogue.web.studio_errors import user_message

                missing_n = len(stats.get("incremental_source_missing") or [])
                base = user_message("E_MEDIA_INCREMENTAL_SOURCE")
                media_warn = (
                    f"{base}（{missing_n} 张）" if missing_n else base
                )

        def capture_cluster_notice(notice: str) -> None:
            nonlocal cluster_notice
            cluster_notice = notice

        profile = StudioProfile.studio_default()
        profile.ingest.featured_dir = featured_path
        profile.ingest.material_dir = material_path
        profile.ingest.max_photos = cfg.ingest.max_photos
        profile.ingest.on_progress = ingest_progress if progress else None
        profile.ingest.on_cull_hint = cull_progress_hint if progress else None
        profile.ingest.on_persist = persist_partial_ingest
        profile.ingest.use_parallel_embed = bool(
            cfg.pipeline.parallel_embed and cfg.vision.enabled != "false"
        )
        profile.ingest.on_complete = capture_ingest_stats

        hooks = StudioHooks(
            on_stage=report,
            on_timing=lambda timings: pipeline_timings.update(timings),
            on_clustering_done=capture_cluster_notice,
        )
        post_curate_kwargs["hooks"] = hooks

        try:
            run_trip(
                trip_json,
                from_stage="ingest",
                until="ingest",
                album_dir=album_dir,
                dedupe=dedupe,
                validate=False,
                cfg=cfg,
                studio_profile=profile,
                studio_hooks=hooks,
            )
        except IngestError as exc:
            _raise_demo_from_ingest(exc)

        _sync_trip_from_disk(trip, svc, trip_json)
        tier_mode = _apply_featured_detected_intent(trip, ingest_stats_holder)
        # D-QH-02: folders.featuredDetected must survive disk-intent-wins persist.
        from travelogue.media.ingest_persist import make_intent_folders_merge_mutator

        svc.update(trip_json, make_intent_folders_merge_mutator(trip))
        _persist_trip_state()

        # BE-FST-01 · ingest 结束后立刻切 curate，避免前端长期停在「已处理 N/N」
        report("curate", 2)

        try:
            run_trip(
                trip_json,
                from_stage="clustering",
                until="structure",
                dedupe=dedupe,
                validate=False,
                cfg=cfg,
                studio_profile=profile,
                studio_hooks=hooks,
            )
        except CurateError as exc:
            raise DemoError(exc.code, str(exc)) from exc

        _sync_trip_from_disk(trip, svc, trip_json)
        # embedMs / clusterMs / ingestMs already flushed via StudioHooks.on_timing
        _flush_pipeline_timings()
        _persist_trip_state()

        if stop_after == "structure":
            return _finalize_pipeline_result(
                svc=svc,
                trip_json=trip_json,
                trip_root=trip_root,
                slug=slug,
                host=host,
                port=port,
                title=title,
                photo_count=photo_count,
                cluster_notice=cluster_notice,
                tier_mode=tier_mode,
                user_date_range=date_payload,
                import_mode=import_mode,
                g1_pending=False,
                media_warn=media_warn,
            )

        return _studio_post_curate(
            **post_curate_kwargs,
            cluster_notice=cluster_notice,
            tier_mode=tier_mode,
            media_warn=media_warn,
        )
