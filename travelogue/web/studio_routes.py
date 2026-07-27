"""Studio HTTP routes (serve --studio) — thin dispatcher facade."""

from __future__ import annotations

from pathlib import Path

from travelogue.web.studio_auth import studio_request_authorized
from travelogue.web.studio_chrome import should_inject_studio_chrome
from travelogue.web.studio_dispatch import dispatch_studio
from travelogue.web.studio_errors import user_message
from travelogue.web.studio_handlers.common import bind_studio_trip
from travelogue.web.studio_handlers.paths import (
    ALBUM_PREVIEW_PATH,
    CANCEL_PATH,
    CHAPTER_LAYOUT_PATH,
    CONFIG_PATH,
    CURATE_SUFFIX,
    EXPORT_PATH,
    HOME_CLASSIC_PATH,
    HOME_V2_PATH,
    IMPORT_PATH,
    INTENT_SUFFIX,
    LONGSHOT_PATH,
    NARRATE_PATH,
    PICK_FOLDER_PATH,
    PIPELINE_SUFFIX,
    PROMOTE_TIER_SUFFIX,
    RERENDER_SUFFIX,
    REVEAL_PATH,
    SAVE_COPY_SUFFIX,
    STATUS_PATH,
    STUDIO_ASSET_PREFIX,
    STUDIO_EVENT_PATH,
    TRIPS_PATH,
)

# Re-export path constants for serve.py and tests.
__all__ = [
    "StudioMixin",
    "HOME_V2_PATH",
    "HOME_CLASSIC_PATH",
    "IMPORT_PATH",
    "STATUS_PATH",
    "CONFIG_PATH",
    "TRIPS_PATH",
    "LONGSHOT_PATH",
    "NARRATE_PATH",
    "REVEAL_PATH",
    "CANCEL_PATH",
    "EXPORT_PATH",
    "PICK_FOLDER_PATH",
    "ALBUM_PREVIEW_PATH",
    "STUDIO_EVENT_PATH",
    "CHAPTER_LAYOUT_PATH",
    "STUDIO_ASSET_PREFIX",
    "SAVE_COPY_SUFFIX",
    "PROMOTE_TIER_SUFFIX",
    "RERENDER_SUFFIX",
    "INTENT_SUFFIX",
    "PIPELINE_SUFFIX",
    "CURATE_SUFFIX",
]


class StudioMixin:
    """Thin facade: auth, trip binding, GET/POST dispatch via studio_dispatch."""

    studio_mode: bool = False
    trips_dir: Path | None = None
    studio_host: str = "127.0.0.1"
    studio_port: int = 8766
    studio_token: str | None = None
    studio_allow_lan: bool = False
    studio_config_path: Path | None = None

    def _studio_require_auth(self) -> bool:
        path = getattr(self, "path", "") or ""
        query = path.split("?", 1)[1] if "?" in path else ""
        headers = getattr(self, "headers", {}) or {}
        if studio_request_authorized(
            host=self.studio_host,
            token=self.studio_token,
            headers=headers,
            allow_lan=self.studio_allow_lan,
            query=query,
        ):
            return True
        self._json_response(
            401,
            {
                "ok": False,
                "error": "E_STUDIO_AUTH",
                "message": user_message("E_STUDIO_AUTH"),
            },
        )
        return False

    def studio_dispatch_GET(self, path: str) -> bool:
        return dispatch_studio("GET", path, self, require_auth=self._studio_require_auth)

    def studio_dispatch_PATCH(self, path: str) -> bool:
        return dispatch_studio("PATCH", path, self, require_auth=self._studio_require_auth)

    def studio_dispatch_DELETE(self, path: str) -> bool:
        return dispatch_studio("DELETE", path, self, require_auth=self._studio_require_auth)

    def studio_dispatch_POST(self, path: str) -> bool:
        return dispatch_studio("POST", path, self, require_auth=self._studio_require_auth)

    def studio_trip_parts(self, path: str) -> tuple[str, str] | None:
        """Parse ``/{tripId}`` or ``/{tripId}/{rel}`` for static file fallback.

        Bare ``/{tripId}`` / ``/{tripId}/`` yield ``rel=""`` so the static
        handler can default to ``index.html`` (avoids 404 on directory URLs).
        """
        if not path.startswith("/"):
            return None
        stripped = path.strip("/")
        if not stripped:
            return None
        parts = stripped.split("/", 1)
        trip_id = parts[0]
        if not trip_id or trip_id.startswith("_") or trip_id.startswith("__"):
            return None
        rel = parts[1] if len(parts) == 2 else ""
        return trip_id, rel

    def studio_bind_trip(self, trip_id: str) -> Path | None:
        if not self.trips_dir:
            return None
        return bind_studio_trip(self, trip_id)

    def should_inject_studio_chrome(self, rel_path: str) -> bool:
        return should_inject_studio_chrome(rel_path)
