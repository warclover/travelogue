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
    template_admin_handlers,
    template_handlers,
    trip_handlers,
)
from travelogue.web.studio_handlers.common import (
    bind_studio_trip,
    match_aesthetic,
    match_bento_preview,
    match_entry,
    match_trip_api,
    match_trip_cohort,
    match_trip_cohort_refresh,
    match_trip_curate,
    match_trip_delete,
    match_trip_intent,
    match_trip_pipeline,
    match_trip_screen_replan,
    match_trip_template,
)
from travelogue.web.studio_handlers.paths import (
    CANCEL_PATH,
    CHAPTER_LAYOUT_PATH,
    CONFIG_PATH,
    CURATE_SUFFIX,
    EXPORT_PATH,
    HOME_CLASSIC_PATH,
    HOME_V2_PATH,
    TEMPLATES_ADMIN_UI_PATH,
    IMPORT_PATH,
    INTENT_SUFFIX,
    LONGSHOT_PATH,
    NARRATE_PATH,
    PICK_FOLDER_PATH,
    ALBUM_PREVIEW_PATH,
    STUDIO_EVENT_PATH,
    TEMPLATES_PATH,
    TEMPLATE_REPLAY_PATH,
    TEMPLATE_RECOMPUTE_PATH,
    TEMPLATE_DECISIONS_PATH,
    TEMPLATE_PREVIEW_PATH,
    TEMPLATES_ADMIN_PATH,
    TEMPLATES_ADMIN_AUDIT_PATH,
    TEMPLATES_ADMIN_DASHBOARD_PATH,
    TEMPLATES_ADMIN_ADMISSION_PATH,
    TEMPLATES_ADMIN_DECISIONS_PATH,
    TEMPLATES_ADMIN_RUNTIME_PATH,
    TEMPLATES_ADMIN_ROLLBACK_PATH,
    TEMPLATES_ADMIN_REGISTER_PATH,
    TEMPLATES_ADMIN_DELETE_PATH,
    TEMPLATES_ADMIN_REVIEW_PATH,
    match_template_admin_patch,
    match_template_admin_version,
    match_template_admin_metadata,
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
            # M21-c：收敛旧并行入口 /v2 → /
            static_handlers.send_redirect(self, "/")
            return True
        if path == STATUS_PATH:
            job_handlers.handle_status(self)
            return True
        if path == CONFIG_PATH:
            config_handlers.handle_config(self)
            return True
        if path == TEMPLATES_ADMIN_UI_PATH:
            static_handlers.handle_templates_admin_page(self)
            return True
        if path == TEMPLATES_PATH:
            template_handlers.handle_templates_list(self)
            return True
        if path.startswith(TEMPLATE_DECISIONS_PATH):
            template_handlers.handle_template_decisions(self)
            return True
        if path == TEMPLATES_ADMIN_PATH:
            template_admin_handlers.handle_templates_admin_list(self)
            return True
        if path == TEMPLATES_ADMIN_AUDIT_PATH:
            template_admin_handlers.handle_templates_admin_audit(self)
            return True
        if path == TEMPLATES_ADMIN_DASHBOARD_PATH:
            template_admin_handlers.handle_templates_admin_dashboard(self)
            return True
        if path == TEMPLATES_ADMIN_DECISIONS_PATH:
            template_admin_handlers.handle_templates_admin_decisions(self)
            return True
        ver_tid = match_template_admin_version(path)
        if ver_tid is not None:
            template_admin_handlers.handle_templates_admin_version_diff(self, ver_tid)
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
        cohort_trip_id = match_trip_cohort(path)
        if cohort_trip_id is not None:
            trip_handlers.handle_get_cohort(self, cohort_trip_id)
            return True
        aesthetic_trip_id = match_aesthetic(path)
        if aesthetic_trip_id is not None:
            trip_handlers.handle_aesthetic(self, aesthetic_trip_id)
            return True
        bento_trip_id = match_bento_preview(path)
        if bento_trip_id is not None:
            trip_handlers.handle_bento_preview(self, bento_trip_id)
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
        admin_tid = match_template_admin_patch(path)
        if admin_tid is not None:
            template_admin_handlers.handle_templates_admin_patch(self, admin_tid)
            return True
        meta_tid = match_template_admin_metadata(path)
        if meta_tid is not None:
            template_admin_handlers.handle_templates_admin_metadata(self, meta_tid)
            return True
        trip_id = match_trip_intent(path)
        if trip_id is not None:
            trip_handlers.handle_patch_intent(self, trip_id)
            return True
        trip_id = match_trip_cohort(path)
        if trip_id is not None:
            trip_handlers.handle_patch_cohort(self, trip_id)
            return True
        trip_id = match_trip_template(path)
        if trip_id is not None:
            trip_handlers.handle_patch_template(self, trip_id)
            return True
        trip_id = match_trip_pipeline(path)
        if trip_id is not None:
            trip_handlers.handle_patch_pipeline(self, trip_id)
            return True
        replan_match = match_trip_screen_replan(path)
        if replan_match is not None:
            replan_trip_id, screen_id = replan_match
            trip_handlers.handle_patch_screen_replan(self, replan_trip_id, screen_id)
            return True
        return False

    def studio_dispatch_DELETE(self, path: str) -> bool:
        if not self._studio_require_post_auth():
            return True
        trip_id = match_trip_delete(path)
        if trip_id is not None:
            trip_handlers.handle_delete_trip(self, trip_id)
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
        if path == TEMPLATE_REPLAY_PATH:
            template_handlers.handle_template_replay(self)
            return True
        if path == TEMPLATE_RECOMPUTE_PATH:
            template_handlers.handle_template_recompute(self)
            return True
        if path == TEMPLATE_PREVIEW_PATH:
            template_handlers.handle_template_preview(self)
            return True
        if path == TEMPLATES_ADMIN_ROLLBACK_PATH:
            template_admin_handlers.handle_templates_admin_rollback(self)
            return True
        if path == TEMPLATES_ADMIN_ADMISSION_PATH:
            template_admin_handlers.handle_templates_admin_admission(self)
            return True
        if path == TEMPLATES_ADMIN_RUNTIME_PATH:
            template_admin_handlers.handle_templates_admin_runtime(self)
            return True
        if path == TEMPLATES_ADMIN_REGISTER_PATH:
            template_admin_handlers.handle_templates_admin_register(self)
            return True
        if path == TEMPLATES_ADMIN_DELETE_PATH:
            template_admin_handlers.handle_templates_admin_delete(self)
            return True
        if path == TEMPLATES_ADMIN_REVIEW_PATH:
            template_admin_handlers.handle_templates_admin_review(self)
            return True
        if path == STUDIO_EVENT_PATH:
            telemetry_handlers.handle_studio_event(self)
            return True
        curate_trip_id = match_trip_curate(path)
        if curate_trip_id is not None:
            trip_handlers.handle_trip_curate(self, curate_trip_id)
            return True
        cohort_refresh_id = match_trip_cohort_refresh(path)
        if cohort_refresh_id is not None:
            trip_handlers.handle_post_cohort_refresh(self, cohort_refresh_id)
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
