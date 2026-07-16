"""Storage usage / cleanup / remount (PRD-MEDIA-REFERENCE-STORAGE-V1)."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.media.source_resolve import assess_source_availability
from travelogue.media.storage_cleanup import (
    deep_cleanup_source,
    estimate_trips_usage,
    list_dev_scratch_dirs,
    safe_cleanup_dev_scratch,
    safe_cleanup_trip,
)
from travelogue.paths import ROOT, is_frozen
from travelogue.web.studio_errors import user_message
from travelogue.web.studio_handlers.common import studio_ctx
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol


def handle_source_status(handler: StudioHandlerProtocol, trip_id: str) -> None:
    ctx = studio_ctx(handler)
    trip_dir = Path(ctx.trips_root) / trip_id
    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        handler._json_response(
            404,
            {"ok": False, "error": "E_TRIP_NOT_FOUND", "message": user_message("E_TRIP_NOT_FOUND")},
        )
        return
    try:
        trip = json.loads(trip_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        handler._json_response(500, {"ok": False, "error": str(exc)})
        return
    health = assess_source_availability(trip, trip_dir)
    handler._json_response(200, {"ok": True, "tripId": trip_id, **health})


def handle_storage_usage(handler: StudioHandlerProtocol) -> None:
    ctx = studio_ctx(handler)
    trips_root = Path(ctx.trips_root)
    usage = estimate_trips_usage(trips_root)
    scratch = []
    if not is_frozen():
        scratch = [str(p) for p in list_dev_scratch_dirs(ROOT)]
    handler._json_response(
        200,
        {
            "ok": True,
            **usage,
            "devScratchVisible": not is_frozen(),
            "devScratchDirs": scratch,
        },
    )


def handle_storage_cleanup(handler: StudioHandlerProtocol) -> None:
    if handler.command != "POST":
        handler._json_response(405, {"ok": False, "error": "method not allowed"})
        return
    payload = handler._read_json_body() or {}
    ctx = studio_ctx(handler)
    trips_root = Path(ctx.trips_root)
    safe = bool(payload.get("safe", True))
    deep_source = bool(payload.get("deepSource", False))
    accept_derivatives_only = bool(payload.get("acceptDerivativesOnly", False))
    include_dev_scratch = bool(payload.get("devScratch", False)) and not is_frozen()
    trip_ids = payload.get("tripIds")
    if trip_ids is not None and not isinstance(trip_ids, list):
        handler._json_response(400, {"ok": False, "error": "tripIds must be a list"})
        return

    targets: list[Path] = []
    if trip_ids:
        for tid in trip_ids:
            td = trips_root / str(tid)
            if (td / "trip.json").is_file():
                targets.append(td)
    else:
        for child in trips_root.iterdir():
            if child.is_dir() and (child / "trip.json").is_file():
                targets.append(child)

    total_freed = 0
    items: list[dict] = []
    cluster_cleared = False
    refused = 0

    for trip_dir in targets:
        if safe:
            result = safe_cleanup_trip(trip_dir)
            total_freed += result.bytes_freed
            cluster_cleared = cluster_cleared or result.cluster_cache_cleared
            for it in result.items:
                items.append(
                    {
                        "tripId": trip_dir.name,
                        "path": it.path,
                        "bytesFreed": it.bytes_freed,
                        "status": it.status,
                        "detail": it.detail,
                    }
                )
        if deep_source:
            trip_json = trip_dir / "trip.json"
            try:
                trip = json.loads(trip_json.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                items.append(
                    {
                        "tripId": trip_dir.name,
                        "path": str(trip_json),
                        "status": "failed",
                        "detail": str(exc),
                    }
                )
                continue
            deep = deep_cleanup_source(
                trip,
                trip_dir,
                accept_derivatives_only=accept_derivatives_only,
            )
            for it in deep.items:
                if it.status == "skipped" and it.detail == "E_MEDIA_CLEANUP_REFUSED":
                    refused += 1
                items.append(
                    {
                        "tripId": trip_dir.name,
                        "path": it.path,
                        "bytesFreed": it.bytes_freed,
                        "status": it.status,
                        "detail": it.detail,
                    }
                )
            total_freed += deep.bytes_freed
            if deep.bytes_freed or any(i.status == "ok" for i in deep.items):
                try:
                    from travelogue.services.trip import TripService

                    svc = TripService(root=trip_dir.parent.parent)

                    def _apply(disk: dict) -> None:
                        disk["assets"] = trip.get("assets")
                        disk["media"] = trip.get("media")

                    svc.update(trip_json, _apply, bump_revision=True)
                except Exception as exc:  # noqa: BLE001
                    items.append(
                        {
                            "tripId": trip_dir.name,
                            "path": "trip.json",
                            "status": "failed",
                            "detail": f"persist: {exc}",
                        }
                    )

    if include_dev_scratch:
        scratch = safe_cleanup_dev_scratch(ROOT)
        total_freed += scratch.bytes_freed
        for it in scratch.items:
            items.append(
                {
                    "tripId": "_dev",
                    "path": it.path,
                    "bytesFreed": it.bytes_freed,
                    "status": it.status,
                    "detail": it.detail,
                }
            )

    if deep_source and refused and total_freed == 0:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_MEDIA_CLEANUP_REFUSED",
                "message": user_message("E_MEDIA_CLEANUP_REFUSED"),
                "items": items,
            },
        )
        return

    usage = estimate_trips_usage(trips_root)
    handler._json_response(
        200,
        {
            "ok": True,
            "bytesFreed": total_freed,
            "items": items,
            "clusterCacheCleared": cluster_cleared,
            "usage": usage,
            "hint": (
                "下次整理该作品可能重新计算场景分组"
                if cluster_cleared
                else None
            ),
        },
    )


def handle_storage_remount(handler: StudioHandlerProtocol) -> None:
    """Remount album root by contentSig matching (W2-capable; basic W1)."""
    if handler.command != "POST":
        handler._json_response(405, {"ok": False, "error": "method not allowed"})
        return
    payload = handler._read_json_body() or {}
    trip_id = str(payload.get("tripId") or "").strip()
    album_raw = str(payload.get("albumPath") or "").strip()
    if not trip_id or not album_raw:
        handler._json_response(400, {"ok": False, "error": "tripId and albumPath required"})
        return
    ctx = studio_ctx(handler)
    trip_dir = Path(ctx.trips_root) / trip_id
    trip_json = trip_dir / "trip.json"
    album = Path(album_raw)
    if not trip_json.is_file():
        handler._json_response(
            404,
            {"ok": False, "error": "E_TRIP_NOT_FOUND", "message": user_message("E_TRIP_NOT_FOUND")},
        )
        return
    if not album.is_dir():
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_MEDIA_SOURCE_MISSING",
                "message": user_message("E_MEDIA_SOURCE_MISSING"),
            },
        )
        return

    from travelogue.media.source_resolve import remount_album

    try:
        trip = json.loads(trip_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        handler._json_response(500, {"ok": False, "error": str(exc)})
        return

    result = remount_album(trip, album)

    try:
        from travelogue.services.trip import TripService

        svc = TripService(root=trip_dir.parent.parent)

        def _apply(disk: dict) -> None:
            disk["assets"] = trip.get("assets")
            disk["media"] = trip.get("media")

        svc.update(trip_json, _apply, bump_revision=True)
    except Exception as exc:  # noqa: BLE001
        handler._json_response(500, {"ok": False, "error": str(exc)})
        return

    code = result.error_code
    handler._json_response(
        200 if result.ok or result.matched else 400,
        {
            "ok": bool(result.matched),
            "matched": result.matched,
            "missing": result.missing,
            "contentChanged": result.content_changed,
            "error": code,
            "message": user_message(code) if code else None,
        },
    )
