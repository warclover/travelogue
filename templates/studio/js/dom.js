/**
 * Travelogue Studio · DOM + low-level UI helpers.
 */
import { SHEET_FOCUSABLE } from "./constants.js";
import { S } from "./state.js";
import { studioAuthHeaders } from "./http.js";

export { studioAuthHeaders };
export { isJobBusyResponse, withJobBusyRetry, postJsonBusyRetry } from "./http.js";

export function $(id) { return document.getElementById(id); }
export function show(el, visible) { if (el) el.hidden = !visible; }

var STUDIO_BG_REGIONS = ["studio-hero", "studio-below"];

/** When a modal/sheet is open, keep keyboard and AT out of main page chrome. */
export function setStudioBackgroundInert(inert) {
  STUDIO_BG_REGIONS.forEach(function (id) {
    var el = $(id);
    if (!el) return;
    if (inert) {
      el.setAttribute("inert", "");
      el.setAttribute("aria-hidden", "true");
    } else {
      el.removeAttribute("inert");
      el.removeAttribute("aria-hidden");
    }
  });
}

/** Safe value for element.style.backgroundImage (blocks CSS-breaking quotes). */
export function cssBackgroundImage(url) {
  if (!url || typeof url !== "string") return "";
  var s = url;
  if (/[\x00-\x1f"'\\]/.test(s)) return "";
  return 'url("' + s.replace(/\\/g, "\\\\").replace(/"/g, "\\22") + '")';
}

export function sheetFocusableElements(sheet) {
  return Array.prototype.filter.call(sheet.querySelectorAll(SHEET_FOCUSABLE), function (el) {
    if (el.disabled || el.getAttribute("aria-hidden") === "true") return false;
    if (el.closest("[hidden]")) return false;
    return true;
  });
}

export function trapSheetFocus(sheet) {
  function onKeydown(e) {
    if (e.key !== "Tab") return;
    var items = sheetFocusableElements(sheet);
    if (!items.length) return;
    var first = items[0];
    var last = items[items.length - 1];
    if (e.shiftKey) {
      if (document.activeElement === first) {
        e.preventDefault();
        last.focus();
      }
    } else if (document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }
  sheet.addEventListener("keydown", onKeydown);
  return function () { sheet.removeEventListener("keydown", onKeydown); };
}

export function releaseSheetFocusTrap(restoreFocus) {
  if (S._sheetFocusRelease) {
    S._sheetFocusRelease();
    S._sheetFocusRelease = null;
  }
  if (restoreFocus && S._sheetPreviousFocus && S._sheetPreviousFocus.focus) {
    try { S._sheetPreviousFocus.focus(); } catch (err) { /* ignore */ }
  }
  S._sheetPreviousFocus = null;
}

export function setTitle(suffix) {
  document.title = suffix ? suffix + " · Travelogue Studio" : "Travelogue Studio";
}

export function formatUpdatedAt(ts) {
  if (!ts) return "";
  var d = new Date(ts * 1000);
  var now = new Date();
  var diffMs = now - d;
  var dayMs = 24 * 3600 * 1000;
  if (diffMs < 60 * 1000) return "刚刚";
  if (diffMs < 3600 * 1000) return Math.floor(diffMs / 60000) + " 分钟前";
  if (diffMs < dayMs) return Math.floor(diffMs / 3600000) + " 小时前";
  if (diffMs < 7 * dayMs) return Math.floor(diffMs / dayMs) + " 天前";
  return d.toLocaleDateString("zh-CN");
}

export function formatBytes(n) {
  if (!n || n < 1024) return "0 KB";
  if (n < 1024 * 1024) return Math.round(n / 1024) + " KB";
  return (n / (1024 * 1024)).toFixed(1) + " MB";
}

export function basenameTitleFromPath(path) {
  if (!path) return "我的旅途";
  var base = String(path).replace(/[/\\]+$/, "").split(/[/\\]/).pop() || "";
  base = base.replace(/\.[^.]+$/, "").trim();
  if (!base) return "我的旅途";
  return base.length > 20 ? base.slice(0, 20) : base;
}

export function bumpImportGeneration() { S._importGen += 1; }
export function isImportGenerationStale(gen) { return gen !== S._importGen; }

export function setImportUiDisabled(disabled) {
  var ids = [
    "studio-open-sheet", "studio-open-sheet-returning", "studio-sheet-pick",
    "studio-sheet-start", "studio-sheet-skip", "studio-browse-folder",
    "studio-submit-path", "studio-demo-album", "studio-path-toggle",
    "studio-sample-cta",
  ];
  ids.forEach(function (id) { var el = $(id); if (el) el.disabled = disabled; });
  var uploadInput = $("album-upload");
  if (uploadInput) uploadInput.disabled = disabled;
}

export function syncImportUiDisabled() {
  setImportUiDisabled(S.isOffline || S.currentState === "Importing" || S._pickInFlight);
}

export function setBusy() { syncImportUiDisabled(); }
