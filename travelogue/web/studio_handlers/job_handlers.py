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

    job = get_job_store().cancel_job(job_id)
    if job is None:
        handler._json_response(404, {"ok": False, "error": "job not found"})
        return

    purged = False
    if job.type == "import" and job.status == "cancelled":
        ctx = studio_ctx(handler)
        purged = cleanup_import_terminal_artifacts(
            ctx.trips_root,
            job_id=job.job_id,
            trip_id=job.trip_id,
            status="cancelled",
        )
    handler._json_response(
        200,
        {"ok": True, "status": job.status, "purged": purged},
    )
