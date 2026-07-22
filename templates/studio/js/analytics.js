/**
 * Studio homepage funnel events (P9-P1-05) · fire-and-forget to local jsonl.
 */
import { studioAuthHeaders } from "./http.js";

const ALLOWED = new Set([
  "open_sheet",
  "pick_folder",
  "import_start",
  "import_success",
  "import_photo_cull_pref",
  "import_keep_dupes_pref",
  "import_photo_keep_mode",
  "success_primary_click",
  "prep_open",
  "demo_try",
  "layout_tier",
  // 首页 v2（M20-h · TELEMETRY §2）
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
  // Longshot 2.0 · PRD §12
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
  "llm_settings_resume",
  "llm_ping",
  "llm_save_and_ping",
  "llm_provider_change",
  "llm_switch_confirm",
  "llm_narrate_click",
  // Wait Tips V1
  "wait_tips_show",
  "wait_tips_auto_advance",
  "wait_tips_manual_nav",
  "wait_tips_pause",
  "wait_tips_dismiss",
  "wait_tips_suppress_short_wait",
  "wait_tips_replay",
  "capability_card_show",
  "capability_card_cta",
  "import_continue_stub",
  "import_fail_auth_shown",
  "import_fail_open_settings",
  "import_fail_open_recent",
  "home_stub_banner_click",
  "home_stub_banner_dismiss",
  "home_stub_banner_show",
  "preview_narrate_fail",
  "bench_resume_click",
  "shelf_scroll_into_view",
  "js_error",
  "template_selector_impression",
  "template_mode_changed",
  "template_manual_selected",
  "template_smart_result_shown",
  "template_fallback_shown",
  "template_create_submitted",
  "cover_opening_style_render",
  "cover_opening_style_assigned",
  "cover_opening_style_change",
  "cover_opening_style_selector_impression",
  "cover_joint_pick",
  // Import Wizard v3 + A.1
  "wizard_step_view",
  "preview_loaded",
  "advanced_drawer_open",
  "folder_picked",
  "import_mode_view",
  "import_mode_switch",
  "layout_density_change",
  "photo_count_hint_show",
  "advanced_fields_toggle",
  "close_confirm",
  // FTUE Optimization V1 · PRD §7
  "ftue_demo_album_click",
  "ftue_demo_album_success",
  "first_success_copy_branch",
  "refine_copy_branch",
  "ftue_reveal_folder",
  "longshot_success_share_hint_shown",
  "help_funnel_reveal_folder",
  // First-Session Trust V1 · PRD §7
  "import_ui_terminal_ms",
  "import_stage_stall",
  "longshot_progress_mode",
  "longshot_success_visible_ms",
  "longshot_reveal_auto_blocked",
  "share_surface_blocked",
  // Share-Face Closeout V1 · PRD §7
  "sfc_vision_warmup_shown",
  "sfc_stub_blanked",
  "sfc_title_fallback",
  "sfc_g1_suppressed_sparse",
  "sfc_stale_label_impression",
  // Share-Face Integrity V1 · D-SFI-01 / §7
  "stub_hits",
  "copy_refresh_shown",
  "copy_refresh_clicked",
  "copy_refresh_done",
  "copy_refresh_failed",
  "outlier_isolated",
  "export_renamed",
  "album_rerender_batch",
  // Dogfood UX Fixpack V1 · PRD §8
  "rename_propagation_migrated",
  "export_ok_toast_shown",
  "export_open_folder_clicked",
  "export_platform_mismatch",
  "mobile_gate_qr_error",
]);

const EVENT_RING_KEY = "travelogue.studio.eventRing";
const EVENT_RING_MAX = 200;

function devRingEnabled() {
  try {
    var h = location.hostname;
    if (h === "127.0.0.1" || h === "localhost" || h === "::1") return true;
    return new URLSearchParams(location.search).get("dev") === "1";
  } catch (e) {
    return false;
  }
}

function pushEventRing(event, meta) {
  if (!devRingEnabled()) return;
  try {
    var ring = JSON.parse(localStorage.getItem(EVENT_RING_KEY) || "[]");
    if (!Array.isArray(ring)) ring = [];
    ring.push({ t: Date.now(), event: event, meta: meta || {} });
    if (ring.length > EVENT_RING_MAX) ring = ring.slice(-EVENT_RING_MAX);
    localStorage.setItem(EVENT_RING_KEY, JSON.stringify(ring));
    if (typeof console !== "undefined" && console.debug) {
      console.debug("[studio]", event, meta || {});
    }
  } catch (e) { /* ignore */ }
}

export function trackStudioEvent(event, meta) {
  if (!ALLOWED.has(event)) return;
  pushEventRing(event, meta);
  try {
    fetch("/__travelogue/studio-event", {
      method: "POST",
      headers: studioAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ event: event, meta: meta || {} }),
      keepalive: true,
    }).catch(function () { /* ignore */ });
  } catch (e) { /* ignore */ }
}

const IMPORT_DRAFT_KEY = "travelogue.studio.importDraft";

/** PRD-P9-F1/F3 · session 内是否曾手动改过照片处理偏好。 */
export function readPhotoCullPrefSource() {
  try {
    var raw = sessionStorage.getItem(IMPORT_DRAFT_KEY);
    if (!raw) return "default";
    var draft = JSON.parse(raw);
    if (!draft) return "default";
    if (draft.photoKeepModeTouched || draft.photoCullTouched || draft.keepDupesTouched) {
      return "draft";
    }
    return "default";
  } catch (e) {
    return "default";
  }
}

/** PRD-P9-F1 · checkbox 变更或 import 完成时上报。 */
export function trackImportPhotoCullPref(meta) {
  meta = meta || {};
  trackStudioEvent("import_photo_cull_pref", {
    enabled: meta.enabled !== false,
    mode: meta.mode || "quick_share",
    photo_count: meta.photo_count != null ? meta.photo_count : null,
    layout_eligible_final: meta.layout_eligible_final != null
      ? meta.layout_eligible_final
      : null,
    cull_user_line_present: meta.cull_user_line_present != null
      ? !!meta.cull_user_line_present
      : null,
    pref_source: meta.pref_source === "draft" ? "draft" : "default",
    derived_from_mode: meta.derived_from_mode === true,
  });
}

/** PRD-P9-F2 · 保留连拍开关变更或 import 完成时上报。 */
export function trackImportKeepDupesPref(meta) {
  meta = meta || {};
  trackStudioEvent("import_keep_dupes_pref", {
    enabled: meta.enabled === true,
    mode: meta.mode || "quick_share",
    photo_count: meta.photo_count != null ? meta.photo_count : null,
    assets_written: meta.assets_written != null ? meta.assets_written : null,
    pref_source: meta.pref_source === "draft" ? "draft" : "default",
    derived_from_mode: meta.derived_from_mode === true,
  });
}

/** PRD-P9-F3 · 照片处理三选一变更或 import 完成时上报。 */
export function trackImportPhotoKeepMode(meta) {
  meta = meta || {};
  var keepMode = String(meta.photo_keep_mode || meta.mode_keep || "recommended").trim().toLowerCase();
  if (keepMode !== "keep_bursts" && keepMode !== "keep_all") keepMode = "recommended";
  trackStudioEvent("import_photo_keep_mode", {
    photo_keep_mode: keepMode,
    mode: meta.mode || "quick_share",
    photo_count: meta.photo_count != null ? meta.photo_count : null,
    pref_source: meta.pref_source === "draft" ? "draft" : "default",
  });
}
