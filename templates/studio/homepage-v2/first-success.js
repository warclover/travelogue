/**
 * 首页 v2 · FirstSuccess 专屏（§9.3 / AC-HP2-18 · 方案 A）。
 *
 * 背景 = 恒常 Bento 首屏；有画册时同屏保留下方书架区。
 */
import {
  HELP_COPY,
  trackHelpEvent,
  hasGenerateCompleteTipSeen,
  markGenerateCompleteTipSeen,
} from "../js/help-onboarding.js";
import { LS, isDemoTrip, SHEET_FOCUSABLE } from "../js/constants.js";
import { trackStudioEvent } from "../js/analytics.js";
import { V2, $, show } from "./store.js";
import { syncVariantGuard } from "./variant-guard.js";
import { syncHomeStubBanner } from "../js/home-stub-banner.js";
import {
  firstSuccessCrossRiverLabel,
  firstSuccessPortfolioCopy,
  firstSuccessRefineLabel,
  shelfExportRequestForTrip,
} from "../js/portfolio-export-logic.js";
import { runShelfLongshot } from "./shelf-longshot.js";

var AUTO_EXPORT_KEY = "travelogue.studio.autoExport";
var LVP_HINT_PENDING_PREFIX = "travelogue.layoutVibeHintPending.";

function markLayoutVibeHintPending(tripId) {
  if (!tripId) return;
  try {
    sessionStorage.setItem(LVP_HINT_PENDING_PREFIX + String(tripId), "1");
  } catch (_e) {}
}

function writeFtueAutoExport(tripId, platform) {
  try {
    sessionStorage.setItem(
      AUTO_EXPORT_KEY,
      JSON.stringify({
        tripId: String(tripId || ""),
        platform: String(platform || "wechat_chat"),
        ts: Date.now(),
      })
    );
  } catch (_e) {}
}

function previewUrlWithAutoExport(baseUrl, platform) {
  var url = String(baseUrl || "");
  if (!url) return url;
  var sep = url.indexOf("?") >= 0 ? "&" : "?";
  return url + sep + "autoExport=" + encodeURIComponent(platform || "wechat_chat");
}

function previewUrlWithExportPanel(baseUrl, opts) {
  var url = String(baseUrl || "");
  if (!url) return url;
  var sep = url.indexOf("?") >= 0 ? "&" : "?";
  var q = "exportPanel=1";
  if (opts && opts.face === "social") q += "&exportFace=social";
  return url + sep + q;
}

function previewUrlWithRefine(baseUrl) {
  var url = String(baseUrl || "");
  if (!url) return url;
  var sep = url.indexOf("?") >= 0 ? "&" : "?";
  return url + sep + "refine=on";
}

function isPortfolioResult(result) {
  var ed = String((result && result.edition) || "").trim().toLowerCase();
  return ed === "portfolio" || ed === "folio";
}

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
  el.textContent = _countdownLeft + " 秒后打开画册预览…";
}

function hasUserTrips() {
  return V2.trips.some(function (t) { return !isDemoTrip(t); });
}

