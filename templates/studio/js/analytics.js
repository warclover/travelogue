/**
 * Studio homepage funnel events (P9-P1-05) · fire-and-forget to local jsonl.
 */
import { studioAuthHeaders } from "./http.js";

const ALLOWED = new Set([
  "open_sheet",
  "pick_folder",
  "import_start",
  "import_success",
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
  "bento_tab_switch",
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
