"""Studio · LVP layout vibe apply handler (M2)."""

from __future__ import annotations

import copy
import logging
import threading

from travelogue.config.layout_vibe import (
    KNOWN_VIBES,
    VIBE_FIT_PHOTO_EXPERIMENTAL,
    VIBE_MAGAZINE_DEFAULT,
    resolve_layout_vibe,
    set_trip_layout_vibe,
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

# BLK-LVP-03 · draft copy pending product/UX sign-off (shipped as UI defaults)
EXPERIMENTAL_CONFIRM_TITLE = "改用「更贴照片比例」？"
EXPERIMENTAL_CONFIRM_BODY = (
    "拼图会更贴原图比例，章节页数或篇幅可能变化。"
    "随时可在「成册风格」改回「杂志成册（推荐）」。"
)

# Keys LVP may rewrite; snapshotted for render-failure rollback.
_LVP_PERSIST_KEYS = (
    "chapters",
    "curation",
    "pipeline",
    "layoutEngine",
    "layoutEngineVersion",
    "exportLayout",
    "studio",
)


def layout_vibe_options() -> list[dict[str, str]]:
    """User-facing cards (no algorithm abbreviations · AC-LVP-04)."""
    return [
        {
            "id": VIBE_MAGAZINE_DEFAULT,
            "label": "杂志成册（推荐）",
            "consequence": "宽画幅节奏稳，单反 3:2 少进扁四宫",
            "badge": "推荐",
        },
        {
            "id": VIBE_FIT_PHOTO_EXPERIMENTAL,
            "label": "更贴照片比例（实验）",
            "consequence": "加权拼图轨道更贴原图，章节页数可能变",
            "badge": "实验",
        },
    ]


def _explicit_confirm(payload: dict) -> bool:
    """AC-LVP-05 · only literal JSON true counts (reject \"false\"/1/\"0\")."""
    for key in ("confirmedExperimental", "confirmed_experimental", "confirmed"):
        if key in payload:
            return payload[key] is True
    return False


def handle_layout_vibe(handler: StudioHandlerProtocol, trip_id: str) -> None:
    """POST /__travelogue/trips/{tripId}/layout-vibe — persist vibe, layout, render."""
    payload = handler._read_json_body() or {}
    raw = str(payload.get("layoutVibe") or payload.get("layout_vibe") or "").strip()
    confirmed = _explicit_confirm(payload)

    if raw not in KNOWN_VIBES:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_LVP_UNKNOWN_VIBE",
                "message": "未知的成册风格",
            },
        )
        return

    # AC-LVP-05 · experimental requires explicit confirm
    if raw == VIBE_FIT_PHOTO_EXPERIMENTAL and not confirmed:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_LVP_CONFIRM_REQUIRED",
                "message": "选用实验风格前请确认可能改变章节篇幅",
                "confirmTitle": EXPERIMENTAL_CONFIRM_TITLE,
                "confirmBody": EXPERIMENTAL_CONFIRM_BODY,
            },
        )
        return

    if respond_if_trip_busy(handler, trip_id):
        return

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip0 = loaded
    from travelogue.config.edition import is_portfolio_trip

    if is_portfolio_trip(trip0):
        handler._json_response(
            409,
            {
                "ok": False,
                "error": "E_LVP_PORTFOLIO",
                "message": "作品集没有成册风格，请改回游记后再选。",
            },
        )
        return
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)
    svc = ctx.trip_service()

    def runner() -> dict:
        from travelogue.layout_engine.api import (
            LAYOUT_ENGINE_SCREENS,
            resolve_layout_engine,
        )
        from travelogue.render.engine import render_trip_surfaces
        from travelogue.services.layout import apply_layout_to_trip

        trip = svc.load(trip_json)
        # Screens layout computes against web profile; do not persist that as a
        # permanent exportLayout flip (same pattern as trip_pipeline_handlers).
        original_export_layout = str(trip.get("exportLayout") or "web")
        snapshot = {k: copy.deepcopy(trip.get(k)) for k in _LVP_PERSIST_KEYS}

        set_trip_layout_vibe(trip, raw)
        engine = resolve_layout_engine(trip)
        export_layout = original_export_layout
        if engine == LAYOUT_ENGINE_SCREENS or export_layout in ("web", "auto"):
            apply_layout_to_trip(
                trip,
                export_layout="web" if export_layout == "auto" else export_layout,
                layout_engine=LAYOUT_ENGINE_SCREENS,
                cfg=ctx.cfg,
            )
        else:
            apply_layout_to_trip(trip, export_layout=export_layout, cfg=ctx.cfg)

        # Keep dual-HTML / coverByLayout semantics when trip was auto.
        trip["exportLayout"] = original_export_layout

        def mutator(t: dict) -> None:
            set_trip_layout_vibe(t, raw)
            for key in (
                "chapters",
                "curation",
                "pipeline",
                "layoutEngine",
                "layoutEngineVersion",
            ):
                if key in trip:
                    t[key] = trip[key]
            # Never rewrite exportLayout from the temporary web apply above.
            t["exportLayout"] = original_export_layout

        svc.update(trip_json, mutator)
        try:
            render_trip_surfaces(
                trip_json,
                trip_dir,
                export_mode="draft",
                validate=False,
                update_pipeline=False,
                cfg=ctx.cfg,
            )
        except Exception:
            # Disk already has new vibe/layout; restore prior snapshot so a
            # failed job does not leave "UI fail / trip changed" half-state.
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
                    "LVP render failed and rollback also failed trip_id=%s", trip_id
                )
            raise
        return {
            "tripId": trip_id,
            "layoutVibe": resolve_layout_vibe(trip),
        }

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
    # Bind before thread start so is_trip_busy / trip_update_or_respond gate works.
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
            "layoutVibe": raw,
        },
    )
