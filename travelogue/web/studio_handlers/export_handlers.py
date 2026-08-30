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


def _ensure_derivatives_for_export(trip_dir: Path) -> None:
    """D6 · sync-materialize missing HD tiers before zip/longshot export."""
    import json

    from travelogue.config import get_config
    from travelogue.media.derivatives import ensure_derivatives_before_export
    from travelogue.media.ingest import IngestError

    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        return
    try:
        trip = json.loads(trip_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(trip, dict):
        return
    result = ensure_derivatives_before_export(trip, trip_dir, app_cfg=get_config())
    if result.errors:
        raise IngestError(
            "E_DERIVATIVE_MATERIALIZE",
            f"derivative materialize failed: {result.errors[0]}",
        )
    trip_json.write_text(
        json.dumps(trip, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def handle_narrate(handler: StudioHandlerProtocol) -> None:
    from travelogue.services.pipeline_state import trip_status
    from travelogue.web.ai_surface import (
        ai_surface_disabled_body,
        resolve_ai_surface_for_request,
    )
    from travelogue.web.studio_narrate import run_studio_llm_narrate, studio_llm_status

    payload = handler._read_json_body()
    if not payload:
        return

    trip_id = str(payload.get("tripId") or "").strip()
    if not trip_id:
        handler._json_response(400, {"ok": False, "error": "tripId required"})
        return

    ctx = studio_ctx(handler)
    # NAS · BE-NAS-02：硬门闩，先于 trip / Key / status / Job（有 Key 亦 403）
    # 读盘最新旗标，避免 serve pin 的 app_config 与 GET /config 不一致
    if not resolve_ai_surface_for_request(handler):
        handler._json_response(403, ai_surface_disabled_body())
        return

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
                "message": "请先在「分章」中确认章节顺序",
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


def _handle_longshot_batch(
    handler: StudioHandlerProtocol,
    *,
    trip_id: str,
    trip_dir: Path,
    payload: dict,
    scale: int,
    fmt: str,
    copy_display: str,
    segment_mode: str,
    longshot2_enabled: bool,
    allowed_platforms: list[str],
    gcs_poster_on: bool,
) -> None:
    """POST /__travelogue/longshot · `platforms[]` 批量分支（PRD-BATCH-EXPORT-MULTISELECT-V1）。

    与单平台路径完全独立：跳过 Output Recipe / intent 解析（批量场景下用户已
    显式多选平台，无需再猜测"该导出成什么"，见 §4 D-BEX 决策）；逐项复用单
    平台路径已有的 `resolve_profile` / playwright fallback 校验规则，一处失败
    即整体拒绝提交（400），提交成功后才进入"逐项跑、单项失败不阻塞其余"的
    Job 内部循环（D-BEX-05，见 `export_trip_longshot_batch`）。
    """
    from travelogue.export.longshot import playwright_longshot_available
    from travelogue.export.longshot_batch import (
        BatchExportRequest,
        export_trip_longshot_batch,
    )
    from travelogue.export.platform_profiles import (
        COMPOSE_PLATFORM_IDS,
        DEFAULT_PLATFORM,
        PORTFOLIO_PLATFORM_IDS,
        PlatformProfileError,
        normalize_platform_id,
        resolve_profile,
    )
    from travelogue.render.copy_display import COPY_DISPLAY_PHOTOS

    platforms_raw = payload.get("platforms") or []

    seen_ids: set[str] = set()
    parsed: list[dict] = []
    for idx, item in enumerate(platforms_raw):
        if not isinstance(item, dict):
            handler._json_response(
                400,
                {
                    "ok": False,
                    "error": "E_LNG2_INVALID_BATCH_ITEM",
                    "message": f"platforms[{idx}] 须为对象",
                },
            )
            return
        raw_platform = item.get("platform")
        if not raw_platform:
            handler._json_response(
                400,
                {
                    "ok": False,
                    "error": "E_LNG2_INVALID_BATCH_ITEM",
                    "message": f"platforms[{idx}].platform 不能为空",
                },
            )
            return
        platform_id = normalize_platform_id(raw_platform)
        if platform_id in seen_ids:
            handler._json_response(
                400,
                {
                    "ok": False,
                    "error": "E_LNG2_DUPLICATE_PLATFORM",
                    "message": f"重复的导出平台：{platform_id}",
                },
            )
            return
        if platform_id in PORTFOLIO_PLATFORM_IDS:
            handler._json_response(
                400,
                {
                    "ok": False,
                    "error": "E_PORTFOLIO_NOT_BATCH",
                    "message": "作品集页图不进批量多选",
                },
            )
            return
        seen_ids.add(platform_id)

        if not gcs_poster_on and platform_id == "poster_bric":
            handler._json_response(
                400,
                {
                    "ok": False,
                    "error": "E_GCS_POSTER_DISABLED",
                    "message": "单屏海报未开启（features.gcs_poster_bric.enabled=false）",
                },
            )
            return

        item_slide_count_raw = item.get("slideCount")
        item_slide_count: int | None
        if item_slide_count_raw is None or item_slide_count_raw == "":
            item_slide_count = None
        else:
            try:
                item_slide_count = int(item_slide_count_raw)
            except (TypeError, ValueError):
                handler._json_response(
                    400,
                    {
                        "ok": False,
                        "error": "E_LNG2_INVALID_SLIDE_COUNT",
                        "message": f"platforms[{idx}].slideCount 须为整数",
                    },
                )
                return
        item_pad_mode_raw = item.get("padMode")
        item_pad_mode = (
            None
            if item_pad_mode_raw is None or item_pad_mode_raw == ""
            else str(item_pad_mode_raw).strip().lower()
        )

        try:
            profile = resolve_profile(
                platform_id,
                slide_count=item_slide_count,
                pad_mode=item_pad_mode,
                longshot2_enabled=longshot2_enabled,
                allowed_platforms=(
                    allowed_platforms if platform_id != DEFAULT_PLATFORM else None
                ),
            )
        except PlatformProfileError as exc:
            handler._json_response(
                400,
                {"ok": False, "error": exc.code, "message": f"[{platform_id}] {exc.message}"},
            )
            return

        parsed.append(
            {
                "platform_id": profile.id,
                "slide_count": item_slide_count,
                "pad_mode": item_pad_mode,
            }
        )

    if not parsed:
        handler._json_response(
            400,
            {"ok": False, "error": "E_LNG2_EMPTY_BATCH", "message": "platforms 不能为空"},
        )
        return

    # M-INS-0c 同款守门：批量暂不支持"部分平台走浏览器兼容模式"的混合态，
    # 缺 Playwright 时直接拒绝提交并指名哪些平台需单独导出（远比半开更安全）。
    # Compose / 九宫格走 Pillow，不依赖 Playwright（AC-ECC-05 / PRD-BATCH §2）。
    force_client = bool(payload.get("forceClient") or payload.get("clientOnly"))
    server_pack_platforms = COMPOSE_PLATFORM_IDS | {"moments_grid"}
    if force_client or not playwright_longshot_available():
        needs_playwright = [
            p["platform_id"] for p in parsed if p["platform_id"] not in server_pack_platforms
        ]
        if needs_playwright:
            handler._json_response(
                400,
                {
                    "ok": False,
                    "error": "E_LNG2_BATCH_CLIENT_FALLBACK_UNSUPPORTED",
                    "message": (
                        "批量导出暂不支持兼容模式，以下平台需单独导出："
                        + "、".join(needs_playwright)
                    ),
                },
            )
            return

    include_appendix = bool(payload.get("includeAppendix"))

    requests_out: list[BatchExportRequest] = []
    for p in parsed:
        item_segment_mode = segment_mode if p["platform_id"] == DEFAULT_PLATFORM else "auto"
        item_copy_display = (
            COPY_DISPLAY_PHOTOS
            if p["platform_id"] in ("wechat_moments", "moments_grid", "poster_bric")
            else copy_display
        )
        requests_out.append(
            BatchExportRequest(
                platform=p["platform_id"],
                slide_count=p["slide_count"],
                pad_mode=p["pad_mode"],
                segment_mode=item_segment_mode,
                copy_display=item_copy_display,
            )
        )

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
        from travelogue.export.longshot import write_longshot_current

        def on_progress(
            item_index: int, item_total: int, item_platform: str, cur: int, total: int, hint: str
        ) -> None:
            prefix = f"[{item_index + 1}/{item_total}] {item_platform}"
            # 细粒度进度条（Task Dock 单项进度）：cur/total 来自当前平台自身的
            # 渲染回调（如 collage_pack 的「拼贴页 i/total」），与 stage_index/
            # stage_count（当前第几个平台/共几个平台）语义正交、互不覆盖。
            store.update(
                job,
                stage_hint=f"{prefix} · {hint}" if hint else prefix,
                stage_index=item_index + 1,
                stage_count=item_total,
                item_stage_index=max(cur, 0),
                item_stage_count=max(total, 1),
            )

        def cancel_check() -> bool:
            return store.is_cancelled(job)

        def cancel_register(abort: object) -> None:
            if callable(abort):
                store.set_longshot_abort(job.job_id, abort)  # type: ignore[arg-type]

        _ensure_derivatives_for_export(trip_dir)
        batch_results = export_trip_longshot_batch(
            trip_dir,
            requests=requests_out,
            common={"scale": scale, "fmt": fmt, "include_appendix": include_appendix},
            progress=on_progress,
            cancel_check=cancel_check,
            cancel_register=cancel_register,
        )

        items: list[dict] = []
        succeeded = 0
        failed = 0
        last_success_rel_outputs: list[str] | None = None
        last_success_kind: str | None = None
        for item_result in batch_results:
            if item_result.ok and item_result.result is not None:
                succeeded += 1
                result = item_result.result
                rel_outputs = [rel_to_trip(trip_dir, out.path) for out in result.outputs]
                page_count = (
                    result.page_count if result.page_count is not None else len(result.outputs)
                )
                items.append(
                    {
                        "platform": result.platform,
                        "ok": True,
                        "outputs": rel_outputs,
                        "captureMethod": result.capture_method,
                        "segmented": result.segmented,
                        "pageCount": page_count,
                        "segmentReason": result.segment_reason,
                        "userHint": result.user_hint,
                        "profileLabel": result.profile_label,
                        "targetPageCount": result.target_page_count,
                        "publishGuide": result.publish_guide,
                        "outputFormat": getattr(result, "output_format", None) or fmt,
                    }
                )
                if rel_outputs:
                    last_success_rel_outputs = rel_outputs
                    last_success_kind = "segmented" if result.segmented else "whole"
            else:
                failed += 1
                code = item_result.error_code or "E_LNG_CAPTURE_FAILED"
                items.append(
                    {
                        "platform": item_result.platform,
                        "ok": False,
                        "error": code,
                        "message": user_message(code, item_result.error_message),
                    }
                )

        # QFX D-QFX-06b 同款约束：仅用最后一个成功平台的产物更新
        # longshot-current.json（该文件本就是"单一 batch/清单"语义，暂不支持
        # 多平台合并追踪——留作 OQ-BEX-04，见 PRD 变更记录）。
        if last_success_rel_outputs:
            write_longshot_current(
                trip_dir,
                batch_id=job.job_id,
                kind=last_success_kind or "whole",
                files=last_success_rel_outputs,
            )

        return {
            "tripId": trip_id,
            "batch": True,
            "items": items,
            "succeededCount": succeeded,
            "failedCount": failed,
        }

    threading.Thread(
        target=lambda: run_longshot_job(job, runner=runner),
        daemon=True,
    ).start()
    handler._json_response(202, {"ok": True, "jobId": job.job_id})


def handle_longshot(handler: StudioHandlerProtocol) -> None:
    import json

    from travelogue.export.dispatch import dispatch_export
    from travelogue.export.longshot import (
        DEFAULT_EXPORT_SCALE,
        playwright_longshot_available,
    )
    from travelogue.export.output_recipe import (
        apply_recipe_layout_to_segment_mode,
        count_kept_n,
        resolve_output_recipe,
    )
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
    if platform_raw not in (None, ""):
        platform_raw = normalize_platform_id(platform_raw)

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

    # PRD-BATCH-EXPORT-MULTISELECT-V1 D-BEX-02 · platforms[] 批量分支，与单平台
    # 路径（下方）完全独立、互不影响；未带 platforms 字段时行为零改动（向后兼容）。
    # 一旦请求显式携带 platforms 键，必须走批量校验（空数组/非 list 直接 400），
    # 禁止静默退回单平台默认导出（避免契约错配）。
    if "platforms" in payload:
        platforms_raw = payload.get("platforms")
        if not isinstance(platforms_raw, list):
            handler._json_response(
                400,
                {
                    "ok": False,
                    "error": "E_LNG2_INVALID_BATCH_ITEM",
                    "message": "platforms 须为数组",
                },
            )
            return
        if not platforms_raw:
            handler._json_response(
                400,
                {
                    "ok": False,
                    "error": "E_LNG2_EMPTY_BATCH",
                    "message": "platforms 不能为空",
                },
            )
            return
        _handle_longshot_batch(
            handler,
            trip_id=trip_id,
            trip_dir=trip_dir,
            payload=payload,
            scale=scale,
            fmt=fmt,
            copy_display=copy_display,
            segment_mode=segment_mode,
            longshot2_enabled=longshot2_enabled,
            allowed_platforms=allowed_platforms,
            gcs_poster_on=gcs_poster_on,
        )
        return

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

    from travelogue.export.portfolio_pages import is_portfolio_pages_platform

    recipe = None
    portfolio_pages_request = is_portfolio_pages_platform(platform_raw)
    use_recipe = bool(recipe_enabled or intent) and not portfolio_pages_request
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

        if recipe.source == "portfolio_bypass":
            handler._json_response(
                400,
                {
                    "ok": False,
                    "error": "E_PORTFOLIO_PACK_REQUIRED",
                    "message": "作品集请导出这一本与页图，不要走群长图",
                    "recipe": recipe.to_dict(),
                },
            )
            return

        platform_id = normalize_platform_id(recipe.platform or platform_raw)
        segment_mode = apply_recipe_layout_to_segment_mode(
            segment_mode,
            recipe_layout=recipe.layout,
            platform_id=platform_id,
            wechat_platform=DEFAULT_PLATFORM,
        )
    elif portfolio_pages_request:
        platform_id = normalize_platform_id(platform_raw)
    elif not longshot2_enabled:
        platform_id = DEFAULT_PLATFORM
    else:
        platform_id = normalize_platform_id(platform_raw)

    from travelogue.config.edition import is_portfolio_trip

    explicit_platform = str(platform_raw or "").strip() not in ("",)
    if is_portfolio_trip(trip) and platform_id == DEFAULT_PLATFORM and not explicit_platform:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_PORTFOLIO_PACK_REQUIRED",
                "message": "作品集请导出这一本与页图，不要走群长图",
            },
        )
        return
    if is_portfolio_trip(trip) and platform_id in ("wechat_chat", "wechat_moments"):
        handler._json_response(
            409,
            {
                "ok": False,
                "error": "E_CLG_NEEDS_JOURNAL",
                "code": "E_CLG_NEEDS_JOURNAL",
                "message": "长图要在游记里做",
            },
        )
        return

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
    include_appendix = bool(payload.get("includeAppendix"))

    include_zip = True
    include_pages = True
    if portfolio_pages_request:
        piece = str(payload.get("portfolioPiece") or "").strip().lower()
        if piece == "pages" or payload.get("includeZip") is False:
            include_zip = False
        if piece == "book" or payload.get("includePages") is False:
            include_pages = False

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

    # M-INS-0c · 真九宫格 / Compose 拼贴（小红书/公众号/画册/海报）不需 Playwright；
    # 其余保留 client fallback（AC-ECC-05）。
    from travelogue.export.platform_profiles import COMPOSE_PLATFORM_IDS, PORTFOLIO_PLATFORM_IDS

    force_client = bool(payload.get("forceClient") or payload.get("clientOnly"))
    server_pack_platforms = COMPOSE_PLATFORM_IDS | {"moments_grid"} | PORTFOLIO_PLATFORM_IDS
    # ISO-04 · 作品集显式微信群走 kept 池，禁止 client 拍 page-* flatten
    skip_client_fallback = profile.id in server_pack_platforms or (
        is_portfolio_trip(trip) and platform_id == DEFAULT_PLATFORM
    )
    if not skip_client_fallback and (
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

        _ensure_derivatives_for_export(trip_dir)
        result = dispatch_export(
            trip_dir,
            scale=scale,
            fmt=fmt,
            progress=on_progress,
            copy_display=copy_display,
            segment_mode=segment_mode,
            platform=profile.id,
            slide_count=slide_count,
            pad_mode=pad_mode,
            include_appendix=include_appendix,
            cancel_check=cancel_check,
            cancel_register=cancel_register,
            include_zip=include_zip,
            include_pages=include_pages,
        )
        rel_outputs = [rel_to_trip(trip_dir, item.path) for item in result.outputs]
        page_count = result.page_count if result.page_count is not None else len(result.outputs)
        # QFX D-QFX-06b · Job 成功后写最小 current（失败则 Job 不标 succeeded）
        from travelogue.export.longshot import write_longshot_current

        if rel_outputs:
            write_longshot_current(
                trip_dir,
                batch_id=job.job_id,
                kind="segmented" if result.segmented else "whole",
                files=rel_outputs,
            )
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
            "skippedPages": list(getattr(result, "skipped_pages", None) or []),
            "shareZip": (
                rel_to_trip(trip_dir, result.share_zip)
                if getattr(result, "share_zip", None)
                else None
            ),
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
        maybe_write_longshot_current_after_upload,
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
    # CQA AC-13 / D-07 · reject reserved + script/shell suffixes (disk name still server-owned)
    from travelogue.export.longshot import client_longshot_filename_denied

    if client_longshot_filename_denied(filename_s):
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_LNG_CAPTURE_FAILED",
                "message": "非法输出文件名",
            },
        )
        return

    try:
        out = write_longshot_upload(
            trip_dir,
            data,
            fmt=fmt,
            filename=None,  # I-CQA-09 · never trust client name for disk
            segment_index=seg_i,
            segment_total=seg_n,
        )
    except LongshotExportError as exc:
        handler._json_response(400, client_error_payload(exc))
        return

    rel = rel_to_trip(trip_dir, out)
    try:
        current_path = maybe_write_longshot_current_after_upload(
            trip_dir,
            rel=rel,
            segment_index=seg_i,
            segment_total=seg_n,
            fmt=fmt,
            batch_id=str(payload.get("batchId") or payload.get("jobId") or "").strip()
            or None,
        )
    except (OSError, ValueError, TypeError) as exc:
        handler._json_response(
            500,
            {
                "ok": False,
                "error": "E_LNG_CURRENT_WRITE",
                "message": "长图已保存，但权威清单写入失败",
                "detail": str(exc)[:240],
            },
        )
        return
    platform = str(payload.get("platform") or "wechat_chat").strip() or "wechat_chat"
    copy_display = str(payload.get("copyDisplay") or COPY_DISPLAY_FULL).strip().lower()
    if current_path is not None:
        from travelogue.export.longshot import default_longshot_output_name
        from travelogue.export.output_ledger import (
            OutputLedgerError,
            load_trip_dict,
            lookup_output_meta,
            output_ledger_enabled,
            record_successful_output,
            spec_from_profile,
        )
        from travelogue.render.context import longshot_bundle_version

        if output_ledger_enabled():
            if seg_n and seg_n > 1:
                ledger_files = [
                    default_longshot_output_name(
                        trip_dir,
                        fmt=fmt,
                        segment_index=i,
                        segment_total=seg_n,
                    )
                    for i in range(1, seg_n + 1)
                ]
            else:
                ledger_files = [Path(rel).name]
            trip = load_trip_dict(trip_dir)
            ledger_profile = "wechat_chat"
            meta = lookup_output_meta(platform, segmented=bool(seg_n and seg_n > 1))
            if meta is not None and meta.surface not in ("folio", "bundle", "spread"):
                ledger_profile = meta.profile
            try:
                record_successful_output(
                    trip_dir,
                    trip=trip,
                    profile=ledger_profile,
                    files=ledger_files,
                    spec=spec_from_profile(ledger_profile, scale=1, fmt=fmt),
                    bundle_fp=longshot_bundle_version(trip),
                    batch_id=str(payload.get("batchId") or payload.get("jobId") or "").strip(),
                    segmented=bool(seg_n and seg_n > 1),
                )
            except OutputLedgerError as exc:
                handler._json_response(
                    500,
                    {
                        "ok": False,
                        "error": "E_OUTPUT_LEDGER",
                        "message": "长图已保存，但成品清单写入失败",
                        "detail": str(exc)[:240],
                    },
                )
                return
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
        _ensure_derivatives_for_export(trip_dir)
        zip_path = export_trip(trip_dir / "trip.json", confirm_privacy=True)
    except ExportError as exc:
        handler._json_response(400, client_error_payload(exc))
        return
    except Exception as exc:
        from travelogue.media.ingest import IngestError

        if isinstance(exc, IngestError):
            handler._json_response(400, client_error_payload(exc))
            return
        raise

    rel_zip = rel_to_trip(trip_dir, zip_path)
    handler._json_response(200, {"ok": True, "zipRelPath": rel_zip, "tripId": trip_id})
