/**
 * 首页 v2 · 导入编排（M20-d）。
 *
 * 复用 v3 共享原语，不复制 v3 视图控制器：
 *  - http.js     postJson / withJobBusyRetry / isJobBusyResponse
 *  - job-poll.js pollJobUntilDone
 *  - constants.js SS / STAGE_LABELS / STUDIO_ERROR_MESSAGES / IMPORT_PHOTO_CAP
 *
 * sessionStorage 写入形状与 v3 完全一致（activeJobId / activePending），
 * 保证跨页 import 续跑（v3 ↔ v2）。Importing UI 为 M20-d 基础版，
 * 冷启动静帧 + 四阶段精修在 M20-g。
 */
import {
  SS, STAGE_LABELS, STUDIO_ERROR_MESSAGES,
} from "../js/constants.js";
import { postJson, withJobBusyRetry, isJobBusyResponse } from "../js/http.js";
import { pollJobUntilDone } from "../js/job-poll.js";
import { trackStudioEvent } from "../js/analytics.js";
import { V2, $, show } from "./store.js";
import { renderColdStartBackground } from "./bento.js";
import {
  captureImportShell, showFirstSuccess,
} from "./first-success.js";
import { showImportFailed } from "./import-failed.js";
import { syncVariantGuard } from "./variant-guard.js";

let _gen = 0;
let _activeJobId = null;

function humanizeError(code, fallback) {
  return STUDIO_ERROR_MESSAGES[code] || fallback || "导入失败，请重试";
}

function basenameTitle(path) {
  if (!path) return "我的旅途";
  var parts = String(path).replace(/[\\/]+$/, "").split(/[\\/]/);
  var name = parts[parts.length - 1] || "我的旅途";
  return name.slice(0, 20);
}

export function buildImportPayload(albumPath, title) {
  return {
    albumPath: albumPath,
    title: (title || basenameTitle(albumPath)).slice(0, 20) || "我的旅途",
    place: "旅途",
    placeUserSet: false,
    force: false,
  };
}

function setStage(text, fillPct) {
  var stage = $("v2-import-stage");
  if (stage && text) stage.textContent = text;
  var fill = $("v2-import-fill");
  if (fill && typeof fillPct === "number") {
    fill.style.width = Math.max(0, Math.min(100, fillPct)) + "%";
  }
}

export function renderImportingPanel(source) {
  captureImportShell();
  var host = $("v2-importing");
  show($("v2-loading"), false);
  show($("v2-headline"), false);
  show($("v2-frame"), false);
  show($("v2-shelf"), false);
  // §9.2 冷启动：无 Import 前壳层背景时铺 demo 静帧（幂等，暖启动不覆盖）。
  renderColdStartBackground(V2.manifest);
  if (!host) return;
  host.replaceChildren();

  var panel = document.createElement("div");
  panel.className = "v2-import-panel";

  var sourceP = document.createElement("p");
  sourceP.className = "v2-import-panel__source";
  sourceP.textContent = "来源 · " + (source || "本机文件夹");
  panel.appendChild(sourceP);

  var title = document.createElement("h2");
  title.className = "v2-import-panel__title";
  title.textContent = "正在生成你的游记画册…";
  panel.appendChild(title);

  var estimate = document.createElement("p");
  estimate.className = "v2-import-panel__estimate";
  estimate.textContent = "自动分章 · 配文 · 排版 · 可离开稍后回来";
  panel.appendChild(estimate);

  var bar = document.createElement("div");
  bar.className = "v2-import-panel__bar";
  var fill = document.createElement("div");
  fill.className = "v2-import-panel__bar-fill";
  fill.id = "v2-import-fill";
  bar.appendChild(fill);
  panel.appendChild(bar);

  var stage = document.createElement("p");
  stage.className = "v2-import-panel__stage";
  stage.id = "v2-import-stage";
  stage.textContent = "准备导入…";
  panel.appendChild(stage);

  var cancelBtn = document.createElement("button");
  cancelBtn.type = "button";
  cancelBtn.className = "v2-import-panel__cancel";
  cancelBtn.id = "v2-import-cancel";
  cancelBtn.textContent = "取消";
  panel.appendChild(cancelBtn);

  host.appendChild(panel);
  show(host, true);
  V2.state = "Importing";
  syncVariantGuard();
  cancelBtn.addEventListener("click", cancelImport);
}

function performCancelImport() {
  _gen += 1; // 使进行中的 poll 作废
  var jobId = _activeJobId;
  try {
    sessionStorage.removeItem(SS.activeJobId);
    sessionStorage.removeItem(SS.activePending);
  } catch (e) { /* ignore */ }
  _activeJobId = null;
  if (jobId) {
    postJson("/__travelogue/cancel", { jobId: jobId }).catch(function () {});
  }
  if (typeof studioToast === "function") {
    studioToast("已取消导入", { duration: 2000 });
  }
  syncVariantGuard();
  if (typeof V2.reroute === "function") V2.reroute();
}

