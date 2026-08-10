"""Shared Studio handler helpers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TypeVar
from urllib.parse import parse_qs, unquote, urlparse

from travelogue.desktop.demo_album import is_demo_album_path, resolve_demo_album_dir
from travelogue.runtime import AppContext, app_context_from_handler
from travelogue.services.trip import TripConflictError, TripService
from travelogue.web.studio_errors import client_error_payload, user_message
from travelogue.web.studio_handlers.paths import (
    CURATE_SUFFIX,
    CURATION_MOMENT_SUFFIX,
    INTENT_SUFFIX,
    MOMENT_SUFFIX,
    PIPELINE_SUFFIX,
    PROMOTE_TIER_SUFFIX,
    RERENDER_SUFFIX,
    SAVE_COPY_SUFFIX,
    TRIPS_PATH,
)
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from travelogue.web.studio_jobs import get_job_store
from travelogue.web.studio_trip_id import is_valid_studio_trip_id

_U = TypeVar("_U")


def rel_to_trip(trip_dir: Path, target: Path) -> str:
    return target.resolve().relative_to(trip_dir.resolve()).as_posix()


def resolve_import_album_path(album_raw: str, *, use_demo: bool = False) -> Path:
    if use_demo or is_demo_album_path(album_raw):
        return resolve_demo_album_dir()
    return Path(album_raw)


def studio_ctx(handler: StudioHandlerProtocol) -> AppContext:
    return app_context_from_handler(handler)


def respond_if_trip_busy(handler: StudioHandlerProtocol, trip_id: str) -> bool:
    """Return True and send 409 when ``trip_id`` has a queued/running studio job."""
    if not trip_id or not get_job_store().is_trip_busy(trip_id):
        return False
    handler._json_response(
        409,
        {
            "ok": False,
            "error": "E_STUDIO_JOB_BUSY",
            "message": user_message("E_STUDIO_JOB_BUSY"),
        },
    )
    return True


def trip_update_or_respond(
    handler: StudioHandlerProtocol,
    svc: TripService,
    trip_json: Path,
    mutator: Callable[[dict], _U],
    *,
    touch_updated: bool = True,
) -> tuple[bool, _U | None]:
    """Run ``svc.update``; on conflict respond 409 and return ``(False, None)``."""
    busy_id = trip_json.parent.name if trip_json else ""
    if respond_if_trip_busy(handler, busy_id):
        return False, None
    try:
        return True, svc.update(trip_json, mutator, touch_updated=touch_updated)
    except TripConflictError as exc:
        handler._json_response(409, client_error_payload(exc))
        return False, None


def resolve_trip_dir(ctx: AppContext, trip_id: str) -> Path | None:
    if not is_valid_studio_trip_id(trip_id):
        return None
    trip_dir = (ctx.trips_root / trip_id).resolve()
    try:
        trip_dir.relative_to(ctx.trips_root)
    except ValueError:
        return None
    if not (trip_dir / "trip.json").is_file():
        return None
    return trip_dir


def bind_studio_trip(handler: StudioHandlerProtocol, trip_id: str) -> Path | None:
    """Resolve trip dir and set handler.trip_json_path (Studio static serving)."""
    trip_dir = resolve_trip_dir(studio_ctx(handler), trip_id)
    if trip_dir is None:
        return None
    handler.trip_json_path = trip_dir / "trip.json"
    return trip_dir


def match_trip_suffix(path: str, suffix: str) -> str | None:
    prefix = TRIPS_PATH + "/"
    if not path.startswith(prefix) or not path.endswith(suffix):
        return None
    trip_id = path[len(prefix) : -len(suffix)]
    if not trip_id or "/" in trip_id:
        return None
    return trip_id


def match_entry(path: str) -> str | None:
    return match_trip_suffix(path, "/entry")


def match_source_status(path: str) -> str | None:
    return match_trip_suffix(path, "/source-status")


def match_aesthetic(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import AESTHETIC_SUFFIX

    return match_trip_suffix(path, AESTHETIC_SUFFIX)


def match_aesthetic_preference(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import AESTHETIC_PREFERENCE_SUFFIX

    return match_trip_suffix(path, AESTHETIC_PREFERENCE_SUFFIX)


def match_bento_preview(path: str) -> str | None:
    return match_trip_suffix(path, "/bento-preview")


def match_trip_delete(path: str) -> str | None:
    """DELETE /__travelogue/trips/{tripId} — M13 shelf delete."""
    prefix = TRIPS_PATH + "/"
    if not path.startswith(prefix):
        return None
    trip_id = unquote(path[len(prefix) :].strip("/"))
    if not trip_id or "/" in trip_id or "\\" in trip_id:
        return None
    return trip_id


def resolve_trip_dir_listed(ctx: AppContext, trip_id: str) -> Path | None:
    """按磁盘目录名解析 trip（与 list_studio_trips 一致，不做 slug 正则限制）。"""
    raw = unquote((trip_id or "").strip())
    if not raw or raw in {".", ".."} or "/" in raw or "\\" in raw or raw.startswith("_"):
        return None
    trips_dir = ctx.trips_root.resolve()
    trip_dir = (trips_dir / raw).resolve()
    try:
        trip_dir.relative_to(trips_dir)
    except ValueError:
        return None
    if not trip_dir.is_dir() or not (trip_dir / "trip.json").is_file():
        return None
    return trip_dir


def match_trip_intent(path: str) -> str | None:
    return match_trip_suffix(path, INTENT_SUFFIX)


def match_trip_cohort_refresh(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import COHORT_REFRESH_SUFFIX

    return match_trip_suffix(path, COHORT_REFRESH_SUFFIX)


def match_trip_cohort(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import COHORT_REFRESH_SUFFIX, COHORT_SUFFIX

    if path.endswith(COHORT_REFRESH_SUFFIX):
        return None
    return match_trip_suffix(path, COHORT_SUFFIX)


def match_trip_pipeline(path: str) -> str | None:
    return match_trip_suffix(path, PIPELINE_SUFFIX)


def match_trip_curate(path: str) -> str | None:
    return match_trip_suffix(path, CURATE_SUFFIX)


def match_trip_layout_vibe(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import LAYOUT_VIBE_SUFFIX

    return match_trip_suffix(path, LAYOUT_VIBE_SUFFIX)


def match_trip_moment_curation(path: str) -> str | None:
    return match_trip_suffix(path, CURATION_MOMENT_SUFFIX)


def match_trip_moment_patch(path: str) -> str | None:
    return match_trip_suffix(path, MOMENT_SUFFIX)


def match_trip_bookends(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import BOOKENDS_SUFFIX

    return match_trip_suffix(path, BOOKENDS_SUFFIX)


def match_trip_bookends_resolve_opening(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import BOOKENDS_RESOLVE_OPENING_SUFFIX

    return match_trip_suffix(path, BOOKENDS_RESOLVE_OPENING_SUFFIX)


def match_trip_bookends_resolve_closing(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import BOOKENDS_RESOLVE_CLOSING_SUFFIX

    return match_trip_suffix(path, BOOKENDS_RESOLVE_CLOSING_SUFFIX)


def match_trip_title_art_resolve(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import TITLE_ART_RESOLVE_SUFFIX

    return match_trip_suffix(path, TITLE_ART_RESOLVE_SUFFIX)


def match_trip_ai_intent_brief(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import AI_INTENT_BRIEF_SUFFIX

    return match_trip_suffix(path, AI_INTENT_BRIEF_SUFFIX)


def match_trip_ai_layout_critic_accept(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import AI_LAYOUT_CRITIC_ACCEPT_SUFFIX

    return match_trip_suffix(path, AI_LAYOUT_CRITIC_ACCEPT_SUFFIX)


def match_trip_ai_layout_critic(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import AI_LAYOUT_CRITIC_SUFFIX

    return match_trip_suffix(path, AI_LAYOUT_CRITIC_SUFFIX)


def match_trip_bookends_repick_opening(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import BOOKENDS_REPICK_OPENING_SUFFIX

    return match_trip_suffix(path, BOOKENDS_REPICK_OPENING_SUFFIX)


def match_trip_bookends_repick_closing(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import BOOKENDS_REPICK_CLOSING_SUFFIX

    return match_trip_suffix(path, BOOKENDS_REPICK_CLOSING_SUFFIX)


def match_trip_bookends_restore_auto(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import BOOKENDS_RESTORE_AUTO_SUFFIX

    return match_trip_suffix(path, BOOKENDS_RESTORE_AUTO_SUFFIX)


def match_trip_asset_media(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import ASSET_MEDIA_SUFFIX

    return match_trip_suffix(path, ASSET_MEDIA_SUFFIX)


def match_trip_template(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import TEMPLATE_SUFFIX

    return match_trip_suffix(path, TEMPLATE_SUFFIX)


def match_trip_chapter_copy_intent(path: str) -> tuple[str, str] | None:
    """PATCH /__travelogue/trips/{tripId}/chapters/{chapterId}/copy-intent"""
    from travelogue.web.studio_handlers.paths import COPY_INTENT_SUFFIX

    prefix = TRIPS_PATH + "/"
    suffix = COPY_INTENT_SUFFIX
    if not path.startswith(prefix) or not path.endswith(suffix):
        return None
    mid = path[len(prefix) : -len(suffix)]
    parts = mid.split("/")
    if len(parts) != 3 or parts[1] != "chapters":
        return None
    trip_id, chapter_id = parts[0], parts[2]
    if not trip_id or not chapter_id:
        return None
    return trip_id, chapter_id


def match_trip_copy_telemetry(path: str) -> str | None:
    """POST /__travelogue/trips/{tripId}/copy-telemetry"""
    from travelogue.web.studio_handlers.paths import COPY_TELEMETRY_SUFFIX

    return match_trip_suffix(path, COPY_TELEMETRY_SUFFIX)


def match_trip_screen_replan(path: str) -> tuple[str, str] | None:
    """PATCH /__travelogue/trips/{tripId}/screens/{screenId}/replan"""
    prefix = TRIPS_PATH + "/"
    suffix = "/replan"
    if not path.startswith(prefix) or not path.endswith(suffix):
        return None
    mid = path[len(prefix) : -len(suffix)]
    parts = mid.split("/")
    if len(parts) != 3 or parts[1] != "screens":
        return None
    trip_id, screen_id = parts[0], parts[2]
    if not trip_id or not screen_id:
        return None
    return trip_id, screen_id


def _match_trip_root_suffix(path: str, suffix: str) -> str | None:
    if not path.endswith(suffix):
        return None
    trip_id = path[: -len(suffix)].strip("/")
    if not trip_id or "/" in trip_id:
        return None
    return trip_id


def match_trip_save_copy(path: str) -> str | None:
    return _match_trip_root_suffix(path, SAVE_COPY_SUFFIX)


def match_trip_promote_tier(path: str) -> str | None:
    return _match_trip_root_suffix(path, PROMOTE_TIER_SUFFIX)


def match_trip_rerender(path: str) -> str | None:
    return _match_trip_root_suffix(path, RERENDER_SUFFIX)


def trip_id_from_query(handler: StudioHandlerProtocol) -> str:
    query = parse_qs(urlparse(handler.path).query)
    return (query.get("tripId") or query.get("tripid") or [""])[0]


def load_trip_or_404(
    handler: StudioHandlerProtocol, trip_id: str
) -> tuple[Path, dict] | None:
    if not is_valid_studio_trip_id(trip_id):
        handler._json_response(400, {"ok": False, "error": "invalid tripId"})
        return None
    ctx = studio_ctx(handler)
    trip_dir = resolve_trip_dir(ctx, trip_id)
    if trip_dir is None:
        handler._json_response(404, {"ok": False, "error": "trip not found"})
        return None
    trip_json = trip_dir / "trip.json"
    trip = ctx.trip_service().load(trip_json)
    return trip_dir, trip
