"""Studio screen replan handler."""

from __future__ import annotations

from travelogue.web.studio_errors import client_error_payload
from travelogue.web.studio_handlers.common import load_trip_or_404, studio_ctx, trip_update_or_respond
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol


def handle_patch_screen_replan(
    handler: StudioHandlerProtocol, trip_id: str, screen_id: str
) -> None:
    """PATCH …/screens/{screenId}/replan — MCS alt_topk or legacy for one screen."""
    from travelogue.curation.layout_planner import aspect_kind_for_asset
    from travelogue.curation.mosaic.replan import (
        ReplanError,
        refresh_trip_displayed_assets,
        replan_screen,
    )
    from travelogue.curation.screen_planner import LAYOUT_ENGINE_SCREENS

    payload = handler._read_json_body() or {}
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    import copy

    before_trip = copy.deepcopy(trip)
    if trip.get("layoutEngine") != LAYOUT_ENGINE_SCREENS:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_LAYOUT_ENGINE",
                "message": "replan requires layoutEngine=screens",
            },
        )
        return
    chapters = trip.get("chapters") or []
    assets = trip.get("assets") or []
    assets_map = {a["id"]: a for a in assets if a.get("id")}
    aspects = {
        aid: aspect_kind_for_asset(a)
        for aid, a in assets_map.items()
        if a.get("layoutEligible", True) is not False
    }
    strategy = str(payload.get("strategy") or "alt_topk").strip().lower()
    if strategy not in ("alt_topk", "legacy"):
        handler._json_response(400, {"ok": False, "error": "invalid strategy"})
        return
    try:
        top_k = int(payload.get("topK") or payload.get("top_k") or 3)
    except (TypeError, ValueError):
        top_k = 3
    ctx = studio_ctx(handler)
    try:
        result = replan_screen(
            chapters,
            screen_id,
            strategy=strategy,  # type: ignore[arg-type]
            top_k=max(1, top_k),
            aspects=aspects,
            assets_map=assets_map,
            cfg=ctx.app_config.mosaic,
            trip_photo_total=len(assets_map),
            burst_seconds=ctx.app_config.layout.mixed_proximity_seconds,
        )
    except ReplanError as exc:
        handler._json_response(
            400,
            client_error_payload(exc, default_code="E_REPLAN_INVALID"),
        )
        return
    feedback_summary = None
    if result.get("applied"):
        trip["chapters"] = chapters
        refresh_trip_displayed_assets(trip, chapters)
        from travelogue.layout_engine.studio_feedback import persist_studio_layout_feedback

        feedback_summary = persist_studio_layout_feedback(
            trip_id,
            trip_dir,
            before_trip,
            trip,
            cfg=ctx.app_config,
        )
    trip_json = trip_dir / "trip.json"
    svc = ctx.trip_service()
    if not result.get("applied"):
        handler._json_response(200, {"ok": True, **result})
        return

    captured_result = result
    captured_feedback = feedback_summary

    def mutator(t: dict) -> tuple[dict, dict | None]:
        t["chapters"] = chapters
        refresh_trip_displayed_assets(t, chapters)
        fb = persist_studio_layout_feedback(
            trip_id,
            trip_dir,
            before_trip,
            t,
            cfg=ctx.app_config,
        )
        return captured_result, fb or captured_feedback

    ok, update_result = trip_update_or_respond(handler, svc, trip_json, mutator)
    if not ok:
        return
    captured_result, feedback_summary = update_result
    payload = {"ok": True, **captured_result}
    if feedback_summary:
        payload["layoutFeedback"] = feedback_summary
    handler._json_response(200, payload)
