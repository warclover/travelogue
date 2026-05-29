"""Studio background jobs (import pipeline)."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable

from travelogue.demo.build import DemoError
from travelogue.web.studio_errors import user_message
from travelogue.web.studio_stages import stage_hint

STAGE_COUNT = 4


@dataclass
class StudioJob:
    job_id: str
    type: str
    status: str = "queued"
    stage: str = ""
    stage_index: int = 0
    stage_count: int = STAGE_COUNT
    stage_hint: str = ""
    trip_id: str | None = None
    error: dict[str, Any] | None = None
    result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "jobId": self.job_id,
            "type": self.type,
            "status": self.status,
            "stage": self.stage,
            "stageIndex": self.stage_index,
            "stageCount": self.stage_count,
            "stageHint": self.stage_hint,
            "tripId": self.trip_id,
            "error": self.error,
            "result": self.result,
        }


class StudioJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, StudioJob] = {}
        self._lock = threading.Lock()
        self._import_running = False
        self._longshot_running = False
        self._narrate_running = False
        self._g1_running = False
        self._import_handles: dict[str, Any] = {}

    def create_import_job(self) -> StudioJob | None:
        with self._lock:
            if self._import_running:
                return None
            job_id = f"job-{uuid.uuid4().hex[:12]}"
            job = StudioJob(job_id=job_id, type="import", status="queued")
            self._jobs[job_id] = job
            self._import_running = True
            return job

    def get(self, job_id: str) -> StudioJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def is_cancelled(self, job: StudioJob) -> bool:
        with self._lock:
            return job.status == "cancelled"

    def update(
        self,
        job: StudioJob,
        *,
        status: str | None = None,
        stage: str | None = None,
        stage_index: int | None = None,
        stage_count: int | None = None,
        stage_hint: str | None = None,
        trip_id: str | None = None,
        error: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
    ) -> None:
        with self._lock:
            if status is not None:
                job.status = status
            if stage is not None:
                job.stage = stage
            if stage_index is not None:
                job.stage_index = stage_index
            if stage_count is not None:
                job.stage_count = stage_count
            if stage_hint is not None:
                job.stage_hint = stage_hint
            if trip_id is not None:
                job.trip_id = trip_id
            if error is not None:
                job.error = error
            if result is not None:
                job.result = result

    def finalize(
        self,
        job: StudioJob,
        *,
        status: str,
        trip_id: str | None = None,
        error: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
    ) -> bool:
        with self._lock:
            if job.status == "cancelled":
                return False
            job.status = status
            if trip_id is not None:
                job.trip_id = trip_id
            if error is not None:
                job.error = error
            if result is not None:
                job.result = result
            return True

    def finish_import(self) -> None:
        with self._lock:
            self._import_running = False

    def create_longshot_job(self) -> StudioJob | None:
        with self._lock:
            if self._longshot_running:
                return None
            job_id = f"job-{uuid.uuid4().hex[:12]}"
            job = StudioJob(
                job_id=job_id,
                type="longshot",
                status="queued",
                stage="longshot",
                stage_index=1,
                stage_count=1,
                stage_hint=stage_hint("longshot", "约 20–40 秒"),
            )
            self._jobs[job_id] = job
            self._longshot_running = True
            return job

    def finish_longshot(self) -> None:
        with self._lock:
            self._longshot_running = False

    def create_narrate_job(self) -> StudioJob | None:
        with self._lock:
            if self._narrate_running:
                return None
            job_id = f"job-{uuid.uuid4().hex[:12]}"
            job = StudioJob(
                job_id=job_id,
                type="narrate",
                status="queued",
                stage="llm_narrate",
                stage_index=1,
                stage_count=1,
                stage_hint=stage_hint("llm_narrate", "约 30–60 秒"),
            )
            self._jobs[job_id] = job
            self._narrate_running = True
            return job

    def finish_narrate(self) -> None:
        with self._lock:
            self._narrate_running = False

    def create_g1_continue_job(self) -> StudioJob | None:
        with self._lock:
            if self._g1_running or self._import_running:
                return None
            job_id = f"job-{uuid.uuid4().hex[:12]}"
            job = StudioJob(
                job_id=job_id,
                type="g1_continue",
                status="queued",
                stage_count=1,
                stage_hint=stage_hint("render", "约 30 秒"),
            )
            self._jobs[job_id] = job
            self._g1_running = True
            return job

    def finish_g1(self) -> None:
        with self._lock:
            self._g1_running = False

    def set_import_handle(self, job_id: str, handle: Any) -> None:
        with self._lock:
            self._import_handles[job_id] = handle

    def pop_import_handle(self, job_id: str) -> Any:
        with self._lock:
            return self._import_handles.pop(job_id, None)

    def cancel_job(self, job_id: str) -> StudioJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            if job.status not in ("queued", "running"):
                return job
            handle = self._import_handles.get(job_id)
            if handle is not None:
                handle.cancel()
            job.status = "cancelled"
            job.error = {
                "code": "E_STUDIO_CANCELLED",
                "message": user_message("E_STUDIO_CANCELLED"),
            }
            if job.type == "import":
                self._import_running = False
                self._import_handles.pop(job_id, None)
            return job


_JOB_STORE = StudioJobStore()


def get_job_store() -> StudioJobStore:
    return _JOB_STORE


def reset_job_store() -> None:
    """Test helper: clear in-memory job state."""
    global _JOB_STORE
    _JOB_STORE = StudioJobStore()


ProgressCallback = Callable[[str, int, str], None]


def run_import_job_subprocess(job: StudioJob, payload: dict[str, Any]) -> None:
    from travelogue.web.studio_subprocess import ImportSubprocess

    store = get_job_store()
    handle = ImportSubprocess(payload)
    store.set_import_handle(job.job_id, handle)
    store.update(job, status="running", stage="ingest", stage_index=1)

    def worker() -> None:
        handle.start()
        try:
            finished = False
            while not finished:
                events = handle.drain()
                if not events and not handle.alive:
                    break
                for event in events:
                    if store.is_cancelled(job):
                        handle.cancel()
                        return
                    if event["type"] == "progress":
                        store.update(
                            job,
                            status="running",
                            stage=event["stage"],
                            stage_index=event["stageIndex"],
                            stage_hint=event.get("stageHint") or "",
                        )
                    elif event["type"] == "done":
                        if store.is_cancelled(job):
                            return
                        result = event["result"]
                        store.finalize(
                            job,
                            status="succeeded",
                            trip_id=result.get("tripId"),
                            result=result,
                        )
                        finished = True
                        break
                    elif event["type"] == "error":
                        if store.is_cancelled(job):
                            return
                        code = event.get("code") or "E_STUDIO_PIPELINE"
                        if code == "E_STUDIO_CANCELLED":
                            store.finalize(
                                job,
                                status="cancelled",
                                error={
                                    "code": code,
                                    "message": user_message(code),
                                },
                            )
                        elif event.get("demo"):
                            store.finalize(
                                job,
                                status="failed",
                                error={
                                    "code": code,
                                    "message": user_message(code, event.get("message", "")),
                                },
                            )
                        else:
                            store.finalize(
                                job,
                                status="failed",
                                error={
                                    "code": code,
                                    "message": user_message(code, event.get("message", code)),
                                },
                            )
                        finished = True
                        break
                if store.is_cancelled(job):
                    handle.cancel()
                    return
                if not finished:
                    time.sleep(0.15)
            if job.status not in ("succeeded", "failed", "cancelled"):
                store.finalize(
                    job,
                    status="failed",
                    error={
                        "code": "E_STUDIO_PIPELINE",
                        "message": user_message("E_STUDIO_PIPELINE"),
                    },
                )
        finally:
            handle.join(timeout=5.0)
            store.finish_import()
            store.pop_import_handle(job.job_id)

    threading.Thread(target=worker, daemon=True).start()


def run_longshot_job(
    job: StudioJob,
    *,
    runner: Callable[[], dict[str, Any]],
) -> None:
    store = get_job_store()
    store.update(job, status="running", stage="longshot", stage_index=1, stage_count=1)
    try:
        if store.is_cancelled(job):
            return
        result = runner()
        if store.is_cancelled(job):
            return
        store.finalize(
            job,
            status="succeeded",
            trip_id=result.get("tripId"),
            result=result,
        )
    except Exception as exc:
        if store.is_cancelled(job):
            return
        from travelogue.export.longshot import LongshotExportError

        if isinstance(exc, LongshotExportError):
            payload = {"code": exc.code, "message": user_message(exc.code, str(exc))}
        elif isinstance(exc, DemoError):
            payload = {"code": exc.code, "message": user_message(exc.code, str(exc))}
        else:
            payload = {
                "code": "E_LNG_CAPTURE_FAILED",
                "message": user_message("E_LNG_CAPTURE_FAILED", str(exc)),
            }
        store.finalize(job, status="failed", error=payload)
    finally:
        store.finish_longshot()


def run_narrate_job(
    job: StudioJob,
    *,
    runner: Callable[[], dict[str, Any]],
) -> None:
    store = get_job_store()
    store.update(
        job,
        status="running",
        stage="llm_narrate",
        stage_index=1,
        stage_count=1,
    )
    try:
        if store.is_cancelled(job):
            return
        result = runner()
        if store.is_cancelled(job):
            return
        store.finalize(
            job,
            status="succeeded",
            trip_id=result.get("tripId"),
            result=result,
        )
    except Exception as exc:
        if store.is_cancelled(job):
            return
        from travelogue.llm.errors import LlmError

        if isinstance(exc, LlmError):
            payload = {"code": exc.code, "message": user_message(exc.code, str(exc))}
        elif isinstance(exc, DemoError):
            payload = {"code": exc.code, "message": user_message(exc.code, str(exc))}
        elif isinstance(exc, FileNotFoundError):
            payload = {
                "code": "E_TRIP_NOT_FOUND",
                "message": user_message("E_TRIP_NOT_FOUND", str(exc)),
            }
        else:
            payload = {"code": "E_NARRATE_API", "message": user_message("E_NARRATE_API", str(exc))}
        store.finalize(job, status="failed", error=payload)
    finally:
        store.finish_narrate()


def run_g1_continue_job(
    job: StudioJob,
    *,
    runner: Callable[[], dict[str, Any]],
) -> None:
    store = get_job_store()
    store.update(
        job,
        status="running",
        stage="g1_continue",
        stage_index=1,
        stage_count=1,
    )
    try:
        if store.is_cancelled(job):
            return
        result = runner()
        if store.is_cancelled(job):
            return
        store.finalize(
            job,
            status="succeeded",
            trip_id=result.get("tripId"),
            result=result,
        )
    except Exception as exc:
        if store.is_cancelled(job):
            return
        if isinstance(exc, DemoError):
            payload = {"code": exc.code, "message": user_message(exc.code, str(exc))}
        else:
            payload = {"code": "E_STUDIO_PIPELINE", "message": str(exc)}
        store.finalize(job, status="failed", error=payload)
    finally:
        store.finish_g1()
