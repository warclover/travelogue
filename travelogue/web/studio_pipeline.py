"""Studio import pipeline: album → preview (Phase 2 M8)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from travelogue.config import AppConfig, app_config_scope, get_config
from travelogue.curation.curate import CurateError, run_curate
from travelogue.demo.build import DemoError
from travelogue.media.ingest import (
    RAW_UNSUPPORTED_MESSAGE,
    IngestError,
    ingest_into_trip,
    scan_image_paths,
)
from travelogue.orchestrator.run import run_trip
from travelogue.orchestrator.studio_hooks import StudioHooks
from travelogue.runtime import AppContext
from travelogue.services.copy_subject import is_generic_place
from travelogue.services.trip import TripService, apply_intent
from travelogue.services.trip_factory import create_trip
from travelogue.util.trip_slug import demo_trip_id_from_album
from travelogue.web.studio_config import resolve_studio_config
from travelogue.web.studio_jobs import ProgressCallback


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
) -> StudioPipelineResult:
    from travelogue.web.studio_intent_telemetry import write_studio_intent_telemetry

    trip_final = svc.load(trip_json)
    meta_final = trip_final.get("meta") or {}
    date_range_warn = _build_date_range_weak_hint(
        user_date_range=user_date_range,
        inferred_start=meta_final.get("dateStart"),
        inferred_end=meta_final.get("dateEnd"),
    )
    display_title = str(meta_final.get("title") or title).strip()[:20] or "我的旅途"
    featured_n, segment_n = _trip_import_stats(trip_final)
    intent_line = _format_intent_line(display_title, featured_n, segment_n)
    curation = trip_final.get("curation") or {}
    cull_user_line = str(curation.get("cullUserLine") or "")
    cull_summary = curation.get("cullSummary") or {}
    cull_warn = str(cull_summary.get("warnMessage") or "") if cull_summary.get("maxPhotosExceeded") else ""
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


def sample_album_preview_thumbs(
    album_dir: Path,
    *,
    count: int = 4,
    thumb_px: int = 112,
    max_photos: int = 250,
) -> tuple[list[str], int]:
    """Return JPEG data-URL thumbs evenly sampled from *album_dir*."""
    import base64
    from io import BytesIO

    from travelogue.media.image_ops import load_image_normalized

    try:
        paths, _stats = scan_image_paths(album_dir, max_photos=max_photos)
    except IngestError:
        return [], 0

    photo_count = len(paths)
    if not paths:
        return [], 0

    thumbs: list[str] = []
    for idx in _even_sample_indices(len(paths), count):
        try:
            loaded = load_image_normalized(paths[idx])
            img = loaded.image
            img.thumbnail((thumb_px, thumb_px))
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=78)
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            thumbs.append(f"data:image/jpeg;base64,{b64}")
        except Exception:
            continue
    return thumbs, photo_count


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
) -> StudioPipelineResult:
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
        import shutil

        shutil.rmtree(trip_dir)

    photo_count = count_album_photos(album_dir, max_photos=cfg.ingest.max_photos)

    if cfg.vision.preload_on_folder_pick and cfg.vision.enabled != "false":
        if progress:
            progress("ingest", 0, "正在预加载视觉模型…")
        from travelogue.vision.clip_encoder import preload_clip_encoder

        preload_clip_encoder(cfg)

    pipeline_timings: dict[str, float] = {}
    pipeline_t0 = time.monotonic()

    def _flush_pipeline_timings(extra: dict[str, float] | None = None) -> None:
        if extra:
            pipeline_timings.update(extra)
        pipeline_timings["totalMs"] = round((time.monotonic() - pipeline_t0) * 1000.0, 2)
        trip.setdefault("pipeline", {})["timings"] = dict(pipeline_timings)

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
                cull_enabled=bool(getattr(cfg.cull, "enabled", True)),
            ),
        )

    def cull_progress_hint(hint: str) -> None:
        report("ingest", 1, hint)

    with app_config_scope(cfg):
        report("ingest", 1)
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
        trip_rollout_id = str(trip.get("tripId") or slug).strip()
        if trip_rollout_id:
            from travelogue.curation.phase6_rollout import resolve_app_config_for_trip

            cfg = resolve_app_config_for_trip(cfg, trip_rollout_id)
            from travelogue.layout_engine.rollout import resolve_lse_config_for_trip

            cfg = resolve_lse_config_for_trip(cfg, trip_rollout_id)
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
        apply_intent(trip, **intent_kwargs)

        if plan_bytes is not None or plan_text:
            from travelogue.services.intent_plan import ingest_travel_plan

            ingest_travel_plan(
                trip,
                trip_root,
                raw_bytes=plan_bytes,
                raw_text=plan_text,
                filename=plan_filename,
            )

        try:
            parallel_embed = None
            if cfg.pipeline.parallel_embed and cfg.vision.enabled != "false":
                from travelogue.vision.parallel_embed import ParallelEmbedCoordinator

                parallel_embed = ParallelEmbedCoordinator(
                    trip_root,
                    cfg=cfg,
                    chunk_size=cfg.pipeline.parallel_embed_chunk,
                )

            def persist_partial_ingest() -> None:
                svc.save(trip, trip_json)

            def on_asset_added(entry: dict) -> None:
                if parallel_embed is not None:
                    parallel_embed.offer(entry)

            ingest_t0 = time.monotonic()
            ingest_result = ingest_into_trip(
                trip,
                trip_root,
                from_dir=album_dir,
                max_photos=cfg.ingest.max_photos,
                dedupe=dedupe,
                app_cfg=cfg,
                featured_dir=(
                    Path(folder_overrides["featuredDir"])
                    if folder_overrides.get("featuredDir")
                    and Path(folder_overrides["featuredDir"]).is_absolute()
                    else (album_dir / folder_overrides["featuredDir"])
                    if folder_overrides.get("featuredDir")
                    else None
                ),
                material_dir=(
                    Path(folder_overrides["materialDir"])
                    if folder_overrides.get("materialDir")
                    and Path(folder_overrides["materialDir"]).is_absolute()
                    else (album_dir / folder_overrides["materialDir"])
                    if folder_overrides.get("materialDir")
                    else None
                ),
                on_progress=ingest_progress if progress else None,
                on_cull_hint=cull_progress_hint if progress else None,
                on_persist=persist_partial_ingest,
                on_asset_added=on_asset_added if parallel_embed else None,
                resume_ingest=True,
            )
            if parallel_embed is not None:
                parallel_embed.finish()
            pipeline_timings["ingestMs"] = round((time.monotonic() - ingest_t0) * 1000.0, 2)
        except IngestError as exc:
            if exc.code == "E_INGEST_RAW_UNSUPPORTED":
                raise DemoError(exc.code, RAW_UNSUPPORTED_MESSAGE) from exc
            if exc.code in ("E_INGEST_TOO_FEW", "E_INGEST_EMPTY"):
                raise DemoError("E_DEMO_TOO_FEW", str(exc)) from exc
            raise DemoError(exc.code, str(exc)) from exc

        # F-P4 M15: record dual-folder detection into intent.folders
        ingest_stats = ingest_result.stats or {}
        tier_mode = _resolve_tier_mode(ingest_stats)
        featured_detected = tier_mode in ("auto", "explicit", "dual") or ingest_stats.get("mode") == "dual"
        existing_folders = dict((trip.get("intent") or {}).get("folders") or {})
        existing_folders["featuredDetected"] = bool(featured_detected)
        apply_intent(trip, folders=existing_folders)

        from travelogue.curation.intent_hints import apply_editorial_intent_hints

        apply_editorial_intent_hints(trip)

        from travelogue.curation.clustering import run_clustering_layer

        # Emit clustering hint as part of the *curate* stage (the next user-facing
        # step) so the ingest hint stays semantically tied to ingest only.
        cluster_t0 = time.monotonic()
        cluster_result = run_clustering_layer(trip, trip_dir=trip_root, cfg=cfg)
        pipeline_timings["clusterMs"] = round((time.monotonic() - cluster_t0) * 1000.0, 2)
        cluster_meta = (trip.get("curation") or {}).get("clustering") or {}
        embed_stats = cluster_meta.get("embedStats") or {}
        if cluster_meta.get("embedSkipped"):
            pipeline_timings["embedMs"] = 0.0
        else:
            pipeline_timings["embedMs"] = float(embed_stats.get("elapsedMs") or 0.0)
        _flush_pipeline_timings()
        cluster_notice = cluster_result.user_notice
        svc.save(trip, trip_json)

        if cluster_result.stage_hint and progress:
            progress("curate", 2, cluster_result.stage_hint)
        else:
            report("curate", 2)
        try:
            curate_t0 = time.monotonic()
            run_curate(
                trip,
                export_layout="auto",
                apply_layout=True,
                trip_dir=trip_root,
                cfg=cfg,
            )
            pipeline_timings["curateMs"] = round((time.monotonic() - curate_t0) * 1000.0, 2)
            _flush_pipeline_timings()
        except CurateError as exc:
            raise DemoError(exc.code, str(exc)) from exc
        svc.save(trip, trip_json)

        g1_pending = bool(cfg.studio.g1_confirm_structure)
        if g1_pending:
            from travelogue.render.engine import render_trip_surfaces
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
            pipeline_timings["renderMs"] = round((time.monotonic() - render_t0) * 1000.0, 2)
            _flush_pipeline_timings()
            svc.save(trip, trip_json)
            report("render", 4)
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
            )

        report("narrate", 3)
        hooks = StudioHooks(on_stage=report)
        from travelogue.web.studio_narrate import resolve_studio_narrate_provider

        narrate_provider = resolve_studio_narrate_provider(cfg=cfg)
        try:
            run_trip(
                trip_json,
                from_stage="lock_structure",
                until="copy",
                skip_locked=True,
                narrate_provider=narrate_provider,
                validate=False,
                cfg=cfg,
                studio_hooks=hooks,
            )
        except Exception as exc:
            code = getattr(exc, "code", "E_STUDIO_PIPELINE")
            raise DemoError(code, str(exc)) from exc

        report("render", 4)
        try:
            render_t0 = time.monotonic()
            run_trip(
                trip_json,
                from_stage="render",
                until="rendered",
                skip_locked=True,
                validate=False,
                cfg=cfg,
                studio_hooks=hooks,
            )
            from travelogue.render.preview import render_preview_jpg

            render_preview_jpg(trip_json, trip_root=trip_root)
            pipeline_timings["renderMs"] = round((time.monotonic() - render_t0) * 1000.0, 2)
            trip = svc.load(trip_json)
            _flush_pipeline_timings()
            svc.save(trip, trip_json)
        except Exception as exc:
            code = getattr(exc, "code", "E_STUDIO_PIPELINE")
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
        )
