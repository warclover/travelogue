"""Studio trip list, entry, intent, pipeline, curate, chapter layout, rerender."""

from __future__ import annotations

import logging
import shutil
import threading
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from urllib.parse import parse_qs, urlparse

from travelogue.demo.build import DemoError
from travelogue.web.studio_errors import internal_error_payload
from travelogue.web.studio_handlers.common import (
    load_trip_or_404,
    resolve_trip_dir_listed,
    studio_ctx,
    trip_id_from_query,
)
from travelogue.web.studio_jobs import get_job_store, run_g1_continue_job
from travelogue.web.studio_trips import list_studio_trips, studio_trips_total
from travelogue.web.studio_trip_id import is_valid_studio_trip_id

_log = logging.getLogger(__name__)


def _is_protected_demo_trip(trip_id: str, trip: dict) -> bool:
    if trip_id == "demo-album":
        return True
    title = str((trip.get("meta") or {}).get("title") or "").strip()
    return title in ("示例旅途", "示例")


def handle_trips(handler: StudioHandlerProtocol) -> None:
    query = parse_qs(urlparse(handler.path).query)
    try:
        limit = int((query.get("limit") or ["20"])[0])
    except ValueError:
        limit = 20
    limit = max(1, min(limit, 100))
    try:
        offset = int((query.get("offset") or ["0"])[0])
    except ValueError:
        offset = 0
    offset = max(0, offset)
    ctx = studio_ctx(handler)
    trips = list_studio_trips(ctx.trips_root, limit=limit, offset=offset)
    total = studio_trips_total(ctx.trips_root)
    handler._json_response(200, {"ok": True, "trips": trips, "total": total})


def handle_delete_trip(handler: StudioHandlerProtocol, trip_id: str) -> None:
    ctx = studio_ctx(handler)
    trip_dir = resolve_trip_dir_listed(ctx, trip_id)
    if trip_dir is None:
        handler._json_response(
            404,
            {"ok": False, "error": "E_TRIP_NOT_FOUND", "message": "游记不存在"},
        )
        return
    disk_id = trip_dir.name
    trip_json = trip_dir / "trip.json"
    try:
        trip = ctx.trip_service().load(trip_json)
    except Exception:
        _log.exception("load trip before delete failed for %s", trip_dir)
        handler._json_response(500, internal_error_payload())
        return
    if _is_protected_demo_trip(disk_id, trip):
        handler._json_response(
            403,
            {
                "ok": False,
                "error": "E_TRIP_DELETE_DENIED",
                "message": "示例画册无法删除",
            },
        )
        return
    store = get_job_store()
    if store.is_trip_busy(disk_id):
        handler._json_response(
            409,
            {
                "ok": False,
                "error": "E_STUDIO_JOB_BUSY",
                "message": "导入进行中，请稍后再试",
            },
        )
        return
    try:
        shutil.rmtree(trip_dir)
    except OSError:
        _log.exception("delete trip failed for %s", trip_dir)
        handler._json_response(500, internal_error_payload())
        return
    handler.send_response(204)
    handler.end_headers()


