/**
 * 首页 v2 · Dev Harness（DEV-HARNESS.md §2/§3）。
 *
 * URL 参数强制态，供 Playwright 跑 AC 自动化与人工走查：
 *  - studioFixture=empty|single-stale|multi|demo-only|error  → mock GET /trips
 *  - studioAssetsFail=1                                       → manifest 失败（降级）
 *  - studioState=…                                            → 跳过正常 bootstrap 路由
 *  - studioJob=running|succeeded                              → mock GET /status + POST /import
 * dev 门控：仅 127.0.0.1 / ?dev=1（与 feature flag dev override 一致）。
 * 生产 build 不应打包（调用方负责 tree-shake）。
 */
import { SS, isDemoTrip } from "../js/constants.js";
import { isLoopback, V2, $, show } from "./store.js";
import { renderBentoEmpty } from "./bento.js";
import { renderShelf } from "./shelf.js";
import { renderImportingPanel } from "./import-run.js";
import { showFirstSuccess, captureImportShell } from "./first-success.js";
import { showImportFailed } from "./import-failed.js";
import { openImportSheet } from "./import-sheet.js";

const HARNESS_JOB_ID = "harness-job-1";

function params() {
  try {
    return new URLSearchParams(window.location.search);
  } catch (e) {
    return new URLSearchParams("");
  }
}

export function harnessEnabled() {
  return isLoopback() || params().get("dev") === "1";
}

const NOW = Math.floor(Date.now() / 1000);
const DAY = 86400;

function trip(id, title, opts) {
  opts = opts || {};
  return {
    tripId: id,
    title: title,
    photoCount: opts.photoCount || 24,
    updatedAt: opts.updatedAt || NOW - DAY,
    previewRelPath: opts.previewRelPath || null,
    previewUrl: opts.previewUrl || null,
    longshotStale: !!opts.longshotStale,
    isDemo: !!opts.isDemo,
  };
}

const FIXTURES = {
  empty: { ok: true, trips: [], total: 0 },
  "single-stale": {
    ok: true,
    total: 1,
    trips: [trip("kyoto-rain", "京都 · 雨后", { longshotStale: true, updatedAt: NOW - 3 * DAY })],
  },
  multi: {
    ok: true,
    total: 5,
    trips: [
      trip("kyoto-rain", "京都 · 雨后", { updatedAt: NOW - DAY }),
      trip("hokkaido", "北海道 · 初雪", { longshotStale: true, updatedAt: NOW - 4 * DAY }),
      trip("lisbon", "里斯本 · 电车", { updatedAt: NOW - 9 * DAY }),
      trip("yunnan", "滇西 · 茶马", { updatedAt: NOW - 20 * DAY }),
      trip("demo-album", "示例 · 旅途", { isDemo: true, updatedAt: NOW - 40 * DAY }),
    ],
  },
  "demo-only": {
    ok: true,
    total: 1,
    trips: [trip("demo-album", "示例 · 旅途", { isDemo: true })],
  },
  many: {
    ok: true,
    total: 25,
    trips: (function () {
      var rows = [];
      for (var i = 0; i < 25; i++) {
        rows.push(trip(
          "shelf-trip-" + String(i + 1).padStart(2, "0"),
          "画册 · " + (i + 1),
          { updatedAt: NOW - i * 3600, photoCount: 12 + (i % 5) }
        ));
      }
      return rows;
    })(),
  },
  error: "__ERROR__",
};

const JOB_FIXTURES = {
  running: {
    status: "running",
    stageIndex: 1,
    stageCount: 4,
    stage: "ingest",
    stageHint: "正在读取你的照片",
  },
  succeeded: {
    status: "succeeded",
    result: {
      tripId: "harness-trip",
      title: "Harness · 测试",
      previewUrl: "/harness-trip/index.html",
      photoCount: 12,
      segmentCount: 2,
    },
  },
};

/** @returns {object|"__ERROR__"|null} fixture 数据；null 表示走真实 fetch。 */
export function harnessTripsOverride() {
  if (!harnessEnabled()) return null;
  var name = params().get("studioFixture");
  if (!name) return null;
  return Object.prototype.hasOwnProperty.call(FIXTURES, name) ? FIXTURES[name] : null;
}

/**
 * 分页 mock（含 many · 25 本）；无 fixture 时返回 null。
 * @returns {Promise<{ok:boolean,trips:object[],total:number}>|null}
 */
export function harnessTripsPageResponse(limit, offset) {
  if (!harnessEnabled()) return null;
  var name = params().get("studioFixture");
  if (!name) return null;
  var fix = FIXTURES[name];
  if (!fix || fix === "__ERROR__") return null;
  var total = typeof fix.total === "number" ? fix.total : fix.trips.length;
  var trips = fix.trips.slice(offset, offset + limit);
  return Promise.resolve({ ok: true, trips: trips, total: total });
}

export function harnessAssetsFail() {
  return harnessEnabled() && params().get("studioAssetsFail") === "1";
}

