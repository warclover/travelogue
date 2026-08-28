/**
 * 首页 v2 · Dev Harness（DEV-HARNESS.md §2/§3）。
 *
 * URL 参数强制态，供 Playwright 跑 AC 自动化与人工走查：
 *  - studioFixture=empty|single-stale|multi|multi-templates|delivered|demo-only|error  → mock GET /trips
 *  - bentoPreviewTrip=<tripId|demo|>                          → 预置预览画册 preference
 *  - bentoTabSession=mine|demo                                 → D-13 session Tab（迁移测试）
 *  - bentoTabSessionTrip=<tripId>                              → 配合 bentoTabSession=mine
 *  - preview=<tripId|demo|>                                   → 同 deep link（生产 URL）
 *  - bentoPreview404=<tripId|all|1>                          → mock bento-preview 404
 *  - studioCurate=succeed                                     → mock POST /curate + job 成功
 *  - studioAssetsFail=1                                       → manifest 失败（降级）
 *  - studioState=…                                            → 跳过正常 bootstrap 路由
 *  - studioJob=running|succeeded                              → mock GET /status + POST /import
 * dev 门控：仅 loopback + 服务端 data-studio-dev=1（LAN 上 ?dev=1 无效）。
 * 生产 build 不应打包（调用方负责 tree-shake）。
 */
import { SS, isDemoTrip } from "../js/constants.js";
import { isLoopback, V2, $, show, V2_BENTO_PREVIEW_TRIP_KEY, V2_BENTO_TAB_SESSION_KEY, V2_BENTO_PREVIEW_TRIP_SESSION_KEY } from "./store.js";
import { renderBentoEmpty } from "./bento.js";
import { renderShelf } from "./shelf.js";
import { renderImportingPanel } from "./import-run.js";
import { showFirstSuccess, captureImportShell } from "./first-success.js";
import { showImportFailed } from "./import-failed.js";
import { openImportSheet } from "./import-entry.js";

const HARNESS_JOB_ID = "harness-job-1";

function params() {
  try {
    return new URLSearchParams(window.location.search);
  } catch (e) {
    return new URLSearchParams("");
  }
}

export function harnessEnabled() {
  if (!isLoopback()) return false;
  try {
    var body = document.body;
    if (body && body.getAttribute("data-studio-dev") === "1") return true;
  } catch (e) { /* ignore */ }
  return params().get("dev") === "1";
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
    shelfCoverRelPath: opts.shelfCoverRelPath || opts.previewRelPath || null,
    previewUrl: opts.previewUrl || null,
    edition: opts.edition || "journal",
    hasLongshotExport: !!opts.hasLongshotExport,
    longshotStale: !!opts.longshotStale,
    algorithmStale: !!opts.algorithmStale,
    aestheticStale: !!opts.aestheticStale,
    cullStale: !!opts.cullStale,
    layoutStale: !!opts.layoutStale,
    previewStale: !!opts.previewStale,
    staleHints: opts.staleHints || (opts.algorithmStale ? ["选片配置已更新，请重新挑选（重新排版将自动重跑选片）"] : []),
    staleHint: opts.staleHint || (opts.algorithmStale ? "选片配置已更新，请重新挑选（重新排版将自动重跑选片）" : null),
    isDemo: !!opts.isDemo,
  };
}

