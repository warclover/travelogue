"""Studio HTTP path constants."""

from __future__ import annotations

HOME_V2_PATH = "/v2"
HOME_CLASSIC_PATH = "/classic"
TEMPLATES_ADMIN_UI_PATH = "/templates-admin"
LSE_FLAGS_UI_PATH = "/lse-flags-admin"
AI_OPS_ADMIN_UI_PATH = "/ai-ops-admin"
AI_OPS_SUMMARY_PATH = "/__travelogue/ai/ops-summary"
LSE_CAPS_API_PATH = "/__travelogue/layout-strategies/capabilities"
IMPORT_PATH = "/__travelogue/import"
STATUS_PATH = "/__travelogue/status"
CONFIG_PATH = "/__travelogue/config"
STORAGE_USAGE_PATH = "/__travelogue/storage/usage"
STORAGE_CLEANUP_PATH = "/__travelogue/storage/cleanup"
STORAGE_REMOUNT_PATH = "/__travelogue/storage/remount"
LLM_STATUS_PATH = "/__travelogue/llm/status"
LLM_SETTINGS_PATH = "/__travelogue/llm/settings"
LLM_PING_PATH = "/__travelogue/llm/ping"
TRIPS_PATH = "/__travelogue/trips"
LONGSHOT_PATH = "/__travelogue/longshot"
LONGSHOT_UPLOAD_PATH = "/__travelogue/longshot/upload"
OUTPUT_RECIPE_PATH = "/__travelogue/output-recipe"
NARRATE_PATH = "/__travelogue/narrate"
REVEAL_PATH = "/__travelogue/reveal"
CANCEL_PATH = "/__travelogue/cancel"
EXPORT_PATH = "/__travelogue/export"
SHUTDOWN_PATH = "/__travelogue/shutdown"
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
LAYOUT_STRATEGIES_PATH = "/__travelogue/layout-strategies"
LAYOUT_STRATEGIES_RUNTIME_APPROVE_PATH = "/__travelogue/layout-strategies/runtime/approve"
LAYOUT_STRATEGIES_SANDBOX_PATH = "/__travelogue/layout-strategies/sandbox"
LAYOUT_STRATEGIES_SHADOW_PATH = "/__travelogue/layout-strategies/shadow"


def match_layout_strategy_rollback(path: str) -> str | None:
    route = _route_path_only(path)
    prefix = LAYOUT_STRATEGIES_PATH.rstrip("/") + "/"
    suffix = "/rollback"
    if not route.startswith(prefix) or not route.endswith(suffix):
        return None
    sid = route[len(prefix) : -len(suffix)].strip("/")
    if not sid or "/" in sid:
        return None
    return sid


def _route_path_only(path: str) -> str:
    from urllib.parse import urlparse

    return urlparse(path).path or path


def match_layout_strategy_decisions(path: str) -> str | None:
    route = _route_path_only(path)
    prefix = LAYOUT_STRATEGIES_PATH.rstrip("/") + "/"
    suffix = "/decisions"
    if not route.startswith(prefix) or not route.endswith(suffix):
        return None
    sid = route[len(prefix) : -len(suffix)].strip("/")
    if not sid or "/" in sid:
        return None
    return sid


def match_layout_strategy_runtime(path: str) -> str | None:
    route = _route_path_only(path)
    prefix = LAYOUT_STRATEGIES_PATH.rstrip("/") + "/"
    suffix = "/runtime"
    if not route.startswith(prefix) or not route.endswith(suffix):
        return None
    sid = route[len(prefix) : -len(suffix)].strip("/")
    if not sid or "/" in sid:
        return None
    return sid


def match_layout_strategy_weights(path: str) -> str | None:
    route = _route_path_only(path)
    prefix = LAYOUT_STRATEGIES_PATH.rstrip("/") + "/weights/"
    if not route.startswith(prefix):
        return None
    wh = route[len(prefix) :].strip("/")
    if not wh or "/" in wh:
        return None
    return wh


def match_layout_strategy_detail(path: str) -> str | None:
    route = _route_path_only(path)
    prefix = LAYOUT_STRATEGIES_PATH.rstrip("/") + "/"
    if not route.startswith(prefix):
        return None
    rest = route[len(prefix) :].strip("/")
    if (
        not rest
        or "/" in rest
        or rest.startswith("weights/")
        or rest.endswith("decisions")
        or rest.endswith("runtime")
        or rest.endswith("rollback")
        or rest == "runtime"
    ):
        return None
    return rest


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
AESTHETIC_SUFFIX = "/aesthetic"
AESTHETIC_PREFERENCE_SUFFIX = "/aesthetic/preference"
PIPELINE_SUFFIX = "/pipeline"
CURATE_SUFFIX = "/curate"
LAYOUT_VIBE_SUFFIX = "/layout-vibe"
MOMENT_SUFFIX = "/moment"
CURATION_MOMENT_SUFFIX = "/curation/moment"
BOOKENDS_SUFFIX = "/bookends"
BOOKENDS_RESOLVE_OPENING_SUFFIX = "/bookends/resolve-opening"
BOOKENDS_RESOLVE_CLOSING_SUFFIX = "/bookends/resolve-closing"
BOOKENDS_REPICK_OPENING_SUFFIX = "/bookends/repick-opening"
BOOKENDS_REPICK_CLOSING_SUFFIX = "/bookends/repick-closing"
BOOKENDS_RESTORE_AUTO_SUFFIX = "/bookends/restore-auto"
TITLE_ART_RESOLVE_SUFFIX = "/title-art/resolve"
AI_INTENT_BRIEF_SUFFIX = "/ai/intent-brief"
ASSET_MEDIA_SUFFIX = "/asset-media-class"
SCREEN_REPLAN_SUFFIX = "/screens"
COPY_INTENT_SUFFIX = "/copy-intent"
COPY_TELEMETRY_SUFFIX = "/copy-telemetry"
