"""Studio longshot, zip export, reveal in folder, LLM narrate."""

from __future__ import annotations

import threading
from pathlib import Path

from travelogue.web.studio_errors import client_error_payload, user_message
from travelogue.web.studio_handlers.common import rel_to_trip, resolve_trip_dir, studio_ctx
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from travelogue.web.studio_jobs import get_job_store, run_longshot_job, run_narrate_job


def _respond_if_source_missing(handler: StudioHandlerProtocol, trip_id: str) -> bool:
    """Return True if response already written (sourceMissing block)."""
    import json

    from travelogue.media.source_resolve import assess_source_availability

    ctx = studio_ctx(handler)
    trip_dir = resolve_trip_dir(ctx, trip_id)
    if trip_dir is None:
        return False
    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        return False
    try:
        trip = json.loads(trip_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    health = assess_source_availability(trip, trip_dir)
    if not health.get("sourceMissing"):
        return False
    handler._json_response(
        409,
        {
            "ok": False,
            "error": "E_MEDIA_SOURCE_MISSING",
            "message": user_message("E_MEDIA_SOURCE_MISSING"),
            **health,
        },
    )
    return True


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


def handle_output_recipe(handler: StudioHandlerProtocol) -> None:
    """GET /__travelogue/output-recipe · Band/Intent 解析（不启动导出）."""
    import json
    from urllib.parse import parse_qs, urlparse

    from travelogue.export.output_recipe import (
        ambiguous_intent_options,
        count_kept_n,
        resolve_output_recipe,
    )
    from travelogue.export.output_recipe.types import OutputRecipeError

    query = parse_qs(urlparse(handler.path).query)
    trip_id = (query.get("tripId") or query.get("tripid") or [""])[0].strip()
    entrypoint = (query.get("entrypoint") or ["preview"])[0].strip() or "preview"
    if not trip_id:
        handler._json_response(400, {"ok": False, "error": "tripId required"})
        return

    ctx = studio_ctx(handler)
    trip_dir = resolve_trip_dir(ctx, trip_id)
    if trip_dir is None:
        handler._json_response(404, {"ok": False, "error": "trip not found"})
        return

    trip_json = trip_dir / "trip.json"
    try:
        trip = json.loads(trip_json.read_text(encoding="utf-8")) if trip_json.is_file() else {}
    except (OSError, json.JSONDecodeError):
        trip = {}

    or_cfg = getattr(ctx.cfg.studio, "output_recipe", None)
    enabled = bool(getattr(or_cfg, "enabled", False))
    try:
        recipe = resolve_output_recipe(
            trip=trip if isinstance(trip, dict) else None,
            entrypoint=entrypoint,
            enabled=enabled,
        )
    except OutputRecipeError as exc:
        handler._json_response(
            400,
            {"ok": False, "error": exc.code, "message": exc.message},
        )
        return

    options = (
        ambiguous_intent_options(phase="B", kept_n=recipe.kept_n)
        if recipe.needs_intent
        else []
    )
    handler._json_response(
        200,
        {
            "ok": True,
            "recipe": recipe.to_dict(),
            "intentOptions": options,
            "keptN": count_kept_n(trip if isinstance(trip, dict) else None),
        },
    )


def handle_longshot(handler: StudioHandlerProtocol) -> None:
    import json

    from travelogue.export.longshot import (
        DEFAULT_EXPORT_SCALE,
        export_trip_longshot,
        playwright_longshot_available,
    )
    from travelogue.export.output_recipe import count_kept_n, resolve_output_recipe
    from travelogue.export.output_recipe.types import OutputRecipeError
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

    if not payload.get("allowMissingSource"):
        blocked = _respond_if_source_missing(handler, trip_id)
        if blocked:
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
    trip_dir = resolve_trip_dir(ctx, trip_id)
    if trip_dir is None:
        handler._json_response(404, {"ok": False, "error": "trip not found"})
        return

    trip_json = trip_dir / "trip.json"
    try:
        trip = json.loads(trip_json.read_text(encoding="utf-8")) if trip_json.is_file() else {}
    except (OSError, json.JSONDecodeError):
        trip = {}

    or_cfg = getattr(cfg.studio, "output_recipe", None)
    recipe_enabled = bool(getattr(or_cfg, "enabled", False))
    entrypoint = str(payload.get("entrypoint") or "preview").strip() or "preview"
    intent_raw = payload.get("intent")
    intent = str(intent_raw).strip() if intent_raw not in (None, "") else None
    platform_raw = payload.get("platform")

    longshot2_enabled = bool(getattr(cfg.studio, "longshot2_enabled", True))
    from travelogue.config.studio import DEFAULT_LONGSHOT2_PLATFORMS

    allowed_platforms = list(
        getattr(cfg.studio, "longshot2_platforms", list(DEFAULT_LONGSHOT2_PLATFORMS))
    )
    if (recipe_enabled or intent) and "moments_grid" not in allowed_platforms:
        allowed_platforms.append("moments_grid")
    gcs_flag = getattr(cfg.studio, "gcs_poster_bric", None)
    gcs_poster_on = bool(getattr(gcs_flag, "enabled", False))
    if gcs_poster_on and "poster_bric" not in allowed_platforms:
        allowed_platforms.append("poster_bric")

    # AC-DFX-04 · flag off 时前后端双拒（禁止半开：UI 可见但任务成功走长图）
    platform_hint = (
        str(platform_raw).strip()
        if platform_raw not in (None, "")
        else ""
    )
    if (
        not gcs_poster_on
        and (intent == "poster_bric" or platform_hint == "poster_bric")
    ):
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_GCS_POSTER_DISABLED",
                "message": "单屏海报未开启（features.gcs_poster_bric.enabled=false）",
            },
        )
        return

    recipe = None
    use_recipe = bool(recipe_enabled or intent)
    if use_recipe:
        try:
            recipe = resolve_output_recipe(
                trip=trip if isinstance(trip, dict) else None,
                entrypoint=entrypoint,
                enabled=True if intent else recipe_enabled,
                intent=intent,
                platform=None if platform_raw in (None, "") else str(platform_raw),
            )
        except OutputRecipeError as exc:
            handler._json_response(
                400,
                {"ok": False, "error": exc.code, "message": exc.message},
            )
            return

        if recipe.needs_intent:
            handler._json_response(
                400,
                {
                    "ok": False,
                    "error": "E_OR_INTENT_REQUIRED",
                    "message": "请先选择分享方式",
                    "recipe": recipe.to_dict(),
                },
            )
            return

        platform_id = normalize_platform_id(recipe.platform or platform_raw)
        if platform_id == DEFAULT_PLATFORM and recipe.layout in ("chapter", "by_chapter"):
            segment_mode = "chapter"
        elif platform_id == DEFAULT_PLATFORM and recipe.layout == "single":
            segment_mode = "full"
    elif not longshot2_enabled:
        platform_id = DEFAULT_PLATFORM
    else:
        platform_id = normalize_platform_id(platform_raw)

    # Moments / grid: always export pure photos (ignore preview copy mode).
    if platform_id in ("wechat_moments", "moments_grid", "poster_bric"):
        from travelogue.render.copy_display import COPY_DISPLAY_PHOTOS

        copy_display = COPY_DISPLAY_PHOTOS

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

    # Validate platform before client fallback (AC-LNG2-05c / AC-OR-R03).
    try:
        profile = resolve_profile(
            platform_id,
            slide_count=slide_count,
            pad_mode=pad_mode,
            longshot2_enabled=longshot2_enabled or use_recipe,
            allowed_platforms=allowed_platforms if platform_id != DEFAULT_PLATFORM else None,
        )
    except PlatformProfileError as exc:
        handler._json_response(
            400,
            {"ok": False, "error": exc.code, "message": exc.message},
        )
        return

    # M-INS-0c · 真九宫格 / 单屏海报不需 Playwright；其余保留 client fallback。
    force_client = bool(payload.get("forceClient") or payload.get("clientOnly"))
    server_pack_platforms = frozenset({"moments_grid", "poster_bric"})
    if profile.id not in server_pack_platforms and (
        force_client or not playwright_longshot_available()
    ):
        handler._json_response(
            200,
            {
                "ok": True,
                "fallback": "client",
                "captureMethod": "p2",
                "tripId": trip_id,
                "message": user_message("E_LNG_CLIENT_FALLBACK"),
            },
        )
        return

    # Non-chat platforms ignore segmentMode (PRD §8.1)
    if profile.id != DEFAULT_PLATFORM:
        segment_mode = "auto"

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

        def cancel_check() -> bool:
            return store.is_cancelled(job)

        def cancel_register(abort: object) -> None:
            if callable(abort):
                store.set_longshot_abort(job.job_id, abort)  # type: ignore[arg-type]

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
            cancel_check=cancel_check,
            cancel_register=cancel_register,
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
            "outputFormat": getattr(result, "output_format", None) or fmt,
            "keptN": count_kept_n(trip if isinstance(trip, dict) else None),
            "intent": getattr(recipe, "intent", None) if recipe else None,
        }

    threading.Thread(
        target=lambda: run_longshot_job(job, runner=runner),
        daemon=True,
    ).start()
    handler._json_response(202, {"ok": True, "jobId": job.job_id})


