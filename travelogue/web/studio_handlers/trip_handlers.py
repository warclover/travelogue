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
    handler._json_response(200, {"ok": True, **build_entry(trip, trip_id)})


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
        if not kwargs:
            handler._json_response(400, {"ok": False, "error": "no intent fields"})
            return
        intent = apply_intent(trip, **kwargs)
        svc.save(trip, trip_json)
    except (ValueError, TypeError) as exc:
        handler._json_response(400, {"ok": False, "error": str(exc)})
        return
    handler._json_response(200, {"ok": True, "intent": intent})


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
