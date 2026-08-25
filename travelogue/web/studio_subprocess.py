"""Run Studio import pipeline in a child process (M10 · GIL isolation)."""

from __future__ import annotations

import logging
import multiprocessing as mp
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)


def _write_import_diag(payload: dict[str, Any], code: str, message: str) -> None:
    """Persist the real failure (code + message + traceback) to a log file.

    The Studio import runs in a spawned child whose stderr is easy to lose
    (terminal cleared, no file handler configured). Writing a stable log file
    guarantees the underlying cause survives for diagnosis regardless of which
    pipeline stage failed.
    """
    try:
        base = payload.get("tripsDir")
        log_dir = Path(base).resolve().parent if base else Path.cwd()
        log_path = log_dir / "studio-import-error.log"
        block = (
            f"\n===== {datetime.now().isoformat(timespec='seconds')} =====\n"
            f"code={code}\n"
            f"album={payload.get('albumPath')!r} tripId={payload.get('tripId')!r} "
            f"mode={payload.get('mode') or payload.get('importMode')!r}\n"
            f"message={message}\n"
            f"{traceback.format_exc()}"
        )
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(block)
    except Exception:
        _log.exception("failed to write studio import diagnostic log")

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

    from travelogue.env import load_dotenv_files
    from travelogue.web.studio_config import resolve_studio_config

    load_dotenv_files()

    cfg: AppConfig | None = None
    cfg_path = payload.get("configPath")
    if cfg_path:
        cfg = get_config(reload=True, path=Path(cfg_path))
    else:
        resolved = resolve_studio_config()
        if resolved is not None:
            cfg = get_config(reload=True, path=resolved)

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
            mode=str(payload.get("mode") or payload.get("importMode") or "quick_share"),
            user_notes=payload.get("userNotes"),
            travel_notes=payload.get("travelNotes"),
            date_range=payload.get("dateRange") if isinstance(payload.get("dateRange"), dict) else None,
            plan_bytes=plan_bytes,
            plan_text=payload.get("planText"),
            plan_filename=str(payload.get("planFilename") or "plan.txt"),
            template_mode=str(payload.get("template_mode") or payload.get("templateMode") or "smart"),
            template_id=payload.get("template_id") or payload.get("templateId"),
            featured_dir=payload.get("featuredDir"),
            material_dir=payload.get("materialDir"),
            layout_density=payload.get("layoutDensity"),
            photo_cull_enabled=bool(payload.get("photoCullEnabled", False)),
            keep_near_duplicates=bool(payload.get("keepNearDuplicates", False)),
            photo_keep_mode=(
                str(payload.get("photoKeepMode")).strip()
                if payload.get("photoKeepMode")
                else None
            ),
            force_stub=bool(payload.get("forceStub")),
            edition=(
                str(payload.get("edition")).strip()
                if payload.get("edition")
                else None
            ),
            page_count=payload.get("pageCount"),
            page_count_source=(
                str(payload.get("pageCountSource")).strip()
                if payload.get("pageCountSource")
                else None
            ),
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
                    "sparseG1Suppressed": bool(
                        getattr(result, "sparse_g1_suppressed", False)
                    ),
                    "photoCount": result.photo_count,
                    "cullUserLine": result.cull_user_line or "",
                    "cullWarn": result.cull_warn or "",
                    "templateFeedbackKind": result.template_feedback_kind or "",
                    "templateFeedbackMessage": result.template_feedback_message or "",
                    "resolvedTemplateId": result.resolved_template_id or "visual-journal",
                    "mode": result.import_mode or "quick_share",
                    "layoutDensity": result.layout_density or "balanced",
                    "layoutDensityEffect": result.layout_density_effect or "ignored_quick",
                    "dateRangeWarn": result.date_range_warn or "",
                    "photoCullEnabled": result.photo_cull_enabled,
                    "layoutEligibleCount": result.layout_eligible_count,
                    "keepNearDuplicates": result.keep_near_duplicates,
                    "photoKeepMode": getattr(result, "photo_keep_mode", None)
                    or "recommended",
                    "assetsWritten": result.assets_written,
                    "mediaWarn": result.media_warn or "",
                    "titleNoiseFallback": bool(
                        getattr(result, "title_noise_fallback", False)
                    ),
                    "shelfCoverRelPath": getattr(
                        result, "shelf_cover_rel_path", ""
                    )
                    or "",
                    "displayTitle": result.title,
                    "edition": getattr(result, "edition", None) or "journal",
                    "overflowLine": getattr(result, "overflow_line", None) or "",
                    "overflowDetail": getattr(result, "overflow_detail", None) or "",
                    "portfolio": getattr(result, "portfolio", None),
                },
            }
        )
    except DemoError as exc:
        _write_import_diag(payload, exc.code, str(exc))
        progress_queue.put(
            {
                "type": "error",
                "code": exc.code,
                "message": user_message(exc.code, str(exc)),
                "demo": True,
            }
        )
    except Exception as exc:
        from travelogue.services.trip import TripSaveError

        if isinstance(exc, TripSaveError):
            code = getattr(exc, "code", None) or "E_TRIP_SAVE_BUSY"
            _write_import_diag(payload, code, f"{type(exc).__name__}: {exc}")
            progress_queue.put(
                {
                    "type": "error",
                    "code": code,
                    "message": user_message(code),
                    "demo": False,
                }
            )
            return
        _log.exception("studio import subprocess failed")
        _write_import_diag(payload, "E_STUDIO_PIPELINE", f"{type(exc).__name__}: {exc}")
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
