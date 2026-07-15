/**
 * 首页 v2 · Import Failed 专屏（继承 v1.4 · 背景 = 恒常 Bento 壳层 · 方案 A）。
 * L0 Hardening：E_LLM_AUTH → T-FAIL-01（用本机文案继续 / 去配置 / 留在首页）。
 */
import { SS, isDemoTrip } from "../js/constants.js";
import { humanizeStudioError, failureNextHint, isLlmAuthRecoverable } from "../js/errors.js";
import { trackStudioEvent } from "../js/analytics.js";
import { V2, $, show, setV2SkipLinkTarget } from "./store.js";
import { captureImportShell } from "./first-success.js";
import { startV2Import } from "./import-run.js";
import { openImportSheet } from "./import-entry.js";
import { syncVariantGuard } from "./variant-guard.js";
import { openLlmSettings } from "../js/llm-settings.js";
import { syncHomeStubBanner } from "../js/home-stub-banner.js";

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

function setHidden(el, hidden) {
  if (!el) return;
  if (hidden) el.setAttribute("hidden", "");
  else el.removeAttribute("hidden");
}

function populateFailedUi(err, pending) {
  var code = err && err.code;
  var authRecoverable = isLlmAuthRecoverable(err);
  var panel = document.querySelector("#v2-failure .v2-failure__panel");
  if (panel) {
    if (authRecoverable) panel.classList.add("v2-failure__panel--auth");
    else panel.classList.remove("v2-failure__panel--auth");
  }

  var eyebrow = $("v2-failure-eyebrow");
  if (eyebrow) {
    eyebrow.textContent = authRecoverable ? "杂志感文案暂不可用" : "导入失败";
  }

  var msgEl = $("v2-failure-msg");
  if (msgEl) {
    msgEl.textContent = authRecoverable
      ? "可以改用本机文案继续生成游记；配置写作引擎后可再升级文案。"
      : humanizeStudioError(code, (err && err.message) || "导入失败，请重试");
  }
  var hintEl = $("v2-failure-hint");
  if (hintEl) {
    hintEl.textContent = authRecoverable
      ? "打开设置 → AI 文案，粘贴 API Key 并测试连接。不配置也可导入、预览和导出长图。"
      : failureNextHint(code);
  }
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

  var continueBtn = $("v2-failure-continue-stub");
  var settingsBtn = $("v2-failure-open-settings");
  var retry = $("v2-failure-retry");
  setHidden(continueBtn, !authRecoverable);
  setHidden(settingsBtn, !authRecoverable);
  // 缺引擎：重试降为次要（配置变更后仍可用）；有 pending 才显示
  var canRetry = !!(pending && (pending.albumPath || pending.uploadForm));
  setHidden(retry, authRecoverable ? !canRetry : false);
  if (retry && authRecoverable) {
    retry.textContent = "仍要重试";
    retry.classList.remove("v2-failure__cta");
    retry.classList.add("v2-failure__secondary");
  } else if (retry) {
    retry.textContent = "重试";
    retry.classList.add("v2-failure__cta");
    retry.classList.remove("v2-failure__secondary");
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
  syncHomeStubBanner();
}

/**
 * @param {{code?:string,message?:string,recoverableWithStub?:boolean}} err
 */
export function showImportFailed(err) {
  _lastErr = err || {};
  V2.state = "Failed";
  captureImportShell();
  restoreImportShell();
  var pending = readPendingImport();
  populateFailedUi(_lastErr, pending);
  try {
    window.scrollTo(0, 0);
  } catch (e) { /* ignore */ }
  show($("v2-failure"), true);

  var authRecoverable = isLlmAuthRecoverable(_lastErr);
  syncHomeStubBanner();
  if (authRecoverable) {
    trackStudioEvent("import_fail_auth_shown", { code: _lastErr.code || "E_LLM_AUTH" });
    setV2SkipLinkTarget("v2-failure-continue-stub");
    var cont = $("v2-failure-continue-stub");
    if (cont && typeof cont.focus === "function") cont.focus();
  } else {
    setV2SkipLinkTarget("v2-failure-retry");
    var retry = $("v2-failure-retry");
    if (retry && typeof retry.focus === "function") retry.focus();
  }
  if (!_wired) wireImportFailed();
}

function retryImportFailed() {
  var pending = readPendingImport();
  if (pending && pending.uploadForm) {
    try { sessionStorage.removeItem(SS.activePending); } catch (e) { /* ignore */ }
    hideImportFailed();
    syncVariantGuard();
    openImportSheet({ forceStep: "pick" });
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

function continueWithStub() {
  var pending = readPendingImport();
  if (pending && pending.uploadForm) {
    try {
      sessionStorage.setItem(SS.forceStubNextUpload, "1");
      sessionStorage.removeItem(SS.activePending);
    } catch (e) { /* ignore */ }
    trackStudioEvent("import_continue_stub", { source: "import_fail_upload" });
    hideImportFailed();
    syncVariantGuard();
    openImportSheet({ forceStep: "pick" });
    if (typeof studioToast === "function") {
      studioToast("请重新选择照片后，将使用本机文案继续", { duration: 2400 });
    }
    return;
  }
  if (!pending || !pending.albumPath) {
    dismissImportFailed();
    return;
  }
  trackStudioEvent("import_continue_stub", { source: "import_fail" });
  var body = Object.assign({}, pending, { forceStub: true, force: true });
  hideImportFailed();
  startV2Import(body, { source: "本机文件夹" }).catch(function () { /* handled */ });
}

function openSettingsFromFail() {
  trackStudioEvent("import_fail_open_settings", { source: "import_fail" });
  openLlmSettings({ source: "import_fail" });
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
  var cont = $("v2-failure-continue-stub");
  if (cont) cont.addEventListener("click", continueWithStub);
  var settings = $("v2-failure-open-settings");
  if (settings) settings.addEventListener("click", openSettingsFromFail);
}
