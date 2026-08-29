/**
 * LIVE · Studio homepage-v2 entry (GET / after M21-c).
 * Loaded by: studio-home-v2.html. Closure root is hardcoded (BLK-RCL-09).
 * Filename v2 ≠ frozen. Not: templates/studio/legacy-freeze/.
 */
import { isDemoTrip } from "../js/constants.js";
import { trackStudioEvent } from "../js/analytics.js";
import { resolveBucketId } from "../js/bucket.js";
import {
  V2, $, show, persistVariant,
  readTripsCache, persistTripsCache,
} from "./store.js";
import { loadManifest } from "./manifest.js";
import { renderBentoEmpty } from "./bento.js";
import { initImportSheet } from "./import-entry.js";
import { resumeV2ImportIfAny } from "./import-run.js";
import { initViewportWatch } from "./unsupported.js";
import { initErrorPipeline } from "./error-pipeline.js";
import {
  harnessTripsOverride, harnessAssetsFail, harnessPreseedSession,
  harnessInstallFetchMocks, harnessInstallBentoPreviewMock,
  harnessInstallCurateMock,
  harnessApplyStartup, harnessEnabled, isDevQuery,
} from "./harness.js";
import { fetchTripsFirstPage } from "./trips-client.js";
import { clearBentoPreviewCache } from "./trip-preview.js";
import { initVariantGuard, syncVariantGuard } from "./variant-guard.js";
import { initThemeSettings } from "./theme.js";
import { initAdvancedOptionsPanel, syncAdvancedOptionsLock } from "./advanced-options.js";
import { initSettingsPanel } from "./settings-panel.js";
import { applyPreviewDeepLink } from "./bento-preview-deeplink.js";
import {
  configureHelpDrawer,
  createHelpOpenButton,
  maybeOpenHelpFromDeepLink,
} from "../js/help-drawer.js";
import { initLlmSettingsEntry } from "../js/llm-settings.js";
import { maybeShowCapabilityCard } from "../js/capability-card.js";
import { maybeShowHomeStubBanner, syncHomeStubBanner } from "../js/home-stub-banner.js";
import {
  ensureAiSurfaceHydrated,
  isAiSurfaceEnabled,
} from "../js/ai-surface.js";
import { syncAiSettingsZone } from "./settings-panel.js";

function initHelpEntry() {
  if (document.getElementById("studio-help-open-home")) return;
  var btn = createHelpOpenButton({
    id: "studio-help-open-home",
    className: "studio-help-open studio-help-open--ghost studio-help-open--home",
  });
  document.body.appendChild(btn);
  configureHelpDrawer({
    getOpenButton: function () {
      return document.getElementById("studio-help-open-home");
    },
  });
  maybeOpenHelpFromDeepLink();
}
function applyTripsData(data) {
  V2.trips = (data && data.trips) || [];
  V2.tripsTotal =
    data && typeof data.total === "number" ? data.total : V2.trips.length;
  V2.isOffline = false;
  persistTripsCache(V2.trips, V2.tripsTotal);
  return V2.trips;
}

function restoreTripsFromCache() {
  var cached = readTripsCache();
  if (!cached) {
    V2.trips = [];
    V2.tripsTotal = 0;
    return [];
  }
  V2.trips = cached.trips.slice();
  V2.tripsTotal = cached.total;
  return V2.trips;
}

function markTripsFetchFailed() {
  V2.isOffline = true;
  return restoreTripsFromCache();
}

function fetchTrips() {
  var override = harnessTripsOverride();
  if (override === "__ERROR__") {
    return Promise.resolve(markTripsFetchFailed());
  }

  return fetchTripsFirstPage()
    .then(function (data) {
      return applyTripsData(data);
    })
    .catch(function () {
      return markTripsFetchFailed();
    });
}

function hasUserTrips() {
  return V2.trips.some(function (t) {
    return !isDemoTrip(t);
  });
}

function trackHomepageView() {
  if (V2._viewTracked) return;
  V2._viewTracked = true;
  var stateMap = {
    IdleEmpty: "empty",
    IdleReturning: "returning",
    Importing: "importing",
    FirstSuccess: "first_success",
    Failed: "failed",
  };
  trackStudioEvent("homepage_view", {
    state: stateMap[V2.state] || V2.state,
    layout: V2.layout,
    variant: "v2",
  });
}

