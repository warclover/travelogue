/**
 * 首页 v2 · DOMContentLoaded 入口（GET /v2）。
 */
import { isDemoTrip } from "../js/constants.js";
import { trackStudioEvent } from "../js/analytics.js";
import { resolveBucketId } from "../js/bucket.js";
import {
  V2, $, show, persistVariant,
} from "./store.js";
import { loadManifest } from "./manifest.js";
import { renderBentoEmpty } from "./bento.js";
import { initImportSheet } from "./import-sheet.js";
import { resumeV2ImportIfAny } from "./import-run.js";
import { initViewportWatch } from "./unsupported.js";
import { initErrorPipeline } from "./error-pipeline.js";
import {
  harnessTripsOverride, harnessAssetsFail, harnessPreseedSession,
  harnessInstallFetchMocks, harnessInstallBentoPreviewMock,
  harnessApplyStartup, harnessEnabled,
} from "./harness.js";
import { fetchTripsFirstPage } from "./trips-client.js";
import { initVariantGuard, syncVariantGuard } from "./variant-guard.js";

function applyTripsData(data) {
  V2.trips = (data && data.trips) || [];
  V2.tripsTotal =
    data && typeof data.total === "number" ? data.total : V2.trips.length;
  V2.isOffline = false;
  return V2.trips;
}

function fetchTrips() {
  var override = harnessTripsOverride();
  if (override === "__ERROR__") {
    V2.isOffline = true;
    V2.trips = [];
    V2.tripsTotal = 0;
    return Promise.resolve([]);
  }

  return fetchTripsFirstPage()
    .then(function (data) {
      return applyTripsData(data);
    })
    .catch(function () {
      V2.isOffline = true;
      V2.trips = [];
      V2.tripsTotal = 0;
      return [];
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
    trackHomepageView();
    return;
  }
  V2.state = hasUserTrips() ? "IdleReturning" : "IdleEmpty";
  renderBentoEmpty(V2.demoManifest);
  import("./bento-tabs.js").then(function (tabs) {
    tabs.refreshUserBentoPreview(V2.trips).finally(finishRoute);
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
    routeFinalState();
  }).finally(function () {
    _reroutePromise = null;
  });
  return _reroutePromise;
}

function startApp() {
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
      routeFinalState();
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
  if (harnessEnabled()) {
    harnessPreseedSession();
    harnessInstallBentoPreviewMock();
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
