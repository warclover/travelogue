"""Studio trip list, entry, aesthetic, and chapter layout handlers."""

from __future__ import annotations

import logging
import shutil
from urllib.parse import parse_qs, urlparse

from travelogue.web.studio_errors import internal_error_payload
from travelogue.web.studio_handlers.common import (
    load_trip_or_404,
    resolve_trip_dir_listed,
    studio_ctx,
    trip_id_from_query,
    trip_update_or_respond,
)
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from travelogue.web.studio_handlers.trip_common import is_protected_demo_trip
from travelogue.web.studio_jobs import get_job_store
from travelogue.web.studio_trip_id import is_valid_studio_trip_id
from travelogue.web.studio_trips import list_studio_trips_page

_log = logging.getLogger(__name__)


def handle_trips(handler: StudioHandlerProtocol) -> None:
    query = parse_qs(urlparse(handler.path).query)
    try:
        limit = int((query.get("limit") or ["20"])[0])
    except ValueError:
        limit = 20
    limit = max(1, min(limit, 100))
    try:
        offset = int((query.get("offset") or ["0"])[0])
    except ValueError:
        offset = 0
    offset = max(0, offset)
    ctx = studio_ctx(handler)
    trips, total = list_studio_trips_page(ctx.trips_root, limit=limit, offset=offset)
    handler._json_response(200, {"ok": True, "trips": trips, "total": total})


def handle_delete_trip(handler: StudioHandlerProtocol, trip_id: str) -> None:
    ctx = studio_ctx(handler)
    trip_dir = resolve_trip_dir_listed(ctx, trip_id)
    if trip_dir is None:
        handler._json_response(
            404,
            {"ok": False, "error": "E_TRIP_NOT_FOUND", "message": "游记不存在"},
        )
        return
    disk_id = trip_dir.name
    trip_json = trip_dir / "trip.json"
    try:
        trip = ctx.trip_service().load(trip_json)
    except Exception:
        _log.exception("load trip before delete failed for %s", trip_dir)
        handler._json_response(500, internal_error_payload())
        return
    if is_protected_demo_trip(disk_id, trip):
        handler._json_response(
            403,
            {
                "ok": False,
                "error": "E_TRIP_DELETE_DENIED",
                "message": "示例画册无法删除",
            },
        )
        return
    store = get_job_store()
    if store.is_trip_busy(disk_id):
        handler._json_response(
            409,
            {
                "ok": False,
                "error": "E_STUDIO_JOB_BUSY",
                "message": "导入进行中，请稍后再试",
            },
        )
        return
    try:
        shutil.rmtree(trip_dir)
    except OSError:
        _log.exception("delete trip failed for %s", trip_dir)
        handler._json_response(500, internal_error_payload())
        return
    handler.send_response(204)
    handler.end_headers()


def handle_entry(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.web.studio_entry import build_entry

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    _trip_dir, trip = loaded
    ctx = studio_ctx(handler)
    enabled = bool(ctx.cfg.aesthetic.enabled)
    handler._json_response(
        200,
        {"ok": True, **build_entry(trip, trip_id, aesthetic_enabled=enabled, trip_dir=_trip_dir)},
    )


def handle_aesthetic(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.web.studio_aesthetic import build_aesthetic_studio_payload

    query = parse_qs(urlparse(handler.path).query)
    asset_id = (query.get("assetId") or query.get("asset_id") or [None])[0]
    try:
        limit = int((query.get("limit") or ["3"])[0])
    except ValueError:
        limit = 3
    limit = max(1, min(limit, 5))

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    _trip_dir, trip = loaded
    ctx = studio_ctx(handler)
    enabled = bool(ctx.cfg.aesthetic.enabled)
    asset_ids = [str(asset_id)] if asset_id else None
    payload = build_aesthetic_studio_payload(
        trip,
        enabled=enabled,
        asset_ids=asset_ids,
        limit=limit,
    )
    handler._json_response(200, {"ok": True, **payload})


def handle_patch_stratum_preference(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.curation.album_profile import apply_stratum_preference
    from travelogue.web.studio_aesthetic import build_stratum_preference_studio_summary

    payload = handler._read_json_body()
    if not payload:
        return
    raw = payload.get("stratumPreference", payload.get("value"))
    if raw is None:
        handler._json_response(400, {"ok": False, "error": "stratumPreference required"})
        return
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)
    svc = ctx.trip_service()
    ok, _ = trip_update_or_respond(
        handler,
        svc,
        trip_json,
        lambda t: apply_stratum_preference(t, str(raw)),
    )
    if not ok:
        return
    trip = svc.load(trip_json)
    handler._json_response(
        200,
        {"ok": True, "stratumPreference": build_stratum_preference_studio_summary(trip)},
    )


def handle_bento_preview(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.web.studio_bento_preview import build_trip_bento_preview

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    if payload is None:
        handler._json_response(
            404,
            {"ok": False, "error": "E_BENTO_PREVIEW_UNAVAILABLE", "message": "暂无预览图"},
        )
        return
    handler._json_response(200, {"ok": True, **payload})


def handle_chapter_layout(handler: StudioHandlerProtocol) -> None:
    from travelogue.curation.chapter_explain import build_chapter_explain, build_layout_explain
    from travelogue.curation.mosaic_explain import build_mosaic_explain

    trip_id = trip_id_from_query(handler)
    if not trip_id or not is_valid_studio_trip_id(trip_id):
        handler._json_response(400, {"ok": False, "error": "tripId required"})
        return
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    stored = ((trip.get("curation") or {}).get("clustering") or {}).get("userSummary")
    if isinstance(stored, dict) and stored.get("summary"):
        explain = dict(stored)
    else:
        explain = build_chapter_explain(trip, trip_dir=trip_dir)
    curation = trip.get("curation") or {}
    layout_explain = build_layout_explain(curation)
    if layout_explain:
        explain["layoutExplain"] = layout_explain
    # LTN C6 · always refresh mosaic explain from live decision log (not stale userSummary).
    mosaic_explain = build_mosaic_explain(curation)
    if mosaic_explain:
        explain["mosaicExplain"] = mosaic_explain
    elif "mosaicExplain" in explain:
        explain.pop("mosaicExplain", None)
    handler._json_response(200, {"ok": True, **explain})
