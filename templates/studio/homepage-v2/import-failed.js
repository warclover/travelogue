/**
 * 首页 v2 · Import Failed 专屏（继承 v1.4 · 背景 = 恒常 Bento 壳层 · 方案 A）。
 * NAS：默认面失败归因去配置出口（FE-NAS-06）；dark 可恢复配置 CTA。
 * L0 Resume：失败保留 pending；无 pending 时书架兜底。
 */
import { SS, isDemoTrip, SHEET_FOCUSABLE } from "../js/constants.js";
import { humanizeStudioError, failureNextHint, isLlmAuthRecoverable } from "../js/errors.js";
import { trackStudioEvent } from "../js/analytics.js";
import { V2, $, show, setV2SkipLinkTarget } from "./store.js";
import { captureImportShell } from "./first-success.js";
import { startV2Import } from "./import-run.js";
import { openImportSheet } from "./import-entry.js";
import { syncVariantGuard } from "./variant-guard.js";
import { openLlmSettings } from "../js/llm-settings.js";
import { syncHomeStubBanner } from "../js/home-stub-banner.js";
import { isAiSurfaceEnabled } from "../js/ai-surface.js";

var _wired = false;
var _lastErr = null;
var _trapHandler = null;
var _escHandler = null;
var _previousFocus = null;

function hasUserTrips() {
  return V2.trips.some(function (t) { return !isDemoTrip(t); });
}

function clearActivePending() {
  try {
    sessionStorage.removeItem(SS.activePending);
  } catch (e) { /* ignore */ }
}

