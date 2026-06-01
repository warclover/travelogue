"""Studio HTTP routes (serve --studio) — thin dispatcher facade."""

from __future__ import annotations

from pathlib import Path

from travelogue.config import AppConfig, get_config
from travelogue.web.studio_auth import studio_post_authorized
from travelogue.web.studio_chrome import should_inject_studio_chrome
from travelogue.web.studio_errors import user_message
from travelogue.web.studio_handlers import (
    config_handlers,
    export_handlers,
    import_handlers,
    job_handlers,
    static_handlers,
    telemetry_handlers,
    trip_handlers,
)
from travelogue.web.studio_handlers.common import (
    bind_studio_trip,
    match_entry,
    match_trip_api,
    match_trip_curate,
    match_trip_intent,
    match_trip_pipeline,
)
from travelogue.web.studio_handlers.paths import (
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
    ALBUM_PREVIEW_PATH,
    STUDIO_EVENT_PATH,
    PIPELINE_SUFFIX,
    PROMOTE_TIER_SUFFIX,
    REVEAL_PATH,
    RERENDER_SUFFIX,
    SAVE_COPY_SUFFIX,
    STATUS_PATH,
    STUDIO_ASSET_PREFIX,
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
    """Thin facade: auth, trip binding, GET/POST dispatch to studio_handlers."""

    studio_mode: bool = False
    trips_dir: Path | None = None
    studio_host: str = "127.0.0.1"
    studio_port: int = 8766
    studio_token: str | None = None
    studio_allow_lan: bool = False
    studio_config_path: Path | None = None

    def _studio_require_post_auth(self) -> bool:
        if studio_post_authorized(
            host=self.studio_host,
            token=self.studio_token,
            headers=self.headers,
            allow_lan=self.studio_allow_lan,
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
        if path == HOME_CLASSIC_PATH:
            static_handlers.handle_home(self)
            return True
        if path == "/":
            if self._dispatch_home_root():
                return True
        if path == HOME_V2_PATH:
            static_handlers.handle_home_v2(self)
            return True
        if path == STATUS_PATH:
            job_handlers.handle_status(self)
            return True
        if path == CONFIG_PATH:
            config_handlers.handle_config(self)
            return True
        if path == TRIPS_PATH:
            trip_handlers.handle_trips(self)
            return True
        if path == CHAPTER_LAYOUT_PATH:
            trip_handlers.handle_chapter_layout(self)
            return True
        entry_trip_id = match_entry(path)
        if entry_trip_id is not None:
            trip_handlers.handle_entry(self, entry_trip_id)
            return True
        if path.startswith(STUDIO_ASSET_PREFIX):
            return static_handlers.handle_studio_asset(self, path)
        return False

    def _dispatch_home_root(self) -> bool:
        """GET / · homepage v2 门控（FEATURE-FLAG §3 / M20-j）。"""
        return static_handlers.handle_home_root(self)

    def studio_dispatch_PATCH(self, path: str) -> bool:
        if not self._studio_require_post_auth():
            return True
        if path == CONFIG_PATH:
            config_handlers.handle_config(self)
            return True
        trip_id = match_trip_intent(path)
        if trip_id is not None:
            trip_handlers.handle_patch_intent(self, trip_id)
            return True
        trip_id = match_trip_pipeline(path)
        if trip_id is not None:
            trip_handlers.handle_patch_pipeline(self, trip_id)
            return True
        return False

    def studio_dispatch_POST(self, path: str) -> bool:
        if not self._studio_require_post_auth():
            return True
        if path == IMPORT_PATH:
            import_handlers.handle_import(self)
            return True
        if path == LONGSHOT_PATH:
            export_handlers.handle_longshot(self)
            return True
        if path == NARRATE_PATH:
            export_handlers.handle_narrate(self)
            return True
        if path == REVEAL_PATH:
            export_handlers.handle_reveal(self)
            return True
        if path == CANCEL_PATH:
            job_handlers.handle_cancel(self)
            return True
        if path == EXPORT_PATH:
            export_handlers.handle_export(self)
            return True
        if path == PICK_FOLDER_PATH:
            config_handlers.handle_pick_folder(self)
            return True
        if path == ALBUM_PREVIEW_PATH:
            import_handlers.handle_album_preview(self)
            return True
        if path == STUDIO_EVENT_PATH:
            telemetry_handlers.handle_studio_event(self)
            return True
        curate_trip_id = match_trip_curate(path)
        if curate_trip_id is not None:
            trip_handlers.handle_trip_curate(self, curate_trip_id)
            return True
        return False

    def studio_trip_parts(self, path: str) -> tuple[str, str] | None:
        if not path.startswith("/"):
            return None
        parts = path.strip("/").split("/", 1)
        if len(parts) != 2:
            return None
        trip_id, rel = parts[0], parts[1]
        if not trip_id or trip_id.startswith("_") or trip_id.startswith("__"):
            return None
        if not rel:
            return None
        return trip_id, rel

    def studio_bind_trip(self, trip_id: str) -> Path | None:
        if not self.trips_dir:
            return None
        return bind_studio_trip(self, trip_id)

    def should_inject_studio_chrome(self, rel_path: str) -> bool:
        return should_inject_studio_chrome(rel_path)

    def _studio_cfg(self) -> AppConfig:
        return self.app_config or get_config()

    def _studio_handle_config(self) -> None:
        config_handlers.handle_config(self)

    def _studio_handle_patch_pipeline(self, trip_id: str) -> None:
        trip_handlers.handle_patch_pipeline(self, trip_id)

    def _studio_handle_patch_intent(self, trip_id: str) -> None:
        trip_handlers.handle_patch_intent(self, trip_id)

    def _studio_handle_rerender(self) -> None:
        trip_handlers.handle_rerender(self)

    def _studio_match_trip_intent(self, path: str) -> str | None:
        return match_trip_intent(path)

    def _studio_match_trip_pipeline(self, path: str) -> str | None:
        return match_trip_pipeline(path)

    def _studio_trip_api(self, path: str) -> tuple[str, str] | None:
        return match_trip_api(path)
