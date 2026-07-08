"""Studio pipeline lock, curate, and rerender handlers."""

from __future__ import annotations

import logging
import threading

from travelogue.demo.build import DemoError
from travelogue.web.studio_errors import internal_error_payload
from travelogue.web.studio_handlers.common import load_trip_or_404, studio_ctx, trip_update_or_respond
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from travelogue.web.studio_jobs import get_job_store, run_g1_continue_job

_log = logging.getLogger(__name__)


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

    if not trip_update_or_respond(
        handler,
        svc,
        trip_json,
        lock_trip_structure,
    )[0]:
        return
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
        from travelogue.domain.pipeline_view import unlock_structure_for_replan

        trip = svc.load(trip_json)
        unlock_structure_for_replan(trip)
        try:
            run_curate(
                trip,
                export_layout="auto",
                apply_layout=True,
                trip_dir=trip_dir,
                cfg=ctx.cfg,
                refresh_algorithms=True,
            )
        except CurateError as exc:
            raise DemoError(exc.code, str(exc)) from exc
        from travelogue.layout_engine.planner.screen_planner import LAYOUT_ENGINE_SCREENS, resolve_layout_engine
        from travelogue.services.layout import apply_layout_to_trip

        if resolve_layout_engine(trip) == LAYOUT_ENGINE_SCREENS and not any(
            ch.get("screens") for ch in (trip.get("chapters") or [])
        ):
            apply_layout_to_trip(
                trip,
                export_layout="web",
                layout_engine="screens",
            )

        def mutator(t: dict) -> None:
            for key in (
                "chapters",
                "assets",
                "curation",
                "pipeline",
                "coverAssetId",
                "coverCandidates",
                "layoutEngine",
                "momentAssetId",
            ):
                if key in trip:
                    t[key] = trip[key]

        svc.update(trip_json, mutator)
        render_trip_surfaces(
            trip_json,
            trip_dir,
            export_mode="draft",
            validate=False,
            update_pipeline=False,
            cfg=ctx.cfg,
        )
        from travelogue.render.preview import render_preview_jpg

        render_preview_jpg(trip_json, trip_root=trip_dir)
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