function finishRoute() {
  if (hasUserTrips()) {
    import("./shelf.js").then(function (m) {
      m.renderShelf(V2.trips, V2.tripsTotal);
      trackHomepageView();
    });
    return;
  }
  import("./shelf.js").then(function (m) {
    m.hideShelf();
    trackHomepageView();
  });
}

function routeFinalState() {
  if (V2.isOffline) show($("v2-offline"), true);
  else show($("v2-offline"), false);
  if (resumeV2ImportIfAny()) {
    V2.state = "Importing";
    syncVariantGuard();
    syncHomeStubBanner();
    trackHomepageView();
    return Promise.resolve();
  }
  V2.state = hasUserTrips() ? "IdleReturning" : "IdleEmpty";
  syncAdvancedOptionsLock();
  syncHomeStubBanner();
  renderBentoEmpty(V2.demoManifest);
  return import("./bento-preview-picker.js").then(function (picker) {
    picker.syncPreviewSelectOptions(V2.trips);
    return picker.applyStoredBentoPreviewPreference(V2.trips).finally(finishRoute);
  });
}

function initDeferredModules() {
  return Promise.all([
    import("./shelf.js"),
    import("./lightbox.js").then(function (m) { m.initLightbox(); }),
    import("./first-success.js").then(function (m) { m.initFirstSuccess(); }),
    import("./import-failed.js").then(function (m) { m.initImportFailed(); }),
    import("./dev-panel.js").then(function (m) { m.initDevPanel(); }),
  ]);
}

var _reroutePromise = null;

function rerouteFromTrips() {
  if (_reroutePromise) return _reroutePromise;
  _reroutePromise = fetchTrips().then(function () {
    var routed = routeFinalState();
    return routed || Promise.resolve();
  }).finally(function () {
    _reroutePromise = null;
  });
  return _reroutePromise;
}

function startApp() {
  clearBentoPreviewCache();
  show($("v2-loading"), true);
  initVariantGuard();
  initImportSheet();

  initDeferredModules().then(function () {
    V2.reroute = rerouteFromTrips;

    var manifestP = harnessAssetsFail() ? Promise.resolve(null) : loadManifest();
    Promise.all([manifestP, fetchTrips()]).then(function (results) {
      V2.demoManifest = results[0];
      V2.manifest = results[0];
      V2.manifestError = !results[0];
      if (harnessApplyStartup()) return;
      var routed = routeFinalState();
      var after = function () {
        maybeShowCapabilityCard();
        maybeShowHomeStubBanner({ delayMs: 900 });
      };
      if (routed && typeof routed.then === "function") {
        routed.then(after).catch(after);
      } else {
        after();
      }
    });
  });
}

function trackExperimentExposure() {
  resolveBucketId().then(function (bucketId) {
    var meta = { variant: "v2" };
    if (bucketId !== null && bucketId !== undefined) meta.bucket_id = bucketId;
    trackStudioEvent("experiment_exposure", meta);
  }).catch(function () {
    trackStudioEvent("experiment_exposure", { variant: "v2" });
  });
}

function init() {
  initErrorPipeline();
  initThemeSettings();
  initSettingsPanel();
  initAdvancedOptionsPanel();
  initHelpEntry();
  applyPreviewDeepLink();
  // NAS · 先水合门控，再决定是否挂 LLM 设置入口（防闪入）
  ensureAiSurfaceHydrated().then(function () {
    syncAiSettingsZone();
    if (isAiSurfaceEnabled()) {
      initLlmSettingsEntry();
    }
  });
  var layoutLab = $("v2-bench-layout-lab");
  if (layoutLab) layoutLab.hidden = !isDevQuery();
  if (harnessEnabled()) {
    harnessPreseedSession();
    harnessInstallBentoPreviewMock();
    harnessInstallCurateMock();
    harnessInstallFetchMocks();
  }
  persistVariant("v2");
  trackExperimentExposure();
  initViewportWatch(startApp);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
