/**
 * 首页 v2 · Bento 预览来源（D-14 · 预览画册 select）。
 */
import { trackStudioEvent } from "../js/analytics.js";
import {
  V2,
  $,
  show,
  syncDerivedBentoTab,
  persistBentoPreviewTripId,
  clearBentoPreviewTripId,
} from "./store.js";
import { renderBentoSurface } from "./bento.js";
import { syncPreviewSelectValue } from "./bento-preview-picker.js";
import {
  persistSessionBentoTab,
  persistSessionLegacyPreviewTripId,
} from "./bento-preview-migrate.js";

function toast(msg, opts) {
  if (typeof studioToast === "function") studioToast(msg, opts);
}

function trackBentoTabSwitch(prevTab, opts) {
  if (opts && opts.silent) return;
  if (V2.bentoTab === prevTab) return;
  trackStudioEvent("bento_tab_switch", {
    tab: V2.bentoTab,
    trip_id: V2.bentoPreviewTripId,
  });
}

function syncSessionPreviewState() {
  if (V2.bentoPreviewTripId) {
    persistSessionBentoTab("mine");
    persistSessionLegacyPreviewTripId(V2.bentoPreviewTripId);
  } else {
    persistSessionBentoTab("demo");
    persistSessionLegacyPreviewTripId(null);
  }
}

/** 同步 demo-flag 与预览不可用提示。 */
export function syncPreviewUi() {
  syncDerivedBentoTab();
  var isDemo = !V2.bentoPreviewTripId;
  document.querySelectorAll("[data-demo-flag]").forEach(function (el) {
    show(el, isDemo);
  });
  var sampleFlag = $("v2-bench-sample-flag");
  if (sampleFlag) show(sampleFlag, isDemo);

  var userFlag = $("v2-carousel-user-flag");
  if (userFlag) {
    if (isDemo) {
      show(userFlag, false);
    } else {
      var trip = V2.userPreviewTrip;
      var name = (trip && (trip.title || trip.tripId)) || "我的画册";
      userFlag.textContent = "我的画册 · " + name;
      show(userFlag, true);
    }
  }

  var unavailable = $("v2-preview-unavailable");
  var openLink = $("v2-preview-unavailable-open");
  var showUnavailable = !!V2.bentoPreviewTripId && !V2.userManifest;
  show(unavailable, showUnavailable);
  if (openLink && V2.userPreviewTrip) {
    var href = V2.userPreviewTrip.previewUrl
      || ("/" + V2.userPreviewTrip.tripId + "/index.html");
    openLink.href = href;
  }
}

export { syncPreviewUi as syncTabUi };

export function activeBentoManifest() {
  if (V2.bentoPreviewTripId && V2.userManifest) return V2.userManifest;
  return V2.demoManifest;
}

/**
 * @param {string|null} tripId null = 示例作品
 * @param {{ silent?: boolean, force?: boolean, skipPersist?: boolean }} [opts]
 */
export function setBentoPreviewTripId(tripId, opts) {
  opts = opts || {};
  var nextId = tripId || null;
  var prevTab = V2.bentoTab;
  if (V2.bentoPreviewTripId === nextId && !opts.force) {
    syncPreviewUi();
    syncPreviewSelectValue();
    return import("./bento-stale.js").then(function (stale) {
      stale.syncBentoStaleBar();
      return V2.userManifest;
    });
  }

  V2.bentoPreviewTripId = nextId;
  if (!opts.skipPersist) persistBentoPreviewTripId(nextId);
  syncDerivedBentoTab();
  syncSessionPreviewState();
  trackBentoTabSwitch(prevTab, opts);

  if (!nextId) {
    V2.userManifest = null;
    V2.userPreviewTrip = null;
    V2.manifest = V2.demoManifest;
    syncPreviewUi();
    syncPreviewSelectValue();
    renderBentoSurface(V2.manifest);
    return import("./bento-stale.js").then(function (stale) {
      stale.syncBentoStaleBar();
      if (!opts.silent) {
        trackStudioEvent("bento_preview_select", {
          trip_id: null,
          source: opts.source || "select",
        });
      }
      return null;
    });
  }

  return refreshBentoUserPreview(V2.trips, {
    tripId: nextId,
    force: !!opts.force,
    silent: !!opts.silent,
  }).then(function (manifest) {
    if (!opts.silent) {
      trackStudioEvent("bento_preview_select", {
        trip_id: nextId,
        source: opts.source || "select",
      });
    }
    return manifest;
  });
}

/** trips 加载后按 preference 或指定 tripId 拉取 bento-preview（单本，无回退链）。 */
export function refreshBentoUserPreview(trips, opts) {
  opts = opts || {};
  if (opts.force) {
    try { window.__v2BentoPreviewForceFetch = true; } catch (e) { /* ignore */ }
  }
  return import("./trip-preview.js").then(function (mod) {
    var tripId = opts.tripId != null ? opts.tripId : V2.bentoPreviewTripId;
    if (!tripId) {
      V2.userManifest = null;
      V2.userPreviewTrip = null;
      V2.manifest = V2.demoManifest;
      syncPreviewUi();
      syncPreviewSelectValue();
      return import("./bento-stale.js").then(function (stale) {
        stale.syncBentoStaleBar();
        return null;
      });
    }

    return mod.ensureTripInCatalog(tripId).then(function (trip) {
      if (!trip) {
        if (V2.isOffline && tripId) {
          trip = { tripId: tripId };
        } else {
          clearBentoPreviewTripId();
          V2.bentoPreviewTripId = null;
          V2.userManifest = null;
          V2.userPreviewTrip = null;
          V2.manifest = V2.demoManifest;
          syncDerivedBentoTab();
          syncSessionPreviewState();
          syncPreviewUi();
          syncPreviewSelectValue();
          toast("原预览画册已不可用，已切回示例", { duration: 2800 });
          renderBentoSurface(V2.manifest);
          return import("./bento-stale.js").then(function (stale) {
            stale.syncBentoStaleBar();
            return null;
          });
        }
      }

      return mod.loadTripBentoPreview(trip.tripId, {
        updatedAt: trip.updatedAt,
        force: !!opts.force,
      }).then(function (manifest) {
        if (V2.bentoPreviewTripId !== trip.tripId) {
          return V2.userManifest;
        }
        V2.userPreviewTrip = trip;
        V2.userManifest = manifest || null;
        if (manifest) manifest.tripId = manifest.tripId || trip.tripId;
        V2.manifest = activeBentoManifest();
        syncSessionPreviewState();
        syncPreviewUi();
        syncPreviewSelectValue();
        renderBentoSurface(V2.manifest);
        return import("./bento-stale.js").then(function (stale) {
          stale.syncBentoStaleBar();
          return V2.userManifest;
        });
      });
    });
  });
}

/** @deprecated 别名 · stale / bootstrap */
export function refreshUserBentoPreview(trips, opts) {
  return refreshBentoUserPreview(trips, opts);
}

/** @deprecated picker 接管 init */
export function initBentoTabs() {}
