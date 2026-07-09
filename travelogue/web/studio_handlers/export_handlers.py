"""Studio longshot, zip export, reveal in folder, LLM narrate."""

from __future__ import annotations

import threading
from pathlib import Path

from travelogue.web.studio_errors import client_error_payload, user_message
from travelogue.web.studio_handlers.common import rel_to_trip, resolve_trip_dir, studio_ctx
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from travelogue.web.studio_jobs import get_job_store, run_longshot_job, run_narrate_job


def handle_narrate(handler: StudioHandlerProtocol) -> None:
    from travelogue.services.pipeline_state import trip_status
    from travelogue.web.studio_narrate import run_studio_llm_narrate, studio_llm_status

    payload = handler._read_json_body()
    if not payload:
        return

    trip_id = str(payload.get("tripId") or "").strip()
    if not trip_id:
        handler._json_response(400, {"ok": False, "error": "tripId required"})
        return

    ctx = studio_ctx(handler)
    trip_dir = resolve_trip_dir(ctx, trip_id)
    if trip_dir is None:
        handler._json_response(404, {"ok": False, "error": "trip not found"})
        return

    trip = ctx.trip_service().load(trip_dir / "trip.json")
    if trip_status(trip) == "structure_draft":
        handler._json_response(
            409,
            {
                "ok": False,
                "error": "E_PIPELINE_ORDER",
                "message": "请先确认章节顺序",
            },
        )
        return

    llm_status = studio_llm_status(cfg=ctx.cfg)
    if not llm_status.get("llmAvailable"):
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_LLM_AUTH",
                "message": "未配置 LLM API Key，无法生成杂志感文案",
            },
        )
        return

    store = get_job_store()
    job = store.create_narrate_job()
    if job is None:
        handler._json_response(
            409,
            {
                "ok": False,
                "error": "E_STUDIO_JOB_BUSY",
                "message": "已有文案生成任务进行中，请稍候",
            },
        )
        return

    def runner() -> dict:
        return run_studio_llm_narrate(trip_dir, cfg=ctx.cfg, trips_dir=ctx.trips_root)

    threading.Thread(
        target=lambda: run_narrate_job(job, runner=runner),
        daemon=True,
    ).start()
    handler._json_response(202, {"ok": True, "jobId": job.job_id})


def handle_longshot(handler: StudioHandlerProtocol) -> None:
    from travelogue.export.longshot import DEFAULT_EXPORT_SCALE, export_trip_longshot
    from travelogue.export.platform_profiles import (
        DEFAULT_PLATFORM,
        PlatformProfileError,
        normalize_platform_id,
        resolve_profile,
    )
    from travelogue.render.copy_display import COPY_DISPLAY_FULL, VALID_COPY_DISPLAY

    payload = handler._read_json_body()
    if not payload:
        return

    trip_id = str(payload.get("tripId") or "").strip()
    if not trip_id:
        handler._json_response(400, {"ok": False, "error": "tripId required"})
        return

    try:
        scale = int(payload.get("scale") or DEFAULT_EXPORT_SCALE)
    except (TypeError, ValueError):
        handler._json_response(
            400,
            {"ok": False, "error": "invalid scale", "message": "scale 须为整数"},
        )
        return
    fmt = str(payload.get("format") or "png").strip().lower()
    if fmt not in ("png", "jpeg", "jpg"):
        handler._json_response(
            400,
            {"ok": False, "error": "invalid format", "message": "format 须为 png 或 jpeg"},
        )
        return
    if fmt == "jpg":
        fmt = "jpeg"

    copy_display_raw = payload.get("copyDisplay")
    if copy_display_raw is None or copy_display_raw == "":
        copy_display = COPY_DISPLAY_FULL
    else:
        copy_display = str(copy_display_raw).strip().lower()
        if copy_display not in VALID_COPY_DISPLAY:
            handler._json_response(
                400,
                {
                    "ok": False,
                    "error": "invalid copyDisplay",
                    "message": "copyDisplay 须为 full 或 photos",
                },
            )
            return

    from travelogue.export.longshot import VALID_SEGMENT_MODES

    segment_mode = str(payload.get("segmentMode") or "auto").strip().lower()
    if segment_mode not in VALID_SEGMENT_MODES:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "invalid segmentMode",
                "message": "segmentMode 须为 auto、full 或 chapter",
            },
        )
        return

    ctx = studio_ctx(handler)
    cfg = ctx.cfg
    longshot2_enabled = bool(getattr(cfg.studio, "longshot2_enabled", True))
    from travelogue.config.studio import DEFAULT_LONGSHOT2_PLATFORMS

    allowed_platforms = list(
        getattr(cfg.studio, "longshot2_platforms", list(DEFAULT_LONGSHOT2_PLATFORMS))
    )

    platform_raw = payload.get("platform")
    # When longshot2 disabled, ignore platform (PRD §13)
    if not longshot2_enabled:
        platform_id = DEFAULT_PLATFORM
    else:
        platform_id = normalize_platform_id(platform_raw)

    slide_count_raw = payload.get("slideCount")
    slide_count: int | None
    if slide_count_raw is None or slide_count_raw == "":
        slide_count = None
    else:
        try:
            slide_count = int(slide_count_raw)
        except (TypeError, ValueError):
            handler._json_response(
                400,
                {
                    "ok": False,
                    "error": "E_LNG2_INVALID_SLIDE_COUNT",
                    "message": "slideCount 须为整数",
                },
            )
            return

    pad_mode_raw = payload.get("padMode")
    pad_mode = (
        None
        if pad_mode_raw is None or pad_mode_raw == ""
        else str(pad_mode_raw).strip().lower()
    )

    try:
        profile = resolve_profile(
            platform_id,
            slide_count=slide_count,
            pad_mode=pad_mode,
            longshot2_enabled=longshot2_enabled,
            allowed_platforms=allowed_platforms if platform_id != DEFAULT_PLATFORM else None,
        )
    except PlatformProfileError as exc:
        handler._json_response(
            400,
            {"ok": False, "error": exc.code, "message": exc.message},
        )
        return

    # Non-chat platforms ignore segmentMode (PRD §8.1)
    if profile.id != DEFAULT_PLATFORM:
        segment_mode = "auto"

    trip_dir = resolve_trip_dir(ctx, trip_id)
    if trip_dir is None:
        handler._json_response(404, {"ok": False, "error": "trip not found"})
        return

    store = get_job_store()
    job = store.create_longshot_job()
    if job is None:
        handler._json_response(
            409,
            {
                "ok": False,
                "error": "E_STUDIO_JOB_BUSY",
                "message": "已有长图任务进行中，请稍候",
            },
        )
        return

    def runner() -> dict:
        def on_progress(cur: int, total: int, hint: str) -> None:
            store.update(
                job,
                stage_hint=hint,
                stage_index=max(cur, 0),
                stage_count=max(total, 1),
            )

        result = export_trip_longshot(
            trip_dir,
            scale=scale,
            fmt=fmt,
            progress=on_progress,
            copy_display=copy_display,
            segment_mode=segment_mode,
            platform=profile.id,
            slide_count=slide_count,
            pad_mode=pad_mode,
        )
        rel_outputs = [rel_to_trip(trip_dir, item.path) for item in result.outputs]
        page_count = result.page_count if result.page_count is not None else len(result.outputs)
        return {
            "tripId": trip_id,
            "outputs": rel_outputs,
            "captureMethod": result.capture_method,
            "segmented": result.segmented,
            "pageCount": page_count,
            "segmentReason": result.segment_reason,
            "userHint": result.user_hint,
            "platform": result.platform,
            "profileLabel": result.profile_label,
            "targetPageCount": result.target_page_count,
            "publishGuide": result.publish_guide,
        }

    threading.Thread(
        target=lambda: run_longshot_job(job, runner=runner),
        daemon=True,
    ).start()
    handler._json_response(202, {"ok": True, "jobId": job.job_id})


