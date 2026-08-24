"""Studio background jobs (import pipeline)."""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from travelogue.demo.build import DemoError
from travelogue.web.studio_errors import job_error_payload, user_message
from travelogue.web.studio_stages import stage_hint

STAGE_COUNT = 4


def _run_longshot_abort(abort: Callable[[], None]) -> None:
    try:
        abort()
    except Exception:
        pass


@dataclass
class StudioJob:
    job_id: str
    type: str
    status: str = "queued"
    stage: str = ""
    stage_index: int = 0
    stage_count: int = STAGE_COUNT
    stage_hint: str = ""
    # PRD-BATCH-EXPORT-MULTISELECT-V1 · 批量导出的"当前平台内部"细粒度进度
    # （如拼贴页 3/5）。语义与 stage_index/stage_count（当前第几个平台/共几个
    # 平台）正交——两者都在跑，前者驱动 Task Dock 的单项进度条，后者驱动清单
    # 的逐平台状态。非批量 job 不设置，默认 None（前端据此判断是否渲染细进度条）。
    item_stage_index: int | None = None
    item_stage_count: int | None = None
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
            "itemStageIndex": self.item_stage_index,
            "itemStageCount": self.item_stage_count,
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
        self._longshot_active_id: str | None = None
        self._longshot_aborts: dict[str, Callable[[], None]] = {}
        # PDG · 独立 deleting 集合（禁止伪造 StudioJob）
        self._deleting_trip_ids: set[str] = set()

    def create_import_job(self) -> StudioJob | None:
        with self._lock:
            if self._import_running:
                return None
            job_id = f"job-{uuid.uuid4().hex[:12]}"
            job = StudioJob(job_id=job_id, type="import", status="queued")
            self._jobs[job_id] = job
            self._import_running = True
            return job

    def is_import_running(self) -> bool:
        with self._lock:
            return self._import_running

    def get(self, job_id: str) -> StudioJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def is_trip_busy(self, trip_id: str) -> bool:
        with self._lock:
            if trip_id in self._deleting_trip_ids:
                return True
            for job in self._jobs.values():
                if job.trip_id == trip_id and job.status in ("queued", "running"):
                    return True
        # CQA AC-10b · on-demand materialize counts as busy (outside job lock)
        from travelogue.media.derivatives import is_on_demand_alive_for_trip_id

        return is_on_demand_alive_for_trip_id(trip_id)

    def is_trip_deleting(self, trip_id: str) -> bool:
        with self._lock:
            return trip_id in self._deleting_trip_ids

    def begin_trip_delete(self, trip_id: str) -> bool:
        """Atomically mark trip deleting. False if busy (job or already deleting)."""
        with self._lock:
            if trip_id in self._deleting_trip_ids:
                return False
            for job in self._jobs.values():
                if job.trip_id == trip_id and job.status in ("queued", "running"):
                    return False
            self._deleting_trip_ids.add(trip_id)
            return True

    def end_trip_delete(self, trip_id: str) -> None:
        with self._lock:
            self._deleting_trip_ids.discard(trip_id)

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
        item_stage_index: int | None = None,
        item_stage_count: int | None = None,
        trip_id: str | None = None,
        error: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
    ) -> None:
        with self._lock:
            if job.status == "cancelled" and status is not None and status != "cancelled":
                # Cooperative cancel wins: never revive a cancelled job.
                status = None
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
            if item_stage_index is not None:
                job.item_stage_index = item_stage_index
            if item_stage_count is not None:
                job.item_stage_count = item_stage_count
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
            self._longshot_active_id = job_id
            return job

    def finish_longshot(self) -> None:
        with self._lock:
            active = self._longshot_active_id
            self._longshot_running = False
            self._longshot_active_id = None
            if active:
                self._longshot_aborts.pop(active, None)

    def set_longshot_abort(self, job_id: str, abort: Callable[[], None] | None) -> None:
        with self._lock:
            if abort is None:
                self._longshot_aborts.pop(job_id, None)
            else:
                self._longshot_aborts[job_id] = abort

    def await_longshot_done(self, job_id: str, timeout: float = 30.0) -> bool:
        """Wait until longshot worker finishes (slot released for this job)."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                if self._longshot_active_id != job_id:
                    return True
            time.sleep(0.1)
        with self._lock:
            return self._longshot_active_id != job_id

    def create_narrate_job(self) -> StudioJob | None:
        with self._lock:
            if self._narrate_running or self._import_running:
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
        abort: Callable[[], None] | None = None
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            if job.status not in ("queued", "running"):
                return job
            prev_status = job.status
            handle = self._import_handles.get(job_id)
            if handle is not None:
                handle.cancel()
            job.status = "cancelled"
            job.error = {
                "code": "E_STUDIO_CANCELLED",
                "message": user_message("E_STUDIO_CANCELLED"),
            }
            # Import with a live subprocess: keep busy lock until worker finally.
            # No handle (queued / tests): release immediately.
            if job.type == "import":
                if handle is None:
                    self._import_running = False
            elif job.type == "longshot":
                # Running worker: keep slot until finish_longshot (await).
                # Queued-only cancel: no worker yet → release immediately.
                abort = self._longshot_aborts.get(job_id)
                if prev_status == "queued":
                    self._longshot_running = False
                    self._longshot_active_id = None
                    self._longshot_aborts.pop(job_id, None)
                    abort = None
            elif job.type == "narrate":
                self._narrate_running = False
            elif job.type == "g1_continue":
                self._g1_running = False
        if abort is not None:
            threading.Thread(target=_run_longshot_abort, args=(abort,), daemon=True).start()
        return job

    def await_import_handle_done(self, job_id: str, timeout: float = 30.0) -> bool:
        """Wait until the import worker pops its handle (finally completed)."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                handle = self._import_handles.get(job_id)
            if handle is None:
                return True
            try:
                handle.join(timeout=0.2)
            except Exception:
                time.sleep(0.2)
        with self._lock:
            return job_id not in self._import_handles