function restoreImportShell() {
  show($("v2-loading"), false);
  var importing = $("v2-importing");
  if (importing) importing.setAttribute("aria-busy", "false");
  show(importing, false);
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

function latestUserTrip() {
  var list = (V2.trips || []).filter(function (t) { return t && !isDemoTrip(t) && t.tripId; });
  if (!list.length) return null;
  return list[0];
}

function populateFailedUi(err, pending) {
  var code = err && err.code;
  // NAS · 默认面不走「配置引擎」失败分支
  var authRecoverable = isAiSurfaceEnabled() && isLlmAuthRecoverable(err);
  var panel = document.querySelector("#v2-failure .v2-failure__panel");
  if (panel) {
    if (authRecoverable) panel.classList.add("v2-failure__panel--auth");
    else panel.classList.remove("v2-failure__panel--auth");
  }

  var eyebrow = $("v2-failure-eyebrow");
  if (eyebrow) {
    eyebrow.textContent = "导入失败";
  }

  var msgEl = $("v2-failure-msg");
  if (msgEl) {
    msgEl.textContent = authRecoverable
      ? "可以继续生成本次导入；配好后可在预览中刷新叙述。"
      : humanizeStudioError(code, (err && err.message) || "导入失败，请重试");
  }
  var hintEl = $("v2-failure-hint");
  if (hintEl) {
    hintEl.textContent = authRecoverable
      ? "可点「继续生成画册」；或检查文件夹后重试。"
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
  var openRecent = $("v2-failure-open-recent");
  var canContinue = !!(pending && (pending.albumPath || pending.uploadForm));
  var recent = !canContinue ? latestUserTrip() : null;

  setHidden(continueBtn, !authRecoverable || !canContinue);
  // 非鉴权失败禁止露出「查看设置」作写作引擎入口（避免导入失败误导为 AI 配置）
  setHidden(settingsBtn, !authRecoverable);
  if (settingsBtn && !authRecoverable) {
    settingsBtn.setAttribute("hidden", "");
  }
  setHidden(openRecent, !(authRecoverable && recent));
  if (continueBtn && authRecoverable) {
    continueBtn.textContent = "继续生成画册";
  }
  // 缺引擎：重试降为次要（配置变更后仍可用）；有 pending 才显示
  var canRetry = !!canContinue;
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

function focusableEls(container) {
  return Array.prototype.slice
    .call(container.querySelectorAll(SHEET_FOCUSABLE))
    .filter(function (el) {
      return !el.hidden && (el.offsetParent !== null || el === document.activeElement);
    });
}

function trapFocus(dialog) {
  releaseTrap(dialog);
  _trapHandler = function (e) {
    if (e.key !== "Tab") return;
    var els = focusableEls(dialog);
    if (!els.length) return;
    var first = els[0];
    var last = els[els.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  };
  dialog.addEventListener("keydown", _trapHandler);
}

function releaseTrap(dialog) {
  if (_trapHandler && dialog) dialog.removeEventListener("keydown", _trapHandler);
  _trapHandler = null;
}

function bindEscDismiss() {
  releaseEsc();
  _escHandler = function (e) {
    if (e.key !== "Escape") return;
    if (!isImportFailedVisible()) return;
    e.preventDefault();
    dismissImportFailed();
  };
  document.addEventListener("keydown", _escHandler);
}

function releaseEsc() {
  if (_escHandler) document.removeEventListener("keydown", _escHandler);
  _escHandler = null;
}

export function hideImportFailed() {
  var overlay = $("v2-failure");
  releaseTrap(overlay);
  releaseEsc();
  show(overlay, false);
  _lastErr = null;
  if (_previousFocus && typeof _previousFocus.focus === "function") {
    try { _previousFocus.focus(); } catch (_e) { /* ignore */ }
  }
  _previousFocus = null;
}

export function dismissImportFailed() {
  clearActivePending();
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
  _previousFocus = document.activeElement;
  show($("v2-failure"), true);

  var authRecoverable = isAiSurfaceEnabled() && isLlmAuthRecoverable(_lastErr);
  syncHomeStubBanner();
  if (authRecoverable) {
    trackStudioEvent("import_fail_auth_shown", { code: _lastErr.code || "E_LLM_AUTH" });
    var canContinue = !!(pending && (pending.albumPath || pending.uploadForm));
    // NAS · M7：焦点永不落到 settings
    var focusId = canContinue
      ? "v2-failure-continue-stub"
      : latestUserTrip()
        ? "v2-failure-open-recent"
        : "v2-failure-retry";
    setV2SkipLinkTarget(focusId);
    var focusEl = $(focusId);
    if (focusEl && typeof focusEl.focus === "function") focusEl.focus();
  } else {
    setV2SkipLinkTarget("v2-failure-retry");
    var retry = $("v2-failure-retry");
    if (retry && typeof retry.focus === "function") retry.focus();
  }
  var overlay = $("v2-failure");
  if (overlay) {
    trapFocus(overlay);
    bindEscDismiss();
  }
  if (!_wired) wireImportFailed();
}

function retryImportFailed() {
  var pending = readPendingImport();
  if (pending && pending.uploadForm) {
    clearActivePending();
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

/**
 * 用本机文案（forceStub）续跑同一 pending；供失败屏与设置 Modal resume 共用。
 */
export function continueWithStub() {
  var pending = readPendingImport();
  if (pending && pending.uploadForm) {
    try {
      sessionStorage.setItem(SS.forceStubNextUpload, "1");
    } catch (e) { /* ignore */ }
    clearActivePending();
    trackStudioEvent("import_continue_stub", { source: "import_fail_upload" });
    hideImportFailed();
    syncVariantGuard();
    openImportSheet({ forceStep: "pick" });
    if (typeof studioToast === "function") {
      studioToast("请重新选择同一批照片后继续（浏览器无法记住上次选中的文件）", { duration: 3200 });
    }
    return;
  }
  if (!pending || !pending.albumPath) {
    var recent = latestUserTrip();
    if (recent) {
      openRecentTripPreview();
      return;
    }
    dismissImportFailed();
    return;
  }
  trackStudioEvent("import_continue_stub", { source: "import_fail" });
  var body = Object.assign({}, pending, { forceStub: true, force: true });
  clearActivePending();
  hideImportFailed();
  startV2Import(body, { source: "本机文件夹" }).catch(function () { /* handled */ });
}

function openRecentTripPreview() {
  var trip = latestUserTrip();
  if (!trip || !trip.tripId) {
    if (typeof studioToast === "function") {
      studioToast("暂无可打开的画册，请重新导入", { duration: 2200 });
    }
    return;
  }
  trackStudioEvent("import_fail_open_recent", { tripId: trip.tripId });
  clearActivePending();
  hideImportFailed();
  syncVariantGuard();
  var url = trip.previewUrl || ("/" + trip.tripId + "/index.html");
  window.location.href = url;
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
  var openRecent = $("v2-failure-open-recent");
  if (openRecent) openRecent.addEventListener("click", openRecentTripPreview);
}
