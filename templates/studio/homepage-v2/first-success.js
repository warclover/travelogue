/**
 * 首页 v2 · FirstSuccess 专屏（§9.3 / AC-HP2-18）。
 *
 * 背景 = Import 前壳层（Bento 或书架）；5s 倒计时后自动打开预览
 * （localStorage.firstPreviewDone 后仅手动）。继承 v3 §6.11 语义。
 */
import { LS } from "../js/constants.js";
import { trackStudioEvent } from "../js/analytics.js";
import { V2, $, show } from "./store.js";
import { syncVariantGuard } from "./variant-guard.js";

var _countdownTimer = null;
var _countdownLeft = 5;
var _successResult = null;
var _autoOpenEnabled = true;
var _wired = false;

function isFirstTime() {
  try {
    return !localStorage.getItem(LS.firstPreviewDone);
  } catch (e) {
    return true;
  }
}

function markFirstPreviewDone(tripId) {
  try {
    localStorage.setItem(LS.firstPreviewDone, tripId || "1");
  } catch (e) { /* ignore */ }
}

function clearCountdown() {
  if (_countdownTimer) {
    clearInterval(_countdownTimer);
    _countdownTimer = null;
  }
}

function updateCountdownLabel() {
  var el = $("v2-success-countdown");
  if (!el) return;
  if (!_autoOpenEnabled || _countdownLeft <= 0) {
    el.textContent = "";
    el.hidden = true;
    return;
  }
  el.hidden = false;
  el.textContent = _countdownLeft + " 秒后打开卷轴预览…";
}

function restoreImportShell() {
  show($("v2-loading"), false);
  show($("v2-importing"), false);
  if (V2.importShell === "shelf") {
    show($("v2-headline"), false);
    show($("v2-frame"), false);
    show($("v2-shelf"), true);
    show($("v2-topbar"), false);
  } else {
    show($("v2-shelf"), false);
    show($("v2-headline"), true);
    show($("v2-frame"), true);
    show($("v2-topbar"), true);
  }
}

function resolvePreviewUrl(result) {
  if (!result) return null;
  if (result.previewUrl) return result.previewUrl;
  if (result.tripId) return "/" + result.tripId + "/index.html";
  return null;
}

function populateSuccessUi(result) {
  result = result || {};
  var title = result.title || "我的旅途";
  var msg = $("v2-success-msg");
  if (msg) {
    var featured = result.featuredCount;
    var segments = result.segmentCount;
    var photoCount = result.photoCount || 0;
    if (result.g1Pending) {
      msg.textContent = "《" + title + "》章节结构已就绪，请先在预览中确认。";
    } else {
      var summary = featured > 0 ? ("精选 " + featured + " 张") : ("照片 " + photoCount + " 张");
      if (segments > 0) summary += "，行程 " + segments + " 段";
      msg.textContent = "《" + title + "》已生成 · " + summary;
    }
  }
  var open = $("v2-success-open");
  var url = resolvePreviewUrl(result);
  if (open && url) open.href = url;

  var cover = $("v2-success-cover");
  var coverImg = $("v2-success-cover-img");
  if (cover && coverImg && result.tripId) {
    coverImg.alt = title;
    coverImg.onerror = function () { show(cover, false); };
    coverImg.onload = function () { show(cover, true); };
    coverImg.src = "/" + result.tripId + "/preview.jpg?t=" + String(Date.now());
  } else if (cover) {
    show(cover, false);
  }
}

function openPreview(action) {
  clearCountdown();
  var url = resolvePreviewUrl(_successResult);
  if (!url) return;
  trackStudioEvent("success_primary_click", { action: action || "open_preview" });
  if (_successResult && _successResult.tripId) {
    markFirstPreviewDone(_successResult.tripId);
  }
  window.location.href = url;
}

function startCountdown() {
  clearCountdown();
  _autoOpenEnabled = isFirstTime();
  _countdownLeft = 5;
  updateCountdownLabel();
  if (!_autoOpenEnabled) return;
  _countdownTimer = setInterval(function () {
    _countdownLeft -= 1;
    updateCountdownLabel();
    if (_countdownLeft <= 0) {
      clearCountdown();
      openPreview("auto_countdown");
    }
  }, 1000);
}

/** Import 开始前记录壳层（Bento vs 书架）。 */
export function captureImportShell() {
  var shelf = $("v2-shelf");
  if (shelf && !shelf.hidden) {
    V2.importShell = "shelf";
    return;
  }
  V2.importShell = "bento";
}

export function isFirstSuccessVisible() {
  var overlay = $("v2-first-success");
  return !!(overlay && !overlay.hidden);
}

export function dismissFirstSuccess() {
  clearCountdown();
  show($("v2-first-success"), false);
  syncVariantGuard();
  if (typeof V2.reroute === "function") V2.reroute();
}

/**
 * @param {{result?:object,tripId?:string,title?:string,previewUrl?:string}} jobOrResult
 */
export function showFirstSuccess(jobOrResult) {
  var result = (jobOrResult && jobOrResult.result) || jobOrResult || {};
  _successResult = result;
  V2.state = "FirstSuccess";
  restoreImportShell();

  populateSuccessUi(result);
  show($("v2-first-success"), true);

  if (!_wired) wireFirstSuccess();
  startCountdown();
}

function wireFirstSuccess() {
  if (_wired) return;
  _wired = true;
  var stay = $("v2-success-stay");
  if (stay) {
    stay.addEventListener("click", function () {
      clearCountdown();
      if (_successResult && _successResult.tripId) {
        markFirstPreviewDone(_successResult.tripId);
      }
      dismissFirstSuccess();
    });
  }
  var open = $("v2-success-open");
  if (open) {
    open.addEventListener("click", function (e) {
      e.preventDefault();
      openPreview("open_preview");
    });
  }
}

export function initFirstSuccess() {
  wireFirstSuccess();
}