export function restoreImportShell() {
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

/** FirstSuccess 顶栏：真实封面图；避免竖版 preview.jpg 封面卡（含标题字） */
function resolveSuccessCoverUrl(result) {
  if (!result || !result.tripId) return null;
  var rel = result.shelfCoverRelPath || result.coverImageRelPath || "";
  if (!rel && Array.isArray(V2.trips)) {
    for (var i = 0; i < V2.trips.length; i++) {
      var trip = V2.trips[i];
      if (trip && trip.tripId === result.tripId) {
        rel = trip.shelfCoverRelPath || trip.previewRelPath || "";
        break;
      }
    }
  }
  rel = String(rel || "").replace(/^\/+/, "");
  // 仍回退 preview.jpg 时，宁可无图也不展示带标题的竖版封面卡
  if (!rel || rel === "preview.jpg") return null;
  return "/" + result.tripId + "/" + rel + "?t=" + String(Date.now());
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
      // 仅实验「导入后先确认章节」仍会 pending；引导打开预览中的分章面板
      msg.textContent = "《" + title + "》已可预览；请在预览中打开「分章」确认顺序。";
      if (details) {
        details.textContent = "";
        show(details, false);
      }
    } else {
      var isPfCopy = isPortfolioResult(result);
      var pfCopy = isPfCopy ? firstSuccessPortfolioCopy(result) : null;
      var summary = featured > 0 ? ("精选 " + featured + " 张") : ("照片 " + photoCount + " 张");
      if (segments > 0) summary += "，行程 " + segments + " 段";
      var line1 = pfCopy && pfCopy.headline
        ? pfCopy.headline
        : ("《" + title + "》已生成 · " + summary);
      var detailLines = [];
      if (pfCopy && pfCopy.detail) detailLines.push(pfCopy.detail);
      var tplLine = result.templateFeedbackMessage || "";
      if (tplLine && !isPfCopy) detailLines.push(tplLine);
      var keepMode = String(result.photoKeepMode || "").trim().toLowerCase();
      if (keepMode === "keep_all") {
        detailLines.push(
          "已尽量保留全部可用照片（仍去掉损坏与完全相同的重复文件）"
        );
      } else {
        if (result.cullUserLine) {
          detailLines.push(result.cullUserLine);
        } else if (result.photoCullEnabled === false) {
          detailLines.push(cullDisabledDetailLine(result));
        }
        if (result.keepNearDuplicates === true) {
          detailLines.push(keepDupesDetailLine(result));
        }
      }
      var density = String(result.layoutDensity || "").toLowerCase();
      var densityLine = !isPfCopy ? densitySummaryLine(density) : "";
      if (densityLine) detailLines.push(densityLine);
      msg.textContent = line1;
      if (details) {
        details.textContent = "";
        detailLines.forEach(function (line) {
          var li = document.createElement("li");
          li.textContent = line;
          details.appendChild(li);
        });
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
  if (result.sparseG1Suppressed) {
    trackStudioEvent("sfc_g1_suppressed_sparse", {
      tripId: result.tripId || null,
      mode: result.mode || "quick_share",
      photoCount: result.photoCount || null,
    });
  }
  var open = $("v2-success-open");
  var secondary = $("v2-success-secondary");
  var refine = $("v2-success-refine");
  var actions = $("v2-success-actions");
  var nextHint = $("v2-success-next-hint");
  var url = resolvePreviewUrl(result);
  var isPf = isPortfolioResult(result);
  markLayoutVibeHintPending(result.tripId);
  if (open && url) open.href = url;
  if (actions) actions.classList.toggle("is-portfolio-pair", isPf);
  // 游记：次按钮链到预览并续跑 wechat_chat。作品集禁止 autoExport（BLK-PFO-03）。
  if (secondary && url) {
    secondary.href = isPf
      ? previewUrlWithExportPanel(url)
      : previewUrlWithAutoExport(url, "wechat_chat");
  }
  if (refine) {
    refine.href = url ? previewUrlWithRefine(url) : "#";
    refine.textContent = firstSuccessRefineLabel(isPf ? "portfolio" : "journal");
    show(refine, isPf);
  }
  if (open) {
    open.textContent = isPf ? "打开这一本" : HELP_COPY.openPreviewCta;
  }
  if (secondary) {
    secondary.textContent = isPf ? "导出作品集" : HELP_COPY.saveLongshotSecondary;
    secondary.classList.toggle("v2-first-success__cta", isPf);
    secondary.classList.toggle("v2-first-success__link", !isPf);
    show(secondary, isPf || (_successRefinedEnabled && _successMode === "quick_share"));
  }
  if (nextHint) {
    nextHint.textContent = "";
    var lead = document.createElement("p");
    lead.className = "v2-first-success__guidance-lead";
    // 游记 NAS · FE-NAS-05：固定 COPY-NAS-FS-01。作品集用人话规格句。
    lead.textContent = isPf
      ? (firstSuccessPortfolioCopy(result).lead ||
        "作品集已做好。打开看看，满意就能导出。")
      : (HELP_COPY.firstSuccessNextNeutral ||
        HELP_COPY.firstSuccessNext ||
        "画册已做好，可预览与导出长图。");
    nextHint.appendChild(lead);
    trackStudioEvent("first_success_copy_branch", {
      copy_branch: "nas_hidden",
      tripId: result.tripId || null,
    });
    // ONB-01 · 生成完成一次性提示；作品集不套游记「再做一本」
    if (HELP_COPY.ftueConvertHint && !isPf && !hasGenerateCompleteTipSeen()) {
      var nextLine = document.createElement("p");
      nextLine.className = "v2-first-success__guidance-next";
      nextLine.textContent = HELP_COPY.ftueConvertHint;
      nextHint.appendChild(nextLine);
      markGenerateCompleteTipSeen();
    }
    if (isPf && url) {
      var cross = document.createElement("a");
      cross.className = "v2-first-success__guidance-next";
      cross.href = previewUrlWithExportPanel(url, { face: "social" });
      cross.textContent = firstSuccessCrossRiverLabel();
      nextHint.appendChild(cross);
    }
    show(nextHint, true);
  }
  var setPreview = $("v2-success-set-preview");
  if (setPreview) {
    show(setPreview, !!result.tripId && !isDemoTrip(result));
  }

  applySuccessCover(result, title);
}

/** 书架刷新后补挂封面（仅图片，不动文案） */
export function refreshSuccessCover(result) {
  if (!result || !isFirstSuccessVisible()) return;
  applySuccessCover(result, result.title || "我的旅途");
}

function applySuccessCover(result, title) {
  var cover = $("v2-success-cover");
  var coverImg = $("v2-success-cover-img");
  var coverUrl = resolveSuccessCoverUrl(result);
  if (cover && coverImg && coverUrl) {
    coverImg.alt = title || "";
    coverImg.onerror = function () { show(cover, false); };
    coverImg.onload = function () { show(cover, true); };
    if (coverImg.getAttribute("src") !== coverUrl) {
      coverImg.src = coverUrl;
    } else {
      show(cover, true);
    }
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
        {
          tripId: _successResult.tripId,
          title: _successResult.title || "我的旅途",
          edition: _successResult.edition,
        },
        shelfExportRequestForTrip(
          { edition: _successResult.edition },
          { surface: "first_success_fallback" },
        ),
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
  if (isPortfolioResult(_successResult)) {
    clearCountdown();
    var cd = $("v2-success-countdown");
    if (cd) show(cd, false);
    return;
  }
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
  var importingHost = $("v2-importing");
  if (importingHost) importingHost.setAttribute("aria-busy", "false");

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
      if (isPortfolioResult(_successResult) && _successResult && _successResult.tripId) {
        trackStudioEvent("success_primary_click", {
          action: "export_portfolio",
          mode: _successMode,
          layoutDensity: _successResult.layoutDensity || null,
        });
        clearCountdown();
        markFirstPreviewDone(_successResult.tripId);
        var pfDest =
          secondary.href ||
          previewUrlWithExportPanel(resolvePreviewUrl(_successResult));
        if (pfDest) {
          window.location.href = pfDest;
          return;
        }
      }
      // FE-DFX-43 · 游记进预览并触发默认微信群长图导出（query + session 双写）
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
        clearCountdown();
        markFirstPreviewDone(_successResult.tripId);
        writeFtueAutoExport(_successResult.tripId, "wechat_chat");
        var dest =
          secondary.href ||
          previewUrlWithAutoExport(
            resolvePreviewUrl(_successResult),
            "wechat_chat"
          );
        if (dest) {
          window.location.href = dest;
          return;
        }
      }
      openPreview("open_preview_secondary");
    });
  }
  var refine = $("v2-success-refine");
  if (refine) {
    refine.addEventListener("click", function (e) {
      e.preventDefault();
      if (!_successResult || !_successResult.tripId) return;
      trackStudioEvent("success_primary_click", {
        action: "refine_portfolio",
        mode: _successMode,
        layoutDensity: _successResult.layoutDensity || null,
      });
      clearCountdown();
      markFirstPreviewDone(_successResult.tripId);
      var refineDest =
        refine.href || previewUrlWithRefine(resolvePreviewUrl(_successResult));
      if (refineDest) window.location.href = refineDest;
    });
  }
  var setPreview = $("v2-success-set-preview");
  if (setPreview) {
    setPreview.addEventListener("click", function () {
      if (!_successResult || !_successResult.tripId || isDemoTrip(_successResult)) return;
      clearCountdown();
      import("./bento-tabs.js").then(function (m) {
        return m.setBentoPreviewTripId(_successResult.tripId, { source: "first_success" });
      }).then(function (out) {
        if (out && out.rejected) return;
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