export function harnessSlowNet() {
  return harnessEnabled() && params().get("studioSlowNet") === "1";
}

export function harnessStateName() {
  if (!harnessEnabled()) return null;
  return params().get("studioState");
}

export function harnessJobName() {
  if (!harnessEnabled()) return null;
  return params().get("studioJob");
}

/** 在 bootstrap 最早阶段写入 sessionStorage（importing-resume 等）。 */
export function harnessPreseedSession() {
  if (!harnessEnabled()) return;
  var state = harnessStateName();
  if (state === "importing-resume") {
    try {
      sessionStorage.setItem(SS.activeJobId, HARNESS_JOB_ID);
      sessionStorage.setItem(SS.activePending, JSON.stringify({
        albumPath: "/harness/album",
        title: "Harness",
      }));
    } catch (e) { /* ignore */ }
  }
}

function jobFixturePayload() {
  var name = harnessJobName();
  if (!name || !Object.prototype.hasOwnProperty.call(JOB_FIXTURES, name)) {
    return JOB_FIXTURES.running;
  }
  return JOB_FIXTURES[name];
}

/** Mock import/status/cancel，供 AC-15/16 等无需真实 pipeline。 */
export function harnessInstallFetchMocks() {
  if (!harnessEnabled() || !harnessJobName()) return;
  var orig = window.fetch;
  window.fetch = function (url, opts) {
    var href = typeof url === "string" ? url : (url && url.url) || "";
    if (href.indexOf("/__travelogue/status") >= 0) {
      var body = Object.assign({ jobId: HARNESS_JOB_ID }, jobFixturePayload());
      return Promise.resolve(new Response(JSON.stringify(body), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }));
    }
    if (href.indexOf("/__travelogue/import") >= 0 && (!opts || opts.method === "POST")) {
      return Promise.resolve(new Response(JSON.stringify({ jobId: HARNESS_JOB_ID }), {
        status: 202,
        headers: { "Content-Type": "application/json" },
      }));
    }
    if (href.indexOf("/__travelogue/cancel") >= 0 && (!opts || opts.method === "POST")) {
      return Promise.resolve(new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }));
    }
    return orig.apply(this, arguments);
  };
}

function trackHarnessView(state) {
  if (V2._viewTracked) return;
  V2._viewTracked = true;
  import("../js/analytics.js").then(function (mod) {
    mod.trackStudioEvent("homepage_view", {
      state: state,
      layout: V2.layout,
      variant: "v2",
      harness: true,
    });
  }).catch(function () { /* ignore */ });
}

/**
 * 强制态路由（studioState）。返回 true 表示已处理，跳过 routeFinalState。
 */
export function harnessApplyStartup() {
  if (!harnessEnabled()) return false;
  var state = harnessStateName();
  if (!state) return false;

  show($("v2-loading"), false);
  show($("v2-offline"), state === "offline");

  switch (state) {
    case "loading":
      show($("v2-loading"), true);
      V2.state = "Loading";
      return true;
    case "idle-empty":
      V2.state = "IdleEmpty";
      renderBentoEmpty(V2.manifest);
      trackHarnessView("empty");
      return true;
    case "idle-returning":
      V2.state = "IdleReturning";
      renderShelf(V2.trips, V2.tripsTotal);
      trackHarnessView("returning");
      return true;
    case "importing":
      captureImportShell();
      renderImportingPanel("harness");
      trackHarnessView("importing");
      return true;
    case "importing-cold":
      V2.importShell = "bento";
      renderImportingPanel("harness");
      trackHarnessView("importing");
      return true;
    case "importing-resume":
      harnessPreseedSession();
      return false; // 走 resumeV2ImportIfAny
    case "first-success": {
      var hasUser = V2.trips.some(function (t) { return !isDemoTrip(t); });
      if (hasUser) {
        V2.importShell = "shelf";
        renderShelf(V2.trips, V2.tripsTotal);
      } else {
        V2.importShell = "bento";
        renderBentoEmpty(V2.manifest);
      }
      showFirstSuccess({
        result: {
          tripId: "harness-trip",
          title: "京都 · 雨后",
          previewUrl: "/harness-trip/index.html",
          photoCount: 24,
          segmentCount: 3,
        },
      });
      trackHarnessView("FirstSuccess");
      return true;
    }
    case "sheet-open":
      V2.state = "IdleEmpty";
      renderBentoEmpty(V2.manifest);
      openImportSheet();
      trackHarnessView("empty");
      return true;
    case "offline":
      V2.isOffline = true;
      V2.state = "IdleEmpty";
      renderBentoEmpty(V2.manifest);
      trackHarnessView("empty");
      return true;
    case "failed":
      captureImportShell();
      renderBentoEmpty(V2.manifest);
      showImportFailed({
        code: "E_STUDIO_PIPELINE",
        message: "Harness · 模拟导入失败",
      });
      trackHarnessView("failed");
      return true;
    default:
      return false;
  }
}