def handle_reveal(handler: StudioHandlerProtocol) -> None:
    from travelogue.export.longshot import LongshotExportError, reveal_path_in_folder

    payload = handler._read_json_body()
    if not payload:
        return

    ctx = studio_ctx(handler)
    trip_id = str(payload.get("tripId") or "").strip()
    rel_path = str(payload.get("relPath") or "").strip()
    path_raw = str(payload.get("path") or "").strip()

    if trip_id and rel_path:
        trip_dir = resolve_trip_dir(ctx, trip_id)
        if trip_dir is None:
            handler._json_response(404, {"ok": False, "error": "trip not found"})
            return
        target = (trip_dir / rel_path).resolve()
        try:
            target.relative_to(trip_dir.resolve())
        except ValueError:
            handler._json_response(
                403,
                {
                    "ok": False,
                    "error": "E_STUDIO_REVEAL_DENIED",
                    "message": user_message("E_STUDIO_REVEAL_DENIED"),
                },
            )
            return
        path_raw = str(target)

    if not path_raw:
        handler._json_response(400, {"ok": False, "error": "path or tripId+relPath required"})
        return

    try:
        reveal_path_in_folder(Path(path_raw), allowed_root=ctx.trips_root)
    except LongshotExportError as exc:
        handler._json_response(403, client_error_payload(exc))
        return

    handler._json_response(200, {"ok": True})


def handle_export(handler: StudioHandlerProtocol) -> None:
    from travelogue.export.packager import ExportError, export_trip

    payload = handler._read_json_body()
    if not payload:
        return

    trip_id = str(payload.get("tripId") or "").strip()
    if not trip_id:
        handler._json_response(400, {"ok": False, "error": "tripId required"})
        return

    ctx = studio_ctx(handler)
    trip_dir = resolve_trip_dir(ctx, trip_id)
    if trip_dir is None:
        handler._json_response(404, {"ok": False, "error": "trip not found"})
        return

    if not payload.get("confirmPrivacy"):
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_EXPORT_PRIVACY",
                "message": "导出 zip 需要确认隐私设置",
            },
        )
        return

    try:
        zip_path = export_trip(trip_dir / "trip.json", confirm_privacy=True)
    except ExportError as exc:
        handler._json_response(400, client_error_payload(exc))
        return

    rel_zip = rel_to_trip(trip_dir, zip_path)
    handler._json_response(200, {"ok": True, "zipRelPath": rel_zip, "tripId": trip_id})
