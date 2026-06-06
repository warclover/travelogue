"""Studio homepage funnel event ingestion."""

from __future__ import annotations

from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from travelogue.web.studio_homepage_telemetry import (
    ALLOWED_STUDIO_HOMEPAGE_EVENTS,
    append_studio_homepage_event,
)


def handle_studio_event(handler: StudioHandlerProtocol) -> None:
    payload = handler._read_json_body()
    if not payload:
        handler._json_response(400, {"ok": False, "error": "empty body"})
        return
    event = str(payload.get("event") or "").strip()
    if event not in ALLOWED_STUDIO_HOMEPAGE_EVENTS:
        handler._json_response(
            400,
            {"ok": False, "error": "invalid event", "allowed": sorted(ALLOWED_STUDIO_HOMEPAGE_EVENTS)},
        )
        return
    meta = payload.get("meta")
    if meta is not None and not isinstance(meta, dict):
        handler._json_response(400, {"ok": False, "error": "meta must be an object"})
        return
    try:
        append_studio_homepage_event(event, meta if isinstance(meta, dict) else None)
        if event in ("template_selector_impression", "template_mode_changed"):
            from travelogue.templating.metrics import record_discovery_event

            record_discovery_event(template_id="*", kind="impression")
        elif event == "template_manual_selected":
            from travelogue.templating.metrics import record_discovery_event

            tid = str((meta or {}).get("template_id") or (meta or {}).get("templateId") or "*")
            record_discovery_event(template_id=tid, kind="select")
    except ValueError as exc:
        handler._json_response(400, {"ok": False, "error": str(exc)})
        return
    handler._json_response(200, {"ok": True})
