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

/** PRD-P9-F1 §6.7 · session 内是否曾手动改过智能挑选开关。 */
export function readPhotoCullPrefSource() {
  try {
    var raw = sessionStorage.getItem(IMPORT_DRAFT_KEY);
    if (!raw) return "default";
    var draft = JSON.parse(raw);
    return draft && draft.photoCullTouched ? "draft" : "default";
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
  });
}
