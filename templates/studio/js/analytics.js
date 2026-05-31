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
]);

export function trackStudioEvent(event, meta) {
  if (!ALLOWED.has(event)) return;
  try {
    fetch("/__travelogue/studio-event", {
      method: "POST",
      headers: studioAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ event: event, meta: meta || {} }),
      keepalive: true,
    }).catch(function () { /* ignore */ });
  } catch (e) { /* ignore */ }
}
