"""Studio pipeline lock, curate, and rerender handlers."""

from __future__ import annotations

import logging
import threading

from travelogue.demo.build import DemoError
from travelogue.web.studio_errors import internal_error_payload
from travelogue.web.studio_handlers.common import (
    load_trip_or_404,
    studio_ctx,
    trip_update_or_respond,
)
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from travelogue.web.studio_jobs import get_job_store, run_g1_continue_job

_log = logging.getLogger(__name__)


def normalize_curate_scope(payload: dict | None) -> str:
    """Return ``full`` or ``tier`` from POST body (M3 · scope=tier)."""
    raw = (payload or {}).get("scope")
    return "tier" if str(raw or "").strip().lower() == "tier" else "full"


def structure_fingerprint(trip: dict) -> str:
    """Stable fingerprint of chapter titles + screen pattern sequence for G1 regen UX."""
    parts: list[str] = []
    for ch in trip.get("chapters") or []:
        title = str(ch.get("title") or "")
        patterns = [
            str(s.get("patternId") or "")
            for s in (ch.get("screens") or [])
            if isinstance(s, dict)
        ]
        parts.append(f"{title}|{len(patterns)}|{','.join(patterns)}")
    return "\n".join(parts)


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

    payload = handler._read_json_body() or {}
    scope = normalize_curate_scope(payload)
    force = bool(payload.get("force", scope == "full"))
    reason = str(payload.get("reason") or "").strip() or None

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip0 = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)
    svc = ctx.trip_service()

    if scope == "tier" and not (trip0.get("chapters") or []):
        handler._json_response(
            409,
            {
                "ok": False,
                "error": "E_CURATE_NO_STRUCTURE",
                "message": "按精选重排需要先有成书章节结构",
            },
        )
        return

    def runner() -> dict:
        from travelogue.domain.pipeline_view import unlock_structure_for_replan

        trip = svc.load(trip_json)
        prev_pipeline = dict(trip.get("pipeline") or {})
        prev_status = prev_pipeline.get("status")
        prev_locks = prev_pipeline.get("locks")
        before_fp = structure_fingerprint(trip)

        if scope == "full":
            unlock_structure_for_replan(trip)
        try:
            run_curate(
                trip,
                export_layout="auto",
                apply_layout=True,
                trip_dir=trip_dir,
                cfg=ctx.cfg,
                refresh_algorithms=scope == "full",
                scope=scope,
                cover_force=force if scope == "tier" else False,
            )
        except CurateError as exc:
            raise DemoError(exc.code, str(exc)) from exc

        if scope == "tier":
            from travelogue.domain.pipeline_view import (
                replace_pipeline_locks,
                set_pipeline_status,
            )

            if prev_status:
                set_pipeline_status(trip, str(prev_status))
            if isinstance(prev_locks, dict):
                replace_pipeline_locks(trip, prev_locks)

        from travelogue.layout_engine.api import (
            LAYOUT_ENGINE_SCREENS,
            resolve_layout_engine,
        )
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
        # MF-09 · after replan, fill missing HD for newly selected assets
        preparing = 0
        try:
            from travelogue.media.derivatives import materialize_on_demand

            od = materialize_on_demand(
                trip, trip_dir, app_cfg=ctx.cfg, persist=True
            )
            preparing = int(od.preparing_count)
            if od.mode == "sync" and od.sync_result is not None:

                def _pipe_mutator(t: dict) -> None:
                    if "pipeline" in trip:
                        t["pipeline"] = trip["pipeline"]
                    t["assets"] = trip.get("assets") or t.get("assets")

                svc.update(trip_json, _pipe_mutator)
        except Exception:
            preparing = 0
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
        out_status = (trip.get("pipeline") or {}).get("status") or (
            "structure_draft" if scope == "full" else prev_status
        )
        after_fp = structure_fingerprint(trip)
        return {
            "tripId": trip_id,
            "scope": scope,
            "reason": reason,
            "pipelineStatus": out_status,
            "structureChanged": before_fp != after_fp,
            "derivativesPreparing": preparing,
        }

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
        {"ok": True, "jobId": job.job_id, "scope": scope},
    )

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
