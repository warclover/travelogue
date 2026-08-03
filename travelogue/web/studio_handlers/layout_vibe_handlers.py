"""Studio · LVP layout vibe apply handler (M2)."""

from __future__ import annotations

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


def handle_layout_vibe(handler: StudioHandlerProtocol, trip_id: str) -> None:
    """POST /__travelogue/trips/{tripId}/layout-vibe — persist vibe, layout, render."""
    payload = handler._read_json_body() or {}
    raw = str(payload.get("layoutVibe") or payload.get("layout_vibe") or "").strip()
    confirmed = bool(
        payload.get("confirmedExperimental")
        or payload.get("confirmed_experimental")
        or payload.get("confirmed")
    )

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

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, _trip0 = loaded
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
        set_trip_layout_vibe(trip, raw)
        engine = resolve_layout_engine(trip)
        export_layout = str(trip.get("exportLayout") or "web")
        if engine == LAYOUT_ENGINE_SCREENS or export_layout in ("web", "auto"):
            apply_layout_to_trip(
                trip,
                export_layout="web" if export_layout == "auto" else export_layout,
                layout_engine=LAYOUT_ENGINE_SCREENS,
                cfg=ctx.cfg,
            )
        else:
            apply_layout_to_trip(trip, export_layout=export_layout, cfg=ctx.cfg)

        def mutator(t: dict) -> None:
            set_trip_layout_vibe(t, raw)
            for key in (
                "chapters",
                "curation",
                "pipeline",
                "layoutEngine",
                "layoutEngineVersion",
                "exportLayout",
            ):
                if key in trip:
                    t[key] = trip[key]

        svc.update(trip_json, mutator)
        render_trip_surfaces(
            trip_json,
            trip_dir,
            export_mode="draft",
            validate=False,
            update_pipeline=False,
            cfg=ctx.cfg,
        )
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
