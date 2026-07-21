"""Local Studio homepage / cover funnel events (domain layer).

Higher layers re-export these symbols; cover_engine must not import services.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MAX_META_BYTES = 4096


def _trim_meta(meta: dict[str, Any]) -> dict[str, Any]:
    """限制 meta 序列化体积，防止 jsonl 被异常 payload 撑爆。"""
    encoded = json.dumps(meta, ensure_ascii=False).encode("utf-8")
    if len(encoded) <= MAX_META_BYTES:
        return meta
    trimmed: dict[str, Any] = {}
    for key, value in meta.items():
        candidate = dict(trimmed)
        candidate[key] = value
        if len(json.dumps(candidate, ensure_ascii=False).encode("utf-8")) <= MAX_META_BYTES:
            trimmed[key] = value
        else:
            break
    trimmed["_truncated"] = True
    return trimmed


ALLOWED_STUDIO_HOMEPAGE_EVENTS = frozenset(
    {
        "open_sheet",
        "pick_folder",
        "import_start",
        "import_success",
        "success_primary_click",
        "prep_open",
        "demo_try",
        "layout_tier",
        # Studio homepage v2 funnel (M20-h · TELEMETRY §2)
        "experiment_exposure",
        "homepage_view",
        "cta_click",
        "sheet_close",
        "sheet_abandon",
        "lightbox_open",
        "spread_page_view",
        "shelf_resume_click",
        "shelf_menu_open",
        "shelf_delete_confirm",
        "shelf_delete_success",
        "shelf_delete_cancel",
        "shelf_longshot_start",
        "shelf_longshot_success",
        "shelf_longshot_fail",
        "shelf_longshot_reveal",
        "shelf_longshot_busy",
        # Longshot export funnel (homepage / preview toolbar)
        "longshot_export_start",
        "longshot_export_success",
        "longshot_export_fail",
        "longshot_export_cancel",
        "longshot_platform_change",
        "bento_tab_switch",
        "bento_preview_select",
        "settings_open",
        "llm_settings_open",
        "llm_settings_save",
        "llm_settings_clear",
        "llm_ping",
        "llm_narrate_click",
        "capability_card_show",
        "capability_card_cta",
        "bench_resume_click",
        "shelf_scroll_into_view",
        "js_error",
        # Phase 13 template funnel
        "template_selector_impression",
        "template_mode_changed",
        "template_manual_selected",
        "template_smart_result_shown",
        "template_fallback_shown",
        "template_create_submitted",
        # Cover Styles V5 (G-CSV-09)
        "cover_opening_style_assigned",
        "cover_opening_style_render",
        "cover_opening_style_change",
        "cover_opening_style_selector_impression",
        "cover_joint_pick",
        # Import Wizard v3（PRD-IMPORT-SHEET-v3-WIZARD §11）
        "wizard_step_view",
        "preview_loaded",
        "advanced_drawer_open",
        "folder_picked",
        "import_mode_view",
        "import_mode_switch",
        "layout_density_change",
        # Import Wizard A.1（PRD-IMPORT-WIZARD-A1-DELTA §6）
        "photo_count_hint_show",
        "advanced_fields_toggle",
        "close_confirm",
        # FTUE Optimization V1 · PRD §7
        "ftue_demo_album_click",
        "ftue_demo_album_success",
        "ftue_reveal_folder",
        "longshot_success_share_hint_shown",
        "help_funnel_reveal_folder",
        # First-Session Trust V1 · PRD §7
        "import_ui_terminal_ms",
        "import_stage_stall",
        "longshot_progress_mode",
        "longshot_success_visible_ms",
        "longshot_reveal_auto_blocked",
        "share_surface_blocked",
        # Share-Face Closeout V1 · PRD §7
        "sfc_vision_warmup_shown",
        "sfc_stub_blanked",
        "sfc_title_fallback",
        "sfc_g1_suppressed_sparse",
        "sfc_stale_label_impression",
        # Share-Face Integrity V1 · D-SFI-01
        "stub_hits",
        # Dogfood UX Fixpack V1 · PRD §8
        "rename_propagation_migrated",
        "export_ok_toast_shown",
        "export_open_folder_clicked",
        "export_platform_mismatch",
        "mobile_gate_qr_error",
        # FE allowlist sync（消 studio-event 400 · FE-DFX-44）
        "home_stub_banner_click",
        "home_stub_banner_dismiss",
        "home_stub_banner_show",
        "import_continue_stub",
        "import_fail_auth_shown",
        "import_fail_open_recent",
        "import_fail_open_settings",
        "import_keep_dupes_pref",
        "import_photo_cull_pref",
        "llm_provider_change",
        "llm_save_and_ping",
        "llm_settings_resume",
        "llm_switch_confirm",
        "preview_narrate_fail",
        "wait_tips_auto_advance",
        "wait_tips_dismiss",
        "wait_tips_manual_nav",
        "wait_tips_pause",
        "wait_tips_replay",
        "wait_tips_show",
        "wait_tips_suppress_short_wait",
    }
)


def studio_homepage_events_path() -> Path:
    return Path.home() / ".travelogue" / "telemetry" / "studio-homepage-events.jsonl"


def append_studio_homepage_event(event: str, meta: dict[str, Any] | None = None) -> Path:
    if event not in ALLOWED_STUDIO_HOMEPAGE_EVENTS:
        raise ValueError(f"unknown studio homepage event: {event}")
    path = studio_homepage_events_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
        "event": event,
    }
    if meta:
        record["meta"] = _trim_meta(meta)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path
