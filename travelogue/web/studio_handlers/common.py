"""Shared Studio handler helpers."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from travelogue.desktop.demo_album import is_demo_album_path, resolve_demo_album_dir
from travelogue.runtime import AppContext, app_context_from_handler
from travelogue.web.studio_handlers.paths import (
    CURATE_SUFFIX,
    INTENT_SUFFIX,
    PIPELINE_SUFFIX,
    PROMOTE_TIER_SUFFIX,
    RERENDER_SUFFIX,
    SAVE_COPY_SUFFIX,
    TRIPS_PATH,
)
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from travelogue.web.studio_trip_id import is_valid_studio_trip_id


def rel_to_trip(trip_dir: Path, target: Path) -> str:
    return target.resolve().relative_to(trip_dir.resolve()).as_posix()


def resolve_import_album_path(album_raw: str, *, use_demo: bool = False) -> Path:
    if use_demo or is_demo_album_path(album_raw):
        return resolve_demo_album_dir()
    return Path(album_raw)


def studio_ctx(handler: StudioHandlerProtocol) -> AppContext:
    return app_context_from_handler(handler)


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


def match_aesthetic(path: str) -> str | None:
    from travelogue.web.studio_handlers.paths import AESTHETIC_SUFFIX

    return match_trip_suffix(path, AESTHETIC_SUFFIX)


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


def match_trip_api(path: str) -> tuple[str, str] | None:
    if path.endswith(SAVE_COPY_SUFFIX):
        trip_id = path[: -len(SAVE_COPY_SUFFIX)].strip("/")
        if trip_id and "/" not in trip_id:
            return trip_id, "save-copy"
    if path.endswith(PROMOTE_TIER_SUFFIX):
        trip_id = path[: -len(PROMOTE_TIER_SUFFIX)].strip("/")
        if trip_id and "/" not in trip_id:
            return trip_id, "promote-tier"
    if path.endswith(RERENDER_SUFFIX):
        trip_id = path[: -len(RERENDER_SUFFIX)].strip("/")
        if trip_id and "/" not in trip_id:
            return trip_id, "rerender"
    return None


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