def handle_entry(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.web.studio_entry import build_entry

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    _trip_dir, trip = loaded
    ctx = studio_ctx(handler)
    enabled = bool(ctx.cfg.aesthetic.enabled)
    handler._json_response(200, {"ok": True, **build_entry(trip, trip_id, aesthetic_enabled=enabled)})


def handle_aesthetic(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.web.studio_aesthetic import build_aesthetic_studio_payload

    query = parse_qs(urlparse(handler.path).query)
    asset_id = (query.get("assetId") or query.get("asset_id") or [None])[0]
    try:
        limit = int((query.get("limit") or ["3"])[0])
    except ValueError:
        limit = 3
    limit = max(1, min(limit, 5))

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    _trip_dir, trip = loaded
    ctx = studio_ctx(handler)
    enabled = bool(ctx.cfg.aesthetic.enabled)
    asset_ids = [str(asset_id)] if asset_id else None
    payload = build_aesthetic_studio_payload(
        trip,
        enabled=enabled,
        asset_ids=asset_ids,
        limit=limit,
    )
    handler._json_response(200, {"ok": True, **payload})


def handle_bento_preview(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.web.studio_bento_preview import build_trip_bento_preview

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    if payload is None:
        handler._json_response(
            404,
            {"ok": False, "error": "E_BENTO_PREVIEW_UNAVAILABLE", "message": "暂无预览图"},
        )
        return
    handler._json_response(200, {"ok": True, **payload})


def handle_chapter_layout(handler: StudioHandlerProtocol) -> None:
    from travelogue.curation.chapter_explain import build_chapter_explain, build_layout_explain

    trip_id = trip_id_from_query(handler)
    if not trip_id or not is_valid_studio_trip_id(trip_id):
        handler._json_response(400, {"ok": False, "error": "tripId required"})
        return
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    stored = ((trip.get("curation") or {}).get("clustering") or {}).get("userSummary")
    if isinstance(stored, dict) and stored.get("summary"):
        explain = dict(stored)
    else:
        explain = build_chapter_explain(trip, trip_dir=trip_dir)
    layout_explain = build_layout_explain(trip.get("curation") or {})
    if layout_explain:
        explain["layoutExplain"] = layout_explain
    handler._json_response(200, {"ok": True, **explain})


def handle_patch_intent(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.services.trip import apply_intent

    payload = handler._read_json_body()
    if not payload:
        return
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)
    svc = ctx.trip_service()
    try:
        kwargs: dict = {}
        if "title" in payload:
            kwargs["title"] = payload.get("title")
        if "places" in payload:
            from travelogue.services.copy_subject import is_generic_place

            kwargs["places"] = payload.get("places")
            if "placesUserSet" in payload:
                kwargs["places_user_set"] = bool(payload.get("placesUserSet"))
            else:
                raw_places = payload.get("places") or []
                kwargs["places_user_set"] = bool(
                    raw_places
                    and not all(is_generic_place(str(p)) for p in raw_places)
                )
        if "userNotes" in payload:
            kwargs["user_notes"] = payload.get("userNotes")
        if "travelPlan" in payload:
            kwargs["travel_plan"] = payload.get("travelPlan")
        if "featuredSubjects" in payload:
            kwargs["featured_subjects"] = payload.get("featuredSubjects")
        if not kwargs:
            handler._json_response(400, {"ok": False, "error": "no intent fields"})
            return
        from travelogue.templating.guardrails import validate_edit_payload
        from travelogue.templating.resolver import resolve_effective_template

        fields: dict[str, str] = {}
        if "title" in kwargs:
            fields["meta.title"] = "meta.title"
        if "places" in kwargs:
            fields["meta.places"] = "meta.places"
        gerrs = validate_edit_payload(resolve_effective_template(trip), fields)
        if gerrs:
            handler._json_response(
                403,
                {"ok": False, "error": "E_TEMPLATE_GUARDRAIL", "message": gerrs[0]},
            )
            return
        intent = apply_intent(trip, **kwargs)
        svc.save(trip, trip_json)
    except (ValueError, TypeError) as exc:
        handler._json_response(400, {"ok": False, "error": str(exc)})
        return
    handler._json_response(200, {"ok": True, "intent": intent})


def handle_get_cohort(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.services.cohort import build_cohort_studio_payload

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    _trip_dir, trip = loaded
    ctx = studio_ctx(handler)
    enabled = bool(ctx.app_config.cohort.enabled)
    payload = build_cohort_studio_payload(trip, cohort_enabled=enabled)
    handler._json_response(200, {"ok": True, **payload})


def handle_patch_cohort(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.services.trip import apply_intent
    from travelogue.curation.cohort_faces import apply_cohort_tags

    payload = handler._read_json_body()
    if not payload:
        return
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)
    svc = ctx.trip_service()
    if not ctx.app_config.cohort.enabled:
        handler._json_response(
            400,
            {"ok": False, "error": "E_COHORT_DISABLED", "message": "cohort.enabled is false in config"},
        )
        return
    try:
        if "featuredSubjects" in payload:
            apply_intent(trip, featured_subjects=payload.get("featuredSubjects"))
        refresh = bool(payload.get("refresh"))
        summary = None
        if refresh or "featuredSubjects" in payload:
            summary = apply_cohort_tags(trip, trip_dir=trip_dir, cfg=ctx.app_config)
            if summary:
                cur = trip.setdefault("curation", {})
                cur["cohort"] = summary
        if not ("featuredSubjects" in payload) and not refresh:
            handler._json_response(400, {"ok": False, "error": "no cohort fields"})
            return
        svc.save(trip, trip_json)
    except (ValueError, TypeError) as exc:
        handler._json_response(400, {"ok": False, "error": str(exc)})
        return
    from travelogue.services.cohort import build_cohort_studio_payload

    body = build_cohort_studio_payload(trip, cohort_enabled=True)
    body["summary"] = (trip.get("curation") or {}).get("cohort") or summary
    handler._json_response(200, {"ok": True, **body})


def handle_patch_screen_replan(
    handler: StudioHandlerProtocol, trip_id: str, screen_id: str
) -> None:
    """PATCH …/screens/{screenId}/replan — MCS alt_topk or legacy for one screen."""
    from travelogue.curation.layout_planner import aspect_kind_for_asset
    from travelogue.curation.mosaic.replan import ReplanError, refresh_trip_displayed_assets, replan_screen
    from travelogue.curation.screen_planner import LAYOUT_ENGINE_SCREENS

    payload = handler._read_json_body() or {}
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    if trip.get("layoutEngine") != LAYOUT_ENGINE_SCREENS:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_LAYOUT_ENGINE",
                "message": "replan requires layoutEngine=screens",
            },
        )
        return
    chapters = trip.get("chapters") or []
    assets = trip.get("assets") or []
    assets_map = {a["id"]: a for a in assets if a.get("id")}
    aspects = {
        aid: aspect_kind_for_asset(a)
        for aid, a in assets_map.items()
        if a.get("layoutEligible", True) is not False
    }
    strategy = str(payload.get("strategy") or "alt_topk").strip().lower()
    if strategy not in ("alt_topk", "legacy"):
        handler._json_response(400, {"ok": False, "error": "invalid strategy"})
        return
    try:
        top_k = int(payload.get("topK") or payload.get("top_k") or 3)
    except (TypeError, ValueError):
        top_k = 3
    ctx = studio_ctx(handler)
    try:
        result = replan_screen(
            chapters,
            screen_id,
            strategy=strategy,  # type: ignore[arg-type]
            top_k=max(1, top_k),
            aspects=aspects,
            assets_map=assets_map,
            cfg=ctx.app_config.mosaic,
            trip_photo_total=len(assets_map),
            burst_seconds=ctx.app_config.layout.mixed_proximity_seconds,
        )
    except ReplanError as exc:
        handler._json_response(
            400,
            {"ok": False, "error": "E_REPLAN_INVALID", "message": str(exc)},
        )
        return
    if result.get("applied"):
        trip["chapters"] = chapters
        refresh_trip_displayed_assets(trip, chapters)
    trip_json = trip_dir / "trip.json"
    ctx.trip_service().save(trip, trip_json)
    handler._json_response(200, {"ok": True, **result})


def handle_post_cohort_refresh(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.curation.cohort_faces import apply_cohort_tags

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)
    if not ctx.app_config.cohort.enabled:
        handler._json_response(
            400,
            {"ok": False, "error": "E_COHORT_DISABLED", "message": "cohort.enabled is false in config"},
        )
        return
    summary = apply_cohort_tags(trip, trip_dir=trip_dir, cfg=ctx.app_config)
    if summary:
        trip.setdefault("curation", {})["cohort"] = summary
    ctx.trip_service().save(trip, trip_json)
    handler._json_response(200, {"ok": True, "summary": summary})


def handle_patch_template(handler: StudioHandlerProtocol, trip_id: str) -> None:
    """受控调整模板策略（PRD §5.10.2）；锁定态拒绝。"""
    from travelogue.templating.resolver import is_template_locked
    from travelogue.templating.router import apply_template_selection
    from travelogue.templating.summary import build_template_summary

    payload = handler._read_json_body()
    if not payload:
        return
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    if is_template_locked(trip):
        handler._json_response(
            409,
            {
                "ok": False,
                "error": "E_TEMPLATE_LOCKED",
                "message": "模板已锁定，无法调整",
            },
        )
        return
    mode_raw = str(payload.get("mode") or payload.get("templateMode") or "smart").strip().lower()
    mode = "manual" if mode_raw == "manual" else "smart"
    template_id = payload.get("templateId") or payload.get("template_id")
    template_id_str = str(template_id).strip() if template_id else None
    if mode == "manual" and not template_id_str:
        handler._json_response(400, {"ok": False, "error": "templateId required for manual mode"})
        return
    ctx = studio_ctx(handler)
    selection = apply_template_selection(
        trip,
        mode=mode,  # type: ignore[arg-type]
        requested_template_id=template_id_str,
        cfg=ctx.cfg,
        recompute=True,
        trip_dir=trip_dir,
        log_action="user_adjust",
    )
    trip_json = trip_dir / "trip.json"
    ctx.trip_service().save(trip, trip_json)
    handler._json_response(
        200,
        {"ok": True, "template": build_template_summary(trip), "templateSelection": selection},
    )


def handle_patch_pipeline(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.services.pipeline_state import trip_status
    from travelogue.web.studio_g1 import continue_after_g1_confirm, lock_trip_structure

    payload = handler._read_json_body()
    if not payload:
        return
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)
    svc = ctx.trip_service()

    target_status = str(payload.get("status") or "").strip()
    continue_pipeline = bool(payload.get("continuePipeline", payload.get("continue", True)))

    if trip_status(trip) != "structure_draft":
        handler._json_response(
            409,
            {"ok": False, "error": "E_PIPELINE_ORDER", "message": "章节结构已确认或不可确认"},
        )
        return
    if target_status and target_status != "structure_locked":
        handler._json_response(400, {"ok": False, "error": "unsupported status"})
        return

    lock_trip_structure(trip)
    svc.save(trip, trip_json)
    if not continue_pipeline:
        handler._json_response(200, {"ok": True, "pipelineStatus": "structure_locked"})
        return

    host = handler.studio_host
    port = handler.studio_port

    def runner() -> dict:
        return continue_after_g1_confirm(trip_json, host=host, port=port, cfg=ctx.cfg)

    store = get_job_store()
    job = store.create_g1_continue_job()
    if job is None:
        handler._json_response(
            409,
            {"ok": False, "error": "E_STUDIO_JOB_BUSY", "message": "已有任务进行中"},
        )
        return
    threading.Thread(
        target=lambda: run_g1_continue_job(job, runner=runner),
        daemon=True,
    ).start()
    handler._json_response(
        202,
        {"ok": True, "jobId": job.job_id, "pipelineStatus": "structure_locked"},
    )


def handle_trip_curate(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.curation.curate import CurateError, run_curate
    from travelogue.render.engine import render_trip_surfaces

    handler._read_json_body()
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, _trip = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)
    svc = ctx.trip_service()

    def runner() -> dict:
        trip = svc.load(trip_json)
        pipe = trip.setdefault("pipeline", {})
        locks = pipe.setdefault("locks", {})
        locks["structure"] = False
        pipe["status"] = "structure_draft"
        try:
            run_curate(
                trip,
                export_layout="auto",
                apply_layout=True,
                trip_dir=trip_dir,
                cfg=ctx.cfg,
            )
        except CurateError as exc:
            raise DemoError(exc.code, str(exc)) from exc
        # Web preview (index.html) needs chapters[].screens; mobile-only curate leaves screens empty
        # while an older render can still show disabled mosaic patterns.
        from travelogue.curation.screen_planner import LAYOUT_ENGINE_SCREENS, resolve_layout_engine
        from travelogue.services.layout import apply_layout_to_trip

        if resolve_layout_engine(trip) == LAYOUT_ENGINE_SCREENS and not any(
            ch.get("screens") for ch in (trip.get("chapters") or [])
        ):
            apply_layout_to_trip(
                trip,
                export_layout="web",
                layout_engine="screens",
            )
        svc.save(trip, trip_json)
        render_trip_surfaces(
            trip_json,
            trip_dir,
            export_mode="draft",
            validate=False,
            update_pipeline=False,
            cfg=ctx.cfg,
        )
        return {"tripId": trip_id, "pipelineStatus": "structure_draft"}

    store = get_job_store()
    job = store.create_g1_continue_job()
    if job is None:
        handler._json_response(
            409,
            {"ok": False, "error": "E_STUDIO_JOB_BUSY", "message": "已有任务进行中"},
        )
        return
    threading.Thread(
        target=lambda: run_g1_continue_job(job, runner=runner),
        daemon=True,
    ).start()
    handler._json_response(202, {"ok": True, "jobId": job.job_id})


def handle_rerender(handler: StudioHandlerProtocol) -> None:
    from travelogue.web.rerender import rerender_draft_trip

    if handler.trip_json_path is None or not handler.trip_json_path.is_file():
        handler._json_response(404, {"ok": False, "error": "trip not found"})
        return
    try:
        rendered = rerender_draft_trip(handler.trip_json_path)
    except Exception:
        _log.exception("rerender failed for %s", handler.trip_json_path)
        handler._json_response(500, internal_error_payload())
        return
    handler._json_response(200, {"ok": True, "rendered": rendered})