export function cancelImport() {
  var doCancel = function () { performCancelImport(); };
  if (typeof studioModal === "function") {
    studioModal({
      title: "确定取消？",
      body: "取消后将丢失当前进度。",
      confirmText: "确定取消",
      cancelText: "继续等待",
      danger: true,
    }).then(function (confirmed) { if (confirmed) doCancel(); });
  } else if (window.confirm("确定取消导入？")) {
    doCancel();
  }
}

function pollImport(jobId, gen, source) {
  _activeJobId = jobId;
  try {
    sessionStorage.setItem(SS.activeJobId, jobId);
  } catch (e) { /* ignore */ }

  return pollJobUntilDone(jobId, {
    intervalMs: 500,
    shouldAbort: function () { return gen !== _gen; },
    onTick: function (job) {
      if (gen !== _gen) return;
      if (job.status === "running" || job.status === "queued") {
        var idx = job.stageIndex || 0;
        var count = job.stageCount || 4;
        var hint = job.stageHint || STAGE_LABELS[job.stage] || "处理中…";
        setStage(hint, count ? (idx / count) * 100 : 0);
      }
    },
  }).then(function (job) {
    if (gen !== _gen) return null;
    _activeJobId = null;
    try {
      sessionStorage.removeItem(SS.activeJobId);
      sessionStorage.removeItem(SS.activePending);
    } catch (e) { /* ignore */ }
    if (job.status === "succeeded") {
      setStage("完成", 100);
      var result = job.result || {};
      trackStudioEvent("import_success", { tripId: result.tripId || null });
      showFirstSuccess({ result: result });
      return job;
    }
    if (job.status === "cancelled") {
      if (typeof V2.reroute === "function") V2.reroute();
      return null;
    }
    var err = job.error || {};
    throw { code: err.code, message: humanizeError(err.code, err.message) };
  });
}

/**
 * 启动一次导入。返回 Promise；调用方（Sheet）负责捕获错误显示。
 * @param {{albumPath:string,title?:string,force?:boolean}} body
 * @param {{source?:string}} [opts]
 */
export function startV2Import(body, opts) {
  opts = opts || {};
  var gen = ++_gen;
  var source = opts.source || "本机文件夹";
  trackStudioEvent("import_start", { via: "path", surface: "v2_sheet" });
  try {
    sessionStorage.setItem(SS.activePending, JSON.stringify(body));
  } catch (e) { /* ignore */ }

  renderImportingPanel(source);

  return withJobBusyRetry(function () {
    return postJson("/__travelogue/import", body);
  }).then(function (res) {
    var data = res.body || {};
    if (res.status === 409 && data.error === "E_DEMO_EXISTS") {
      var confirmOverwrite = typeof studioModal === "function"
        ? studioModal({
            title: "该游记已存在",
            body: "是否覆盖已有内容？覆盖后无法撤销。",
            confirmText: "覆盖并重新导入",
            cancelText: "取消",
          })
        : Promise.resolve(window.confirm(data.message || "该游记已存在。是否覆盖？"));
      return confirmOverwrite.then(function (ok) {
        if (!ok) {
          if (typeof V2.reroute === "function") V2.reroute();
          return null;
        }
        var forced = Object.assign({}, body, { force: true });
        return startV2Import(forced, opts);
      });
    }
    if (isJobBusyResponse(res)) {
      throw { code: "E_STUDIO_JOB_BUSY", message: humanizeError("E_STUDIO_JOB_BUSY") };
    }
    if (res.status !== 202 || !data.jobId) {
      throw { code: data.error, message: humanizeError(data.error, data.message) };
    }
    return pollImport(data.jobId, gen, source);
  }).catch(function (err) {
    if (gen !== _gen) return; // 已被取消/新导入覆盖
    try { sessionStorage.removeItem(SS.activeJobId); } catch (e) { /* ignore */ }
    _activeJobId = null;
    showImportFailed(err);
    throw err;
  });
}

/**
 * 跨页恢复：若存在 activeJobId，渲染 Importing 并续 poll（不闪 Idle）。
 * 返回是否恢复了一次导入。
 */
export function resumeV2ImportIfAny() {
  var jobId = null;
  var pendingRaw = null;
  try {
    jobId = sessionStorage.getItem(SS.activeJobId);
    pendingRaw = sessionStorage.getItem(SS.activePending);
  } catch (e) { /* ignore */ }
  if (!jobId) return false;
  var source = "本机文件夹";
  try {
    if (pendingRaw) {
      var pending = JSON.parse(pendingRaw);
      if (pending && pending.albumPath) source = "本机文件夹";
    }
  } catch (e) { /* ignore */ }
  var gen = ++_gen;
  renderImportingPanel(source);
  setStage("恢复上次导入…", 0);
  pollImport(jobId, gen, source).catch(function (err) {
    if (gen !== _gen) return;
    showImportFailed(err);
  });
  return true;
}
