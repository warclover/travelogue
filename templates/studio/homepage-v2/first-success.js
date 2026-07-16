/**
 * 首页 v2 · FirstSuccess 专屏（§9.3 / AC-HP2-18 · 方案 A）。
 *
 * 背景 = 恒常 Bento 首屏；有画册时同屏保留下方书架区。
 */
import {
  HELP_COPY,
  trackHelpEvent,
} from "../js/help-onboarding.js";
import { LS, isDemoTrip, SHEET_FOCUSABLE } from "../js/constants.js";
import { trackStudioEvent } from "../js/analytics.js";
import { V2, $, show } from "./store.js";
import { syncVariantGuard } from "./variant-guard.js";
import { runShelfLongshot } from "./shelf-longshot.js";
import { syncHomeStubBanner } from "../js/home-stub-banner.js";

var _countdownTimer = null;
var _countdownLeft = 5;
var _successResult = null;
var _autoOpenEnabled = true;
var _wired = false;
var _successMode = "quick_share";
var _successRefinedEnabled = true;
var _trapHandler = null;
var _escHandler = null;
var _previousFocus = null;

var DENSITY_COPY = {
  zh: {
    hero_first: "已为你突出大图、放大精彩瞬间",
    collage_first: "已为你多图拼贴、记录更多细节",
  },
  en: {
    hero_first: "Large photos emphasized to highlight key moments",
    collage_first: "More collage layouts to capture extra detail",
  },
};

function successUiLang() {
  var lang = (typeof navigator !== "undefined" && navigator.language) || "zh";
  return String(lang).toLowerCase().indexOf("en") === 0 ? "en" : "zh";
}

function densitySummaryLine(density) {
  var key = String(density || "").toLowerCase();
  var pack = DENSITY_COPY[successUiLang()] || DENSITY_COPY.zh;
  if (key === "hero_first") return pack.hero_first;
  if (key === "collage_first") return pack.collage_first;
  return "";
}

function cullDisabledDetailLine(result) {
  var n = result.photoCount || 0;
  var m = typeof result.layoutEligibleCount === "number"
    ? result.layoutEligibleCount
    : n;
  if (m === n) {
    return "不做智能挑选 · " + m + " 张进入排版";
  }
  return "不做智能挑选 · 导入 " + n + " 张 · " + m + " 张进入排版\n"
    + "部分极低清晰度照片未进入排版";
}

// PRD-P9-F2 §5.7 · 保留连拍/近似照片的完成态说明
function keepDupesDetailLine(result) {
  var n = result.photoCount || 0;
  var a = typeof result.assetsWritten === "number" ? result.assetsWritten : n;
  if (a >= n) {
    return "已保留全部相近照片";
  }
  return "已保留连拍与近似照片（仍去除了完全相同的重复文件）";
}

function loadSuccessFeatureFlag() {
  return fetch("/__travelogue/config")
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var studio = (data && data.studio) || {};
      if (typeof studio.successRefinedDefaultEnabled === "boolean") {
        _successRefinedEnabled = studio.successRefinedDefaultEnabled;
      }
    })
    .catch(function () {
      _successRefinedEnabled = true;
    });
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

function resolvePreviewUrl(result) {
  if (!result) return null;
  if (result.previewUrl) return result.previewUrl;
  if (result.tripId) return "/" + result.tripId + "/index.html";
  return null;
}

