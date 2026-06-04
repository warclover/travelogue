"""Studio HTTP path constants."""

from __future__ import annotations

HOME_V2_PATH = "/v2"
HOME_CLASSIC_PATH = "/classic"
TEMPLATES_ADMIN_UI_PATH = "/templates-admin"
IMPORT_PATH = "/__travelogue/import"
STATUS_PATH = "/__travelogue/status"
CONFIG_PATH = "/__travelogue/config"
TRIPS_PATH = "/__travelogue/trips"
LONGSHOT_PATH = "/__travelogue/longshot"
NARRATE_PATH = "/__travelogue/narrate"
REVEAL_PATH = "/__travelogue/reveal"
CANCEL_PATH = "/__travelogue/cancel"
EXPORT_PATH = "/__travelogue/export"
PICK_FOLDER_PATH = "/__travelogue/pick-folder"
ALBUM_PREVIEW_PATH = "/__travelogue/album-preview"
TEMPLATES_PATH = "/__travelogue/templates"
TEMPLATE_REPLAY_PATH = "/__travelogue/templates/replay"
TEMPLATE_RECOMPUTE_PATH = "/__travelogue/templates/recompute"
TEMPLATE_DECISIONS_PATH = "/__travelogue/templates/decisions"
TEMPLATE_PREVIEW_PATH = "/__travelogue/templates/preview"
TEMPLATE_SUFFIX = "/template"
TEMPLATES_ADMIN_PATH = "/__travelogue/templates/admin"
TEMPLATES_ADMIN_AUDIT_PATH = "/__travelogue/templates/admin/audit"
TEMPLATES_ADMIN_DASHBOARD_PATH = "/__travelogue/templates/admin/dashboard"
TEMPLATES_ADMIN_ADMISSION_PATH = "/__travelogue/templates/admin/admission"
TEMPLATES_ADMIN_DECISIONS_PATH = "/__travelogue/templates/admin/decisions"
TEMPLATES_ADMIN_RUNTIME_PATH = "/__travelogue/templates/admin/runtime"
TEMPLATES_ADMIN_ROLLBACK_PATH = "/__travelogue/templates/admin/rollback"


def match_template_admin_metadata(path: str) -> str | None:
    prefix = TEMPLATES_ADMIN_PATH.rstrip("/") + "/"
    suffix = "/metadata"
    if not path.startswith(prefix) or not path.endswith(suffix):
        return None
    tid = path[len(prefix) : -len(suffix)].strip("/")
    if not tid or "/" in tid:
        return None
    return tid


TEMPLATES_ADMIN_REGISTER_PATH = "/__travelogue/templates/admin/register"
TEMPLATES_ADMIN_DELETE_PATH = "/__travelogue/templates/admin/delete"
TEMPLATES_ADMIN_REVIEW_PATH = "/__travelogue/templates/admin/review"


def match_template_admin_version(path: str) -> str | None:
    prefix = TEMPLATES_ADMIN_PATH.rstrip("/") + "/"
    suffix = "/version"
    if not path.startswith(prefix) or not path.endswith(suffix):
        return None
    tid = path[len(prefix) : -len(suffix)].strip("/")
    if not tid or "/" in tid:
        return None
    return tid


def match_template_admin_patch(path: str) -> str | None:
    prefix = TEMPLATES_ADMIN_PATH.rstrip("/") + "/"
    if not path.startswith(prefix):
        return None
    tid = path[len(prefix) :].strip("/")
    if not tid or "/" in tid or tid.endswith("/metadata") or tid.endswith("/version"):
        return None
    return tid
STUDIO_EVENT_PATH = "/__travelogue/studio-event"
CHAPTER_LAYOUT_PATH = "/__travelogue/chapter-layout"
STUDIO_ASSET_PREFIX = "/__studio/"
SAVE_COPY_SUFFIX = "/__travelogue/save-copy"
PROMOTE_TIER_SUFFIX = "/__travelogue/promote-tier"
RERENDER_SUFFIX = "/__travelogue/rerender"
INTENT_SUFFIX = "/intent"
COHORT_SUFFIX = "/cohort"
COHORT_REFRESH_SUFFIX = "/cohort/refresh"
PIPELINE_SUFFIX = "/pipeline"
CURATE_SUFFIX = "/curate"
