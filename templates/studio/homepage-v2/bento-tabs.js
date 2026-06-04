/**
 * 首页 v2 · Bento 预览 Tab（示例作品 / 最近一本 · 方案 B′）。
 */
import { trackStudioEvent } from "../js/analytics.js";
import { V2, $, show } from "./store.js";
import { renderBentoSurface } from "./bento.js";
import { fetchTripsFirstPage } from "./trips-client.js";

var _wired = false;
var _userTabInteracted = false;

function syncTabUi() {
  var demoBtn = $("v2-tab-demo");
  var mineBtn = $("v2-tab-mine");
  var tab = V2.bentoTab || "demo";
  if (demoBtn) {
    demoBtn.classList.toggle("is-active", tab === "demo");
    demoBtn.setAttribute("aria-selected", tab === "demo" ? "true" : "false");
  }
  if (mineBtn) {
    mineBtn.classList.toggle("is-active", tab === "mine");
    mineBtn.setAttribute("aria-selected", tab === "mine" ? "true" : "false");
    mineBtn.disabled = !V2.userManifest;
  }

  document.querySelectorAll("[data-demo-flag]").forEach(function (el) {
    show(el, tab === "demo");
  });
}

export function activeBentoManifest() {
  if (V2.bentoTab === "mine" && V2.userManifest) return V2.userManifest;
  return V2.demoManifest;
}

export function setBentoTab(tab, opts) {
  opts = opts || {};
  if (tab === "mine" && !V2.userManifest) return;
  if (V2.bentoTab === tab && !opts.force) return;
  V2.bentoTab = tab;
  V2.manifest = activeBentoManifest();
  syncTabUi();
  renderBentoSurface(V2.manifest);
  if (!opts.silent) {
    trackStudioEvent("bento_tab_switch", {
      tab: tab,
      trip_id: tab === "mine" && V2.userManifest ? V2.userManifest.tripId : null,
    });
  }
}

export function initBentoTabs() {
  if (_wired) return;
  _wired = true;
  var demoBtn = $("v2-tab-demo");
  var mineBtn = $("v2-tab-mine");
  if (demoBtn) {
    demoBtn.addEventListener("click", function () {
      _userTabInteracted = true;
      setBentoTab("demo");
    });
  }
  if (mineBtn) {
    mineBtn.addEventListener("click", function () {
      _userTabInteracted = true;
      fetchTripsFirstPage()
        .then(function (data) {
          V2.trips = data.trips || [];
          V2.tripsTotal = typeof data.total === "number" ? data.total : V2.trips.length;
          V2.isOffline = false;
          return refreshUserBentoPreview(V2.trips);
        })
        .catch(function () {})
        .finally(function () {
          setBentoTab("mine", { force: true });
        });
    });
  }
}

/** trips 加载后拉取最近一本预览 manifest。 */
export function refreshUserBentoPreview(trips) {
  return import("./trip-preview.js").then(function (mod) {
    var primary = mod.pickBentoPreviewTrip(trips);
    if (!primary) {
      V2.userManifest = null;
      if (!_userTabInteracted || V2.bentoTab === "mine") {
        V2.bentoTab = "demo";
      }
      syncTabUi();
      return null;
    }

    var candidates = mod.pickRecentUserTrips(trips);
    var ordered = [primary].concat(
      candidates.filter(function (t) { return t.tripId !== primary.tripId; })
    );

    function tryAt(i) {
      if (i >= ordered.length) return Promise.resolve(null);
      var trip = ordered[i];
      return mod.loadTripBentoPreview(trip.tripId).then(function (manifest) {
        if (manifest) {
          manifest.tripId = manifest.tripId || trip.tripId;
          return manifest;
        }
        return tryAt(i + 1);
      });
    }

    return tryAt(0).then(function (manifest) {
      V2.userManifest = manifest || null;
      if (!_userTabInteracted) {
        V2.bentoTab = V2.userManifest ? "mine" : "demo";
      } else if (!V2.userManifest && V2.bentoTab === "mine") {
        V2.bentoTab = "demo";
      }
      V2.manifest = activeBentoManifest();
      syncTabUi();
      if (V2.manifest) {
        renderBentoSurface(V2.manifest);
      }
      return V2.userManifest;
    });
  });
}

export { syncTabUi };