def handle_longshot_upload(handler: StudioHandlerProtocol) -> None:
    """Accept client-captured longshot PNG/JPEG and write into the trip dir (D-INS-09)."""
    import base64
    import binascii

    from travelogue.export.longshot import (
        LongshotExportError,
        write_longshot_upload,
    )
    from travelogue.render.copy_display import COPY_DISPLAY_FULL

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

    fmt = str(payload.get("format") or "png").strip().lower()
    if fmt == "jpg":
        fmt = "jpeg"
    if fmt not in ("png", "jpeg"):
        handler._json_response(
            400,
            {"ok": False, "error": "invalid format", "message": "format 须为 png 或 jpeg"},
        )
        return

    raw_b64 = payload.get("data") or payload.get("base64") or ""
    if not isinstance(raw_b64, str) or not raw_b64.strip():
        handler._json_response(
            400,
            {"ok": False, "error": "E_LNG_CAPTURE_FAILED", "message": "缺少长图数据"},
        )
        return
    text = raw_b64.strip()
    if "," in text and text.lower().startswith("data:"):
        text = text.split(",", 1)[1]
    try:
        data = base64.b64decode(text, validate=False)
    except (binascii.Error, ValueError):
        handler._json_response(
            400,
            {"ok": False, "error": "E_LNG_CAPTURE_FAILED", "message": "长图数据无法解码"},
        )
        return

    segment_index = payload.get("segmentIndex")
    segment_total = payload.get("segmentTotal")
    try:
        seg_i = int(segment_index) if segment_index not in (None, "") else None
        seg_n = int(segment_total) if segment_total not in (None, "") else None
    except (TypeError, ValueError):
        handler._json_response(
            400,
            {"ok": False, "error": "invalid segment", "message": "分段序号无效"},
        )
        return

    filename = payload.get("filename") or payload.get("relPath")
    filename_s = str(filename).strip() if filename else None

    try:
        out = write_longshot_upload(
            trip_dir,
            data,
            fmt=fmt,
            filename=filename_s,
            segment_index=seg_i,
            segment_total=seg_n,
        )
    except LongshotExportError as exc:
        handler._json_response(400, client_error_payload(exc))
        return

    rel = rel_to_trip(trip_dir, out)
    platform = str(payload.get("platform") or "wechat_chat").strip() or "wechat_chat"
    copy_display = str(payload.get("copyDisplay") or COPY_DISPLAY_FULL).strip().lower()
    publish_guide = [
        "长图已保存到本机",
        "打开微信，按文件名顺序发到群聊",
        "可点『在文件夹中显示』找到文件",
    ]
    handler._json_response(
        200,
        {
            "ok": True,
            "tripId": trip_id,
            "outputs": [rel],
            "captureMethod": "p2",
            "segmented": bool(seg_n and seg_n > 1),
            "pageCount": seg_n or 1,
            "platform": platform,
            "copyDisplay": copy_display,
            "publishGuide": "\n".join(publish_guide),
            "userHint": "已使用兼容模式保存",
        },
    )


def handle_shutdown(handler: StudioHandlerProtocol) -> None:
    """Stop Studio HTTP server (loopback / authenticated desktop exit)."""
    from travelogue.web.studio_lifecycle import request_studio_shutdown

    if not request_studio_shutdown():
        handler._json_response(
            503,
            {
                "ok": False,
                "error": "E_STUDIO_SHUTDOWN",
                "message": "当前进程未注册可退出的 Studio 服务",
            },
        )
        return
    handler._json_response(
        200,
        {"ok": True, "message": user_message("E_STUDIO_SHUTDOWN")},
    )


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

    if not payload.get("allowMissingSource"):
        blocked = _respond_if_source_missing(handler, trip_id)
        if blocked:
            return

    try:
        zip_path = export_trip(trip_dir / "trip.json", confirm_privacy=True)
    except ExportError as exc:
        handler._json_response(400, client_error_payload(exc))
        return

    rel_zip = rel_to_trip(trip_dir, zip_path)
    handler._json_response(200, {"ok": True, "zipRelPath": rel_zip, "tripId": trip_id})
