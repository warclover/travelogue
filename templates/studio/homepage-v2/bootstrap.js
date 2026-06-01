/**
 * 首页 v2 · DOMContentLoaded 入口（GET /v2）。
 *
 * 职责（M20-a）：
 *  - variant 标记（加法持久化）+ dev-only「经典首页 → /」链（仅 loopback）
 *  - 视口闸：窄视口走 Unsupported 壳层（完整 M20-f）
 *  - 并行加载 manifest + trips；按 §4.4 时序在最终态首帧前仅显示 skeleton
 *  - 路由 Loading → IdleEmpty(Bento) / IdleReturning(书架占位) / Importing(占位)
 *
 * 复用 v3 共享模块：constants.js（SS/isDemoTrip）。Import Sheet 接入 import-flow.js
 * 在 M20-d；Importing 续 poll 在 M20-g。
 */
import { isDemoTrip } from "../js/constants.js";
import { trackStudioEvent } from "../js/analytics.js";
import {
  V2, $, show, persistVariant,
} from "./store.js";
import { loadManifest } from "./manifest.js";
import { renderBentoEmpty } from "./bento.js";
import { initImportSheet } from "./import-sheet.js";
import { resumeV2ImportIfAny } from "./import-run.js";
import { initLightbox } from "./lightbox.js";
import { renderShelf } from "./shelf.js";
import { initViewportWatch } from "./unsupported.js";
import { initErrorPipeline } from "./error-pipeline.js";
import {
  harnessTripsOverride, harnessAssetsFail, harnessPreseedSession,
  harnessInstallFetchMocks, harnessApplyStartup,
} from "./harness.js";
import { fetchTripsFirstPage } from "./trips-client.js";
import { initFirstSuccess } from "./first-success.js";
import { initImportFailed } from "./import-failed.js";
import { resolveBucketId } from "./bucket.js";
import { initVariantGuard, syncVariantGuard } from "./variant-guard.js";
import { initDevPanel } from "./dev-panel.js";

function wireTopbar() {
  initVariantGuard();
  var addr = $("v2-copy-addr");
  if (addr) {
    var copy = function () {
      var text = "127.0.0.1:8766";
      var done = function () {
        if (typeof studioToast === "function") {
          studioToast("已复制本地地址", { duration: 1800 });
        }
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () {});
      }
    };
    addr.addEventListener("click", copy);
    addr.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        copy();
      }
    });
  }
}

function applyTripsData(data) {
  V2.trips = (data && data.trips) || [];
  V2.tripsTotal =
    data && typeof data.total === "number" ? data.total : V2.trips.length;
  V2.isOffline = false;
  return V2.trips;
}

function fetchTrips() {
  // dev harness：studioFixture 直接 mock /trips（DEV-HARNESS §3）
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

// §4.4：homepage_view 仅在最终态首帧触发一次。
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

function routeFinalState() {
  if (V2.isOffline) show($("v2-offline"), true);
  else show($("v2-offline"), false);
  // §4.4：activeJobId 存在 → 直接 Importing 续 poll，不闪 Idle。
  if (resumeV2ImportIfAny()) {
    V2.state = "Importing";
    syncVariantGuard();
    trackHomepageView();
    return;
  }
  if (hasUserTrips()) {
    V2.state = "IdleReturning";
    renderShelf(V2.trips, V2.tripsTotal);
    trackHomepageView();
    return;
  }
  V2.state = "IdleEmpty";
  show($("v2-shelf"), false);
  show($("v2-topbar"), true); // 书架隐藏后恢复 Bento topbar
  renderBentoEmpty(V2.manifest);
  trackHomepageView();
}

// 首次进入支持态（wide / iPad 横屏）才加载数据并路由（一次性）。
function startApp() {
  show($("v2-loading"), true);
  wireTopbar();
  initImportSheet();
  initLightbox();
  initFirstSuccess();
  initImportFailed();
  initDevPanel();

  // import 结束 / 取消后重新拉 trips 并路由（import-run 通过此钩子回调）。
  V2.reroute = function () {
    fetchTrips().then(function () { routeFinalState(); });
  };

  // §4.4：trips resolve 前仅 skeleton；resolve 后一次性进入最终态。
  // dev harness studioAssetsFail=1 → manifest 强制降级（AC-HP2-22）。
  var manifestP = harnessAssetsFail() ? Promise.resolve(null) : loadManifest();
  Promise.all([manifestP, fetchTrips()]).then(function (results) {
    V2.manifest = results[0];
    V2.manifestError = !results[0];
    if (harnessApplyStartup()) return;
    routeFinalState();
  });
}

function init() {
  initErrorPipeline(); // 最早接错误管道（§17.2 JS error rate）
  harnessPreseedSession();
  harnessInstallFetchMocks();
  persistVariant("v2");
  resolveBucketId().then(function (bucketId) {
    trackStudioEvent("experiment_exposure", { variant: "v2", bucket_id: bucketId });
  }).catch(function () {
    trackStudioEvent("experiment_exposure", { variant: "v2" });
  });
  // 视口闸（§10）：不支持 → Unsupported 壳层；支持 → startApp（一次性）。
  // resize / orientationchange 动态重判。
  initViewportWatch(startApp);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
