/**
 * 首页 v2 · Import Failed 专屏（继承 v1.4 · 背景 = 恒常 Bento 壳层 · 方案 A）。
 */
import { SS, isDemoTrip } from "../js/constants.js";
import { humanizeStudioError, failureNextHint } from "../js/errors.js";
import { V2, $, show, setV2SkipLinkTarget } from "./store.js";
import { captureImportShell } from "./first-success.js";
import { startV2Import } from "./import-run.js";
import { openImportSheet } from "./import-sheet.js";
import { syncVariantGuard } from "./variant-guard.js";

var _wired = false;
var _lastErr = null;

function hasUserTrips() {
  return V2.trips.some(function (t) { return !isDemoTrip(t); });
}

function restoreImportShell() {
  show($("v2-loading"), false);
  show($("v2-importing"), false);
  show($("v2-headline"), true);
  show($("v2-frame"), true);
  import("./shelf.js").then(function (m) {
    if (hasUserTrips()) {
      m.renderShelf(V2.trips, V2.tripsTotal);
    } else {
      m.hideShelf();
    }
  });
}

function readPendingImport() {
  try {
    var raw = sessionStorage.getItem(SS.activePending);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (e) {
    return null;
  }
}

function populateFailedUi(err, pending) {
  var code = err && err.code;
  var msg = humanizeStudioError(code, (err && err.message) || "导入失败，请重试");
  var msgEl = $("v2-failure-msg");
  if (msgEl) msgEl.textContent = msg;
  var hintEl = $("v2-failure-hint");
  if (hintEl) hintEl.textContent = failureNextHint(code);
  var echoEl = $("v2-failure-echo");
  var path = pending && pending.albumPath;
  if (echoEl) {
    if (path) {
      echoEl.textContent = path;
      show(echoEl, true);
    } else {
      echoEl.textContent = "";
      show(echoEl, false);
    }
  }
}

export function isImportFailedVisible() {
  var el = $("v2-failure");
  return !!(el && !el.hidden);
}

export function hideImportFailed() {
  show($("v2-failure"), false);
  _lastErr = null;
}

export function dismissImportFailed() {
  hideImportFailed();
  syncVariantGuard();
  if (typeof V2.reroute === "function") V2.reroute();
}

/**
 * @param {{code?:string,message?:string}} err
 */
export function showImportFailed(err) {
  _lastErr = err || {};
  V2.state = "Failed";
  captureImportShell();
  restoreImportShell();
  populateFailedUi(_lastErr, readPendingImport());
  show($("v2-failure"), true);
  setV2SkipLinkTarget("v2-failure-retry");
  if (!_wired) wireImportFailed();
}

function retryImportFailed() {
  var pending = readPendingImport();
  if (pending && pending.uploadForm) {
    try { sessionStorage.removeItem(SS.activePending); } catch (e) { /* ignore */ }
    hideImportFailed();
    syncVariantGuard();
    openImportSheet();
    if (typeof studioToast === "function") {
      studioToast("请重新选择要上传的照片后重试", { duration: 2200 });
    }
    return;
  }
  if (!pending || !pending.albumPath) {
    dismissImportFailed();
    return;
  }
  hideImportFailed();
  startV2Import(pending, { source: "本机文件夹" }).catch(function () { /* handled */ });
}

export function initImportFailed() {
  wireImportFailed();
}

function wireImportFailed() {
  if (_wired) return;
  _wired = true;
  var retry = $("v2-failure-retry");
  if (retry) retry.addEventListener("click", retryImportFailed);
  var stay = $("v2-failure-stay");
  if (stay) stay.addEventListener("click", dismissImportFailed);
}
