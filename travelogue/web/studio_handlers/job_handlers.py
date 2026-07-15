"""Studio job status and cancel."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from travelogue.web.studio_handlers.common import studio_ctx
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from travelogue.web.studio_incomplete_purge import cleanup_import_terminal_artifacts
from travelogue.web.studio_jobs import get_job_store


def handle_status(handler: StudioHandlerProtocol) -> None:
    query = parse_qs(urlparse(handler.path).query)
    job_ids = query.get("jobId") or query.get("jobid") or []
    if not job_ids:
        handler._json_response(400, {"ok": False, "error": "jobId required"})
        return
    job = get_job_store().get(job_ids[0])
    if job is None:
        handler._json_response(404, {"ok": False, "error": "job not found"})
        return
    handler._json_response(200, job.to_dict())


def handle_cancel(handler: StudioHandlerProtocol) -> None:
    payload = handler._read_json_body()
    if not payload:
        return

    job_id = str(payload.get("jobId") or "").strip()
    if not job_id:
        handler._json_response(400, {"ok": False, "error": "jobId required"})
        return

    store = get_job_store()
    job = store.cancel_job(job_id)
    if job is None:
        handler._json_response(404, {"ok": False, "error": "job not found"})
        return

    purged = False
    purged_outputs = False
    if job.type == "import" and job.status == "cancelled":
        # Wait for worker finally (join subprocess → purge) before answering,
        # so clients do not re-import into a half-dead trip directory.
        store.await_import_handle_done(job.job_id, timeout=30.0)
        ctx = studio_ctx(handler)
        cleanup_import_terminal_artifacts(
            ctx.trips_root,
            job_id=job.job_id,
            trip_id=job.trip_id,
            status="cancelled",
        )
        if job.trip_id:
            purged = not (ctx.trips_root / job.trip_id).is_dir()
        else:
            purged = True
    elif job.type == "longshot" and job.status == "cancelled":
        # Await runner exit so a second longshot cannot race the same trip.
        store.await_longshot_done(job.job_id, timeout=30.0)
        purged_outputs = True
    handler._json_response(
        200,
        {
            "ok": True,
            "status": job.status,
            "purged": purged,
            "purgedOutputs": purged_outputs,
        },
    )
