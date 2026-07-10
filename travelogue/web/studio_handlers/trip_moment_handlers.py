"""Studio · Phase 23 moment pool + signature PATCH."""

from __future__ import annotations

import logging

from travelogue.services.moment_curation import (
    apply_moment_signature,
    build_moment_curation_payload,
    validate_moment_asset_id,
)
from travelogue.web.studio_errors import client_error_payload, internal_error_payload
from travelogue.web.studio_handlers.common import (
    load_trip_or_404,
    studio_ctx,
    trip_update_or_respond,
)
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol

_log = logging.getLogger(__name__)


def handle_get_moment_curation(handler: StudioHandlerProtocol, trip_id: str) -> None:
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    _trip_dir, trip = loaded
    payload = build_moment_curation_payload(trip)
    handler._json_response(200, {"ok": True, **payload})


def handle_patch_moment(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.web.rerender import rerender_draft_trip

    body = handler._read_json_body()
    if not body:
        return
    moment_id = str(body.get("momentAssetId") or body.get("assetId") or "").strip()
    if not moment_id:
        handler._json_response(400, {"ok": False, "error": "E_MOMENT_MISSING_ID"})
        return

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    trip_json = trip_dir / "trip.json"
    err = validate_moment_asset_id(trip, moment_id)
    if err:
        handler._json_response(
            400,
            {"ok": False, "error": err, "message": "momentAssetId must be in pool and not cover"},
        )
        return

    ctx = studio_ctx(handler)
    try:
        ok, moment_id_out = trip_update_or_respond(
            handler,
            ctx.trip_service(),
            trip_json,
            lambda t: (apply_moment_signature(t, moment_id), moment_id)[1],
        )
        if not ok:
            return
    except ValueError as exc:
        handler._json_response(400, client_error_payload(exc))
        return

    try:
        rerender_draft_trip(trip_json)
    except Exception:
        _log.exception("moment patch rerender failed for %s", trip_id)
        handler._json_response(500, internal_error_payload())
        return

    trip = ctx.trip_service().load(trip_json)
    handler._json_response(
        200,
        {
            "ok": True,
            "momentAssetId": moment_id,
            "curation": build_moment_curation_payload(trip),
        },
    )
