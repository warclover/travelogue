/**
 * 首页 v2 · FirstSuccess 专屏（§9.3 / AC-HP2-18 · 方案 A）。
 *
 * 背景 = 恒常 Bento 首屏；有画册时同屏保留下方书架区。
 */
import { LS, isDemoTrip } from "../js/constants.js";
import { trackStudioEvent } from "../js/analytics.js";
import { V2, $, show } from "./store.js";
import { syncVariantGuard } from "./variant-guard.js";
import { runShelfLongshot } from "./shelf-longshot.js";

var _countdownTimer = null;
var _countdownLeft = 5;
var _successResult = null;
var _autoOpenEnabled = true;
var _wired = false;
var _successMode = "quick_share";
var _successRefinedEnabled = true;

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
      if (result.cullUserLine) detailLines.push(result.cullUserLine);
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
  var open = $("v2-success-open");
  var secondary = $("v2-success-secondary");
  var url = resolvePreviewUrl(result);
  if (open && url) open.href = url;
  if (secondary && url) secondary.href = url;
  if (open) {
    open.textContent = _successMode === "fine_craft" ? "打开卷轴预览 →" : "保存长图";
  }
  if (secondary) {
    secondary.textContent = "打开卷轴预览";
    show(secondary, _successRefinedEnabled && _successMode === "quick_share");
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
      if (_successRefinedEnabled && _successMode === "quick_share" && _successResult && _successResult.tripId) {
        trackStudioEvent("success_primary_click", {
          action: "save_longshot",
          mode: _successMode,
          layoutDensity: _successResult.layoutDensity || null,
        });
        runShelfLongshot({ tripId: _successResult.tripId, title: _successResult.title || "我的旅途" }, {
          surface: "first_success",
        });
        return;
      }
      openPreview("open_preview");
    });
  }
  var secondary = $("v2-success-secondary");
  if (secondary) {
    secondary.addEventListener("click", function (e) {
      e.preventDefault();
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
