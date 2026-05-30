"""Studio import pipeline: album → preview (Phase 2 M8)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from travelogue.config import AppConfig, app_config_scope, get_config
from travelogue.curation.curate import CurateError, run_curate
from travelogue.demo.build import DemoError, resolve_demo_config
from travelogue.media.ingest import IngestError, ingest_into_trip, scan_image_paths
from travelogue.orchestrator.run import run_trip
from travelogue.orchestrator.studio_hooks import StudioHooks
from travelogue.runtime import AppContext
from travelogue.services.copy_subject import is_generic_place
from travelogue.services.trip import TripService, apply_intent
from travelogue.services.trip_factory import create_trip
from travelogue.util.trip_slug import demo_trip_id_from_album
from travelogue.web.studio_jobs import ProgressCallback
from travelogue.web.studio_stages import ingest_stage_hint, stage_hint


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
    g1_pending: bool = False,
) -> StudioPipelineResult:
    from travelogue.web.studio_intent_telemetry import write_studio_intent_telemetry

    trip_final = svc.load(trip_json)
    meta_final = trip_final.get("meta") or {}
    display_title = str(meta_final.get("title") or title).strip()[:20] or "我的旅途"
    featured_n, segment_n = _trip_import_stats(trip_final)
    intent_line = _format_intent_line(display_title, featured_n, segment_n)
    write_studio_intent_telemetry(
        trip_final,
        trip_root,
        tier_mode=tier_mode,
        g1_pending=g1_pending,
        g1_confirmed=not g1_pending and (trip_final.get("pipeline") or {}).get("status")
        not in (None, "structure_draft"),
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
    )


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
    user_notes: str | None = None,
    plan_bytes: bytes | None = None,
    plan_text: str | None = None,
    plan_filename: str = "plan.txt",
) -> StudioPipelineResult:
    album_dir = album_dir.resolve()
    cfg_path = resolve_demo_config(config)
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
    ingest_hint = ingest_stage_hint(photo_count)

    def report(stage: str, index: int, hint: str | None = None) -> None:
        resolved = hint or (ingest_hint if stage == "ingest" else stage_hint(stage))
        if progress:
            progress(stage, index, resolved)
        time.sleep(0)

    def ingest_progress(cur: int, total: int) -> None:
        report("ingest", 1, f"已处理 {cur}/{total} 张 · {ingest_hint}")

    with app_config_scope(cfg):
        report("ingest", 1)
        cluster_notice = ""
        trip_json = create_trip(
            slug,
            trips_root,
            title=title,
            place=place,
            export_layout="auto",
        )
        trip_root = trip_json.parent
        app_ctx = AppContext(cfg=cfg, trips_root=trips_root.resolve())
        svc = app_ctx.trip_service()
        trip = svc.load(trip_json)
        # F-P4 M15: single-writer intent — mirrors meta.title/places + trip.userNotes
        # (never meta.userNotes, which is not in schema).
        place_raw = str(place or "").strip()
        resolved_place_user_set = (
            bool(place_user_set)
            if place_user_set is not None
            else bool(place_raw) and not is_generic_place(place_raw)
        )
        apply_intent(
            trip,
            title=title,
            places=[place_raw] if resolved_place_user_set else [],
            places_user_set=resolved_place_user_set,
            user_notes=user_notes,
        )

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
            def persist_partial_ingest() -> None:
                svc.save(trip, trip_json)

            ingest_result = ingest_into_trip(
                trip,
                trip_root,
                from_dir=album_dir,
                max_photos=cfg.ingest.max_photos,
                dedupe=dedupe,
                app_cfg=cfg,
                on_progress=ingest_progress if progress else None,
                on_persist=persist_partial_ingest,
                resume_ingest=True,
            )
        except IngestError as exc:
            if exc.code in ("E_INGEST_TOO_FEW", "E_INGEST_EMPTY"):
                raise DemoError("E_DEMO_TOO_FEW", str(exc)) from exc
            raise DemoError(exc.code, str(exc)) from exc

        # F-P4 M15: record dual-folder detection into intent.folders
        ingest_stats = ingest_result.stats or {}
        tier_mode = _resolve_tier_mode(ingest_stats)
        featured_detected = tier_mode in ("auto", "explicit", "dual") or ingest_stats.get("mode") == "dual"
        apply_intent(trip, folders={"featuredDetected": bool(featured_detected)})

        from travelogue.curation.intent_hints import apply_editorial_intent_hints

        apply_editorial_intent_hints(trip)

        from travelogue.curation.clustering import run_clustering_layer

        # Emit clustering hint as part of the *curate* stage (the next user-facing
        # step) so the ingest hint stays semantically tied to ingest only.
        cluster_result = run_clustering_layer(trip, trip_dir=trip_root, cfg=cfg)
        cluster_notice = cluster_result.user_notice
        svc.save(trip, trip_json)

        if cluster_result.stage_hint and progress:
            progress("curate", 2, cluster_result.stage_hint)
        else:
            report("curate", 2)
        try:
            run_curate(
                trip,
                export_layout="auto",
                apply_layout=True,
                trip_dir=trip_root,
                cfg=cfg,
            )
        except CurateError as exc:
            raise DemoError(exc.code, str(exc)) from exc
        svc.save(trip, trip_json)

        g1_pending = bool(cfg.studio.g1_confirm_structure)
        if g1_pending:
            from travelogue.render.engine import render_trip_surfaces
            from travelogue.services.pipeline_state import trip_status

            render_trip_surfaces(
                trip_json,
                trip_root,
                export_mode="draft",
                validate=False,
                update_pipeline=False,
                cfg=cfg,
            )
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
                g1_pending=g1_pending,
            )

        report("narrate", 3)
        hooks = StudioHooks(on_stage=report)
        try:
            run_trip(
                trip_json,
                from_stage="lock_structure",
                until="copy",
                skip_locked=True,
                narrate_provider="stub",
                validate=False,
                cfg=cfg,
                studio_hooks=hooks,
            )
        except Exception as exc:
            code = getattr(exc, "code", "E_STUDIO_PIPELINE")
            raise DemoError(code, str(exc)) from exc

        report("render", 4)
        try:
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
            g1_pending=False,
        )
