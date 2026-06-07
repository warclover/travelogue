"""Studio asset mediaClass manual override (PRD §3.4 collage 改判)."""

from __future__ import annotations

from travelogue.web.studio_handlers.common import load_trip_or_404
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol

_ALLOWED = frozenset({"photo", "collage", "screenshot", "thumbnail", "reupload", "archive", "unknown"})


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
    assets = trip.get("assets") or []
    updated = False
    for asset in assets:
        if str(asset.get("id") or "") == asset_id:
            asset["mediaClass"] = media_class
            updated = True
            break
    if not updated:
        handler._json_response(404, {"ok": False, "error": "E_ASSET_NOT_FOUND"})
        return
    from travelogue.web.studio_handlers.common import studio_ctx

    ctx = studio_ctx(handler)
    ctx.trip_service().save(trip, trip_dir / "trip.json")
    handler._json_response(
        200,
        {"ok": True, "assetId": asset_id, "mediaClass": media_class},
    )
