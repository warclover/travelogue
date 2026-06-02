"""Run Studio import pipeline in a child process (M10 · GIL isolation)."""

from __future__ import annotations

import logging
import multiprocessing as mp
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

def _import_worker(payload: dict[str, Any], progress_queue: mp.Queue, cancel_event: mp.Event) -> None:
    from travelogue.config import AppConfig, get_config
    from travelogue.demo.build import DemoError
    from travelogue.web.studio_errors import user_message
    from travelogue.web.studio_pipeline import run_studio_pipeline

    def progress(stage: str, stage_index: int, stage_hint: str) -> None:
        if cancel_event.is_set():
            raise DemoError("E_STUDIO_CANCELLED", "cancelled")
        progress_queue.put(
            {
                "type": "progress",
                "stage": stage,
                "stageIndex": stage_index,
                "stageHint": stage_hint,
            }
        )

    cfg: AppConfig | None = None
    cfg_path = payload.get("configPath")
    if cfg_path:
        cfg = get_config(reload=True, path=Path(cfg_path))

    plan_bytes: bytes | None = None
    raw_plan = payload.get("planBytes")
    if isinstance(raw_plan, (bytes, bytearray)):
        plan_bytes = bytes(raw_plan)
    elif isinstance(raw_plan, str) and raw_plan:
        import base64

        plan_bytes = base64.b64decode(raw_plan.encode("ascii"))

    try:
        result = run_studio_pipeline(
            Path(payload["albumPath"]),
            trips_dir=Path(payload["tripsDir"]) if payload.get("tripsDir") else None,
            trip_id=payload.get("tripId"),
            title=str(payload.get("title") or "我的旅途"),
            place=str(payload.get("place") or "旅途"),
            place_user_set=(
                bool(payload["placeUserSet"])
                if "placeUserSet" in payload
                else None
            ),
            force=bool(payload.get("force")),
            dedupe=bool(payload.get("dedupe", True)),
            host=str(payload.get("host") or "127.0.0.1"),
            port=int(payload.get("port") or 8766),
            config=Path(cfg_path) if cfg_path else None,
            app_config=cfg,
            progress=progress,
            user_notes=payload.get("userNotes"),
            plan_bytes=plan_bytes,
            plan_text=payload.get("planText"),
            plan_filename=str(payload.get("planFilename") or "plan.txt"),
        )
        progress_queue.put(
            {
                "type": "done",
                "result": {
                    "tripId": result.trip_id,
                    "tripDir": str(result.trip_dir),
                    "previewUrl": result.preview_url,
                    "clusterNotice": result.cluster_notice or "",
                    "title": result.title,
                    "intentLine": result.intent_line,
                    "featuredCount": result.featured_count,
                    "segmentCount": result.segment_count,
                    "tierMode": result.tier_mode,
                    "g1Pending": result.g1_pending,
                    "photoCount": result.photo_count,
                    "cullUserLine": result.cull_user_line or "",
                    "cullWarn": result.cull_warn or "",
                },
            }
        )
    except DemoError as exc:
        progress_queue.put(
            {
                "type": "error",
                "code": exc.code,
                "message": user_message(exc.code, str(exc)),
                "demo": True,
            }
        )
    except Exception:
        _log.exception("studio import subprocess failed")
        progress_queue.put(
            {
                "type": "error",
                "code": "E_STUDIO_PIPELINE",
                "message": user_message("E_STUDIO_PIPELINE"),
                "demo": False,
            }
        )


class ImportSubprocess:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._ctx = mp.get_context("spawn")
        self._cancel = self._ctx.Event()
        self._queue: mp.Queue = self._ctx.Queue()
        self._process = self._ctx.Process(
            target=_import_worker,
            args=(payload, self._queue, self._cancel),
            daemon=True,
        )

    def start(self) -> None:
        self._process.start()

    def cancel(self) -> None:
        self._cancel.set()
        if self._process.is_alive():
            self._process.terminate()

    def join(self, timeout: float | None = None) -> None:
        self._process.join(timeout)

    @property
    def alive(self) -> bool:
        return self._process.is_alive()

    def drain(self) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        while True:
            try:
                events.append(self._queue.get_nowait())
            except Exception:
                break
        return events
