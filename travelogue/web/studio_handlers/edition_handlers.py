"""PFM · 精修/书架切成册身份（BE-PFM-15）。只从 curate 装配段重入。"""

from __future__ import annotations

import copy
import logging
import threading

from travelogue.config.edition import (
    EDITION_PORTFOLIO,
    E_PORTFOLIO_PAGE_COUNT,
    E_PORTFOLIO_PAGES_JOURNAL,
    E_PORTFOLIO_UNAVAILABLE,
    PortfolioUnavailableError,
    apply_refine_edition,
    apply_refine_page_count,
    is_portfolio_pipeline_enabled,
    make_studio_edition_mutator,
    normalize_edition,
    portfolio_pipeline_config,
    read_page_count_intent,
    resolve_edition,
)
from travelogue.web.studio_errors import user_message
from travelogue.web.studio_handlers.common import (
    load_trip_or_404,
    respond_if_trip_busy,
    studio_ctx,
)
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from travelogue.web.studio_jobs import get_job_store, run_g1_continue_job

_log = logging.getLogger(__name__)

E_PORTFOLIO_CONFIRM_REQUIRED = "E_PORTFOLIO_CONFIRM_REQUIRED"
E_PORTFOLIO_SWITCH_DISABLED = "E_PORTFOLIO_SWITCH_DISABLED"

_PERSIST_KEYS = (
    "chapters",
    "curation",
    "pipeline",
    "layoutEngine",
    "layoutEngineVersion",
    "exportLayout",
    "studio",
    "items",
)


def handle_trip_edition(handler: StudioHandlerProtocol, trip_id: str) -> None:
    """POST /__travelogue/trips/{tripId}/edition — stamp identity, compose, render."""
    payload = handler._read_json_body() or {}
    confirmed = payload.get("confirmed") is True
    pages_changing = "pageCount" in payload

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip0 = loaded
    current = resolve_edition(trip0)
    target = (
        normalize_edition(payload.get("edition"))
        if "edition" in payload
        else current
    )
    identity_changing = target != current

    page_source = None
    page_n = None
    if pages_changing:
        if target != EDITION_PORTFOLIO:
            handler._json_response(
                400,
                {
                    "ok": False,
                    "error": E_PORTFOLIO_PAGES_JOURNAL,
                    "message": "页数只能在作品集精修改",
                },
            )
            return
        try:
            page_source, page_n = apply_refine_page_count({}, payload.get("pageCount"))
        except ValueError:
            handler._json_response(
                400,
                {
                    "ok": False,
                    "error": E_PORTFOLIO_PAGE_COUNT,
                    "message": "页数无效",
                },
            )
            return
        cur_source, cur_n = read_page_count_intent(trip0)
        pages_changing = (page_source, page_n) != (cur_source, cur_n)

    if not identity_changing and not pages_changing:
        handler._json_response(
            200,
            {"ok": True, "edition": current, "unchanged": True},
        )
        return

    if identity_changing and not confirmed:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": E_PORTFOLIO_CONFIRM_REQUIRED,
                "message": "切换成册类型前请确认页面将重排",
            },
        )
        return

    ctx = studio_ctx(handler)
    pipe = portfolio_pipeline_config(ctx.cfg)
    if target == EDITION_PORTFOLIO and identity_changing:
        if not is_portfolio_pipeline_enabled(ctx.cfg):
            handler._json_response(
                409,
                {
                    "ok": False,
                    "error": E_PORTFOLIO_UNAVAILABLE,
                    "message": "此功能已关闭",
                },
            )
            return
        if not pipe.allow_refine_switch:
            handler._json_response(
                409,
                {
                    "ok": False,
                    "error": E_PORTFOLIO_SWITCH_DISABLED,
                    "message": "精修切换未开启",
                },
            )
            return

    if respond_if_trip_busy(handler, trip_id):
        return

    trip_json = trip_dir / "trip.json"
    svc = ctx.trip_service()

    def runner() -> dict:
        from travelogue.curation.curate import CurateError, run_curate
        from travelogue.demo.build import DemoError
        from travelogue.domain.copy_migrate import (
            collect_user_copy,
            migrate_copy_after_recompose,
        )
        from travelogue.domain.pipeline_view import (
            revert_copy_lock_for_edit,
            set_pipeline_lock,
            unlock_structure_for_replan,
        )
        from travelogue.render.engine import render_trip_surfaces

        trip = svc.load(trip_json)
        snapshot = {k: copy.deepcopy(trip.get(k)) for k in _PERSIST_KEYS}
        try:
            if identity_changing:
                apply_refine_edition(trip, target, ctx.cfg)
            if pages_changing and target == EDITION_PORTFOLIO:
                apply_refine_page_count(trip, payload.get("pageCount"))
        except PortfolioUnavailableError as exc:
            raise DemoError(exc.code, str(exc)) from exc
        except ValueError as exc:
            raise DemoError(E_PORTFOLIO_PAGE_COUNT, str(exc)) from exc

        unlock_structure_for_replan(trip)
        copy_fragments = collect_user_copy(trip)
        try:
            run_curate(
                trip,
                export_layout="auto",
                apply_layout=True,
                trip_dir=trip_dir,
                cfg=ctx.cfg,
                refresh_algorithms=False,
                scope="full",
            )
        except CurateError as exc:
            raise DemoError(exc.code, str(exc)) from exc

        migrate_copy_after_recompose(trip, copy_fragments, edition=target)
        # 确认模态已问过；structure 解锁会把 status 降到 structure_draft，
        # revert 只认 copy_locked，所以再清一次 leftover copy 锁。
        revert_copy_lock_for_edit(trip)
        set_pipeline_lock(trip, "copy", False)

        def mutator(t: dict) -> None:
            for key in _PERSIST_KEYS:
                if key == "studio":
                    continue
                if key in trip:
                    t[key] = trip[key]
            make_studio_edition_mutator(trip)(t)

        svc.update(trip_json, mutator)
        try:
            render_trip_surfaces(
                trip_json,
                trip_dir,
                export_mode="draft",
                validate=False,
                update_pipeline=False,
                stamp_render_bundle=True,
                cfg=ctx.cfg,
            )
        except Exception:
            def restore(t: dict) -> None:
                for key, value in snapshot.items():
                    if value is None:
                        t.pop(key, None)
                    else:
                        t[key] = copy.deepcopy(value)

            try:
                svc.update(trip_json, restore)
            except Exception:
                _log.exception(
                    "edition switch render failed and rollback also failed trip_id=%s",
                    trip_id,
                )
            raise
        return {"tripId": trip_id, "edition": target, "pageCount": page_n, "pageCountSource": page_source or "auto"}

    store = get_job_store()
    job = store.create_g1_continue_job()
    if job is None:
        handler._json_response(
            409,
            {
                "ok": False,
                "error": "E_STUDIO_JOB_BUSY",
                "message": user_message("E_STUDIO_JOB_BUSY"),
            },
        )
        return
    store.update(job, trip_id=trip_id)
    threading.Thread(
        target=lambda: run_g1_continue_job(job, runner=runner),
        daemon=True,
    ).start()
    handler._json_response(
        202,
        {
            "ok": True,
            "jobId": job.job_id,
            "edition": target,
            "pageCount": page_n,
            "pageCountSource": page_source or "auto",
        },
    )