const FIXTURES = {
  empty: { ok: true, trips: [], total: 0 },
  "single-stale": {
    ok: true,
    total: 1,
    trips: [trip("kyoto-rain", "京都 · 雨后", {
      hasLongshotExport: true,
      longshotStale: true,
      updatedAt: NOW - 3 * DAY,
    })],
  },
  "single-algorithm-stale": {
    ok: true,
    total: 1,
    trips: [trip("kyoto-rain", "京都 · 雨后", {
      algorithmStale: true,
      cullStale: true,
      layoutStale: true,
      updatedAt: NOW - 2 * DAY,
      previewRelPath: "preview.jpg",
    })],
  },
  multi: {
    ok: true,
    total: 5,
    trips: [
      trip("kyoto-rain", "京都 · 雨后", { updatedAt: NOW - DAY }),
      trip("hokkaido", "北海道 · 初雪", { longshotStale: true, updatedAt: NOW - 4 * DAY }),
      trip("lisbon", "里斯本 · 电车", { updatedAt: NOW - 9 * DAY }),
      trip("yunnan", "滇西 · 茶马", { updatedAt: NOW - 20 * DAY }),
      trip("demo-album", "斯里兰卡见闻录", { isDemo: true, updatedAt: NOW - 40 * DAY }),
    ],
  },
  "multi-templates": {
    ok: true,
    total: 2,
    trips: [
      Object.assign(trip("kyoto-rain", "京都 · 雨后", { updatedAt: NOW - DAY }), {
        templateSourceLabel: "智能匹配",
        resolvedTemplateId: "visual-journal",
        templateLocked: false,
      }),
      Object.assign(trip("hokkaido", "北海道 · 初雪", { updatedAt: NOW - 2 * DAY }), {
        templateSourceLabel: "手动指定",
        templateLocked: true,
      }),
    ],
  },
  delivered: {
    ok: true,
    total: 2,
    trips: [
      trip("kyoto-rain", "京都 · 雨后", {
        hasLongshotExport: true,
        updatedAt: NOW - DAY,
      }),
      trip("demo-album", "斯里兰卡见闻录", { isDemo: true, updatedAt: NOW - 40 * DAY }),
    ],
  },
  "demo-only": {
    ok: true,
    total: 1,
    trips: [trip("demo-album", "斯里兰卡见闻录", { isDemo: true })],
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
    stageHint: "正在分析你指定的照片",
  },
  succeeded: {
    status: "succeeded",
    result: {
      tripId: "harness-trip",
      title: "Harness · 测试",
      previewUrl: "/harness-trip/index.html",
      photoCount: 12,
      layoutEligibleCount: 12,
      photoCullEnabled: true,
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

/** 在 bootstrap 最早阶段写入 sessionStorage（importing-resume 等）与 D-14 preference。 */
export function harnessPreseedSession() {
  if (!harnessEnabled()) return;
  var previewTrip = params().get("bentoPreviewTrip");
  if (previewTrip !== null) {
    try {
      if (previewTrip === "" || previewTrip === "demo") {
        localStorage.removeItem(V2_BENTO_PREVIEW_TRIP_KEY);
      } else {
        localStorage.setItem(V2_BENTO_PREVIEW_TRIP_KEY, previewTrip);
      }
    } catch (e) { /* ignore */ }
  }
  var sessionTab = params().get("bentoTabSession");
  if (sessionTab === "mine" || sessionTab === "demo") {
    try {
      if (sessionTab === "mine") {
        sessionStorage.setItem(V2_BENTO_TAB_SESSION_KEY, "mine");
        var sessionTrip = params().get("bentoTabSessionTrip");
        if (sessionTrip) {
          sessionStorage.setItem(V2_BENTO_PREVIEW_TRIP_SESSION_KEY, sessionTrip);
        }
      } else {
        sessionStorage.removeItem(V2_BENTO_TAB_SESSION_KEY);
      }
    } catch (e) { /* ignore */ }
  }
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

const HARNESS_CURATE_JOB_ID = "harness-curate-1";

function bentoPreviewShould404(tripId) {
  var rule = params().get("bentoPreview404");
  if (!rule) return false;
  if (rule === "1" || rule === "all") return true;
  return rule.split(",").some(function (part) {
    return part.trim() === tripId;
  });
}

function trackBentoPreviewFetch(tripId) {
  try {
    window.__v2BentoPreviewFetches = window.__v2BentoPreviewFetches || {};
    window.__v2BentoPreviewFetches[tripId] = (window.__v2BentoPreviewFetches[tripId] || 0) + 1;
  } catch (e) { /* ignore */ }
}

/** Mock bento-preview / curate / status（AC-D14-05/08）。 */
export function harnessInstallBentoPreviewMock() {
  if (!harnessEnabled()) return;
  if (window.__v2BentoPreviewMock) return;
  window.__v2BentoPreviewMock = true;
  var orig = window.fetch;
  window.fetch = function (url, opts) {
    var href = typeof url === "string" ? url : (url && url.url) || "";
    var method = ((opts && opts.method) || (url && url.method) || "GET").toUpperCase();

    if (params().get("studioCurate") === "succeed") {
      if (href.indexOf("/trips/") >= 0 && href.indexOf("/curate") >= 0 && method === "POST") {
        try { window.__v2CurateMockPost = true; } catch (e) { /* ignore */ }
        return Promise.resolve(new Response(JSON.stringify({ jobId: HARNESS_CURATE_JOB_ID }), {
          status: 202,
          headers: { "Content-Type": "application/json" },
        }));
      }
      if (href.indexOf("/__travelogue/status") >= 0) {
        try { window.__v2CurateStatusPoll = true; } catch (e) { /* ignore */ }
        return Promise.resolve(new Response(JSON.stringify({
          jobId: HARNESS_CURATE_JOB_ID,
          status: "succeeded",
          stage: "curate",
          stageHint: "排版完成",
        }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }));
      }
    }

    if (href.indexOf("/bento-preview") >= 0) {
      // 无 studioFixture 时走真实 /trips/{id}/bento-preview（本地 dogfood）
      if (!params().get("studioFixture")) {
        return orig.apply(this, arguments);
      }
      var parts = href.split("/trips/");
      var tripId = parts[1] ? decodeURIComponent(parts[1].split("/")[0]) : "harness-trip";
      trackBentoPreviewFetch(tripId);
      if (bentoPreviewShould404(tripId)) {
        return Promise.resolve(new Response(JSON.stringify({
          ok: false,
          error: "E_BENTO_PREVIEW_UNAVAILABLE",
        }), {
          status: 404,
          headers: { "Content-Type": "application/json" },
        }));
      }
      var body = {
        ok: true,
        version: "1",
        source: "user",
        tripId: tripId,
        title: "Harness · " + tripId,
        previewUrl: "/" + tripId + "/index.html",
        meta: { photoCount: 12, chapterCount: 3 },
        assets: {
          background: "/" + tripId + "/preview.jpg",
          longshot: "/" + tripId + "/preview.jpg",
        },
        pages: [
          { id: "cover", role: "cover", label: "封面", url: "/" + tripId + "/preview.jpg" },
          { id: "ch01", role: "chapter", label: "第1章", chapterIndex: 1, url: "/" + tripId + "/scroll/ch01.webp" },
          { id: "ch02", role: "chapter", label: "第2章", chapterIndex: 2, url: "/" + tripId + "/scroll/ch02.webp" },
          { id: "ch03", role: "chapter", label: "第3章", chapterIndex: 3, url: "/" + tripId + "/scroll/ch03.webp" },
          { id: "epilogue", role: "epilogue", label: "尾声", url: "/" + tripId + "/scroll/epilogue.webp" },
        ],
      };
      return Promise.resolve(new Response(JSON.stringify(body), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }));
    }
    return orig.apply(this, arguments);
  };
}

/** @deprecated 合并至 harnessInstallBentoPreviewMock */
export function harnessInstallCurateMock() {}

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
      try {
        window.__v2HarnessImportBodies = window.__v2HarnessImportBodies || [];
        if (opts && opts.body instanceof FormData) {
          var fields = {};
          opts.body.forEach(function (value, key) {
            if (key === "files[]") return;
            fields[key] = value;
          });
          window.__v2HarnessImportBodies.push({ kind: "multipart", fields: fields });
        } else if (opts && typeof opts.body === "string") {
          window.__v2HarnessImportBodies.push({
            kind: "json",
            fields: JSON.parse(opts.body),
          });
        }
      } catch (e) { /* ignore */ }
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
      renderBentoEmpty(V2.manifest);
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
      renderBentoEmpty(V2.manifest);
      renderShelf(V2.trips, V2.tripsTotal);
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
      // 兼容旧 harness 名；打开 Wizard（Sheet 已退役）
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