function populateSuccessUi(result) {
  result = result || {};
  _successMode = String(result.mode || "quick_share").toLowerCase();
  if (_successMode !== "fine_craft") _successMode = "quick_share";
  if (!_successRefinedEnabled) _successMode = "fine_craft";
  var title = result.title || "我的旅途";
  var msg = $("v2-success-msg");
  var details = $("v2-success-details");
  if (msg) {
    var featured = result.featuredCount;
    var segments = result.segmentCount;
    var photoCount = result.photoCount || 0;
    if (result.g1Pending) {
      msg.textContent = "《" + title + "》章节结构已就绪，请先在预览中确认。";
      if (details) {
        details.textContent = "";
        show(details, false);
      }
    } else {
      var summary = featured > 0 ? ("精选 " + featured + " 张") : ("照片 " + photoCount + " 张");
      if (segments > 0) summary += "，行程 " + segments + " 段";
      var line1 = "《" + title + "》已生成 · " + summary;
      var detailLines = [];
      var tplLine = result.templateFeedbackMessage || "";
      if (tplLine) detailLines.push(tplLine);
      if (result.cullUserLine) {
        detailLines.push(result.cullUserLine);
      } else if (result.photoCullEnabled === false) {
        detailLines.push(cullDisabledDetailLine(result));
      }
      if (result.keepNearDuplicates === true) {
        detailLines.push(keepDupesDetailLine(result));
      }
      var density = String(result.layoutDensity || "").toLowerCase();
      var densityLine = densitySummaryLine(density);
      if (densityLine) detailLines.push(densityLine);
      msg.textContent = line1;
      if (details) {
        var detailBody = detailLines.join("\n");
        details.textContent = detailBody;
        show(details, detailLines.length > 0);
      }
      var ariaBody = line1 + (detailLines.length ? "; " + detailLines.join("; ") : "");
      msg.setAttribute("aria-label", ariaBody);
      if (result.templateFeedbackKind) {
        var ev = result.templateFeedbackKind === "fallback"
          ? "template_fallback_shown"
          : (result.templateFeedbackKind === "manual"
            ? "template_manual_selected"
            : "template_smart_result_shown");
        trackStudioEvent(ev, {
          tripId: result.tripId || null,
          templateId: result.resolvedTemplateId || null,
        });
      }
    }
  }
  if (result.cullWarn && typeof studioToast === "function") {
    studioToast(result.cullWarn, { duration: 5000 });
  }
  if (result.dateRangeWarn && typeof studioToast === "function") {
    studioToast(result.dateRangeWarn, { duration: 4200 });
  }
  if (result.clusterNotice && typeof studioToast === "function") {
    studioToast(result.clusterNotice, { duration: 4200 });
  }
  if (result.mediaWarn && typeof studioToast === "function") {
    studioToast(result.mediaWarn, { duration: 5200 });
  }
  var open = $("v2-success-open");
  var secondary = $("v2-success-secondary");
  var nextHint = $("v2-success-next-hint");
  var url = resolvePreviewUrl(result);
  if (open && url) open.href = url;
  if (secondary && url) secondary.href = url;
  // D-HELP-10 · 方案 A：主 CTA 恒为打开预览；保存长图为次按钮
  if (open) {
    open.textContent = HELP_COPY.openPreviewCta;
  }
  if (secondary) {
    secondary.textContent = HELP_COPY.saveLongshotSecondary;
    show(secondary, _successRefinedEnabled && _successMode === "quick_share");
  }
  if (nextHint) {
    nextHint.textContent = HELP_COPY.firstSuccessNext;
    show(nextHint, true);
  }
  var setPreview = $("v2-success-set-preview");
  if (setPreview) {
    show(setPreview, !!result.tripId);
  }

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
  if (!url) {
    if (_successResult && _successResult.tripId) {
      if (typeof studioToast === "function") {
        studioToast("预览暂不可用，已为你切换到保存长图。", { duration: 2800 });
      }
      trackStudioEvent("success_preview_unavailable_fallback_longshot", {
        tripId: _successResult.tripId,
      });
      runShelfLongshot(
        { tripId: _successResult.tripId, title: _successResult.title || "我的旅途" },
        { surface: "first_success_fallback" },
      );
    }
    return;
  }
  trackStudioEvent("success_primary_click", {
    action: action || "open_preview",
    mode: _successMode,
    layoutDensity: _successResult && _successResult.layoutDensity
      ? _successResult.layoutDensity
      : null,
  });
  trackStudioEvent("preview_open_from_success", {
    mode: _successMode,
    tripId: _successResult && _successResult.tripId ? _successResult.tripId : null,
  });
  trackHelpEvent("help_funnel_preview_open", {
    tripId: _successResult && _successResult.tripId ? _successResult.tripId : null,
    source: action || "open_preview",
  });
  if (_successResult && _successResult.tripId) {
    markFirstPreviewDone(_successResult.tripId);
  }
  window.location.href = url;
}

function startCountdown() {
  clearCountdown();
  _autoOpenEnabled = false;
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

/** Import 开始前记录壳层（方案 A：恒 Bento 首页）。 */
export function captureImportShell() {
  V2.importShell = "bento";
}

export function isFirstSuccessVisible() {
  var overlay = $("v2-first-success");
  return !!(overlay && !overlay.hidden);
}

function focusableEls(container) {
  return Array.prototype.slice
    .call(container.querySelectorAll(SHEET_FOCUSABLE))
    .filter(function (el) {
      return el.offsetParent !== null || el === document.activeElement;
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
    if (!isFirstSuccessVisible()) return;
    e.preventDefault();
    dismissFirstSuccess();
  };
  document.addEventListener("keydown", _escHandler);
}

function releaseEsc() {
  if (_escHandler) document.removeEventListener("keydown", _escHandler);
  _escHandler = null;
}

export function dismissFirstSuccess() {
  clearCountdown();
  var overlay = $("v2-first-success");
  releaseTrap(overlay);
  releaseEsc();
  show(overlay, false);
  syncVariantGuard();
  if (_previousFocus && typeof _previousFocus.focus === "function") {
    try { _previousFocus.focus(); } catch (_e) { /* ignore */ }
  }
  _previousFocus = null;
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
  _previousFocus = document.activeElement;
  show($("v2-first-success"), true);
  syncHomeStubBanner();

  if (!_wired) wireFirstSuccess();
  var overlay = $("v2-first-success");
  if (overlay) {
    trapFocus(overlay);
    bindEscDismiss();
    var focusTarget = $("v2-success-open") || $("v2-success-stay");
    if (focusTarget && typeof focusTarget.focus === "function") focusTarget.focus();
  }
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
  var secondary = $("v2-success-secondary");
  if (secondary) {
    secondary.addEventListener("click", function (e) {
      e.preventDefault();
      // 次按钮「保存长图」：显式跳过验货（D-HELP-10）
      if (_successRefinedEnabled && _successResult && _successResult.tripId) {
        trackStudioEvent("success_primary_click", {
          action: "save_longshot",
          mode: _successMode,
          layoutDensity: _successResult.layoutDensity || null,
        });
        trackHelpEvent("help_funnel_skip_preview", {
          tripId: _successResult.tripId,
          mode: _successMode,
        });
        runShelfLongshot({ tripId: _successResult.tripId, title: _successResult.title || "我的旅途" }, {
          surface: "first_success",
        });
        return;
      }
      openPreview("open_preview_secondary");
    });
  }
  var setPreview = $("v2-success-set-preview");
  if (setPreview) {
    setPreview.addEventListener("click", function () {
      if (!_successResult || !_successResult.tripId) return;
      clearCountdown();
      import("./bento-tabs.js").then(function (m) {
        return m.setBentoPreviewTripId(_successResult.tripId, { source: "first_success" });
      }).then(function () {
        if (typeof studioToast === "function") {
          studioToast("已设为首页预览", { duration: 2200 });
        }
        markFirstPreviewDone(_successResult.tripId);
        dismissFirstSuccess();
      });
    });
  }
}

export function initFirstSuccess() {
  loadSuccessFeatureFlag();
  wireFirstSuccess();
}
