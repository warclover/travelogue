/**
 * 首页 v2 · Bento 主预览区算法过期提示条。
 */
import { trackStudioEvent } from "../js/analytics.js";
import { isDemoTrip } from "../js/constants.js";
import { V2, $, show, persistTripsCache } from "./store.js";
import { bentoStaleMessage, shouldShowBentoStaleBar } from "./shelf-actions-logic.js";
import { runTripCurateJob } from "./curate-client.js";
import { clearBentoPreviewCache, resolvePreviewTrip } from "./trip-preview.js";
import { fetchTripsFirstPage } from "./trips-client.js";

var _curateInFlight = false;
var _wired = false;

function toast(msg, opts) {
  if (typeof studioToast === "function") studioToast(msg, opts);
}

function activePreviewTrip() {
  if (!V2.bentoPreviewTripId) return null;
  var fresh = resolvePreviewTrip(V2.trips, V2.bentoPreviewTripId);
  if (fresh) {
    V2.userPreviewTrip = fresh;
    return fresh;
  }
  return V2.userPreviewTrip;
}

function patchTripFreshness(tripId) {
  function patch(row) {
    if (!row || row.tripId !== tripId) return;
    row.algorithmStale = false;
    row.aestheticStale = false;
    row.cullStale = false;
    row.layoutStale = false;
    row.previewStale = false;
    row.staleHint = null;
    row.staleHints = [];
  }
  (V2.trips || []).forEach(patch);
  patch(V2.userPreviewTrip);
  if (V2.pickerCatalogTrips) V2.pickerCatalogTrips.forEach(patch);
}

function reloadTripsList() {
  return fetchTripsFirstPage().then(function (data) {
    V2.trips = (data && data.trips) || [];
    V2.tripsTotal = typeof data.total === "number" ? data.total : V2.trips.length;
    V2.isOffline = false;
    persistTripsCache(V2.trips, V2.tripsTotal);
    return V2.trips;
  }).catch(function () {
    return V2.trips;
  });
}

function refreshAfterCurate(tripId) {
  clearBentoPreviewCache();
  try { window.__v2RefreshAfterCurate = true; } catch (e) { /* ignore */ }
  return reloadTripsList().then(function () {
    patchTripFreshness(tripId);
    return import("./bento-preview-picker.js").then(function (picker) {
      picker.syncPreviewSelectOptions(V2.trips);
      return import("./bento-tabs.js").then(function (tabs) {
        return tabs.refreshBentoUserPreview(V2.trips, { force: true, tripId: tripId });
      });
    });
  }).then(function () {
    return import("./shelf.js").then(function (shelf) {
      if (V2.trips.some(function (t) { return !isDemoTrip(t); })) {
        shelf.renderShelf(V2.trips, V2.tripsTotal);
      }
    });
  }).then(function () {
    return import("./bento.js").then(function (bench) {
      bench.renderBenchRecent();
      syncBentoStaleBar();
    });
  });
}

export function triggerHomepageRecurate(tripId, surface) {
  if (!tripId || _curateInFlight) return Promise.resolve(false);
  _curateInFlight = true;
  trackStudioEvent("homepage_recurate_start", { trip_id: tripId, surface: surface || "unknown" });
  var actionBtn = $("v2-bento-stale-action");
  if (actionBtn) actionBtn.disabled = true;
  return runTripCurateJob(tripId, {
    onProgress: function (hint) {
      toast(hint, { duration: 2200 });
    },
  }).then(function (job) {
    if (job && job.status === "succeeded") {
      trackStudioEvent("homepage_recurate_success", { trip_id: tripId, surface: surface || "unknown" });
      toast("排版已更新", { duration: 2600 });
      return refreshAfterCurate(tripId).then(function () { return true; });
    }
    trackStudioEvent("homepage_recurate_failed", { trip_id: tripId, surface: surface || "unknown" });
    toast("重新排版失败，请稍后重试", { duration: 3200, error: true });
    return false;
  }).catch(function () {
    trackStudioEvent("homepage_recurate_failed", { trip_id: tripId, surface: surface || "unknown" });
    toast("重新排版失败，请稍后重试", { duration: 3200, error: true });
    return false;
  }).finally(function () {
    _curateInFlight = false;
    if (actionBtn) actionBtn.disabled = false;
    syncBentoStaleBar();
  });
}

function wireStaleAction() {
  if (_wired) return;
  _wired = true;
  var btn = $("v2-bento-stale-action");
  if (!btn) return;
  btn.addEventListener("click", function () {
    var trip = activePreviewTrip();
    if (!trip) return;
    triggerHomepageRecurate(trip.tripId, "bento_bar");
  });
}

/** 同步 Bento 主预览区 stale 提示（仅「我的画册」Tab + algorithmStale）。 */
export function syncBentoStaleBar() {
  wireStaleAction();
  var host = $("v2-bento-stale");
  var textEl = $("v2-bento-stale-text");
  var actionBtn = $("v2-bento-stale-action");
  if (!host) return;

  var trip = activePreviewTrip();
  var visible = shouldShowBentoStaleBar(trip);
  show(host, visible);
  if (!visible) return;

  if (textEl) textEl.textContent = bentoStaleMessage(trip);
  if (actionBtn) {
    actionBtn.disabled = _curateInFlight;
    actionBtn.textContent = _curateInFlight ? "排版中…" : "重新排版";
  }
}
