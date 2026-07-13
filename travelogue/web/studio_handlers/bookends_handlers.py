"""Studio · Bookends Engine HTTP API (PRD §7.2 · B2b)."""

from __future__ import annotations

import logging

from travelogue.cover_engine.api import (
    BookendsLockedError,
    ClosingConflictError,
    ClosingPendingError,
    build_bookends_studio_payload,
    decision_to_dict,
    repick_closing,
    repick_opening,
    resolve_closing,
    resolve_opening,
    restore_auto,
)
from travelogue.cover_engine.lock import is_closing_locked, is_opening_locked
from travelogue.web.studio_errors import client_error_payload, internal_error_payload
from travelogue.web.studio_handlers.common import (
    load_trip_or_404,
    studio_ctx,
    trip_update_or_respond,
)
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol

_log = logging.getLogger(__name__)


def _locked_payload(which: str) -> dict:
    label = "封面" if which == "opening" else "封底"
    return {
        "ok": False,
        "error": "E_BOOKENDS_LOCKED",
        "message": f"{label}已按你的选择固定；如需重选请先恢复自动挑选，或使用 force。",
        "which": which,
    }


def _rerender(trip_json) -> bool:
    from travelogue.web.rerender import rerender_draft_trip

    try:
        rerender_draft_trip(trip_json)
        return True
    except Exception:
        _log.exception("bookends rerender failed for %s", trip_json)
        return False


def handle_get_bookends(handler: StudioHandlerProtocol, trip_id: str) -> None:
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    _trip_dir, trip = loaded
    payload = build_bookends_studio_payload(trip)
    handler._json_response(200, payload)


def handle_post_resolve_opening(handler: StudioHandlerProtocol, trip_id: str) -> None:
    body = handler._read_json_body() or {}
    force = bool(body.get("force", True))
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    if not force and is_opening_locked(trip):
        handler._json_response(409, _locked_payload("opening"))
        return
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)

    def mutator(t: dict):
        return resolve_opening(t, force=force)

    ok, decision = trip_update_or_respond(handler, ctx.trip_service(), trip_json, mutator)
    if not ok:
        return
    if not _rerender(trip_json):
        handler._json_response(500, internal_error_payload())
        return
    out = {"ok": True, **decision_to_dict(decision)}
    if decision.low_confidence:
        out["statusCode"] = "E_BOOKENDS_LOW_CONFIDENCE"
    handler._json_response(200, out)


def handle_post_resolve_closing(handler: StudioHandlerProtocol, trip_id: str) -> None:
    body = handler._read_json_body() or {}
    force = bool(body.get("force", False))
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    if not force and is_closing_locked(trip):
        handler._json_response(409, _locked_payload("closing"))
        return
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)

    def mutator(t: dict):
        return resolve_closing(t, force=force, persist=True)

    try:
        ok, decision = trip_update_or_respond(
            handler, ctx.trip_service(), trip_json, mutator
        )
    except ClosingPendingError as exc:
        handler._json_response(
            409,
            {"ok": False, "error": "E_BOOKENDS_CLOSING_PENDING", "message": str(exc)},
        )
        return
    except BookendsLockedError:
        handler._json_response(409, _locked_payload("closing"))
        return
    if not ok:
        return
    if not _rerender(trip_json):
        handler._json_response(500, internal_error_payload())
        return
    out = {"ok": True, **decision_to_dict(decision)}
    if decision.degraded:
        out["statusCode"] = "E_BOOKENDS_NO_CLOSING_CANDIDATE"
    elif decision.low_confidence:
        out["statusCode"] = "E_BOOKENDS_LOW_CONFIDENCE"
    handler._json_response(200, out)


def handle_post_repick_opening(handler: StudioHandlerProtocol, trip_id: str) -> None:
    body = handler._read_json_body() or {}
    asset_id = str(body.get("assetId") or "").strip() or None
    style_id = str(body.get("styleId") or "").strip() or None
    keep_cover = bool(body.get("keepCover", False))
    confirm = bool(
        body.get("confirmClosingConflict") or body.get("confirm_closing_conflict")
    )
    if not asset_id and not style_id:
        handler._json_response(400, {"ok": False, "error": "E_BOOKENDS_MISSING_TARGET"})
        return

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)

    def mutator(t: dict):
        return repick_opening(
            t,
            asset_id=asset_id,
            style_id=style_id,
            keep_cover=keep_cover,
            confirm_closing_conflict=confirm,
        )

    try:
        ok, decision = trip_update_or_respond(
            handler, ctx.trip_service(), trip_json, mutator
        )
    except ClosingConflictError as exc:
        handler._json_response(
            409,
            {
                "ok": False,
                "error": "E_BOOKENDS_CLOSING_CONFLICT",
                "message": "封底与新封面冲突，需要重选封底",
                "requiresConfirm": True,
                "violations": exc.violations,
            },
        )
        return
    except ValueError as exc:
        handler._json_response(400, client_error_payload(exc))
        return
    if not ok:
        return
    if not _rerender(trip_json):
        handler._json_response(500, internal_error_payload())
        return
    out = decision_to_dict(decision)
    toast = (decision.explain or {}).get("cascadeToast")
    if toast:
        out["toast"] = toast
    handler._json_response(200, {"ok": True, **out})


def handle_post_repick_closing(handler: StudioHandlerProtocol, trip_id: str) -> None:
    body = handler._read_json_body() or {}
    asset_id = str(body.get("assetId") or "").strip() or None
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)

    def mutator(t: dict):
        return repick_closing(t, asset_id=asset_id)

    try:
        ok, decision = trip_update_or_respond(
            handler, ctx.trip_service(), trip_json, mutator
        )
    except ClosingPendingError as exc:
        handler._json_response(
            409,
            {"ok": False, "error": "E_BOOKENDS_CLOSING_PENDING", "message": str(exc)},
        )
        return
    except ValueError as exc:
        handler._json_response(400, client_error_payload(exc))
        return
    if not ok:
        return
    if not _rerender(trip_json):
        handler._json_response(500, internal_error_payload())
        return
    handler._json_response(200, {"ok": True, **decision_to_dict(decision)})


def handle_post_restore_auto(handler: StudioHandlerProtocol, trip_id: str) -> None:
    body = handler._read_json_body() or {}
    confirmed = bool(body.get("confirmed") or body.get("confirm"))
    if not confirmed:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_BOOKENDS_CONFIRM_REQUIRED",
                "message": "恢复自动挑选将覆盖你的手选封面与封底，请确认。",
            },
        )
        return
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)

    def mutator(t: dict):
        return restore_auto(t)

    ok, decision = trip_update_or_respond(handler, ctx.trip_service(), trip_json, mutator)
    if not ok:
        return
    if not _rerender(trip_json):
        handler._json_response(500, internal_error_payload())
        return
    handler._json_response(200, {"ok": True, **decision_to_dict(decision)})
