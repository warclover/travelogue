"""Studio asset mediaClass manual override (PRD §3.4 collage 改判)."""

from __future__ import annotations

from travelogue.web.studio_handlers.common import (
    load_trip_or_404,
    studio_ctx,
    trip_update_or_respond,
)
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol

_ALLOWED = frozenset({"photo", "collage", "screenshot", "thumbnail", "reupload", "archive", "unknown"})


def _set_media_class(trip: dict, asset_id: str, media_class: str) -> None:
    for asset in trip.get("assets") or []:
        if str(asset.get("id") or "") == asset_id:
            asset["mediaClass"] = media_class
            return
    raise KeyError(asset_id)


def handle_asset_media_class(handler: StudioHandlerProtocol, trip_id: str) -> None:
    payload = handler._read_json_body() or {}
    asset_id = str(payload.get("assetId") or "").strip()
    media_class = str(payload.get("mediaClass") or "").strip().lower()
    if not asset_id or not media_class:
        handler._json_response(400, {"ok": False, "error": "assetId and mediaClass required"})
        return
    if media_class not in _ALLOWED:
        handler._json_response(400, {"ok": False, "error": "E_MEDIA_CLASS_INVALID"})
        return
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    if not any(str(a.get("id") or "") == asset_id for a in (trip.get("assets") or [])):
        handler._json_response(404, {"ok": False, "error": "E_ASSET_NOT_FOUND"})
        return
    ctx = studio_ctx(handler)
    ok, _ = trip_update_or_respond(
        handler,
        ctx.trip_service(),
        trip_dir / "trip.json",
        lambda t: _set_media_class(t, asset_id, media_class),
    )
    if not ok:
        return
    handler._json_response(
        200,
        {"ok": True, "assetId": asset_id, "mediaClass": media_class},
    )
