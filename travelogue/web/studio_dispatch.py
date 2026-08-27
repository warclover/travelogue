"""Declarative Studio route table and dispatcher (M-C1 / D-ARC-07).

``studio_trip_parts`` static file fallback in ``serve.py`` is intentionally
**outside** this table — only explicit API/page routes are registered here.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from travelogue.web.studio_handlers import (
    ai_ops_handlers,
    config_handlers,
    export_handlers,
    import_handlers,
    job_handlers,
    layout_strategy_handlers,
    llm_settings_handlers,
    static_handlers,
    storage_handlers,
    telemetry_handlers,
    template_admin_handlers,
    template_handlers,
    trip_handlers,
)
from travelogue.web.studio_handlers.common import (
    bind_studio_trip,
    match_aesthetic,
    match_aesthetic_preference,
    match_bento_preview,
    match_entry,
    match_trip_output_item,
    match_trip_outputs,
    match_source_status,
    match_trip_ai_intent_brief,
    match_trip_ai_layout_critic,
    match_trip_ai_layout_critic_accept,
    match_trip_ai_layout_feedback,
    match_trip_asset_media,
    match_trip_bookends,
    match_trip_bookends_repick_closing,
    match_trip_bookends_repick_opening,
    match_trip_bookends_resolve_closing,
    match_trip_bookends_resolve_opening,
    match_trip_bookends_restore_auto,
    match_trip_chapter_copy_intent,
    match_trip_cohort,
    match_trip_cohort_refresh,
    match_trip_copy_telemetry,
    match_trip_curate,
    match_trip_delete,
    match_trip_intent,
    match_trip_edition,
    match_trip_layout_vibe,
    match_trip_moment_curation,
    match_trip_moment_patch,
    match_trip_pipeline,
    match_trip_promote_tier,
    match_trip_rerender,
    match_trip_save_copy,
    match_trip_screen_replan,
    match_trip_sibling_journal,
    match_trip_template,
    match_trip_title_art_resolve,
)
from travelogue.web.studio_handlers.paths import (
    ALBUM_PREVIEW_PATH,
    CANCEL_PATH,
    CHAPTER_LAYOUT_PATH,
    CONFIG_PATH,
    EXPORT_PATH,
    HOME_CLASSIC_PATH,
    HOME_V2_PATH,
    IMPORT_PATH,
    LAYOUT_STRATEGIES_PATH,
    LAYOUT_STRATEGIES_RUNTIME_APPROVE_PATH,
    LAYOUT_STRATEGIES_SANDBOX_PATH,
    LAYOUT_STRATEGIES_SHADOW_PATH,
    LLM_PING_PATH,
    LLM_SETTINGS_PATH,
    LLM_STATUS_PATH,
    LONGSHOT_PATH,
    LONGSHOT_UPLOAD_PATH,
    LSE_CAPS_API_PATH,
    LSE_FLAGS_UI_PATH,
    NARRATE_PATH,
    OUTPUT_RECIPE_PATH,
    PICK_FOLDER_PATH,
    REVEAL_PATH,
    SHUTDOWN_PATH,
    STATUS_PATH,
    STORAGE_CLEANUP_PATH,
    STORAGE_REMOUNT_PATH,
    STORAGE_USAGE_PATH,
    STUDIO_ASSET_PREFIX,
    STUDIO_EVENT_PATH,
    TEMPLATE_DECISIONS_PATH,
    TEMPLATE_PREVIEW_PATH,
    TEMPLATE_RECOMPUTE_PATH,
    TEMPLATE_REPLAY_PATH,
    TEMPLATES_ADMIN_ADMISSION_PATH,
    TEMPLATES_ADMIN_AUDIT_PATH,
    TEMPLATES_ADMIN_DASHBOARD_PATH,
    TEMPLATES_ADMIN_DECISIONS_PATH,
    TEMPLATES_ADMIN_DELETE_PATH,
    TEMPLATES_ADMIN_PATH,
    TEMPLATES_ADMIN_REGISTER_PATH,
    TEMPLATES_ADMIN_REVIEW_PATH,
    TEMPLATES_ADMIN_ROLLBACK_PATH,
    TEMPLATES_ADMIN_RUNTIME_PATH,
    TEMPLATES_ADMIN_UI_PATH,
    TEMPLATES_PATH,
    TRIPS_PATH,
    AI_OPS_ADMIN_UI_PATH,
    AI_OPS_SUMMARY_PATH,
    AI_UNLOCK_GATE_PATH,
    match_layout_strategy_decisions,
    match_layout_strategy_detail,
    match_layout_strategy_rollback,
    match_layout_strategy_runtime,
    match_layout_strategy_weights,
    match_template_admin_metadata,
    match_template_admin_patch,
    match_template_admin_version,
)

RouteKind = Literal["exact", "prefix", "capture"]
Matcher = Callable[[str], Any]
Invoker = Callable[[Any, Any], None]


@dataclass(frozen=True, slots=True)
class RouteSpec:
    method: str
    path: str
    handler: str
    kind: RouteKind = "exact"
    auth: bool = False


# Declarative route table — order matches legacy if-chain precedence.
ROUTE_SPECS: tuple[RouteSpec, ...] = (
    # GET — public home + studio static assets (auth=False)
    RouteSpec("GET", HOME_CLASSIC_PATH, "static_handlers.handle_home"),
    RouteSpec("GET", "/", "static_handlers.handle_home_root"),
    RouteSpec("GET", HOME_V2_PATH, "static_handlers.send_redirect"),
    RouteSpec("GET", f"{STUDIO_ASSET_PREFIX}*", "static_handlers.handle_studio_asset", "prefix"),
    # GET — authenticated APIs / admin UIs
    RouteSpec("GET", STATUS_PATH, "job_handlers.handle_status", auth=True),
    RouteSpec("GET", CONFIG_PATH, "config_handlers.handle_config", auth=True),
    RouteSpec("GET", OUTPUT_RECIPE_PATH, "export_handlers.handle_output_recipe", auth=True),
    RouteSpec("GET", STORAGE_USAGE_PATH, "storage_handlers.handle_storage_usage", auth=True),
    RouteSpec("GET", LLM_STATUS_PATH, "llm_settings_handlers.handle_llm_status", auth=True),
    RouteSpec("GET", TEMPLATES_ADMIN_UI_PATH, "static_handlers.handle_templates_admin_page", auth=True),
    RouteSpec("GET", LSE_FLAGS_UI_PATH, "static_handlers.handle_lse_flags_admin_page", auth=True),
    RouteSpec("GET", AI_OPS_ADMIN_UI_PATH, "ai_ops_handlers.handle_ai_ops_admin_page", auth=True),
    RouteSpec("GET", AI_OPS_SUMMARY_PATH, "ai_ops_handlers.handle_get_ai_ops_summary", auth=True),
    RouteSpec("GET", AI_UNLOCK_GATE_PATH, "ai_ops_handlers.handle_get_unlock_gate", auth=True),
    RouteSpec("GET", LSE_CAPS_API_PATH, "layout_strategy_handlers.handle_lse_capabilities_get", auth=True),
    RouteSpec("GET", TEMPLATES_PATH, "template_handlers.handle_templates_list", auth=True),
    RouteSpec(
        "GET",
        f"{TEMPLATE_DECISIONS_PATH}*",
        "template_handlers.handle_template_decisions",
        "prefix",
        auth=True,
    ),
    RouteSpec("GET", TEMPLATES_ADMIN_PATH, "template_admin_handlers.handle_templates_admin_list", auth=True),
    RouteSpec("GET", TEMPLATES_ADMIN_AUDIT_PATH, "template_admin_handlers.handle_templates_admin_audit", auth=True),
    RouteSpec(
        "GET",
        TEMPLATES_ADMIN_DASHBOARD_PATH,
        "template_admin_handlers.handle_templates_admin_dashboard",
        auth=True,
    ),
    RouteSpec(
        "GET",
        TEMPLATES_ADMIN_DECISIONS_PATH,
        "template_admin_handlers.handle_templates_admin_decisions",
        auth=True,
    ),
    RouteSpec("GET", LAYOUT_STRATEGIES_PATH, "layout_strategy_handlers.handle_layout_strategies_list", auth=True),
    RouteSpec(
        "GET",
        "/__travelogue/layout-strategies/{strategyId}/decisions",
        "layout_strategy_handlers.handle_layout_strategy_decisions",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "GET",
        "/__travelogue/layout-strategies/weights/{weightsHash}",
        "layout_strategy_handlers.handle_layout_strategy_weights",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "GET",
        "/__travelogue/layout-strategies/{strategyId}",
        "layout_strategy_handlers.handle_layout_strategy_detail",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "GET",
        "/__travelogue/templates/admin/{templateId}/version",
        "template_admin_handlers.handle_templates_admin_version_diff",
        "capture",
        auth=True,
    ),
    RouteSpec("GET", TRIPS_PATH, "trip_handlers.handle_trips", auth=True),
    RouteSpec(
        "GET",
        "/__travelogue/trips/{tripId}/outputs",
        "trip_handlers.handle_get_outputs",
        "capture",
        auth=True,
    ),
    RouteSpec("GET", CHAPTER_LAYOUT_PATH, "trip_handlers.handle_chapter_layout", auth=True),
    RouteSpec("GET", "/__travelogue/trips/{tripId}/entry", "trip_handlers.handle_entry", "capture", auth=True),
    RouteSpec(
        "GET",
        "/__travelogue/trips/{tripId}/source-status",
        "storage_handlers.handle_source_status",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "GET",
        "/__travelogue/trips/{tripId}/cohort",
        "trip_handlers.handle_get_cohort",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "GET",
        "/__travelogue/trips/{tripId}/aesthetic",
        "trip_handlers.handle_aesthetic",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "GET",
        "/__travelogue/trips/{tripId}/bento-preview",
        "trip_handlers.handle_bento_preview",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "GET",
        "/__travelogue/trips/{tripId}/curation/moment",
        "trip_handlers.handle_get_moment_curation",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "GET",
        "/__travelogue/trips/{tripId}/bookends",
        "trip_handlers.handle_get_bookends",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "GET",
        "/__travelogue/trips/{tripId}/sibling-journal",
        "trip_handlers.handle_sibling_journal",
        "capture",
        auth=True,
    ),
    # PATCH
    RouteSpec("PATCH", CONFIG_PATH, "config_handlers.handle_config", auth=True),
    RouteSpec("POST", STORAGE_CLEANUP_PATH, "storage_handlers.handle_storage_cleanup", auth=True),
    RouteSpec("POST", STORAGE_REMOUNT_PATH, "storage_handlers.handle_storage_remount", auth=True),
    RouteSpec("POST", LLM_SETTINGS_PATH, "llm_settings_handlers.handle_llm_settings", auth=True),
    RouteSpec("DELETE", LLM_SETTINGS_PATH, "llm_settings_handlers.handle_llm_settings", auth=True),
    RouteSpec("POST", LLM_PING_PATH, "llm_settings_handlers.handle_llm_ping", auth=True),
    RouteSpec("PATCH", LSE_CAPS_API_PATH, "layout_strategy_handlers.handle_lse_capabilities_patch", auth=True),
    RouteSpec(
        "PATCH",
        "/__travelogue/templates/admin/{templateId}",
        "template_admin_handlers.handle_templates_admin_patch",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "PATCH",
        "/__travelogue/templates/admin/{templateId}/metadata",
        "template_admin_handlers.handle_templates_admin_metadata",
        "capture",
        auth=True,
    ),
    RouteSpec("PATCH", "/__travelogue/trips/{tripId}/intent", "trip_handlers.handle_patch_intent", "capture", auth=True),
    RouteSpec("PATCH", "/__travelogue/trips/{tripId}/cohort", "trip_handlers.handle_patch_cohort", "capture", auth=True),
    RouteSpec("PATCH", "/__travelogue/trips/{tripId}/template", "trip_handlers.handle_patch_template", "capture", auth=True),
    RouteSpec("PATCH", "/__travelogue/trips/{tripId}/pipeline", "trip_handlers.handle_patch_pipeline", "capture", auth=True),
    RouteSpec(
        "PATCH",
        "/__travelogue/trips/{tripId}/screens/{screenId}/replan",
        "trip_handlers.handle_patch_screen_replan",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "PATCH",
        "/__travelogue/trips/{tripId}/chapters/{chapterId}/copy-intent",
        "trip_handlers.handle_patch_copy_intent",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "PATCH",
        "/__travelogue/trips/{tripId}/asset-media-class",
        "trip_handlers.handle_asset_media_class",
        "capture",
        auth=True,
    ),
    RouteSpec("PATCH", "/__travelogue/trips/{tripId}/moment", "trip_handlers.handle_patch_moment", "capture", auth=True),
    RouteSpec(
        "PATCH",
        "/__travelogue/trips/{tripId}/aesthetic/preference",
        "trip_handlers.handle_patch_stratum_preference",
        "capture",
        auth=True,
    ),
    # DELETE
    RouteSpec(
        "DELETE",
        "/__travelogue/trips/{tripId}/outputs/{outputId}",
        "trip_handlers.handle_delete_output",
        "capture",
        auth=True,
    ),
    RouteSpec("DELETE", "/__travelogue/trips/{tripId}", "trip_handlers.handle_delete_trip", "capture", auth=True),
    # POST
    RouteSpec("POST", AI_UNLOCK_GATE_PATH, "ai_ops_handlers.handle_post_unlock_gate", auth=True),
    RouteSpec("POST", IMPORT_PATH, "import_handlers.handle_import", auth=True),
    RouteSpec("POST", LONGSHOT_PATH, "export_handlers.handle_longshot", auth=True),
    RouteSpec("POST", LONGSHOT_UPLOAD_PATH, "export_handlers.handle_longshot_upload", auth=True),
    RouteSpec("POST", NARRATE_PATH, "export_handlers.handle_narrate", auth=True),
    RouteSpec("POST", REVEAL_PATH, "export_handlers.handle_reveal", auth=True),
    RouteSpec("POST", CANCEL_PATH, "job_handlers.handle_cancel", auth=True),
    RouteSpec("POST", EXPORT_PATH, "export_handlers.handle_export", auth=True),
    RouteSpec("POST", SHUTDOWN_PATH, "export_handlers.handle_shutdown", auth=True),
    RouteSpec("POST", PICK_FOLDER_PATH, "config_handlers.handle_pick_folder", auth=True),
    RouteSpec("POST", ALBUM_PREVIEW_PATH, "import_handlers.handle_album_preview", auth=True),
    RouteSpec("POST", TEMPLATE_REPLAY_PATH, "template_handlers.handle_template_replay", auth=True),
    RouteSpec("POST", TEMPLATE_RECOMPUTE_PATH, "template_handlers.handle_template_recompute", auth=True),
    RouteSpec("POST", TEMPLATE_PREVIEW_PATH, "template_handlers.handle_template_preview", auth=True),
    RouteSpec("POST", TEMPLATES_ADMIN_ROLLBACK_PATH, "template_admin_handlers.handle_templates_admin_rollback", auth=True),
    RouteSpec("POST", TEMPLATES_ADMIN_ADMISSION_PATH, "template_admin_handlers.handle_templates_admin_admission", auth=True),
    RouteSpec("POST", TEMPLATES_ADMIN_RUNTIME_PATH, "template_admin_handlers.handle_templates_admin_runtime", auth=True),
    RouteSpec(
        "POST",
        LAYOUT_STRATEGIES_RUNTIME_APPROVE_PATH,
        "layout_strategy_handlers.handle_layout_strategy_runtime_approve",
        auth=True,
    ),
    RouteSpec("POST", LAYOUT_STRATEGIES_SANDBOX_PATH, "layout_strategy_handlers.handle_layout_strategy_sandbox", auth=True),
    RouteSpec("POST", LAYOUT_STRATEGIES_SHADOW_PATH, "layout_strategy_handlers.handle_layout_strategy_shadow", auth=True),
    RouteSpec(
        "POST",
        "/__travelogue/layout-strategies/{strategyId}/rollback",
        "layout_strategy_handlers.handle_layout_strategy_rollback",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "POST",
        "/__travelogue/layout-strategies/{strategyId}/runtime",
        "layout_strategy_handlers.handle_layout_strategy_runtime_propose",
        "capture",
        auth=True,
    ),
    RouteSpec("POST", TEMPLATES_ADMIN_REGISTER_PATH, "template_admin_handlers.handle_templates_admin_register", auth=True),
    RouteSpec("POST", TEMPLATES_ADMIN_DELETE_PATH, "template_admin_handlers.handle_templates_admin_delete", auth=True),
    RouteSpec("POST", TEMPLATES_ADMIN_REVIEW_PATH, "template_admin_handlers.handle_templates_admin_review", auth=True),
    RouteSpec("POST", STUDIO_EVENT_PATH, "telemetry_handlers.handle_studio_event", auth=True),
    RouteSpec("POST", "/__travelogue/trips/{tripId}/curate", "trip_handlers.handle_trip_curate", "capture", auth=True),
    RouteSpec(
        "POST",
        "/__travelogue/trips/{tripId}/layout-vibe",
        "trip_handlers.handle_layout_vibe",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "POST",
        "/__travelogue/trips/{tripId}/edition",
        "trip_handlers.handle_trip_edition",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "POST",
        "/__travelogue/trips/{tripId}/bookends/resolve-opening",
        "trip_handlers.handle_post_resolve_opening",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "POST",
        "/__travelogue/trips/{tripId}/bookends/resolve-closing",
        "trip_handlers.handle_post_resolve_closing",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "POST",
        "/__travelogue/trips/{tripId}/bookends/repick-opening",
        "trip_handlers.handle_post_repick_opening",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "POST",
        "/__travelogue/trips/{tripId}/bookends/repick-closing",
        "trip_handlers.handle_post_repick_closing",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "POST",
        "/__travelogue/trips/{tripId}/bookends/restore-auto",
        "trip_handlers.handle_post_restore_auto",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "POST",
        "/__travelogue/trips/{tripId}/title-art/resolve",
        "trip_handlers.handle_post_resolve_title_art",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "POST",
        "/__travelogue/trips/{tripId}/ai/intent-brief",
        "ai_ops_handlers.handle_post_intent_brief",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "POST",
        "/__travelogue/trips/{tripId}/ai/layout-critic/accept",
        "ai_ops_handlers.handle_post_layout_critic_accept",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "POST",
        "/__travelogue/trips/{tripId}/ai/layout-critic",
        "ai_ops_handlers.handle_post_layout_critic",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "POST",
        "/__travelogue/trips/{tripId}/ai/layout-feedback",
        "ai_ops_handlers.handle_post_layout_feedback",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "POST",
        "/__travelogue/trips/{tripId}/asset-media-class",
        "trip_handlers.handle_asset_media_class",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "POST",
        "/__travelogue/trips/{tripId}/cohort/refresh",
        "trip_handlers.handle_post_cohort_refresh",
        "capture",
        auth=True,
    ),
    RouteSpec(
        "POST",
        "/__travelogue/trips/{tripId}/copy-telemetry",
        "trip_handlers.handle_post_copy_telemetry",
        "capture",
        auth=True,
    ),
    RouteSpec("POST", "{tripId}/__travelogue/save-copy", "serve._handle_save_copy", "capture", auth=True),
    RouteSpec("POST", "{tripId}/__travelogue/promote-tier", "serve._handle_promote_tier", "capture", auth=True),
    RouteSpec("POST", "{tripId}/__travelogue/rerender", "trip_handlers.handle_rerender", "capture", auth=True),
)


def studio_route_snapshot() -> list[dict[str, str]]:
    """Return sorted method+path+handler triples for AC-ARC-13 snapshot tests."""
    rows = [{"method": s.method, "path": s.path, "handler": s.handler} for s in ROUTE_SPECS]
    return sorted(rows, key=lambda r: (r["method"], r["path"], r["handler"]))


def _bind_trip_or_404(handler: Any, trip_id: str) -> bool:
    if bind_studio_trip(handler, trip_id) is None:
        handler.send_error(404)
        return False
    return True


def _invoke_save_copy(handler: Any, trip_id: str) -> None:
    if not _bind_trip_or_404(handler, trip_id):
        return
    handler._handle_save_copy()


def _invoke_promote_tier(handler: Any, trip_id: str) -> None:
    if not _bind_trip_or_404(handler, trip_id):
        return
    handler._handle_promote_tier()


def _invoke_rerender(handler: Any, trip_id: str) -> None:
    if not _bind_trip_or_404(handler, trip_id):
        return
    trip_handlers.handle_rerender(handler)


def _invoke_redirect_home(handler: Any, _cap: Any = None) -> None:
    static_handlers.send_redirect(handler, "/")


def _invoke_studio_asset(handler: Any, path: str) -> None:
    static_handlers.handle_studio_asset(handler, path)


def _invoke_template_decisions(handler: Any, path: str) -> None:
    template_handlers.handle_template_decisions(handler)


_CAPTURE_MATCHERS: dict[str, Matcher] = {
    "/__travelogue/layout-strategies/{strategyId}/decisions": match_layout_strategy_decisions,
    "/__travelogue/layout-strategies/weights/{weightsHash}": match_layout_strategy_weights,
    "/__travelogue/layout-strategies/{strategyId}": match_layout_strategy_detail,
    "/__travelogue/templates/admin/{templateId}/version": match_template_admin_version,
    "/__travelogue/trips/{tripId}/entry": match_entry,
    "/__travelogue/trips/{tripId}/outputs": match_trip_outputs,
    "/__travelogue/trips/{tripId}/outputs/{outputId}": match_trip_output_item,
    "/__travelogue/trips/{tripId}/source-status": match_source_status,
    "/__travelogue/trips/{tripId}/cohort": match_trip_cohort,
    "/__travelogue/trips/{tripId}/aesthetic": match_aesthetic,
    "/__travelogue/trips/{tripId}/bento-preview": match_bento_preview,
    "/__travelogue/trips/{tripId}/curation/moment": match_trip_moment_curation,
    "/__travelogue/trips/{tripId}/bookends": match_trip_bookends,
    "/__travelogue/trips/{tripId}/sibling-journal": match_trip_sibling_journal,
    "/__travelogue/trips/{tripId}/bookends/resolve-opening": match_trip_bookends_resolve_opening,
    "/__travelogue/trips/{tripId}/bookends/resolve-closing": match_trip_bookends_resolve_closing,
    "/__travelogue/trips/{tripId}/bookends/repick-opening": match_trip_bookends_repick_opening,
    "/__travelogue/trips/{tripId}/bookends/repick-closing": match_trip_bookends_repick_closing,
    "/__travelogue/trips/{tripId}/bookends/restore-auto": match_trip_bookends_restore_auto,
    "/__travelogue/trips/{tripId}/title-art/resolve": match_trip_title_art_resolve,
    "/__travelogue/trips/{tripId}/ai/intent-brief": match_trip_ai_intent_brief,
    "/__travelogue/trips/{tripId}/ai/layout-critic/accept": match_trip_ai_layout_critic_accept,
    "/__travelogue/trips/{tripId}/ai/layout-critic": match_trip_ai_layout_critic,
    "/__travelogue/trips/{tripId}/ai/layout-feedback": match_trip_ai_layout_feedback,
    "/__travelogue/templates/admin/{templateId}": match_template_admin_patch,
    "/__travelogue/templates/admin/{templateId}/metadata": match_template_admin_metadata,
    "/__travelogue/trips/{tripId}/intent": match_trip_intent,
    "/__travelogue/trips/{tripId}/template": match_trip_template,
    "/__travelogue/trips/{tripId}/pipeline": match_trip_pipeline,
    "/__travelogue/trips/{tripId}/screens/{screenId}/replan": match_trip_screen_replan,
    "/__travelogue/trips/{tripId}/chapters/{chapterId}/copy-intent": match_trip_chapter_copy_intent,
    "/__travelogue/trips/{tripId}/asset-media-class": match_trip_asset_media,
    "/__travelogue/trips/{tripId}/moment": match_trip_moment_patch,
    "/__travelogue/trips/{tripId}/aesthetic/preference": match_aesthetic_preference,
    "/__travelogue/trips/{tripId}": match_trip_delete,
    "/__travelogue/layout-strategies/{strategyId}/rollback": match_layout_strategy_rollback,
    "/__travelogue/layout-strategies/{strategyId}/runtime": match_layout_strategy_runtime,
    "/__travelogue/trips/{tripId}/curate": match_trip_curate,
    "/__travelogue/trips/{tripId}/layout-vibe": match_trip_layout_vibe,
    "/__travelogue/trips/{tripId}/edition": match_trip_edition,
    "/__travelogue/trips/{tripId}/cohort/refresh": match_trip_cohort_refresh,
    "/__travelogue/trips/{tripId}/copy-telemetry": match_trip_copy_telemetry,
    "{tripId}/__travelogue/save-copy": match_trip_save_copy,
    "{tripId}/__travelogue/promote-tier": match_trip_promote_tier,
    "{tripId}/__travelogue/rerender": match_trip_rerender,
}


def _invoke_capture(handler_fn: Callable[..., None], handler: Any, cap: Any) -> None:
    if isinstance(cap, tuple):
        handler_fn(handler, *cap)
    else:
        handler_fn(handler, cap)


def _resolve_handler(handler_id: str) -> Callable[..., None]:
    if handler_id == "static_handlers.send_redirect":
        return lambda h: _invoke_redirect_home(h)

    module_name, fn_name = handler_id.rsplit(".", 1)
    module = {
        "static_handlers": static_handlers,
        "config_handlers": config_handlers,
        "llm_settings_handlers": llm_settings_handlers,
        "job_handlers": job_handlers,
        "layout_strategy_handlers": layout_strategy_handlers,
        "template_handlers": template_handlers,
        "template_admin_handlers": template_admin_handlers,
        "trip_handlers": trip_handlers,
        "import_handlers": import_handlers,
        "export_handlers": export_handlers,
        "storage_handlers": storage_handlers,
        "telemetry_handlers": telemetry_handlers,
        "ai_ops_handlers": ai_ops_handlers,
    }[module_name]
    return getattr(module, fn_name)


def _build_invoker(spec: RouteSpec) -> Invoker:
    if spec.handler == "static_handlers.handle_studio_asset":
        return lambda h, cap: _invoke_studio_asset(h, cap)
    if spec.handler == "template_handlers.handle_template_decisions":
        return lambda h, cap: _invoke_template_decisions(h, cap)
    if spec.handler == "serve._handle_save_copy":
        return lambda h, cap: _invoke_save_copy(h, cap)
    if spec.handler == "serve._handle_promote_tier":
        return lambda h, cap: _invoke_promote_tier(h, cap)
    if spec.handler == "trip_handlers.handle_rerender":
        return lambda h, cap: _invoke_rerender(h, cap)

    if spec.kind == "exact":
        return lambda h, _cap=None: _resolve_handler(spec.handler)(h)
    return lambda h, cap: _invoke_capture(_resolve_handler(spec.handler), h, cap)


@dataclass(frozen=True, slots=True)
class _CompiledRoute:
    spec: RouteSpec
    match: Matcher
    invoke: Invoker


def _compile_route(spec: RouteSpec) -> _CompiledRoute:
    if spec.kind == "exact":
        path = spec.path

        def match_exact(p: str) -> bool:
            return p == path

        invoker = _build_invoker(spec)
        if spec.handler == "static_handlers.send_redirect":
            invoker = lambda h, _cap=None: _invoke_redirect_home(h)
        return _CompiledRoute(spec, match_exact, invoker)

    if spec.kind == "prefix":
        prefix = spec.path[:-1] if spec.path.endswith("*") else spec.path

        def match_prefix(p: str) -> str | None:
            return p if p.startswith(prefix) else None

        return _CompiledRoute(spec, match_prefix, _build_invoker(spec))

    matcher = _CAPTURE_MATCHERS[spec.path]
    return _CompiledRoute(spec, matcher, _build_invoker(spec))


_COMPILED_BY_METHOD: dict[str, tuple[_CompiledRoute, ...]] = {}


def _routes_for(method: str) -> Sequence[_CompiledRoute]:
    cached = _COMPILED_BY_METHOD.get(method)
    if cached is not None:
        return cached
    compiled = tuple(_compile_route(spec) for spec in ROUTE_SPECS if spec.method == method)
    _COMPILED_BY_METHOD[method] = compiled
    return compiled


def dispatch_studio(method: str, path: str, handler: Any, *, require_auth: Callable[[], bool]) -> bool:
    """Match ``path`` against the route table and invoke the handler.

    Returns True when a route matched (including auth rejection short-circuit).
    """
    from travelogue.web.studio_json import StudioJsonBodyError

    for route in _routes_for(method):
        cap = route.match(path)
        if cap is False or cap is None:
            continue
        if route.spec.auth and not require_auth():
            return True
        try:
            route.invoke(handler, cap if cap is not True else None)
        except StudioJsonBodyError:
            pass
        return True
    return False