_JOB_STORE = StudioJobStore()


def get_job_store() -> StudioJobStore:
    return _JOB_STORE


def reset_job_store() -> None:
    """Test helper: clear in-memory job state."""
    global _JOB_STORE
    _JOB_STORE = StudioJobStore()


ProgressCallback = Callable[[str, int, str], None]


def _cleanup_import_if_incomplete(job: StudioJob, payload: dict[str, Any]) -> None:
    """M3 · D-QH-05：cancelled/failed 且未 previewable 时清理半成品 + upload staging。"""
    if job.type != "import" or job.status not in ("cancelled", "failed"):
        return
    trips_raw = payload.get("tripsDir")
    if not trips_raw:
        return
    from pathlib import Path

    from travelogue.web.studio_incomplete_purge import cleanup_import_terminal_artifacts

    trip_id = job.trip_id or (str(payload.get("tripId") or "").strip() or None)
    if not trip_id:
        album = str(payload.get("albumPath") or "").strip()
        if album:
            from travelogue.util.trip_slug import demo_trip_id_from_album

            trip_id = demo_trip_id_from_album(
                Path(album),
                title=str(payload.get("title") or "") or None,
                place=str(payload.get("place") or "") or None,
                explicit=None,
            )

    cleanup_import_terminal_artifacts(
        Path(trips_raw),
        job_id=job.job_id,
        trip_id=trip_id,
        status=job.status,
    )


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
                        # ACP W2 · Intent Brief async stage (fail-open, non-blocking)
                        try:
                            from travelogue.web.studio_handlers.ai_ops_handlers import (
                                maybe_run_intent_brief_async,
                            )

                            tid = str(result.get("tripId") or "")
                            if tid:
                                maybe_run_intent_brief_async(tid)
                        except Exception:
                            pass
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
                                error=job_error_payload(code),
                            )
                        elif event.get("demo"):
                            store.finalize(
                                job,
                                status="failed",
                                error=job_error_payload(
                                    code, detail=str(event.get("message") or "")
                                ),
                            )
                        else:
                            store.finalize(
                                job,
                                status="failed",
                                error=job_error_payload(
                                    code, detail=str(event.get("message") or code)
                                ),
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
                    error=job_error_payload("E_STUDIO_PIPELINE"),
                )
        finally:
            handle.join(timeout=5.0)
            try:
                _cleanup_import_if_incomplete(job, payload)
            except Exception:
                _log = __import__("logging").getLogger(__name__)
                _log.exception("cleanup incomplete import failed for %s", job.job_id)
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
        from travelogue.export.longshot import LongshotCancelled, LongshotExportError

        if isinstance(exc, LongshotCancelled) or (
            isinstance(exc, LongshotExportError) and getattr(exc, "code", None) == "E_LNG_CANCELLED"
        ):
            return
        if isinstance(exc, LongshotExportError):
            payload = job_error_payload(exc.code, detail=str(exc))
        elif isinstance(exc, DemoError):
            payload = job_error_payload(exc.code, detail=str(exc))
        else:
            payload = job_error_payload("E_LNG_CAPTURE_FAILED", detail=str(exc))
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
            payload = job_error_payload(exc.code, detail=str(exc))
        elif isinstance(exc, DemoError):
            payload = job_error_payload(exc.code, detail=str(exc))
        elif isinstance(exc, FileNotFoundError):
            payload = job_error_payload("E_TRIP_NOT_FOUND", detail=str(exc))
        else:
            payload = job_error_payload("E_NARRATE_API", detail=str(exc))
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
            payload = job_error_payload(exc.code, detail=str(exc))
        else:
            payload = job_error_payload("E_STUDIO_PIPELINE")
        store.finalize(job, status="failed", error=payload)
    finally:
        store.finish_g1()
