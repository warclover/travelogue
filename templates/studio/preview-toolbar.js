/**
 * Travelogue Studio · preview page toolbar (ESM).
 */
"use strict";

import {
  postJson,
  patchJson,
  postJsonBusyRetry,
  isJobBusyResponse,
} from "./js/http.js";
import { startJobPollInterval, pollJobUntilDone } from "./js/job-poll.js";
import {
  buildLongshotRequest,
  resolveCopyDisplayFromDom,
} from "./js/longshot-client.js";
import { STUDIO_USER_NOTES_MAX_LEN } from "./js/constants.js";
import { trackStudioEvent } from "./js/analytics.js";
import { mountCohortDrawer } from "./cohort-drawer.js";
import { mountPreviewTaskDock } from "./preview-toolbar-v3-task-dock.js";
import { mountPreviewUnifiedSheet } from "./preview-toolbar-v3-sheet.js";

var isJobBusy409 = isJobBusyResponse;
var HINT_KEY = "travelogue.studio.editHint.dismissed";
var COLLAPSE_KEY = "travelogue.studio.previewToolbar.collapsed";
var READER_VIEW_KEY = "travelogue.studio.readerView";
var SHEET_HINT_KEY = "travelogue.studio.previewSheet.hintSeen";
var LONGSHOT_MODE_KEY = "travelogue:longshotMode";
var LONGSHOT_SCALE_KEY = "travelogue:longshotScale";
var COVER_STYLE_TOAST_KEY = "travelogue.coverStyleToast.";
var COVER_OPENING_STYLE_OPTIONS = [
  { id: "card-br", label: "书名卡" },
  { id: "split-mat", label: "分屏衬纸" },
  { id: "magazine-head", label: "杂志顶题" },
];
var SLOW_JOB_MS = 30000;
var longshotPollCancel = null;
var narratePollCancel = null;
var longshotJobId = null;
var narrateJobId = null;

function presentPreviewUrl() {
  return document.documentElement.getAttribute("data-present-preview-url") || "";
}

function presentAutoplayHref(opts) {
  var url = presentPreviewUrl();
  if (!url) return "";
  var href = url;
  if (opts && opts.featured) {
    href += (href.indexOf("?") >= 0 ? "&" : "?") + "presentFeatured=1";
  }
  return href + "#present/1";
}

/** Folio / editorial-room SVG glyphs for v4 icon dock. */
function dockIconSvg(name) {
  var attrs =
    'class="preview-toolbar__dock-icon" viewBox="0 0 24 24" ' +
    'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" ' +
    'stroke-linejoin="round" aria-hidden="true" focusable="false"';
  var accent =
    'class="preview-toolbar__dock-icon-accent" fill="currentColor" stroke="none"';
  switch (name) {
    case "back":
      return (
        "<svg " +
        attrs +
        ">" +
        '<path d="M3.5 3.5h10.2L20.5 7.2V20a1.4 1.4 0 0 1-1.4 1.4H5.4A1.4 1.4 0 0 1 4 20V3.5h-.5z"/>' +
        '<path d="M13.7 3.5V7.4H20.5"/>' +
        '<path d="M13.7 3.5H20.5" ' +
        accent +
        "/>" +
        '<path d="M8 12.2 4.8 12l3.2-2.8"/>' +
        '<path d="M4.8 12h6.8" stroke-width="2"/>' +
        "</svg>"
      );
    case "play":
      return (
        "<svg " +
        attrs +
        ">" +
        '<rect x="2.5" y="2.5" width="19" height="19" rx="2"/>' +
        '<circle cx="5.2" cy="6.8" r="1.05" fill="currentColor" stroke="none"/>' +
        '<circle cx="5.2" cy="12" r="1.05" fill="currentColor" stroke="none"/>' +
        '<circle cx="5.2" cy="17.2" r="1.05" fill="currentColor" stroke="none"/>' +
        '<circle cx="18.8" cy="6.8" r="1.05" fill="currentColor" stroke="none"/>' +
        '<circle cx="18.8" cy="12" r="1.05" fill="currentColor" stroke="none"/>' +
        '<circle cx="18.8" cy="17.2" r="1.05" fill="currentColor" stroke="none"/>' +
        '<polygon points="9,7.5 9,16.5 17.5,12" ' +
        accent +
        "/>" +
        "</svg>"
      );
    case "settings":
      return (
        "<svg " +
        attrs +
        ' stroke-width="1.9">' +
        '<path d="M12 2.3L15.65 5.68L20.41 7.15L19.3 12L20.41 16.85L15.65 18.32L12 21.7L8.35 18.32L3.59 16.85L4.7 12L3.59 7.15L8.35 5.68Z"/>' +
        '<circle cx="12" cy="12" r="3.4"/>' +
        "</svg>"
      );
    case "scroll":
      return (
        "<svg " +
        attrs +
        ">" +
        '<rect x="7" y="2" width="10" height="5.2" rx="0.9" opacity="0.42"/>' +
        '<rect x="5" y="7.2" width="14" height="5.6" rx="0.9" opacity="0.68"/>' +
        '<rect x="3" y="12.8" width="18" height="8.2" rx="1"/>' +
        '<path d="M6.5 20.8h11" stroke-dasharray="2.2 1.6" opacity="0.8" stroke-width="1.6"/>' +
        '<path d="M3 13.8h18" ' +
        accent +
        ' stroke-width="1.45"/>' +
        "</svg>"
      );
    default:
      return "";
  }
}

function dockLongshotContentHtml(state) {
  if (state === "running") {
    return (
      '<span class="preview-toolbar__dock-export-inner preview-toolbar__dock-export-inner--running">' +
      '<span class="preview-toolbar__longshot__spinner" aria-hidden="true"></span>' +
      '<span class="preview-toolbar__dock-export-label">导出中</span></span>'
    );
  }
  return (
    '<span class="preview-toolbar__dock-export-inner">' +
    dockIconSvg("scroll") +
    '<span class="preview-toolbar__dock-export-label">长图</span></span>'
  );
}

function insertScreenplayControl(parent, beforeNode, opts) {
  if (!parent) return null;
  opts = opts || {};
  var label = opts.label != null ? opts.label : "▶ 全屏放映";
  if (opts.dock) label = "▶";
  var v3Class = opts.v3 ? " preview-toolbar__screenplay--v3" : "";
  var dockClass = opts.dock ? " preview-toolbar__dock-btn preview-toolbar__dock-btn--screenplay preview-toolbar__dock-btn--folio" : "";
  if (document.documentElement.getAttribute("data-screenplay") === "on") {
    var screenplayBtn = document.createElement("button");
    screenplayBtn.type = "button";
    screenplayBtn.className =
      "preview-toolbar__ctl preview-toolbar__screenplay" + v3Class + dockClass;
    screenplayBtn.setAttribute("data-screenplay-trigger", "start");
    screenplayBtn.setAttribute("data-screenplay-label", label);
    screenplayBtn.setAttribute("data-screenplay-busy", "退出放映");
    screenplayBtn.setAttribute("aria-pressed", "false");
    screenplayBtn.setAttribute("aria-label", "全屏放映，逐屏展示");
    screenplayBtn.title = "全屏逐屏放映";
    if (opts.dock) {
      screenplayBtn.innerHTML = dockIconSvg("play");
    } else {
      screenplayBtn.textContent = label;
    }
    parent.insertBefore(screenplayBtn, beforeNode || null);
    return screenplayBtn;
  }
  var href = presentAutoplayHref();
  if (!href) return null;
  var autoplayLink = document.createElement("a");
  autoplayLink.className =
    "preview-toolbar__ctl preview-toolbar__screenplay" + v3Class + dockClass;
  autoplayLink.href = href;
  if (opts.dock) {
    autoplayLink.innerHTML = dockIconSvg("play");
  } else {
    autoplayLink.textContent = label;
  }
  autoplayLink.setAttribute("aria-label", "全屏放映，逐屏展示");
  autoplayLink.title = "全屏逐屏放映";
  parent.insertBefore(autoplayLink, beforeNode || null);
  return autoplayLink;
}

  var DRAWER_FOCUSABLE =
    'a[href],button:not([disabled]),input:not([disabled]),textarea:not([disabled]),select:not([disabled]),[tabindex="0"]';
  var COPY_INTENT_MOODS = ["松弛", "热闹", "赶路", "意外", "仪式感", "平静"];
  var COPY_INTENT_FOCUSES = ["人", "地方", "食物", "关系", "自我感受"];

  function copyIntentApiUrl(tripId, chapterId) {
    return (
      "/__travelogue/trips/" +
      encodeURIComponent(tripId) +
      "/chapters/" +
      encodeURIComponent(chapterId) +
      "/copy-intent"
    );
  }

  function buildCopyIntentChipHtml(values, chipClass) {
    return values
      .map(function (value) {
        return (
          '<button type="button" class="preview-drawer__chip ' +
          chipClass +
          '" data-value="' +
          value +
          '" aria-pressed="false">' +
          value +
          "</button>"
        );
      })
      .join("");
  }

  function trapDrawerFocus(container) {
    function onKeydown(e) {
      if (e.key !== "Tab") return;
      var items = container.querySelectorAll(DRAWER_FOCUSABLE);
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
    container.addEventListener("keydown", onKeydown);
    return function () {
      container.removeEventListener("keydown", onKeydown);
    };
  }

  function tripIdFromPath() {
    var parts = window.location.pathname.replace(/^\/+|\/+$/g, "").split("/");
    return parts[0] || "";
  }

  function tripApiBase(tripId) {
    return "/" + encodeURIComponent(tripId) + "/__travelogue";
  }

  var _toastTimer = null;
  var _longshotDrawerTimer = null;
  var LONGSHOT_DRAWER_AUTO_MS = 3000;

  function clearLongshotDrawerTimer() {
    if (_longshotDrawerTimer) {
      clearTimeout(_longshotDrawerTimer);
      _longshotDrawerTimer = null;
    }
  }

  function scheduleLongshotDrawerAutoHide(root) {
    clearLongshotDrawerTimer();
    _longshotDrawerTimer = setTimeout(function () {
      _longshotDrawerTimer = null;
      hideLongshotDrawer(root);
    }, LONGSHOT_DRAWER_AUTO_MS);
  }

  function toolbarConfirm(opts) {
    if (typeof studioModal === "function") {
      return studioModal(opts);
    }
    var msg = (opts.title ? opts.title + "\n\n" : "") + (opts.body || "");
    return Promise.resolve(window.confirm(msg));
  }

  function toolbarAlert(message, opts) {
    opts = opts || {};
    if (message) showToolbarToast(message, { error: !!opts.error });
  }

  function showToolbarToast(message, opts) {
    opts = opts || {};
    var el = document.getElementById("preview-toolbar-toast");
    if (!el) {
      el = document.createElement("p");
      el.id = "preview-toolbar-toast";
      el.className = "preview-toolbar__toast";
      el.setAttribute("role", "status");
      el.hidden = true;
      document.body.appendChild(el);
    }
    el.textContent = message;
    el.classList.toggle("preview-toolbar__toast--error", !!opts.error);
    el.hidden = false;
    clearTimeout(_toastTimer);
    _toastTimer = setTimeout(function () {
      el.hidden = true;
    }, opts.duration || (opts.error ? 5000 : 2800));
  }

  function maybeShowCoverOpeningStyleToast(tripId) {
    if (!tripId) return;
    var section = document.querySelector(".cover-opening[data-cover-opening]");
    if (!section) return;
    var style = section.getAttribute("data-cover-opening") || "card-br";
    var storageKey = COVER_STYLE_TOAST_KEY + tripId;
    try {
      if (localStorage.getItem(storageKey)) return;
      localStorage.setItem(storageKey, "1");
    } catch (e) {
      return;
    }
    trackStudioEvent("cover_opening_style_render", {
      tripId: tripId,
      coverOpeningStyle: style,
    });
    showToolbarToast(
      "这本游记的封面版式已为你选定（电脑与手机版式不同），可在「排版」设置中更换",
      { duration: 4200 }
    );
  }

  var _layoutPending = false;
  var _pendingDockDismissed = false;
  var _layoutPendingMessage = "";
  var _g1Pending = false;
  var _g1DockDismissed = false;
  var _sheetEditDirty = false;
  var _sheetEditBaseline = "";

  function isPreviewToolbarV4(root) {
    return !!(root && root.classList.contains("preview-toolbar--v4"));
  }

  function isPreviewToolbarV3(root) {
    return !!(
      root &&
      (root.classList.contains("preview-toolbar--v3") ||
        root.classList.contains("preview-toolbar--v4"))
    );
  }

  function dockLongshotIconHtml(state) {
    return dockLongshotContentHtml(state);
  }

  function setDockLongshotAria(btn, state) {
    if (!btn) return;
    if (state === "running") {
      btn.setAttribute("aria-label", "导出中");
      updateDockTip(btn, "导出中…");
    } else {
      btn.setAttribute("aria-label", "导出长图");
      updateDockTip(btn, "导出长图");
    }
  }

  function applyDockLongshotIdle(btn) {
    if (!btn) return;
    btn.innerHTML = dockLongshotIconHtml("idle");
    setDockLongshotAria(btn, "idle");
  }

  function updateDockTip(btn, text) {
    if (btn && btn._dockTipEl) {
      btn._dockTipEl.textContent = text;
    }
  }

  function ensureDockTooltip(btn, label) {
    if (!btn || btn.querySelector(".preview-toolbar__dock-tip")) return;
    btn.classList.add("preview-toolbar__dock-btn--has-tip");
    var tip = document.createElement("span");
    tip.className = "preview-toolbar__dock-tip";
    tip.setAttribute("role", "tooltip");
    tip.textContent = label;
    btn.appendChild(tip);
    btn._dockTipEl = tip;
  }

  function syncDockScreenplayTip(btn) {
    if (!btn || !btn._dockTipEl) return;
    btn._dockTipEl.textContent =
      btn.getAttribute("aria-pressed") === "true" ? "退出放映" : "放映";
  }

  function initDockTooltips(root) {
    if (!isPreviewToolbarV4(root)) return;
    var dock = root.querySelector(".preview-toolbar__dock");
    if (!dock) return;

    ensureDockTooltip(
      dock.querySelector(".preview-toolbar__dock-btn--back"),
      "返回"
    );
    ensureDockTooltip(dock.querySelector(".preview-toolbar__menu-btn"), "编辑与设置");

    var exportBtn = dock.querySelector(".preview-toolbar__dock-btn--export");
    ensureDockTooltip(exportBtn, "导出长图");

    var screenplayBtn = dock.querySelector(".preview-toolbar__screenplay--v3");
    ensureDockTooltip(screenplayBtn, "放映");
    if (screenplayBtn && typeof MutationObserver !== "undefined") {
      syncDockScreenplayTip(screenplayBtn);
      var spObs = new MutationObserver(function () {
        syncDockScreenplayTip(screenplayBtn);
      });
      spObs.observe(screenplayBtn, {
        attributes: true,
        attributeFilter: ["aria-pressed"],
      });
      root._dockScreenplayTipObs = spObs;
    }
  }

  function initDockScrollFade(root) {
    if (!isPreviewToolbarV4(root)) return;
    var dock = root.querySelector(".preview-toolbar__dock");
    var cover = document.querySelector('.cover-opening[data-block="cover-opening"]');
    if (!dock || !cover || typeof IntersectionObserver === "undefined") return;

    var fadeObs = new IntersectionObserver(
      function (entries) {
        var onCover = entries[0] && entries[0].isIntersecting;
        dock.classList.toggle("preview-toolbar__dock--dim", !onCover);
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    fadeObs.observe(cover);
    root._dockFadeObs = fadeObs;
  }

  function snapshotEditPanel(el) {
    if (!el) return "";
    var title = el.querySelector(".preview-drawer__title-input");
    var notes = el.querySelector(".preview-drawer__notes");
    var anchors = [];
    el.querySelectorAll(".preview-drawer__anchor").forEach(function (inp) {
      anchors.push((inp.value || "").trim());
    });
    var mood = el.querySelector(".preview-drawer__chip-mood.is-selected");
    var focus = el.querySelector(".preview-drawer__chip-focus.is-selected");
    var note = el.querySelector(".preview-drawer__copy-intent-note");
    var sub = el.querySelector(".preview-drawer__copy-intent-subsequent");
    return JSON.stringify({
      title: title ? title.value : "",
      notes: notes ? notes.value : "",
      anchors: anchors,
      mood: mood ? mood.getAttribute("data-value") : "",
      focus: focus ? focus.getAttribute("data-value") : "",
      intentNote: note ? note.value : "",
      subsequent: sub ? sub.checked : false,
    });
  }

  function markSheetEditBaseline(root, panel) {
    _sheetEditBaseline = snapshotEditPanel(panel);
    _sheetEditDirty = false;
    if (root) root._sheetEditDirty = false;
  }

  function wireSheetEditDirty(root, panel) {
    if (!panel || panel.dataset.sheetDirtyBound === "1") return;
    panel.dataset.sheetDirtyBound = "1";
    function syncDirty() {
      _sheetEditDirty = snapshotEditPanel(panel) !== _sheetEditBaseline;
      if (root) root._sheetEditDirty = _sheetEditDirty;
    }
    panel.addEventListener("input", syncDirty);
    panel.addEventListener("change", syncDirty);
    panel.querySelectorAll(".preview-drawer__chip-mood, .preview-drawer__chip-focus").forEach(
      function (btn) {
        btn.addEventListener("click", function () {
          window.setTimeout(syncDirty, 0);
        });
      }
    );
  }

  function refreshTaskDockState(root) {
    if (!root || !isPreviewToolbarV3(root) || !root._taskDock) return;
    if (root._exportDockActive || root._exportResultShowing) return;
    if (_g1Pending && !_g1DockDismissed) {
      root._taskDock.showG1({});
      return;
    }
    if (_layoutPending && !_pendingDockDismissed) {
      root._taskDock.showPending({
        title: _layoutPendingMessage || "有编辑尚未应用排版",
      });
      return;
    }
    root._taskDock.hide();
  }

  function setLayoutPending(on) {
    _layoutPending = !!on;
    if (on) _pendingDockDismissed = false;
    document.querySelectorAll(".preview-toolbar__apply-layout").forEach(function (btn) {
      btn.hidden = !_layoutPending;
    });
    document.querySelectorAll(".preview-toolbar__pending-row").forEach(function (row) {
      row.hidden = !_layoutPending;
    });
    var toolbar = document.querySelector(".preview-toolbar");
    if (toolbar && isPreviewToolbarV3(toolbar)) {
      if (toolbar._sheet) toolbar._sheet.setPendingDot(_layoutPending);
      refreshTaskDockState(toolbar);
      if (toolbar._sheet && typeof toolbar._sheet.refreshLayoutTab === "function") {
        toolbar._sheet.refreshLayoutTab();
      }
      return;
    }
    if (toolbar) {
      syncLongshotPreviewRowVisibility(toolbar);
      requestAnimationFrame(function () {
        syncToolbarHeight(toolbar);
      });
    }
  }

  function longshotApi() {
    return window.TravelogueLongshot || null;
  }

  function readStoredLongshotScale() {
    try {
      var s = parseInt(localStorage.getItem(LONGSHOT_SCALE_KEY), 10);
      if (s === 2 || s === 3) return s;
    } catch (e) {}
    return 2;
  }

  function readStoredLongshotMode() {
    try {
      var m = localStorage.getItem(LONGSHOT_MODE_KEY);
      if (m === "full" || m === "chapter") return m;
    } catch (e2) {}
    return "chapter";
  }

  function writeStoredLongshotPrefs(mode, scale) {
    try {
      localStorage.setItem(LONGSHOT_MODE_KEY, mode);
      localStorage.setItem(LONGSHOT_SCALE_KEY, String(scale));
    } catch (e) {}
    var ls = longshotApi();
    if (ls) {
      if (typeof ls.setUserSelectedMode === "function") ls.setUserSelectedMode(mode);
      if (typeof ls.setUserSelectedScale === "function") ls.setUserSelectedScale(scale);
    }
  }

  function readLongshotExportPrefs() {
    var ls = longshotApi();
    var scale =
      ls && typeof ls.getUserSelectedScale === "function"
        ? ls.getUserSelectedScale()
        : readStoredLongshotScale();
    var mode =
      ls && typeof ls.getUserSelectedMode === "function"
        ? ls.getUserSelectedMode()
        : readStoredLongshotMode();
    var captions =
      ls && typeof ls.areCaptionsVisible === "function"
        ? ls.areCaptionsVisible()
        : document.documentElement.getAttribute("data-caption-display") !== "off";
    return {
      scale: scale,
      mode: mode,
      captions: captions,
      copyDisplay: resolveCopyDisplayFromDom(document),
    };
  }

  function formatLongshotExportMetaLabel() {
    var prefs = readLongshotExportPrefs();
    var modeLabel = prefs.mode === "full" ? "完整" : "按章";
    var copyLabel = prefs.copyDisplay === "photos" ? "纯照片" : "完整文案";
    var capLabel = prefs.captions ? "" : " · 无图注";
    return modeLabel + " · " + prefs.scale + "× · " + copyLabel + capLabel;
  }

  function refreshLongshotExportMeta(root) {
    setLongshotExportMeta(root, formatLongshotExportMetaLabel());
  }

  function normalizeSegmentMode(mode) {
    if (mode === "full" || mode === "chapter") return mode;
    return "auto";
  }

  function buildLongshotRequestFromPage(tripId) {
    var prefs = readLongshotExportPrefs();
    return buildLongshotRequest(tripId, {
      scale: prefs.scale,
      format: "png",
      copyDisplay: prefs.copyDisplay,
      segmentMode: normalizeSegmentMode(prefs.mode),
    });
  }

  function isReaderSurfaceMode() {
    return document.documentElement.getAttribute("data-surface-mode") === "reader";
  }

  function syncLongshotPreviewRowVisibility(root) {
    if (!root) return;
    var row = root.querySelector(".preview-toolbar__longshot-preview-row");
    if (!row) return;
    row.hidden = isReaderSurfaceMode() || _layoutPending;
    requestAnimationFrame(function () {
      syncToolbarHeight(root);
    });
  }

  function syncLongshotPreviewChips(root) {
    if (!root) return;
    var html = document.documentElement;
    var photosOnly = html.getAttribute("data-photos-only") === "on";
    var narrativeHidden = html.getAttribute("data-copy-display") === "photos";
    var captionsOn = html.getAttribute("data-caption-display") !== "off";

    root.querySelectorAll("[data-copy-preset]").forEach(function (btn) {
      var on = photosOnly
        ? btn.getAttribute("data-copy-preset") === "photos"
        : btn.getAttribute("data-copy-preset") === "full";
      btn.classList.toggle("is-selected", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });

    var captionChip = root.querySelector('[data-preview-chip="caption"]');
    if (captionChip) {
      captionChip.setAttribute("aria-pressed", captionsOn ? "true" : "false");
      captionChip.textContent = captionsOn ? "图注：开" : "图注：关";
      captionChip.disabled = photosOnly;
    }

    var narrativeChip = root.querySelector('[data-preview-chip="narrative"]');
    if (narrativeChip) {
      var showNarrative = !narrativeHidden;
      narrativeChip.setAttribute("aria-pressed", showNarrative ? "true" : "false");
      narrativeChip.textContent = showNarrative ? "导语：显" : "导语：隐";
      narrativeChip.disabled = photosOnly;
    }

    refreshLongshotExportMeta(root);
  }

  function applyToolbarCopyPreset(root, preset) {
    var html = document.documentElement;
    if (preset === "photos") {
      if (typeof window.travelogueApplyPhotosOnly === "function") {
        window.travelogueApplyPhotosOnly(true);
      } else {
        html.setAttribute("data-photos-only", "on");
      }
      var ls = longshotApi();
      if (ls && typeof ls.applyCaptionDisplay === "function") {
        ls.applyCaptionDisplay(false);
      } else {
        html.setAttribute("data-caption-display", "off");
      }
      try {
        sessionStorage.setItem("travelogue:photosOnly", "on");
      } catch (e) {}
    } else {
      if (typeof window.travelogueApplyPhotosOnly === "function") {
        window.travelogueApplyPhotosOnly(false);
      } else {
        html.removeAttribute("data-photos-only");
      }
      html.removeAttribute("data-copy-display");
      var lsFull = longshotApi();
      if (lsFull && typeof lsFull.applyCaptionDisplay === "function") {
        lsFull.applyCaptionDisplay(true);
      } else {
        html.removeAttribute("data-caption-display");
      }
      try {
        sessionStorage.removeItem("travelogue:photosOnly");
        sessionStorage.setItem("travelogue:copyDisplay", "full");
      } catch (e2) {}
    }
    syncLongshotPreviewChips(root);
  }

  function toggleToolbarNarrative(root) {
    if (document.documentElement.getAttribute("data-photos-only") === "on") return;
    var html = document.documentElement;
    var hidden = html.getAttribute("data-copy-display") === "photos";
    if (hidden) {
      html.removeAttribute("data-copy-display");
      try {
        sessionStorage.setItem("travelogue:copyDisplay", "full");
      } catch (e) {}
    } else {
      html.setAttribute("data-copy-display", "photos");
      try {
        sessionStorage.setItem("travelogue:copyDisplay", "photos");
      } catch (e2) {}
    }
    syncLongshotPreviewChips(root);
  }

  function toggleToolbarCaptions(root) {
    if (document.documentElement.getAttribute("data-photos-only") === "on") return;
    var ls = longshotApi();
    var captionsOn = document.documentElement.getAttribute("data-caption-display") !== "off";
    var next =
      ls && typeof ls.areCaptionsVisible === "function"
        ? !ls.areCaptionsVisible()
        : !captionsOn;
    if (ls && typeof ls.applyCaptionDisplay === "function") {
      ls.applyCaptionDisplay(next);
    } else {
      if (next) document.documentElement.removeAttribute("data-caption-display");
      else document.documentElement.setAttribute("data-caption-display", "off");
    }
    syncLongshotPreviewChips(root);
  }

  function initLongshotPreviewRow(root) {
    var row = root.querySelector(".preview-toolbar__longshot-preview-row");
    if (!row || row.dataset.bound === "1") return;
    row.dataset.bound = "1";

    row.querySelectorAll("[data-copy-preset]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        applyToolbarCopyPreset(root, btn.getAttribute("data-copy-preset"));
      });
    });

    var captionChip = row.querySelector('[data-preview-chip="caption"]');
    if (captionChip) {
      captionChip.addEventListener("click", function () {
        toggleToolbarCaptions(root);
      });
    }

    var narrativeChip = row.querySelector('[data-preview-chip="narrative"]');
    if (narrativeChip) {
      narrativeChip.addEventListener("click", function () {
        toggleToolbarNarrative(root);
      });
    }

    syncLongshotPreviewChips(root);
    syncLongshotPreviewRowVisibility(root);
  }

  var _studioExportPopoverClose = null;

  function closeStudioExportPopover() {
    document.querySelectorAll(".preview-toolbar__export-popover").forEach(function (pop) {
      pop.hidden = true;
    });
    if (_studioExportPopoverClose) {
      document.removeEventListener("click", _studioExportPopoverClose, true);
      _studioExportPopoverClose = null;
    }
  }

  function syncStudioExportPopoverUI(pop) {
    var prefs = readLongshotExportPrefs();
    pop.querySelectorAll("[data-studio-longshot-mode]").forEach(function (btn) {
      var on = btn.getAttribute("data-studio-longshot-mode") === prefs.mode;
      btn.classList.toggle("is-selected", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
    pop.querySelectorAll("[data-studio-longshot-scale]").forEach(function (btn) {
      var on = String(btn.getAttribute("data-studio-longshot-scale")) === String(prefs.scale);
      btn.classList.toggle("is-selected", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  function ensureStudioExportPopover(root) {
    var wrap = root.querySelector(".preview-toolbar__export-zone-wrap");
    if (!wrap) return null;
    var pop = wrap.querySelector(".preview-toolbar__export-popover");
    if (pop) return pop;

    pop = document.createElement("div");
    pop.className = "preview-toolbar__export-popover";
    pop.hidden = true;
    pop.setAttribute("role", "dialog");
    pop.setAttribute("aria-label", "导出设置");
    pop.innerHTML =
      '<p class="preview-toolbar__export-popover-title">导出设置</p>' +
      '<p class="preview-toolbar__export-popover-note">调整范围与清晰度；点左侧「保存长图」开始导出。</p>' +
      '<div class="preview-toolbar__export-popover-field">' +
      '<span class="preview-toolbar__export-popover-label">导出范围</span>' +
      '<div class="preview-toolbar__export-popover-seg" role="group">' +
      '<button type="button" data-studio-longshot-mode="chapter">按章导出</button>' +
      '<button type="button" data-studio-longshot-mode="full">完整长图</button>' +
      "</div></div>" +
      '<div class="preview-toolbar__export-popover-field">' +
      '<span class="preview-toolbar__export-popover-label">清晰度</span>' +
      '<div class="preview-toolbar__export-popover-seg" role="group">' +
      '<button type="button" data-studio-longshot-scale="2">标准 2×</button>' +
      '<button type="button" data-studio-longshot-scale="3">高清 3×</button>' +
      "</div></div>" +
      '<div class="preview-toolbar__export-popover-actions">' +
      '<button type="button" class="preview-toolbar__export-popover-ok" data-action="ok">确定</button>' +
      '<button type="button" class="preview-toolbar__export-popover-cancel" data-action="cancel">取消</button>' +
      "</div>";

    var draftMode = "chapter";
    var draftScale = 2;

    pop.querySelectorAll("[data-studio-longshot-mode]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        draftMode = btn.getAttribute("data-studio-longshot-mode") || "chapter";
        pop.querySelectorAll("[data-studio-longshot-mode]").forEach(function (b) {
          var on = b === btn;
          b.classList.toggle("is-selected", on);
          b.setAttribute("aria-pressed", on ? "true" : "false");
        });
      });
    });
    pop.querySelectorAll("[data-studio-longshot-scale]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        draftScale = parseInt(btn.getAttribute("data-studio-longshot-scale"), 10) || 2;
        pop.querySelectorAll("[data-studio-longshot-scale]").forEach(function (b) {
          var on = b === btn;
          b.classList.toggle("is-selected", on);
          b.setAttribute("aria-pressed", on ? "true" : "false");
        });
      });
    });

    pop.addEventListener("click", function (e) {
      e.stopPropagation();
    });

    pop._applyDraft = function () {
      writeStoredLongshotPrefs(draftMode, draftScale);
    };
    pop._readDraftFromPrefs = function () {
      var prefs = readLongshotExportPrefs();
      draftMode = prefs.mode;
      draftScale = prefs.scale;
      syncStudioExportPopoverUI(pop);
    };

    wrap.appendChild(pop);
    return pop;
  }

  function openStudioLongshotExportPanel(root) {
    return new Promise(function (resolve, reject) {
      var pop = ensureStudioExportPopover(root);
      if (!pop) {
        reject(new Error("no popover"));
        return;
      }
      closeStudioExportPopover();
      pop._readDraftFromPrefs();
      pop.hidden = false;

      function finish(ok) {
        closeStudioExportPopover();
        if (ok) resolve();
        else reject(new Error("cancelled"));
      }

      var okBtn = pop.querySelector('[data-action="ok"]');
      var cancelBtn = pop.querySelector('[data-action="cancel"]');

      function onOk() {
        pop._applyDraft();
        finish(true);
      }
      function onCancel() {
        finish(false);
      }

      okBtn.addEventListener("click", onOk, { once: true });
      cancelBtn.addEventListener("click", onCancel, { once: true });

      _studioExportPopoverClose = function (e) {
        if (pop.contains(e.target)) return;
        if (root.querySelector(".preview-toolbar__longshot-caret") === e.target) return;
        okBtn.removeEventListener("click", onOk);
        cancelBtn.removeEventListener("click", onCancel);
        finish(false);
      };
      window.setTimeout(function () {
        document.addEventListener("click", _studioExportPopoverClose, true);
      }, 0);
    });
  }

  function openLongshotExportOptions(root) {
    var ls = longshotApi();
    if (ls && typeof ls.openExportPanel === "function") {
      ls
        .openExportPanel()
        .then(function () {
          refreshLongshotExportMeta(root);
          syncLongshotPreviewChips(root);
        })
        .catch(function () {});
      return;
    }
    openStudioLongshotExportPanel(root)
      .then(function () {
        refreshLongshotExportMeta(root);
        syncLongshotPreviewChips(root);
      })
      .catch(function () {});
  }

  function revealTripPath(tripId, relPath) {
    return postJson("/__travelogue/reveal", { tripId: tripId, relPath: relPath });
  }

  function longshotProgressPct(job) {
    if (!job || job.status !== "running") return null;
    var cur = Number(job.stageIndex);
    var total = Number(job.stageCount);
    if (!isFinite(cur) || !isFinite(total) || total < 1) return null;
    var hint = String(job.stageHint || "");
    var isChapter = /第\s*\d+\s*\/\s*\d+\s*段/.test(hint);
    if (total === 1 && !isChapter) return 10;
    if (cur <= 0 && total > 1) return 5;
    return Math.min(100, Math.max(0, Math.round((cur / total) * 100)));
  }

  function pollJob(jobId, root, onDone, onSlow, kind) {
    kind = kind || "longshot";
    if (kind === "narrate") {
      if (narratePollCancel) {
        narratePollCancel();
        narratePollCancel = null;
      }
    } else if (longshotPollCancel) {
      longshotPollCancel();
      longshotPollCancel = null;
    }
    var cancelFn = startJobPollInterval(jobId, {
      intervalMs: 800,
      slowMs: SLOW_JOB_MS,
      onSlow: onSlow,
      onTick: function (job) {
        if (
          kind === "longshot" &&
          job.status === "running" &&
          root &&
          jobId === longshotJobId
        ) {
          var pct = longshotProgressPct(job);
          setLongshotExportState(root, "running", {
            hint: job.stageHint ? "正在保存… " + job.stageHint : "正在保存…",
            pct: pct,
          });
        }
      },
      onDone: function (job) {
        if (kind === "narrate") {
          narratePollCancel = null;
        } else {
          longshotPollCancel = null;
          if (jobId === longshotJobId) longshotJobId = null;
        }
        onDone(job);
      },
    });
    if (kind === "narrate") {
      narratePollCancel = cancelFn;
    } else {
      longshotPollCancel = cancelFn;
    }
  }

  function exportZoneEl(root) {
    return root.querySelector(".preview-toolbar__export-zone");
  }

  function longshotBtnEl(root) {
    return (
      root.querySelector(".preview-toolbar__longshot--main") ||
      root.querySelector(".preview-toolbar__longshot")
    );
  }

  function longshotCaretEl(root) {
    return root.querySelector(".preview-toolbar__longshot-caret");
  }

  function setLongshotControlsDisabled(root, disabled) {
    var main = longshotBtnEl(root);
    var caret = longshotCaretEl(root);
    if (main) main.disabled = !!disabled;
    if (caret) caret.disabled = !!disabled;
    if (isPreviewToolbarV3(root)) {
      var menuBtn = root.querySelector(".preview-toolbar__menu-btn");
      if (menuBtn) menuBtn.disabled = !!disabled;
      var screenplayCtl = root.querySelector(".preview-toolbar__screenplay--v3");
      if (screenplayCtl) {
        if (screenplayCtl.tagName === "BUTTON") {
          screenplayCtl.disabled = !!disabled;
        } else {
          screenplayCtl.classList.toggle("preview-toolbar__screenplay--disabled", !!disabled);
          if (disabled) {
            screenplayCtl.setAttribute("aria-disabled", "true");
            screenplayCtl.setAttribute("tabindex", "-1");
          } else {
            screenplayCtl.removeAttribute("aria-disabled");
            screenplayCtl.removeAttribute("tabindex");
          }
        }
      }
    }
  }

  function setLongshotExportMeta(root, text, opts) {
    opts = opts || {};
    var meta = root.querySelector(".preview-toolbar__export-meta");
    if (!meta) return;
    meta.textContent = text || "写入画册目录";
    var actionable = !!opts.actionable;
    meta.classList.toggle("preview-toolbar__export-meta--action", actionable);
    if (actionable) {
      meta.setAttribute("role", "button");
      meta.setAttribute("tabindex", "0");
      meta.title = opts.title || "展开保存结果";
    } else {
      meta.removeAttribute("role");
      meta.removeAttribute("tabindex");
      meta.removeAttribute("title");
    }
  }

  function openLongshotResultDrawer(root) {
    if (isPreviewToolbarV3(root)) {
      if (root._lastLongshotJob && root._taskDock) {
        root._taskDock.showSuccess(root._lastLongshotJob, tripIdFromPath());
      }
      return;
    }
    setToolbarCollapsed(root, false, false);
    clearLongshotDrawerTimer();
    var drawer = root.querySelector(".preview-toolbar__drawer");
    if (!drawer) return;
    if (root._lastLongshotJob && drawer.childElementCount === 0) {
      showLongshotDrawer(root, root._lastLongshotJob, { autoHide: false });
      return;
    }
    drawer.hidden = false;
    requestAnimationFrame(function () {
      syncToolbarHeight(root);
    });
  }

  function bindLongshotExportMeta(root) {
    var meta = root.querySelector(".preview-toolbar__export-meta");
    if (!meta || meta.dataset.bound === "1") return;
    meta.dataset.bound = "1";
    meta.addEventListener("click", function () {
      if (!meta.classList.contains("preview-toolbar__export-meta--action")) return;
      openLongshotResultDrawer(root);
    });
    meta.addEventListener("keydown", function (e) {
      if (!meta.classList.contains("preview-toolbar__export-meta--action")) return;
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openLongshotResultDrawer(root);
      }
    });
  }

  function setLongshotExportProgress(root, visible, pct) {
    var prog = root.querySelector(".preview-toolbar__export-progress");
    var fill = root.querySelector(".preview-toolbar__export-progress-fill");
    if (prog) prog.hidden = !visible;
    if (fill && typeof pct === "number") fill.style.width = pct + "%";
  }

  function longshotSplitEl(root) {
    return root.querySelector(".preview-toolbar__longshot-split");
  }

  function setLongshotSplitState(root, state) {
    var split = longshotSplitEl(root);
    if (!split) return;
    ["idle", "running", "done"].forEach(function (s) {
      split.classList.remove("preview-toolbar__longshot-split--" + s);
    });
    if (state === "running") {
      split.classList.add("preview-toolbar__longshot-split--running");
    } else if (state === "done") {
      split.classList.add("preview-toolbar__longshot-split--done");
    } else {
      split.classList.add("preview-toolbar__longshot-split--idle");
    }
  }

  function setLongshotExportState(root, state, opts) {
    opts = opts || {};
    var zone = exportZoneEl(root);
    var btn = longshotBtnEl(root);
    if (!btn) return;
    var isV3 = isPreviewToolbarV3(root);
    var isDock = isPreviewToolbarV4(root);

    ["idle", "running", "done", "error"].forEach(function (s) {
      btn.classList.remove("preview-toolbar__longshot--" + s);
    });
    btn.classList.remove("preview-toolbar__longshot--primary");
    if (zone) {
      zone.classList.remove("preview-toolbar__export-zone--stale");
      zone.classList.remove("preview-toolbar__export-zone--running");
    }
    var badge = root.querySelector(".preview-toolbar__export-stale");

    if (state === "running") {
      btn.classList.add("preview-toolbar__longshot--running");
      if (!isV3) setLongshotSplitState(root, "running");
      if (zone) zone.classList.add("preview-toolbar__export-zone--running");
      setLongshotControlsDisabled(root, true);
      if (isV3) {
        if (isDock) {
          btn.innerHTML = dockLongshotIconHtml("running");
          setDockLongshotAria(btn, "running");
        } else {
          btn.innerHTML =
            '<span class="preview-toolbar__longshot__spinner" aria-hidden="true"></span> 导出中…';
        }
        root._exportDockActive = true;
        if (root._taskDock) {
          var prefs = readLongshotExportPrefs();
          var modeLabel = prefs.mode === "full" ? "完整" : "按章";
          var sub =
            modeLabel + " · " + prefs.scale + "×" + (opts.hint ? " · " + opts.hint : "");
          root._taskDock.updateExporting({
            title: "正在导出长图",
            subtitle: sub,
            pct: typeof opts.pct === "number" ? opts.pct : 8,
          });
        }
      } else {
        btn.innerHTML =
          '<span class="preview-toolbar__longshot__spinner" aria-hidden="true"></span> 正在保存…';
        setLongshotExportMeta(root, opts.hint || "生成长图中", { actionable: false });
        var pctRun = typeof opts.pct === "number" ? opts.pct : 8;
        setLongshotExportProgress(root, true, pctRun);
      }
      if (badge) badge.hidden = true;
      return;
    }
    if (state === "done") {
      if (isV3) {
        btn.classList.add("preview-toolbar__longshot--idle");
        setLongshotControlsDisabled(root, false);
        if (isDock) {
          btn.innerHTML = dockLongshotIconHtml("idle");
          setDockLongshotAria(btn, "idle");
        } else {
          btn.textContent = "导出长图";
        }
        root._exportDockActive = false;
        if (badge) badge.hidden = true;
        return;
      }
      btn.classList.add("preview-toolbar__longshot--done");
      setLongshotSplitState(root, "done");
      setLongshotControlsDisabled(root, false);
      btn.textContent = "✓ 已保存";
      setLongshotExportMeta(root, "点击查看详情", { actionable: true });
      setLongshotExportProgress(root, false);
      if (badge) badge.hidden = true;
      return;
    }
    if (state === "error") {
      btn.classList.add("preview-toolbar__longshot--idle");
      if (!isV3) setLongshotSplitState(root, "idle");
      setLongshotControlsDisabled(root, false);
      if (isDock) {
        applyDockLongshotIdle(btn);
      } else {
        btn.textContent = isV3 ? "导出长图" : "保存长图";
      }
      if (isV3) {
        root._exportDockActive = false;
        if (root._taskDock) root._taskDock.showError(opts.hint || "保存失败，请重试");
      } else {
        setLongshotExportMeta(root, opts.hint || "保存失败，请重试", { actionable: false });
        setLongshotExportProgress(root, false);
      }
      if (badge) badge.hidden = true;
      return;
    }
    if (state === "stale") {
      btn.classList.add("preview-toolbar__longshot--idle");
      if (!isV3) setLongshotSplitState(root, "idle");
      setLongshotControlsDisabled(root, false);
      if (isDock) {
        applyDockLongshotIdle(btn);
      } else {
        btn.textContent = isV3 ? "导出长图" : "保存长图";
      }
      if (zone) zone.classList.add("preview-toolbar__export-zone--stale");
      if (isV3) {
        btn.classList.add("preview-toolbar__longshot--stale");
        if (badge) badge.hidden = true;
      } else {
        if (badge) badge.hidden = false;
        setLongshotExportMeta(root, "内容已更新", { actionable: false });
        setLongshotExportProgress(root, false);
      }
      return;
    }
    btn.classList.add("preview-toolbar__longshot--idle");
    if (!isV3) setLongshotSplitState(root, "idle");
    setLongshotControlsDisabled(root, false);
    if (isDock) {
      applyDockLongshotIdle(btn);
    } else {
      btn.textContent = isV3 ? "导出长图" : "保存长图";
    }
    btn.classList.remove("preview-toolbar__longshot--stale");
    root._exportDockActive = false;
    if (badge) badge.hidden = true;
    if (!isV3) {
      refreshLongshotExportMeta(root);
      setLongshotExportProgress(root, false);
    }
  }

  function hideLongshotDrawer(root) {
    clearLongshotDrawerTimer();
    var drawer = root.querySelector(".preview-toolbar__drawer");
    if (!drawer) return;
    drawer.hidden = true;
    requestAnimationFrame(function () {
      syncToolbarHeight(root);
    });
  }

  function getLongshotDrawer(root) {
    var drawer = root.querySelector(".preview-toolbar__drawer");
    if (drawer) return drawer;
    drawer = document.createElement("div");
    drawer.className = "preview-toolbar__drawer";
    drawer.id = "preview-toolbar-longshot-drawer";
    drawer.setAttribute("role", "status");
    drawer.hidden = true;
    var body = toolbarBody(root);
    var pending = body.querySelector(".preview-toolbar__pending-row");
    if (pending) {
      body.insertBefore(drawer, pending.nextSibling);
    } else {
      var bar = body.querySelector(".preview-toolbar__bar");
      if (bar) body.insertBefore(drawer, bar.nextSibling);
      else body.appendChild(drawer);
    }
    return drawer;
  }

  function setSlowHint(root, text, visible) {
    var el = root.querySelector(".preview-toolbar__slow-hint");
    if (!el) {
      el = document.createElement("span");
      el.className = "preview-toolbar__slow-hint";
      el.hidden = true;
      var actions = root.querySelector(".preview-toolbar__actions");
      if (actions) actions.appendChild(el);
    }
    el.hidden = !visible;
    el.textContent = text || "";
  }

  function toolbarBody(root) {
    return root.querySelector(".preview-toolbar__body") || root;
  }

  function syncToolbarHeight(root) {
    if (isPreviewToolbarV4(root)) {
      root.style.height = "";
      document.documentElement.style.setProperty("--preview-toolbar-h", "0px");
      return;
    }
    if (isPreviewToolbarV3(root)) {
      root.style.height = "";
      document.documentElement.style.setProperty("--preview-toolbar-h", "48px");
      return;
    }
    var collapsed = root.classList.contains("preview-toolbar--collapsed");
    var strip = root.querySelector(".preview-toolbar__collapsed-strip");
    if (collapsed) {
      var sh = (strip && strip.offsetHeight) || 32;
      root.style.height = sh + "px";
      document.documentElement.style.setProperty("--preview-toolbar-h", sh + "px");
      return;
    }
    root.style.height = "";
    document.documentElement.style.setProperty(
      "--preview-toolbar-h",
      (root.offsetHeight || 56) + "px"
    );
  }

  function setToolbarCollapsed(root, collapsed, persist) {
    root.classList.toggle("preview-toolbar--collapsed", collapsed);
    document.documentElement.setAttribute(
      "data-preview-toolbar-collapsed",
      collapsed ? "on" : "off"
    );
    var handle = root.querySelector(".preview-toolbar__handle");
    var collapseBtn = root.querySelector(".preview-toolbar__collapse");
    if (handle) {
      handle.setAttribute("aria-expanded", collapsed ? "false" : "true");
    }
    if (collapseBtn) {
      collapseBtn.setAttribute("aria-expanded", collapsed ? "false" : "true");
    }
    if (persist !== false) {
      try {
        localStorage.setItem(COLLAPSE_KEY, collapsed ? "1" : "0");
      } catch (e) {}
    }
    requestAnimationFrame(function () {
      syncToolbarHeight(root);
    });
  }

  function toggleToolbarCollapsed(root) {
    setToolbarCollapsed(root, !root.classList.contains("preview-toolbar--collapsed"));
  }

  function bindToolbarCollapse(root) {
    var handle = root.querySelector(".preview-toolbar__handle");
    var collapseBtn = root.querySelector(".preview-toolbar__collapse");
    if (handle) {
      handle.addEventListener("click", function () {
        setToolbarCollapsed(root, false);
      });
    }
    if (collapseBtn) {
      collapseBtn.addEventListener("click", function () {
        setToolbarCollapsed(root, true);
      });
    }
    if (typeof ResizeObserver !== "undefined") {
      var ro = new ResizeObserver(function () {
        syncToolbarHeight(root);
      });
      ro.observe(root);
    }
    window.addEventListener("resize", function () {
      syncToolbarHeight(root);
    });
  }

  function showLongshotDrawer(root, job, opts) {
    opts = opts || {};
    root._lastLongshotJob = job;
    if (isPreviewToolbarV3(root)) {
      hideLongshotDrawer(root);
      root._exportResultShowing = true;
      if (root._taskDock) {
        root._taskDock.showSuccess(job, tripIdFromPath());
      }
      if (job.status === "failed") {
        setLongshotExportState(root, "error", {
          hint: (job.error && (job.error.message || job.error.code)) || "导出失败",
        });
      } else {
        setLongshotExportState(root, "idle");
      }
      hideStaleHint(root);
      return;
    }
    var tripId = tripIdFromPath();
    var drawer = getLongshotDrawer(root);
    setToolbarCollapsed(root, false, false);
    drawer.hidden = false;
    drawer.textContent = "";

    var head = document.createElement("div");
    head.className = "preview-toolbar__drawer-head";
    var title = document.createElement("p");
    title.className = "preview-toolbar__drawer-title";
    var closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "preview-toolbar__drawer-close";
    closeBtn.setAttribute("aria-label", "关闭");
    closeBtn.textContent = "×";
    closeBtn.addEventListener("click", function () {
      hideLongshotDrawer(root);
    });
    head.appendChild(title);
    head.appendChild(closeBtn);
    drawer.appendChild(head);

    if (job.status === "failed") {
      title.textContent = "保存失败";
      var err = (job.error && (job.error.message || job.error.code)) || "导出失败";
      var errEl = document.createElement("p");
      errEl.className = "preview-toolbar__longshot-error";
      errEl.textContent = err;
      drawer.appendChild(errEl);
      requestAnimationFrame(function () {
        syncToolbarHeight(root);
      });
      return;
    }

    title.textContent = "✓ 长图已保存";

    var result = job.result || {};
    var outputs = result.outputs || [];
    var method = result.captureMethod || "p0";
    var segmented = result.segmented || outputs.length > 1;

    var homeHint = document.createElement("p");
    homeHint.className = "preview-toolbar__longshot-compat";
    homeHint.textContent = "已写入画册目录；返回 Studio 首页即可在手机框预览。";
    drawer.appendChild(homeHint);

    if (segmented && outputs.length > 1) {
      var segEl = document.createElement("p");
      segEl.className = "preview-toolbar__longshot-compat";
      segEl.textContent =
        result.userHint ||
        "已按章导出 " + outputs.length + " 张，底部含页码（如 2/5）便于微信按序发送。";
      drawer.appendChild(segEl);
    }
    if (method === "p1") {
      var compatEl = document.createElement("p");
      compatEl.className = "preview-toolbar__longshot-compat";
      compatEl.textContent = "已使用兼容模式导出，与预览可能有细微差异。";
      drawer.appendChild(compatEl);
    }

    var actions = document.createElement("div");
    actions.className = "preview-toolbar__drawer-actions";

    if (outputs.length) {
      var list = document.createElement("ul");
      list.className = "preview-toolbar__longshot-paths";
      outputs.forEach(function (rel) {
        var li = document.createElement("li");
        li.textContent = rel;
        list.appendChild(li);
      });
      drawer.appendChild(list);

      var revealBtn = document.createElement("button");
      revealBtn.type = "button";
      revealBtn.className = "preview-toolbar__reveal";
      revealBtn.textContent = "在文件夹中显示";
      revealBtn.addEventListener("click", function () {
        revealTripPath(tripId, outputs[0]);
      });
      actions.appendChild(revealBtn);
    }

    var dismissBtn = document.createElement("button");
    dismissBtn.type = "button";
    dismissBtn.className = "preview-toolbar__drawer-secondary";
    dismissBtn.textContent = "收起";
    dismissBtn.addEventListener("click", function () {
      hideLongshotDrawer(root);
    });
    actions.appendChild(dismissBtn);
    drawer.appendChild(actions);

    hideStaleHint(root);
    if (opts.autoHide !== false) {
      scheduleLongshotDrawerAutoHide(root);
    }
    requestAnimationFrame(function () {
      syncToolbarHeight(root);
    });
  }

  function showStaleHint(root) {
    setLongshotExportState(root, "stale");
  }

  function hideStaleHint(root) {
    var btn = longshotBtnEl(root);
    if (btn && btn.classList.contains("preview-toolbar__longshot--done")) return;
    setLongshotExportState(root, "idle");
  }

  function refreshStaleHint(root, tripId) {
    fetch("/__travelogue/trips")
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        var trips = data.trips || [];
        var trip = trips.filter(function (t) { return t.tripId === tripId; })[0];
        if (!trip) return;
        if (trip.layoutCssStale) {
          _layoutPendingMessage = "布局 CSS 已过期，请应用排版重新渲染";
          var pendingText = root.querySelector(".preview-toolbar__pending-text");
          if (pendingText) {
            pendingText.textContent = _layoutPendingMessage;
          }
          setLayoutPending(true);
          return;
        }
        _layoutPendingMessage = "";
        if (trip.longshotStale) {
          showStaleHint(root);
        }
      })
      .catch(function () {});
  }

  function toggleAdvancedMenu(root) {
    var menu = root.querySelector(".preview-toolbar__menu");
    if (!menu) return;
    menu.hidden = !menu.hidden;
  }

  function exportZip(tripId) {
    toolbarConfirm({
      title: "导出 zip",
      body: "导出 zip 包用于自行托管或备份，不是微信分享主路径。继续？",
      confirmText: "继续",
    }).then(function (ok) {
      if (!ok) return;
      return postJson("/__travelogue/export", { tripId: tripId, confirmPrivacy: true });
    }).then(function (res) {
      if (!res) return;
      if (res.status !== 200 || !res.body.ok) {
        toolbarAlert((res.body && res.body.message) || "导出失败", { error: true });
        return;
      }
      var zipRel = res.body.zipRelPath;
      if (!zipRel) return;
      return toolbarConfirm({
        title: "zip 已生成",
        body: "是否在文件夹中显示？",
        confirmText: "显示",
        cancelText: "关闭",
      }).then(function (reveal) {
        if (reveal) revealTripPath(tripId, zipRel);
      });
    }).catch(function () {
      toolbarAlert("导出失败", { error: true });
    });
  }

  function startLongshot(root, tripId) {
    var btn = longshotBtnEl(root);
    if (!btn || btn.disabled) return;
    setToolbarCollapsed(root, false, false);
    hideLongshotDrawer(root);
    setLongshotExportState(root, "running", { hint: "正在保存…" });
    setSlowHint(root, "", false);

    postJsonBusyRetry("/__travelogue/longshot", buildLongshotRequestFromPage(tripId), {
      onBusy: function () {
        setLongshotExportState(root, "running", { hint: "排队中，请稍候…" });
      },
    })
      .then(function (res) {
        if (isJobBusy409(res)) {
          setLongshotExportState(root, "running", { hint: "排队中，请稍候…" });
          return;
        }
        if (res.status === 409) {
          setLongshotExportState(root, "error", {
            hint: (res.body && res.body.message) || "请稍候再试",
          });
          return;
        }
        if (res.status !== 202 || !res.body.jobId) {
          setLongshotExportState(root, "error", { hint: "无法开始导出" });
          return;
        }
        longshotJobId = res.body.jobId;
        pollJob(
          res.body.jobId,
          root,
          function (job) {
            setSlowHint(root, "", false);
            if (job.status === "succeeded") {
              setLongshotExportState(root, "done");
              showLongshotDrawer(root, job);
            } else if (job.status === "failed") {
              setLongshotExportState(root, "error");
              showLongshotDrawer(root, job);
            } else {
              setLongshotExportState(root, "idle");
            }
          },
          function () {
            setSlowHint(root, "比预期久一些，请耐心等待…", true);
          }
        );
      })
      .catch(function () {
        setLongshotExportState(root, "error", { hint: "网络错误" });
      });
  }

  function startLlmNarrate(root, tripId, btn) {
    if (!btn || btn.disabled) return;
    toolbarConfirm({
      title: "生成杂志感文案",
      body: "将调用 LLM 重写 hook、导语与图注，可能覆盖未锁定的文案。继续？",
      confirmText: "继续",
    }).then(function (ok) {
      if (!ok) return;
      setToolbarCollapsed(root, false, false);
      btn.disabled = true;
      setSlowHint(root, "", false);
      setSlowHint(root, "正在生成杂志感文案…", true);
      return postJson("/__travelogue/narrate", { tripId: tripId });
    }).then(function (res) {
      if (!res) return;
      if (res.status === 409 || res.status === 400) {
        setSlowHint(root, (res.body && res.body.message) || "无法开始", true);
        btn.disabled = false;
        return;
      }
      if (res.status !== 202 || !res.body.jobId) {
        setSlowHint(root, "无法开始文案生成", true);
        btn.disabled = false;
        return;
      }
      narrateJobId = res.body.jobId;
      pollJob(
        res.body.jobId,
        root,
        function (job) {
          btn.disabled = false;
          narrateJobId = null;
          setSlowHint(root, "", false);
          if (job.status === "succeeded") {
            window.location.reload();
            return;
          }
          var err = (job.error && (job.error.message || job.error.code)) || "文案生成失败";
          toolbarAlert(err, { error: true });
        },
        function () {
          setSlowHint(root, "比预期久一些，请耐心等待…", true);
        },
        "narrate"
      );
    }).catch(function () {
      btn.disabled = false;
      setSlowHint(root, "网络错误", true);
    });
  }

  function refreshPreviewCover(root) {
    var body = toolbarBody(root);
    var card = body.querySelector(".preview-toolbar__preview-card");
    if (card) card.remove();
  }

  function applyLayoutRerender(tripId, root) {
    var btn = root.querySelector(".preview-toolbar__apply-layout");
    var pendingBtn = root.querySelector(".preview-toolbar__pending-apply");
    if (btn) btn.disabled = true;
    if (pendingBtn) pendingBtn.disabled = true;
    return postJson(tripApiBase(tripId) + "/rerender", {})
      .then(function (res) {
        if (btn) btn.disabled = false;
        if (pendingBtn) pendingBtn.disabled = false;
        if (res.status !== 200 || !res.body.ok) {
          showToolbarToast((res.body && res.body.error) || "排版失败", { error: true });
          return;
        }
        setLayoutPending(false);
        showToolbarToast("排版已更新");
        window.location.reload();
      })
      .catch(function () {
        if (btn) btn.disabled = false;
        if (pendingBtn) pendingBtn.disabled = false;
        showToolbarToast("排版失败", { error: true });
      });
  }

  function saveMagazineTitle(tripId, next, el, onDone) {
    var prev = (el.dataset.title || el.textContent || "").trim();
    if (next === prev) {
      if (onDone) onDone(false);
      return;
    }
    el.classList.add("preview-toolbar__title--saving");
    if (el.classList.contains("cover-opening__title")) {
      el.classList.add("cover-opening__title--saving");
    }
    postJson(tripApiBase(tripId) + "/save-copy", {
      patches: [{ path: "meta.title", value: next }],
    })
      .then(function (res) {
        el.classList.remove("preview-toolbar__title--saving");
        el.classList.remove("cover-opening__title--saving");
        if (res.status !== 200 || !res.body.ok) {
          showToolbarToast((res.body && res.body.error) || "保存失败", { error: true });
          if (onDone) onDone(false);
          return;
        }
        el.textContent = next;
        el.dataset.title = next;
        showToolbarToast("杂志名已保存");
        try {
          window.dispatchEvent(new CustomEvent("travelogue:copy-saved"));
        } catch (e0) {}
        if (res.body.rendered && res.body.rendered.length) {
          window.location.reload();
          return;
        }
        if (onDone) onDone(true);
      })
      .catch(function () {
        el.classList.remove("preview-toolbar__title--saving");
        el.classList.remove("cover-opening__title--saving");
        showToolbarToast("保存失败", { error: true });
        if (onDone) onDone(false);
      });
  }

  function initCoverTitleEdit(tripId) {
    if (isSharePreview()) return;
    var titleEl = document.querySelector(".cover-opening__title");
    if (!titleEl || titleEl.dataset.coverTitleEdit === "on") return;
    titleEl.dataset.coverTitleEdit = "on";
    titleEl.classList.add("cover-opening__title--editable");
    titleEl.setAttribute("role", "button");
    titleEl.setAttribute("tabindex", "0");
    titleEl.setAttribute("aria-label", "点击编辑杂志名");
    titleEl.title = "点击编辑杂志名";
    titleEl.dataset.title = (titleEl.textContent || "").trim();

    fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (data && data.intentSummary && data.intentSummary.title) {
          var t = String(data.intentSummary.title).trim();
          titleEl.textContent = t;
          titleEl.dataset.title = t;
        }
      })
      .catch(function () {});

    function openEditor() {
      if (titleEl.classList.contains("cover-opening__title--saving")) return;
      if (titleEl.parentElement.querySelector(".cover-opening__title-input")) return;
      var input = document.createElement("input");
      input.type = "text";
      input.className = "cover-opening__title-input";
      input.maxLength = 20;
      input.value = titleEl.dataset.title || titleEl.textContent || "";
      titleEl.hidden = true;
      titleEl.parentElement.insertBefore(input, titleEl.nextSibling);
      input.focus();
      input.select();

      function finish(save) {
        var next = (input.value || "").trim();
        input.remove();
        titleEl.hidden = false;
        if (!save) {
          titleEl.textContent = titleEl.dataset.title || titleEl.textContent;
          return;
        }
        if (next.length > 20) {
          showToolbarToast("杂志名最多 20 个字", { error: true });
          return;
        }
        if (!next) {
          showToolbarToast("杂志名不能为空", { error: true });
          return;
        }
        saveMagazineTitle(tripId, next, titleEl);
      }

      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          finish(true);
        }
        if (e.key === "Escape") {
          e.preventDefault();
          finish(false);
        }
      });
      input.addEventListener("blur", function () {
        finish(true);
      });
    }

    titleEl.addEventListener("click", openEditor);
    titleEl.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openEditor();
      }
    });
  }

  function initTitleEdit(root, tripId) {
    var wrap = root.querySelector(".preview-toolbar__title-wrap");
    if (!wrap) return;

    var display = document.createElement("button");
    display.type = "button";
    display.className = "preview-toolbar__title";
    display.title = "点击编辑杂志名";
    display.textContent = "我的旅途";
    wrap.appendChild(display);

    function setTitle(text) {
      var t = (text || "我的旅途").trim() || "我的旅途";
      display.textContent = t.length > 20 ? t.slice(0, 20) : t;
      display.dataset.title = t;
    }

    fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (data && data.intentSummary && data.intentSummary.title) {
          setTitle(data.intentSummary.title);
        }
      })
      .catch(function () {});

    display.addEventListener("click", function () {
      if (wrap.querySelector(".preview-toolbar__title-input")) return;
      var input = document.createElement("input");
      input.type = "text";
      input.className = "preview-toolbar__title-input";
      input.maxLength = 20;
      input.value = display.dataset.title || display.textContent || "";
      display.hidden = true;
      wrap.appendChild(input);
      input.focus();
      input.select();

      function finish(save) {
        var next = (input.value || "").trim();
        input.remove();
        display.hidden = false;
        if (!save) {
          setTitle(display.dataset.title || display.textContent);
          return;
        }
        if (next.length > 20) {
          showToolbarToast("杂志名最多 20 个字", { error: true });
          return;
        }
        if (!next) {
          showToolbarToast("杂志名不能为空", { error: true });
          return;
        }
        var prev = (display.dataset.title || "").trim();
        if (next === prev) {
          setTitle(next);
          return;
        }
        display.classList.add("preview-toolbar__title--saving");
        saveMagazineTitle(tripId, next, display, function () {
          display.classList.remove("preview-toolbar__title--saving");
          setTitle(next);
        });
      }

      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          finish(true);
        }
        if (e.key === "Escape") {
          e.preventDefault();
          finish(false);
        }
      });
      input.addEventListener("blur", function () {
        finish(true);
      });
    });
  }

  var AESTHETIC_STRATUM_LABELS = {
    person: "人像",
    landscape: "风景",
    food: "美食",
    group: "合影",
    general: "通用",
  };
  var AESTHETIC_PURPOSE_LABELS = {
    cover: "封面",
    hero: "主图",
    moment: "瞬间",
  };

  function formatAestheticPurposeLine(row) {
    var purposes = row && row.purposes;
    if (!purposes) return "";
    return ["cover", "hero", "moment"]
      .filter(function (p) { return purposes[p] != null; })
      .map(function (p) {
        var label = (row.purposeLabels && row.purposeLabels[p]) || AESTHETIC_PURPOSE_LABELS[p] || p;
        return label + " " + Math.round(Number(purposes[p]) * 100);
      })
      .join(" · ");
  }

  function renderAestheticAlbumProfile(container, profile, pref, tripId) {
    if (!profile || !container) return;
    var block = document.createElement("div");
    block.className = "preview-drawer__aesthetic-album";
    var head = document.createElement("p");
    head.className = "preview-drawer__aesthetic-head";
    var skew = profile.isSkewed ? " · 层偏斜" : "";
    head.textContent =
      "成册分层 · 主层 " +
      (profile.dominantLabel || profile.dominantStratum || "—") +
      skew;
    block.appendChild(head);
    var meta = document.createElement("p");
    meta.className = "preview-drawer__aesthetic-meta";
    var parts = [];
    var pct = profile.strataPct || {};
    Object.keys(pct).forEach(function (key) {
      var label =
        (profile.strataLabels && profile.strataLabels[key]) ||
        AESTHETIC_STRATUM_LABELS[key] ||
        key;
      parts.push(label + " " + pct[key] + "%");
    });
    meta.textContent = parts.length ? parts.join(" · ") : "—";
    block.appendChild(meta);
    if (pref && pref.options && pref.options.length) {
      var hint = document.createElement("p");
      hint.className = "preview-drawer__aesthetic-meta";
      hint.textContent = pref.selectionHint || "";
      block.appendChild(hint);
      var prefRow = document.createElement("div");
      prefRow.className = "preview-drawer__aesthetic-pref";
      pref.options.forEach(function (opt) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "preview-drawer__aesthetic-pref-btn";
        if (opt.value === pref.value) btn.classList.add("is-active");
        btn.textContent = opt.label || opt.value;
        btn.addEventListener("click", function () {
          if (opt.value === pref.value) return;
          patchJson(
            "/__travelogue/trips/" +
              encodeURIComponent(tripId) +
              "/aesthetic/preference",
            { stratumPreference: opt.value }
          ).then(function (result) {
            var data = result && (result.data || result.body);
            if (!data || !data.ok) return;
            renderAestheticAlbumProfile(container, profile, data.stratumPreference, tripId);
          });
        });
        prefRow.appendChild(btn);
      });
      block.appendChild(prefRow);
      if (pref.recurateHint) {
        var recurate = document.createElement("p");
        recurate.className = "preview-drawer__aesthetic-meta";
        recurate.textContent = pref.recurateHint;
        block.appendChild(recurate);
      }
    }
    container.querySelectorAll(".preview-drawer__aesthetic-album").forEach(function (node) {
      node.remove();
    });
    container.appendChild(block);
  }

  function loadAestheticExplain(tripId, container) {
    if (!container) return;
    fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/aesthetic")
      .then(function (resp) { return resp.ok ? resp.json() : null; })
      .then(function (data) {
        if (!data || !data.ok || !data.enabled) {
          container.hidden = true;
          return;
        }
        var assets = data.assets || [];
        if (!assets.length) {
          container.hidden = true;
          return;
        }
        container.hidden = false;
        container.innerHTML = "";
        renderExplainBlock(container, "照片审美分项", {
          summary:
            "已评分 " +
            (data.scoredCount != null ? data.scoredCount : assets.length) +
            " 张 · 成册中各图分层 / purpose / top-3 维度",
          details: [],
        });
        if (data.albumProfile) {
          renderAestheticAlbumProfile(
            container,
            data.albumProfile,
            data.stratumPreference,
            tripId
          );
        }
        assets.forEach(function (row) {
          var block = document.createElement("div");
          block.className = "preview-drawer__aesthetic-asset";
          var head = document.createElement("p");
          head.className = "preview-drawer__aesthetic-head";
          var overall =
            row.overall != null ? Math.round(Number(row.overall) * 100) + " 分" : "—";
          var stratum = row.stratumLabel || row.stratum || "";
          head.textContent =
            (row.id || "?") +
            " · overall " +
            overall +
            (stratum ? " · " + stratum : "");
          block.appendChild(head);
          var purposeLine = formatAestheticPurposeLine(row);
          if (purposeLine) {
            var purposeMeta = document.createElement("p");
            purposeMeta.className = "preview-drawer__aesthetic-meta";
            purposeMeta.textContent = purposeLine;
            block.appendChild(purposeMeta);
          }
          if (row.mllmScore != null) {
            var mllmMeta = document.createElement("p");
            mllmMeta.className = "preview-drawer__aesthetic-meta";
            mllmMeta.textContent =
              "MLLM " + Math.round(Number(row.mllmScore) * 100) + " 分";
            block.appendChild(mllmMeta);
          }
          if (row.critique) {
            var critique = document.createElement("p");
            critique.className = "preview-drawer__aesthetic-critique";
            critique.textContent =
              typeof row.critique === "string"
                ? row.critique
                : row.critique.summary || row.critique.text || "";
            block.appendChild(critique);
          }
          var list = document.createElement("ul");
          list.className = "preview-drawer__explain-list";
          (row.explain || []).forEach(function (item) {
            var li = document.createElement("li");
            li.textContent = item.reason || item.label || item.code || "";
            list.appendChild(li);
          });
          block.appendChild(list);
          container.appendChild(block);
        });
      })
      .catch(function () {
        container.hidden = true;
      });
  }

  function initDisplayedAestheticTitles(tripId) {
    fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/aesthetic")
      .then(function (resp) { return resp.ok ? resp.json() : null; })
      .then(function (data) {
        if (!data || !data.ok || !data.enabled) return;
        var byId = {};
        (data.assets || []).forEach(function (row) {
          if (row && row.id) byId[row.id] = row;
        });
        document
          .querySelectorAll('.layout-screen[data-block="layout-screen"][data-asset-ids]')
          .forEach(function (screen) {
            var aid = (screen.getAttribute("data-asset-ids") || "").split(",")[0];
            var row = byId[aid];
            if (!row || !row.explain || !row.explain.length) return;
            var img = screen.querySelector("img");
            if (!img) return;
            var tips = row.explain
              .map(function (item) { return item.reason || item.label; })
              .filter(Boolean)
              .join("；");
            var pct = row.overall != null ? Math.round(Number(row.overall) * 100) : null;
            var stratum = row.stratumLabel || row.stratum || "";
            var purposeLine = formatAestheticPurposeLine(row);
            img.setAttribute(
              "title",
              [
                pct != null ? "审美 " + pct : "",
                stratum ? stratum : "",
                purposeLine,
                tips,
              ]
                .filter(Boolean)
                .join(" · ")
            );
          });
      })
      .catch(function () { /* fail-open */ });
  }

  function fetchEntry(tripId) {
    return fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry")
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; });
  }

  function currentChapterId() {
    var sections = document.querySelectorAll("section.chapter[data-chapter-id]");
    var best = null;
    var bestVis = 0;
    sections.forEach(function (sec) {
      var rect = sec.getBoundingClientRect();
      var vis = Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0);
      if (vis > bestVis) {
        bestVis = vis;
        best = sec.getAttribute("data-chapter-id");
      }
    });
    return best;
  }

  function renderExplainBlock(container, title, block) {
    if (!container || !block || !block.summary) return;
    var head = document.createElement("h3");
    head.className = "preview-drawer__subhead";
    head.textContent = title;
    container.appendChild(head);
    var lead = document.createElement("p");
    lead.className = "preview-drawer__explain-lead";
    lead.textContent = block.summary;
    container.appendChild(lead);
    if (block.details && block.details.length) {
      var list = document.createElement("ul");
      list.className = "preview-drawer__explain-list";
      block.details.forEach(function (line) {
        var li = document.createElement("li");
        li.textContent = line;
        list.appendChild(li);
      });
      container.appendChild(list);
    }
  }

  function loadChapterExplain(tripId, container) {
    if (!container) return;
    fetch("/__travelogue/chapter-layout?tripId=" + encodeURIComponent(tripId))
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        if (!data || !data.ok || !data.summary) {
          container.textContent = "暂无分章说明";
          return;
        }
        container.innerHTML = "";
        renderExplainBlock(container, "为什么这样分章？", {
          summary: data.summary,
          details: data.details,
        });
        if (data.layoutExplain) {
          renderExplainBlock(container, "排版引擎", data.layoutExplain);
        }
      })
      .catch(function () {
        container.textContent = "无法加载分章说明";
      });
  }

  function initPreviewDrawers(root, tripId) {
    var shell = document.createElement("div");
    shell.className = "preview-drawer-root";
    shell.hidden = true;
    shell.innerHTML =
      '<div class="preview-drawer__scrim"></div>' +
      '<div class="preview-drawer" role="dialog" aria-modal="true" aria-labelledby="preview-drawer-title" hidden>' +
      '<div class="preview-drawer__handle" aria-hidden="true"></div>' +
      '<div class="preview-drawer__head">' +
      '<h2 id="preview-drawer-title" class="preview-drawer__title"></h2>' +
      '<button type="button" class="preview-drawer__close" aria-label="关闭">×</button>' +
      "</div>" +
      '<div class="preview-drawer__body"></div>' +
      "</div>";
    document.body.appendChild(shell);

    var drawer = shell.querySelector(".preview-drawer");
    var titleEl = shell.querySelector(".preview-drawer__title");
    var bodyEl = shell.querySelector(".preview-drawer__body");
    var drawerBodyEl = bodyEl;
    var scrim = shell.querySelector(".preview-drawer__scrim");
    var closeBtn = shell.querySelector(".preview-drawer__close");
    var entryCache = null;
    var drawerFocusRelease = null;
    var drawerPreviousFocus = null;
    var drawerEmbedTarget = null;

    var editTpl =
      '<label class="preview-drawer__label" for="preview-drawer-title-input">杂志名</label>' +
      '<input id="preview-drawer-title-input" class="preview-drawer__title-input" type="text" maxlength="20" autocomplete="off" placeholder="我的旅途">' +
      '<label class="preview-drawer__label" for="preview-drawer-notes">写给编辑的一句话</label>' +
      '<textarea id="preview-drawer-notes" class="preview-drawer__notes" maxlength="' +
      STUDIO_USER_NOTES_MAX_LEN +
      '" rows="3" placeholder="例如：带娃慢走，想突出雨后的京都"></textarea>' +
      '<p class="preview-drawer__chapter-label">当前章：<strong class="preview-drawer__chapter-name"></strong></p>' +
      '<p class="preview-drawer__label">记忆锚点（0–3 个）</p>' +
      '<div class="preview-drawer__anchors">' +
      '<input type="text" class="preview-drawer__anchor" maxlength="24" placeholder="锚点 1">' +
      '<input type="text" class="preview-drawer__anchor" maxlength="24" placeholder="锚点 2">' +
      '<input type="text" class="preview-drawer__anchor" maxlength="24" placeholder="锚点 3">' +
      "</div>" +
      '<p class="preview-drawer__hint">短词即可，会写进图说，不会瞎编</p>' +
      '<details class="preview-drawer__copy-intent">' +
      '<summary class="preview-drawer__label">章级意图（可选）</summary>' +
      '<p class="preview-drawer__sublabel">这一章更像什么感觉？</p>' +
      '<div class="preview-drawer__chips preview-drawer__chips--mood" role="group" aria-label="章级情绪">' +
      buildCopyIntentChipHtml(COPY_INTENT_MOODS, "preview-drawer__chip-mood") +
      "</div>" +
      '<p class="preview-drawer__sublabel">更想突出什么？</p>' +
      '<div class="preview-drawer__chips preview-drawer__chips--focus" role="group" aria-label="章级关注点">' +
      buildCopyIntentChipHtml(COPY_INTENT_FOCUSES, "preview-drawer__chip-focus") +
      "</div>" +
      '<label class="preview-drawer__label" for="preview-drawer-copy-intent-note">短念头（≤30 字）</label>' +
      '<input id="preview-drawer-copy-intent-note" class="preview-drawer__copy-intent-note" type="text" maxlength="30" autocomplete="off" placeholder="例如：雨停后风很轻">' +
      '<label class="preview-drawer__copy-intent-apply">' +
      '<input type="checkbox" class="preview-drawer__copy-intent-subsequent" /> 应用到后续章节' +
      "</label>" +
      '<p class="preview-drawer__hint preview-drawer__copy-intent-hint">可选填；有语音素材时会优先用原声</p>' +
      '<p class="preview-drawer__hint preview-drawer__copy-intent-voice-skip" hidden>本章有录音，已优先用原声，无需填写意图</p>' +
      "</details>" +
      '<p class="preview-drawer__featured-help">★ 在任意一屏右下角可将照片标为精选，之后点「应用排版」生效</p>' +
      '<p class="preview-drawer__featured-help">拼图/整图屏左上角可改判媒资类型（普通照片 ↔ 拼图），改后请应用排版</p>' +
      '<button type="button" class="preview-drawer__ghost preview-drawer__narrate-anchors">保存并重新生成文案</button>' +
      '<button type="button" class="preview-drawer__primary preview-drawer__save-edit">保存编辑</button>';

    var structTpl =
      '<div class="preview-drawer__g1"></div>' +
      '<div class="preview-drawer__g1-actions" hidden>' +
      '<button type="button" class="preview-drawer__g1-confirm">章节顺序 OK</button>' +
      '<button type="button" class="preview-drawer__g1-regenerate">重新生成结构</button>' +
      "</div>" +
      '<div class="preview-drawer__explain"></div>' +
      '<div class="preview-drawer__aesthetic" hidden></div>' +
      '<button type="button" class="preview-drawer__primary preview-drawer__apply-layout">应用排版</button>';

    function pollStudioJob(jobId, onDone) {
      pollJobUntilDone(jobId, { intervalMs: 800 })
        .then(onDone)
        .catch(function () {
          onDone({ status: "failed", error: { message: "网络错误" } });
        });
    }

    function confirmG1Structure() {
      return patchJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/pipeline", {
        status: "structure_locked",
        continuePipeline: true,
      });
    }

    function chapterRow(chId) {
      if (!entryCache || !entryCache.chapters) return null;
      for (var i = 0; i < entryCache.chapters.length; i++) {
        if (entryCache.chapters[i].id === chId) return entryCache.chapters[i];
      }
      return null;
    }

    function fillAnchors(chId) {
      var inputs = drawerBodyEl.querySelectorAll(".preview-drawer__anchor");
      var row = chapterRow(chId);
      var anchors = (row && row.memoryAnchors) || [];
      for (var i = 0; i < inputs.length; i++) {
        inputs[i].value = anchors[i] || "";
      }
      var nameEl = drawerBodyEl.querySelector(".preview-drawer__chapter-name");
      if (nameEl) nameEl.textContent = (row && row.title) || chId || "—";
    }

    function wireChipGroup(container, chipClass) {
      if (!container) return;
      container.querySelectorAll("." + chipClass).forEach(function (btn) {
        btn.addEventListener("click", function () {
          var wasSelected = btn.classList.contains("is-selected");
          container.querySelectorAll("." + chipClass).forEach(function (b) {
            b.classList.remove("is-selected");
            b.setAttribute("aria-pressed", "false");
          });
          if (!wasSelected) {
            btn.classList.add("is-selected");
            btn.setAttribute("aria-pressed", "true");
          }
        });
      });
    }

    function fillCopyIntent(chId) {
      var row = chapterRow(chId);
      var intent = (row && row.copyIntent) || {};
      drawerBodyEl.querySelectorAll(".preview-drawer__chip-mood").forEach(function (btn) {
        var on = btn.getAttribute("data-value") === intent.mood;
        btn.classList.toggle("is-selected", on);
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
      drawerBodyEl.querySelectorAll(".preview-drawer__chip-focus").forEach(function (btn) {
        var on = btn.getAttribute("data-value") === intent.focus;
        btn.classList.toggle("is-selected", on);
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
      var noteInp = drawerBodyEl.querySelector(".preview-drawer__copy-intent-note");
      if (noteInp) noteInp.value = intent.note || "";
      updateCopyIntentVisibility(chId);
    }

    function chapterHasVoice(chId) {
      var row = chapterRow(chId);
      return !!(row && row.hasVoice);
    }

    function updateCopyIntentVisibility(chId) {
      var details = drawerBodyEl.querySelector(".preview-drawer__copy-intent");
      var skipNote = drawerBodyEl.querySelector(".preview-drawer__copy-intent-voice-skip");
      var hint = drawerBodyEl.querySelector(".preview-drawer__copy-intent-hint");
      var applyLabel = drawerBodyEl.querySelector(".preview-drawer__copy-intent-apply");
      if (!details) return;
      var skip = chapterHasVoice(chId);
      details.open = !skip && details.open;
      details.hidden = skip;
      if (skipNote) skipNote.hidden = !skip;
      if (hint) hint.hidden = skip;
      if (applyLabel) applyLabel.hidden = skip;
    }

    function readCopyIntentPayload() {
      if (chapterHasVoice(currentChapterId())) {
        return null;
      }
      var moodBtn = drawerBodyEl.querySelector(".preview-drawer__chip-mood.is-selected");
      var focusBtn = drawerBodyEl.querySelector(".preview-drawer__chip-focus.is-selected");
      var noteInp = drawerBodyEl.querySelector(".preview-drawer__copy-intent-note");
      var subsequent = drawerBodyEl.querySelector(".preview-drawer__copy-intent-subsequent");
      var noteVal = noteInp ? (noteInp.value || "").trim() : "";
      var payload;
      if (!moodBtn && !focusBtn && !noteVal) {
        payload = { clear: true };
      } else {
        payload = {
          mood: moodBtn ? moodBtn.getAttribute("data-value") : null,
          focus: focusBtn ? focusBtn.getAttribute("data-value") : null,
          note: noteVal || null,
        };
      }
      if (subsequent && subsequent.checked) {
        payload.applyToSubsequent = true;
      }
      return payload;
    }

    function fillChapterFields(chId) {
      fillAnchors(chId);
      fillCopyIntent(chId);
    }

    function closeDrawer() {
      if (drawerEmbedTarget) {
        drawerEmbedTarget = null;
        return;
      }
      drawerBodyEl = bodyEl;
      if (drawerFocusRelease) {
        drawerFocusRelease();
        drawerFocusRelease = null;
      }
      shell.hidden = true;
      drawer.hidden = true;
      document.body.classList.remove("preview-drawer-open");
      if (drawerPreviousFocus && drawerPreviousFocus.focus) {
        drawerPreviousFocus.focus();
      }
      drawerPreviousFocus = null;
    }

    function activateDrawerFocus() {
      drawerPreviousFocus = document.activeElement;
      if (drawerFocusRelease) drawerFocusRelease();
      closeBtn.focus();
      drawerFocusRelease = trapDrawerFocus(drawer);
    }

    function runG1Confirm(triggerBtn) {
      if (triggerBtn) triggerBtn.disabled = true;
      showToolbarToast("正在确认并继续制作…");
      return confirmG1Structure()
        .then(function (res) {
          if (res.status === 202 && res.body && res.body.jobId) {
            pollStudioJob(res.body.jobId, function (job) {
              if (triggerBtn) triggerBtn.disabled = false;
              if (job.status === "succeeded") {
                showToolbarToast("章节已确认，杂志已更新");
                window.location.reload();
                return;
              }
              var err = (job.error && (job.error.message || job.error.code)) || "确认失败";
              showToolbarToast(err, { error: true });
            });
            return;
          }
          if (triggerBtn) triggerBtn.disabled = false;
          showToolbarToast((res.body && res.body.error) || "确认失败", { error: true });
        })
        .catch(function () {
          if (triggerBtn) triggerBtn.disabled = false;
          showToolbarToast("确认失败", { error: true });
        });
    }

    function openDrawer(mode) {
      if (!entryCache) {
        fetchEntry(tripId).then(function (data) {
          entryCache = data || {};
          openDrawer(mode);
        });
        return;
      }
      var targetBody = drawerEmbedTarget || bodyEl;
      var useOverlay = !drawerEmbedTarget;
      drawerBodyEl = targetBody;

      if (useOverlay) {
        shell.hidden = false;
        drawer.hidden = false;
        document.body.classList.add("preview-drawer-open");
        setToolbarCollapsed(root, false, false);
        requestAnimationFrame(activateDrawerFocus);
      } else {
        targetBody.innerHTML = "";
      }

      if (mode === "edit") {
        if (useOverlay) titleEl.textContent = "编辑";
        targetBody.innerHTML = editTpl;
        var titleInput = targetBody.querySelector(".preview-drawer__title-input");
        var notes = targetBody.querySelector(".preview-drawer__notes");
        if (titleInput && entryCache.intentSummary) {
          titleInput.value = entryCache.intentSummary.title || "";
        }
        if (notes && entryCache.intentSummary) {
          notes.value = entryCache.intentSummary.userNotes || "";
        }
        fillChapterFields(currentChapterId());
        wireChipGroup(targetBody.querySelector(".preview-drawer__chips--mood"), "preview-drawer__chip-mood");
        wireChipGroup(targetBody.querySelector(".preview-drawer__chips--focus"), "preview-drawer__chip-focus");
        if (drawerEmbedTarget) {
          markSheetEditBaseline(root, targetBody);
          wireSheetEditDirty(root, targetBody);
        }

        function persistEditDrawer(btn, opts) {
          opts = opts || {};
          var chId = currentChapterId();
          var titleVal = (titleInput && titleInput.value || "").trim();
          var notesVal = (notes.value || "").trim();
          var anchorInputs = targetBody.querySelectorAll(".preview-drawer__anchor");
          var anchors = [];
          anchorInputs.forEach(function (inp) {
            var v = (inp.value || "").trim();
            if (v) anchors.push(v);
          });
          btn.disabled = true;
          if (titleVal.length > 20) {
            btn.disabled = false;
            showToolbarToast("杂志名最多 20 个字", { error: true });
            return Promise.resolve(false);
          }
          var tasks = [
            patchJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/intent", {
              title: titleVal || null,
              userNotes: notesVal || null,
            }),
          ];
          if (chId) {
            tasks.push(
              postJson(tripApiBase(tripId) + "/save-copy", {
                patches: [{
                  path: "chapters." + chId + ".curation.memoryAnchors",
                  value: anchors.join(", "),
                }],
              })
            );
            var copyIntentPayload = readCopyIntentPayload();
            if (copyIntentPayload) {
              tasks.push(patchJson(copyIntentApiUrl(tripId, chId), copyIntentPayload));
            }
          }
          return Promise.all(tasks)
            .then(function (results) {
              btn.disabled = false;
              var ok = results.every(function (r) { return r.status === 200 && r.body.ok; });
              if (!ok) {
                var errMsg = "保存失败";
                results.forEach(function (r) {
                  if (r.status !== 200 || !r.body.ok) {
                    errMsg = (r.body && (r.body.message || r.body.error)) || errMsg;
                  }
                });
                showToolbarToast(errMsg, { error: true });
                return false;
              }
              if (entryCache.intentSummary) {
                entryCache.intentSummary.userNotes = notesVal;
                if (titleVal) entryCache.intentSummary.title = titleVal;
              }
              if (chId && entryCache.chapters) {
                var row = chapterRow(chId);
                if (row) {
                  row.memoryAnchors = anchors;
                  var ciResult = null;
                  for (var ri = 0; ri < results.length; ri++) {
                    if (results[ri].body && "copyIntent" in results[ri].body) {
                      ciResult = results[ri];
                      break;
                    }
                  }
                  if (ciResult && ciResult.body) {
                    row.copyIntent = ciResult.body.copyIntent || null;
                    var appliedIds = ciResult.body.chapterIds || [chId];
                    appliedIds.forEach(function (appliedId) {
                      var appliedRow = chapterRow(appliedId);
                      if (appliedRow) {
                        appliedRow.copyIntent = ciResult.body.copyIntent || null;
                      }
                    });
                  }
                }
              }
              if (!opts.skipToast) {
                var copyIntentPayload = readCopyIntentPayload();
                var hasIntent = copyIntentPayload && copyIntentPayload.clear !== true;
                showToolbarToast(
                  anchors.length > 0 || hasIntent
                    ? "编辑已保存。可在「编辑与设置」中重新生成文案以写入锚点与点缀。"
                    : "编辑已保存"
                );
              }
              if (drawerEmbedTarget) {
                markSheetEditBaseline(root, targetBody);
              }
              return true;
            })
            .catch(function () {
              btn.disabled = false;
              showToolbarToast("保存失败", { error: true });
              return false;
            });
        }

        targetBody.querySelector(".preview-drawer__save-edit").addEventListener("click", function () {
          var btn = this;
          persistEditDrawer(btn).then(function (ok) {
            if (ok) closeDrawer();
          });
        });
        var narrateAnchorsBtn = targetBody.querySelector(".preview-drawer__narrate-anchors");
        if (narrateAnchorsBtn) {
          narrateAnchorsBtn.addEventListener("click", function () {
            var btn = this;
            persistEditDrawer(btn, { skipToast: true }).then(function (ok) {
              if (!ok) return;
              closeDrawer();
              startLlmNarrate(root, tripId, btn);
            });
          });
        }
        return;
      }

      if (mode === "cohort") {
        if (useOverlay) titleEl.textContent = "旅行主角 · 同框";
        targetBody.innerHTML = "";
        mountCohortDrawer({
          tripId: tripId,
          bodyEl: targetBody,
          showToast: showToolbarToast,
          onClose: closeDrawer,
          onEntryRefresh: function () {
            return fetchEntry(tripId).then(function (data) {
              entryCache = data || {};
              return entryCache;
            });
          },
          onApplyLayout: function () {
            return applyLayoutRerender(tripId, root);
          },
        });
        return;
      }

      if (useOverlay) titleEl.textContent = "结构";
      targetBody.innerHTML = structTpl;
      var g1 = targetBody.querySelector(".preview-drawer__g1");
      var g1Actions = targetBody.querySelector(".preview-drawer__g1-actions");
      var status = entryCache.pipelineStatus || "";
      var pending = entryCache.g1Pending || status === "structure_draft";
      if (pending) {
        g1.className = "preview-drawer__g1 preview-drawer__g1--warn";
        g1.textContent = "章节结构待确认：请浏览各章顺序，确认后将生成文案并完成排版。";
        if (g1Actions) g1Actions.hidden = false;
        var confirmBtn = targetBody.querySelector(".preview-drawer__g1-confirm");
        var regenBtn = targetBody.querySelector(".preview-drawer__g1-regenerate");
        if (confirmBtn) {
          confirmBtn.addEventListener("click", function () {
            runG1Confirm(confirmBtn);
          });
        }
        if (regenBtn) {
          regenBtn.addEventListener("click", function () {
            toolbarConfirm({
              title: "重新生成结构",
              body: "将重新生成章节结构，可能覆盖当前分章。继续？",
              confirmText: "继续",
              danger: true,
            }).then(function (ok) {
              if (!ok) return;
              regenBtn.disabled = true;
              return postJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/curate", { force: true });
            }).then(function (res) {
              if (!res) return;
              if (res.status === 202 && res.body && res.body.jobId) {
                pollStudioJob(res.body.jobId, function (job) {
                  regenBtn.disabled = false;
                  if (job.status === "succeeded") {
                    showToolbarToast("结构已重新生成");
                    window.location.reload();
                    return;
                  }
                  showToolbarToast("重新生成失败", { error: true });
                });
                return;
              }
              regenBtn.disabled = false;
              showToolbarToast("无法开始", { error: true });
            }).catch(function () {
              regenBtn.disabled = false;
              showToolbarToast("重新生成失败", { error: true });
            });
          });
        }
      } else {
        g1.className = "preview-drawer__g1 preview-drawer__g1--info";
        g1.textContent = "章节已按行程排好，可在预览中改字、锚点与精选。";
        if (g1Actions) g1Actions.hidden = true;
      }
      loadChapterExplain(tripId, targetBody.querySelector(".preview-drawer__explain"));
      loadAestheticExplain(tripId, targetBody.querySelector(".preview-drawer__aesthetic"));
      var applyBtn = targetBody.querySelector(".preview-drawer__apply-layout");
      if (applyBtn) {
        applyBtn.hidden = !_layoutPending;
        applyBtn.addEventListener("click", function () {
          closeDrawer();
          applyLayoutRerender(tripId, root);
        });
      }
    }

    scrim.addEventListener("click", closeDrawer);
    closeBtn.addEventListener("click", closeDrawer);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !shell.hidden) closeDrawer();
    });

    fetchEntry(tripId).then(function (data) {
      entryCache = data || {};
    });

    return {
      openEdit: function () { openDrawer("edit"); },
      openStructure: function () { openDrawer("structure"); },
      openCohort: function () { openDrawer("cohort"); },
      openEmbed: function (mode, el) {
        drawerEmbedTarget = el;
        openDrawer(mode);
      },
      confirmStructure: function () { return runG1Confirm(null); },
      close: closeDrawer,
      refreshEntry: function () {
        return fetchEntry(tripId).then(function (data) {
          entryCache = data || {};
          return entryCache;
        });
      },
    };
  }

  function initG1V3(root, tripId, drawers, sheet) {
    Promise.all([
      fetch("/__travelogue/config").then(function (r) { return r.ok ? r.json() : null; }),
      fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry").then(function (r) {
        return r.ok ? r.json() : null;
      }),
    ])
      .then(function (rows) {
        var cfg = rows[0];
        var entry = rows[1];
        if (!cfg || !entry || !entry.g1Pending) return;
        if (!(cfg.studio && cfg.studio.g1ConfirmStructure)) return;
        _g1Pending = true;
        _g1DockDismissed = false;
        if (sheet) sheet.setStructureDot(true);
        refreshTaskDockState(root);
      })
      .catch(function () {});
  }

  function initG1Banner(root, tripId, drawers) {
    var body = toolbarBody(root);
    if (!body) return;
    Promise.all([
      fetch("/__travelogue/config").then(function (r) { return r.ok ? r.json() : null; }),
      fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry").then(function (r) {
        return r.ok ? r.json() : null;
      }),
    ])
      .then(function (rows) {
        var cfg = rows[0];
        var entry = rows[1];
        if (!cfg || !entry || !entry.g1Pending) return;
        if (!(cfg.studio && cfg.studio.g1ConfirmStructure)) return;
        if (body.querySelector(".preview-toolbar__g1-banner")) return;

        var banner = document.createElement("div");
        banner.className = "preview-toolbar__g1-banner";
        banner.setAttribute("role", "status");
        banner.innerHTML =
          '<p class="preview-toolbar__g1-banner-text">章节结构待确认（G1 已开启）</p>' +
          '<div class="preview-toolbar__g1-banner-actions">' +
          '<button type="button" class="preview-toolbar__g1-banner-open">查看结构</button>' +
          '<button type="button" class="preview-toolbar__g1-banner-confirm">确认并继续</button>' +
          "</div>";
        var bar = body.querySelector(".preview-toolbar__bar");
        if (bar && bar.nextSibling) {
          body.insertBefore(banner, bar.nextSibling);
        } else {
          body.appendChild(banner);
        }
        banner.querySelector(".preview-toolbar__g1-banner-open").addEventListener("click", function () {
          drawers.openStructure();
        });
        banner.querySelector(".preview-toolbar__g1-banner-confirm").addEventListener("click", function () {
          drawers.confirmStructure();
        });
      })
      .catch(function () {});
  }

  function startFeaturedPresent() {
    var featuredHref = presentAutoplayHref({ featured: true });
    if (featuredHref) {
      window.location.href = featuredHref;
      showToolbarToast("精选全屏放映已开始");
      return;
    }
    var toggle = document.getElementById("featured-present-toggle");
    var start = document.getElementById("screenplay-start");
    if (!start) {
      showToolbarToast("当前页面不支持全屏放映", { error: true });
      return;
    }
    if (toggle && toggle.getAttribute("aria-pressed") !== "true") {
      toggle.click();
    }
    start.click();
    showToolbarToast("精选全屏放映已开始");
  }

  function initCollageMediaControls(tripId, assetMediaById) {
    assetMediaById = assetMediaById || {};
    var apiUrl =
      "/__travelogue/trips/" + encodeURIComponent(tripId) + "/asset-media-class";

    function shouldShowControl(screen, assetId) {
      var raw = screen.getAttribute("data-asset-ids") || "";
      var ids = raw.split(",").filter(function (id) { return !!id; });
      if (ids.length === 1) return true;
      var mc = assetMediaById[assetId] || "photo";
      var pattern = screen.getAttribute("data-pattern") || "";
      var hint = screen.getAttribute("data-layout-hint") || "";
      return mc === "collage" || pattern === "screen-full-frame" || hint === "full-frame";
    }

    function applyMediaClass(assetId, mediaClass, selectEl) {
      if (selectEl.disabled) return;
      selectEl.disabled = true;
      patchJson(apiUrl, { assetId: assetId, mediaClass: mediaClass })
        .then(function (res) {
          selectEl.disabled = false;
          if (res.status !== 200 || !res.body.ok) {
            showToolbarToast((res.body && res.body.error) || "改判失败", { error: true });
            selectEl.value = assetMediaById[assetId] || "photo";
            return;
          }
          assetMediaById[assetId] = mediaClass;
          selectEl.value = mediaClass;
          setLayoutPending(true);
          showToolbarToast(
            mediaClass === "collage"
              ? "已标记为拼图 · 点应用排版后生效"
              : "已标记为普通照片 · 点应用排版后生效"
          );
        })
        .catch(function () {
          selectEl.disabled = false;
          showToolbarToast("改判失败", { error: true });
        });
    }

    document
      .querySelectorAll('.layout-screen[data-block="layout-screen"][data-asset-ids]')
      .forEach(function (screen) {
        if (screen.querySelector(".preview-toolbar__collage-ctrl")) return;
        var raw = screen.getAttribute("data-asset-ids") || "";
        var assetId = raw.split(",")[0];
        if (!assetId || !shouldShowControl(screen, assetId)) return;

        var wrap = document.createElement("div");
        wrap.className = "preview-toolbar__collage-ctrl";
        var label = document.createElement("span");
        label.className = "preview-toolbar__collage-label";
        label.textContent = "媒资";
        var sel = document.createElement("select");
        sel.className = "preview-toolbar__collage-select";
        sel.setAttribute("aria-label", "拼图改判");
        [["photo", "普通照片"], ["collage", "拼图"]].forEach(function (pair) {
          var opt = document.createElement("option");
          opt.value = pair[0];
          opt.textContent = pair[1];
          sel.appendChild(opt);
        });
        sel.value = assetMediaById[assetId] === "collage" ? "collage" : "photo";
        sel.addEventListener("change", function (e) {
          e.stopPropagation();
          applyMediaClass(assetId, sel.value, sel);
        });
        wrap.appendChild(label);
        wrap.appendChild(sel);
        screen.style.position = screen.style.position || "relative";
        screen.appendChild(wrap);
      });
  }

  function initFeaturedStars(tripId) {
    var screens = document.querySelectorAll('.layout-screen[data-block="layout-screen"][data-asset-ids]');
    screens.forEach(function (screen) {
      if (screen.querySelector(".preview-toolbar__featured-star")) return;
      var raw = screen.getAttribute("data-asset-ids") || "";
      var assetId = raw.split(",")[0];
      if (!assetId) return;

      var star = document.createElement("button");
      star.type = "button";
      star.className = "preview-toolbar__featured-star";
      star.setAttribute("aria-label", "标为精选");
      star.textContent = "★";
      if (screen.getAttribute("data-featured") === "true") {
        star.classList.add("preview-toolbar__featured-star--on");
        star.setAttribute("aria-pressed", "true");
      }
      star.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        if (star.disabled) return;
        star.disabled = true;
        postJson(tripApiBase(tripId) + "/promote-tier", {
          assetIds: [assetId],
          rerender: false,
        })
          .then(function (res) {
            star.disabled = false;
            if (res.status !== 200 || !res.body.ok) {
              showToolbarToast((res.body && res.body.error) || "标记失败", { error: true });
              return;
            }
            star.classList.add("preview-toolbar__featured-star--on");
            star.setAttribute("aria-pressed", "true");
            screen.setAttribute("data-featured", "true");
            setLayoutPending(true);
            showToolbarToast("已标为精选 · 点应用排版后生效");
          })
          .catch(function () {
            star.disabled = false;
            showToolbarToast("标记失败", { error: true });
          });
      });
      screen.style.position = screen.style.position || "relative";
      screen.appendChild(star);
    });
  }

  function revealTripFolder(tripId) {
    fetch("/__travelogue/trips")
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        var trips = data.trips || [];
        var trip = trips.filter(function (t) { return t.tripId === tripId; })[0];
        var rel = (trip && trip.previewRelPath) || "index.html";
        return revealTripPath(tripId, rel);
      })
      .catch(function () {
        showToolbarToast("无法打开文件夹", { error: true });
      });
  }

  function readCoverOpeningStyleFromDom() {
    var section = document.querySelector(".cover-opening[data-cover-opening]");
    return section ? section.getAttribute("data-cover-opening") || "card-br" : "card-br";
  }

  function mountCoverStyleControls(slot, tripId) {
    if (!slot || slot.querySelector(".preview-sheet__cover-styles")) return;
    var section = document.createElement("div");
    section.className = "preview-sheet__section preview-sheet__cover-section";
    section.innerHTML =
      '<span class="preview-sheet__label">封面版式</span>' +
      '<p class="preview-sheet__hint preview-sheet__hint--compact">电脑预览有效；窄屏与手机版式不同。</p>' +
      '<div class="preview-sheet__cover-styles" role="group" aria-label="封面版式"></div>';
    var group = section.querySelector(".preview-sheet__cover-styles");
    var selectedStyle = readCoverOpeningStyleFromDom();

    function syncSelection(style) {
      if (!group) return;
      group.querySelectorAll("[data-cover-style]").forEach(function (btn) {
        var on = btn.getAttribute("data-cover-style") === style;
        btn.classList.toggle("is-on", on);
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
    }

    function setBusy(busy) {
      if (!group) return;
      group.querySelectorAll("[data-cover-style]").forEach(function (btn) {
        btn.disabled = !!busy;
      });
    }

    COVER_OPENING_STYLE_OPTIONS.forEach(function (opt) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "preview-sheet__cover-style";
      btn.setAttribute("data-cover-style", opt.id);
      btn.setAttribute("aria-label", opt.label);
      btn.innerHTML =
        '<span class="preview-sheet__cover-thumb" data-cover-thumb="' +
        opt.id +
        '" aria-hidden="true"></span>' +
        '<span class="preview-sheet__cover-label">' +
        opt.label +
        "</span>";
      btn.addEventListener("click", function () {
        var next = opt.id;
        if (!next || next === selectedStyle) return;
        setBusy(true);
        postJson(tripApiBase(tripId) + "/save-copy", {
          patches: [{ path: "meta.coverOpeningStyle", value: next }],
        })
          .then(function (res) {
            setBusy(false);
            if (res.status !== 200 || !res.body.ok) {
              showToolbarToast((res.body && res.body.error) || "保存失败", { error: true });
              return;
            }
            var prev = selectedStyle;
            selectedStyle = next;
            syncSelection(next);
            setLayoutPending(true);
            showToolbarToast("封面版式已保存 · 点应用排版后生效");
            trackStudioEvent("cover_opening_style_change", {
              tripId: tripId,
              coverOpeningStyle: next,
              previousCoverOpeningStyle: prev,
            });
          })
          .catch(function () {
            setBusy(false);
            showToolbarToast("保存失败", { error: true });
          });
      });
      group.appendChild(btn);
    });

    syncSelection(selectedStyle);
    fetchEntry(tripId)
      .then(function (data) {
        if (data && data.coverOpeningStyle) {
          selectedStyle = data.coverOpeningStyle;
          syncSelection(selectedStyle);
        }
      })
      .catch(function () {});

    slot.appendChild(section);
    trackStudioEvent("cover_opening_style_selector_impression", {
      surface: "preview-sheet",
      tripId: tripId,
      coverOpeningStyle: selectedStyle,
    });
  }

  function mountTemplateControls(slot, tripId, opts) {
    opts = opts || {};
    if (!slot || slot.querySelector(".preview-toolbar__template")) return;
    fetchEntry(tripId)
      .then(function (data) {
        var t = data && data.template;
        if (!t) return;
        var pill = document.createElement("span");
        pill.className =
          "preview-toolbar__template" + (opts.inSheet ? " preview-toolbar__template--sheet" : "");
        pill.setAttribute("title", t.feedbackMessage || "");
        var label = t.sourceLabel || "模板";
        if (t.locked) label += " · 已锁定";
        pill.textContent = label + " · " + (t.resolvedTemplateId || "visual-journal");
        slot.appendChild(pill);
        trackStudioEvent("template_selector_impression", {
          surface: opts.inSheet ? "preview-sheet" : "preview",
          tripId: tripId,
        });
        if (t.locked) return;
        var wrap = document.createElement("span");
        wrap.className = "preview-toolbar__template-adjust";
        var sel = document.createElement("select");
        sel.setAttribute("aria-label", "调整模板");
        ["smart", "manual:visual-journal", "manual:event-recap"].forEach(function (v) {
          var o = document.createElement("option");
          o.value = v;
          o.textContent = v === "smart" ? "智能匹配" : v.slice(7);
          sel.appendChild(o);
        });
        if (t.mode === "manual" && t.resolvedTemplateId) {
          sel.value = "manual:" + t.resolvedTemplateId;
        } else {
          sel.value = "smart";
        }
        var btn = document.createElement("button");
        btn.type = "button";
        btn.textContent = "应用";
        btn.addEventListener("click", function () {
          var v = String(sel.value || "smart");
          var body = { mode: v.indexOf("manual:") === 0 ? "manual" : "smart" };
          if (body.mode === "manual") body.templateId = v.slice(7);
          fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/template", {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          })
            .then(function (r) {
              return r.json().then(function (j) {
                return { ok: r.ok, j: j };
              });
            })
            .then(function (res) {
              if (!res.ok) {
                showToolbarToast((res.j && res.j.message) || "模板调整失败", { error: true });
                return;
              }
              showToolbarToast("模板策略已更新", { duration: 2000 });
              pill.textContent =
                ((res.j.template && res.j.template.sourceLabel) || "已更新") +
                " · " +
                ((res.j.template && res.j.template.resolvedTemplateId) ||
                  t.resolvedTemplateId ||
                  "visual-journal");
            })
            .catch(function () {
              showToolbarToast("模板调整失败", { error: true });
            });
        });
        wrap.appendChild(sel);
        wrap.appendChild(btn);
        slot.appendChild(wrap);
      })
      .catch(function () {});
  }

  function initTemplateBadge(root, tripId) {
    var bar = root.querySelector(".preview-toolbar__bar");
    var cluster = bar && bar.querySelector(".preview-toolbar__cluster");
    if (!cluster) return;
    mountTemplateControls(cluster, tripId, { inSheet: false });
  }

  function snapshotReadingPayload() {
    var reading = window.__TRAVELOGUE_READING__;
    if (!reading || typeof reading !== "object") return null;
    try {
      return JSON.parse(JSON.stringify(reading));
    } catch (e) {
      return null;
    }
  }

  function applyReaderSurfaceMode(readerMode) {
    var html = document.documentElement;
    var reading = window.__TRAVELOGUE_READING__ || {};
    if (readerMode) {
      html.setAttribute("data-reading-profile", "reader_immersive");
      html.setAttribute("data-surface-mode", "reader");
      html.removeAttribute("data-folio");
      reading.profile = "reader_immersive";
      reading.scroll = reading.scroll || {};
      reading.scroll.folio = "off";
    } else {
      html.setAttribute("data-reading-profile", "studio_preview");
      html.removeAttribute("data-surface-mode");
      html.setAttribute("data-folio", "lite");
      reading.profile = "studio_preview";
      reading.scroll = reading.scroll || {};
      reading.scroll.folio = "lite";
    }
    window.__TRAVELOGUE_READING__ = reading;
    if (window.TravelogueBreath && typeof window.TravelogueBreath.destroy === "function") {
      window.TravelogueBreath.destroy();
    }
    if (window.TravelogueBreath && typeof window.TravelogueBreath.init === "function") {
      window.TravelogueBreath.init();
    }
  }

  function initPreviewModeSeg(root, actions) {
    var baseline = snapshotReadingPayload();
    var seg = document.createElement("div");
    seg.className = "preview-toolbar__mode-seg";
    seg.setAttribute("role", "group");
    seg.setAttribute("aria-label", "预览模式");

    var readerBtn = document.createElement("button");
    readerBtn.type = "button";
    readerBtn.textContent = "阅读视图";
    var editBtn = document.createElement("button");
    editBtn.type = "button";
    editBtn.textContent = "编辑预览";
    seg.appendChild(readerBtn);
    seg.appendChild(editBtn);
    actions.insertBefore(seg, actions.firstChild);

    var readerOn = true;
    try {
      var stored = localStorage.getItem(READER_VIEW_KEY);
      if (stored === "0") readerOn = false;
      else if (stored === "1") readerOn = true;
    } catch (e) {}

    function syncSeg() {
      readerBtn.classList.toggle("is-selected", readerOn);
      editBtn.classList.toggle("is-selected", !readerOn);
      readerBtn.setAttribute("aria-pressed", readerOn ? "true" : "false");
      editBtn.setAttribute("aria-pressed", readerOn ? "false" : "true");
    }

    function setReaderMode(on) {
      readerOn = !!on;
      applyReaderSurfaceMode(readerOn);
      syncSeg();
      syncLongshotPreviewRowVisibility(root);
      try {
        localStorage.setItem(READER_VIEW_KEY, readerOn ? "1" : "0");
      } catch (e2) {}
    }

    readerBtn.addEventListener("click", function () {
      setReaderMode(true);
    });
    editBtn.addEventListener("click", function () {
      setReaderMode(false);
    });

    if (baseline && baseline.profile === "reader_immersive") {
      setReaderMode(true);
    } else {
      setReaderMode(readerOn);
    }
    syncSeg();
  }

  function initToolbarV3(root, tripId) {
    var dock = root.querySelector(".preview-toolbar__dock");
    var actions = dock || root.querySelector(".preview-toolbar__actions");
    if (!isPreviewToolbarV4(root)) {
      initTitleEdit(root, tripId);
    }
    var drawers = initPreviewDrawers(root, tripId);

    var readerOn = false;
    try {
      var stored = localStorage.getItem(READER_VIEW_KEY);
      if (stored === "1") readerOn = true;
    } catch (e0) {}
    var baseline = snapshotReadingPayload();
    if (baseline && baseline.profile === "reader_immersive") readerOn = true;
    applyReaderSurfaceMode(readerOn);

    function syncLongshotPrefsUi(container) {
      if (!container) return;
      var prefs = readLongshotExportPrefs();
      container.querySelectorAll("[data-studio-longshot-mode]").forEach(function (btn) {
        var on = btn.getAttribute("data-studio-longshot-mode") === prefs.mode;
        btn.classList.toggle("is-on", on);
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
      container.querySelectorAll("[data-studio-longshot-scale]").forEach(function (btn) {
        var on = String(btn.getAttribute("data-studio-longshot-scale")) === String(prefs.scale);
        btn.classList.toggle("is-on", on);
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
    }

    function syncReaderModeUi(container) {
      if (!container) return;
      var on = isReaderSurfaceMode();
      container.querySelectorAll("[data-reader-mode]").forEach(function (btn) {
        var reader = btn.getAttribute("data-reader-mode") === "reader";
        btn.classList.toggle("is-on", reader === on);
        btn.setAttribute("aria-pressed", reader === on ? "true" : "false");
      });
    }

    var cohortEnabled = false;
    var menuBtn = root.querySelector(".preview-toolbar__menu-btn");
    try {
      if (menuBtn && !sessionStorage.getItem(SHEET_HINT_KEY)) {
        menuBtn.classList.add("preview-toolbar__menu-btn--pulse");
      }
    } catch (eHint) {}

    var sheetHooks = {
      drawers: drawers,
      get cohortEnabled() { return cohortEnabled; },
      isLayoutPending: function () { return _layoutPending; },
      confirmLeaveCurrentTab: function (tabId, done) {
        if (tabId !== "edit" || !_sheetEditDirty) {
          done(true);
          return;
        }
        toolbarConfirm({
          title: "未保存的编辑",
          body: "当前「文字」Tab 有未保存改动，离开将丢弃。",
          confirmText: "离开",
          cancelText: "留下",
        }).then(done);
      },
      onSheetTabShown: function (tabId) {
        if (tabId !== "edit") {
          _sheetEditDirty = false;
          root._sheetEditDirty = false;
        }
      },
      onSheetOpened: function () {
        try {
          sessionStorage.setItem(SHEET_HINT_KEY, "1");
        } catch (eOpen) {}
        if (menuBtn) menuBtn.classList.remove("preview-toolbar__menu-btn--pulse");
      },
      syncLongshotPrefsUi: syncLongshotPrefsUi,
      syncReaderModeUi: syncReaderModeUi,
      setLongshotMode: function (mode) {
        var prefs = readLongshotExportPrefs();
        writeStoredLongshotPrefs(mode, prefs.scale);
      },
      setLongshotScale: function (scale) {
        var prefs = readLongshotExportPrefs();
        writeStoredLongshotPrefs(prefs.mode, scale === 3 ? 3 : 2);
      },
      setReaderMode: function (on) {
        applyReaderSurfaceMode(!!on);
        try {
          localStorage.setItem(READER_VIEW_KEY, on ? "1" : "0");
        } catch (e1) {}
      },
      onRevealFolder: function () {
        revealTripFolder(tripId);
      },
      onExportZip: function () {
        exportZip(tripId);
      },
      onPresentFeatured: function () {
        startFeaturedPresent();
      },
      onLlmNarrate: function (btn) {
        startLlmNarrate(root, tripId, btn);
      },
      onApplyLayout: function () {
        applyLayoutRerender(tripId, root);
      },
      mountTemplateControls: function (slot) {
        mountTemplateControls(slot, tripId, { inSheet: true });
      },
      mountCoverStyleControls: function (slot) {
        mountCoverStyleControls(slot, tripId);
      },
      syncCopyDisplayUi: function (container) {
        if (!container) return;
        var html = document.documentElement;
        var photosOnly = html.getAttribute("data-photos-only") === "on";
        var narrativeHidden = html.getAttribute("data-copy-display") === "photos";
        var captionsOn = html.getAttribute("data-caption-display") !== "off";
        container.querySelectorAll("[data-copy-preset]").forEach(function (btn) {
          var on = photosOnly
            ? btn.getAttribute("data-copy-preset") === "photos"
            : btn.getAttribute("data-copy-preset") === "full";
          btn.classList.toggle("is-on", on);
          btn.setAttribute("aria-pressed", on ? "true" : "false");
        });
        var captionChip = container.querySelector('[data-preview-chip="caption"]');
        if (captionChip) {
          captionChip.classList.toggle("is-on", captionsOn);
          captionChip.setAttribute("aria-pressed", captionsOn ? "true" : "false");
          captionChip.textContent = captionsOn ? "图注：开" : "图注：关";
          captionChip.disabled = photosOnly;
        }
        var narrativeChip = container.querySelector('[data-preview-chip="narrative"]');
        if (narrativeChip) {
          narrativeChip.classList.toggle("is-on", !narrativeHidden);
          narrativeChip.setAttribute("aria-pressed", !narrativeHidden ? "true" : "false");
          narrativeChip.textContent = !narrativeHidden ? "导语：显" : "导语：隐";
          narrativeChip.disabled = photosOnly;
        }
      },
      applyCopyPreset: function (preset) {
        applyToolbarCopyPreset(root, preset);
      },
      toggleCaptions: function () {
        toggleToolbarCaptions(root);
      },
      toggleNarrative: function () {
        toggleToolbarNarrative(root);
      },
      trapFocus: function (el) {
        return trapDrawerFocus(el);
      },
      refreshAdvancedOptions: function (panel) {
        if (!panel) return;
        drawers.refreshEntry().then(function (data) {
          var count = (data && data.intentSummary && data.intentSummary.featuredCount) || 0;
          panel.querySelectorAll(".preview-sheet__list-item--optional").forEach(function (li) {
            var action = li.querySelector("[data-action]");
            if (!action) return;
            if (action.getAttribute("data-action") === "present") {
              li.hidden = count < 1;
            }
          });
        });
        fetch("/__travelogue/config")
          .then(function (r) { return r.ok ? r.json() : null; })
          .then(function (cfg) {
            if (!cfg || !cfg.llmAvailable) return;
            panel.querySelectorAll(".preview-sheet__list-item--optional").forEach(function (li) {
              var action = li.querySelector('[data-action="llm"]');
              if (action) li.hidden = false;
            });
          })
          .catch(function () {});
      },
    };

    fetch("/__travelogue/config")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (cfg) {
        cohortEnabled = !!(cfg && cfg.cohort && cfg.cohort.enabled);
      })
      .catch(function () {});

    root._taskDock = mountPreviewTaskDock(root, {
      onCancelExport: function () {
        if (longshotPollCancel) {
          longshotPollCancel();
          longshotPollCancel = null;
        }
        if (longshotJobId) {
          postJson("/__travelogue/cancel", { jobId: longshotJobId }).catch(function () {});
          longshotJobId = null;
        }
        root._exportDockActive = false;
        setLongshotExportState(root, "idle");
        root._taskDock.hide();
      },
      onRevealFolder: function (relPath, tid) {
        revealTripPath(tid || tripId, relPath);
      },
      onCopyPath: function (text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(function () {
            showToolbarToast("路径已复制");
          }).catch(function () {
            showToolbarToast(text);
          });
        } else {
          showToolbarToast(text);
        }
      },
      onApplyLayout: function () {
        applyLayoutRerender(tripId, root);
      },
      onDismissPending: function () {
        _pendingDockDismissed = true;
        refreshTaskDockState(root);
      },
      onOpenStructure: function () {
        if (root._sheet) root._sheet.open("structure");
      },
      onConfirmStructure: function () {
        drawers.confirmStructure();
      },
      onDismissG1: function () {
        _g1DockDismissed = true;
        refreshTaskDockState(root);
      },
      onResultDismissed: function () {
        root._exportResultShowing = false;
        refreshTaskDockState(root);
      },
    });

    root._sheet = mountPreviewUnifiedSheet(root, sheetHooks);
    initG1V3(root, tripId, drawers, root._sheet);
    initDisplayedAestheticTitles(tripId);

    var exportWrap = document.createElement("div");
    exportWrap.className = "preview-toolbar__export-zone-wrap";

    var exportZone = document.createElement("div");
    exportZone.className = "preview-toolbar__export-zone";

    var longshotBtn = document.createElement("button");
    longshotBtn.type = "button";
    longshotBtn.className =
      "preview-toolbar__longshot preview-toolbar__longshot--v3 preview-toolbar__longshot--idle";
    if (isPreviewToolbarV4(root)) {
      longshotBtn.className +=
        " preview-toolbar__dock-btn preview-toolbar__dock-btn--export";
      longshotBtn.innerHTML = dockLongshotIconHtml("idle");
      longshotBtn.setAttribute("aria-label", "导出长图");
    } else {
      longshotBtn.textContent = "导出长图";
    }

    exportZone.appendChild(longshotBtn);
    exportWrap.appendChild(exportZone);
    var menuWrap = actions.querySelector(".preview-toolbar__menu-wrap");
    if (isPreviewToolbarV4(root)) {
      insertScreenplayControl(actions, menuWrap, { label: "▶", v3: true, dock: true });
      var exportDivider = document.createElement("span");
      exportDivider.className = "preview-toolbar__dock-divider";
      exportDivider.setAttribute("aria-hidden", "true");
      actions.appendChild(exportDivider);
      actions.appendChild(exportWrap);
    } else {
      actions.insertBefore(exportWrap, menuWrap);
      insertScreenplayControl(actions, menuWrap, { label: "放映", v3: true });
    }

    setLongshotExportState(root, "idle");

    longshotBtn.addEventListener("click", function () {
      startLongshot(root, tripId);
    });

    if (window.location.search.indexOf("focus=longshot") >= 0) {
      requestAnimationFrame(function () {
        longshotBtn.focus();
        longshotBtn.classList.add("preview-toolbar__longshot--focus");
      });
    }

    refreshStaleHint(root, tripId);
    refreshPreviewCover(root);
    fetchEntry(tripId).then(function (data) {
      initFeaturedStars(tripId);
      initCollageMediaControls(tripId, (data && data.assetMediaById) || {});
    });

    window.addEventListener("travelogue:copy-saved", function () {
      showStaleHint(root);
    });

    if (isPreviewToolbarV4(root)) {
      initDockTooltips(root);
      initDockScrollFade(root);
      initCoverTitleEdit(tripId);
    }

    maybeShowCoverOpeningStyleToast(tripId);
    syncToolbarHeight(root);
  }

  function isSharePreview() {
    var q = window.location.search || "";
    return q.indexOf("share=1") >= 0 || q.indexOf("mode=share") >= 0;
  }

  function initShareMinimal() {
    document.documentElement.setAttribute("data-preview-share", "on");

    var root = document.createElement("div");
    root.className = "preview-toolbar preview-toolbar--share-minimal";
    root.innerHTML =
      '<div class="preview-toolbar__body">' +
      '<div class="preview-toolbar__bar preview-toolbar__bar--minimal">' +
      '<div class="preview-toolbar__spacer" aria-hidden="true"></div>' +
      '<div class="preview-toolbar__cluster">' +
      '<a class="preview-toolbar__back" href="/" title="返回 Studio 首页">← 返回</a>' +
      "</div>" +
      "</div>" +
      "</div>";
    document.body.insertBefore(root, document.body.firstChild);

    var shareCluster = root.querySelector(".preview-toolbar__cluster");
    insertScreenplayControl(shareCluster, shareCluster && shareCluster.firstChild);

    var footerHomes = document.querySelectorAll(".footer-cta__studio-home");
    if (footerHomes.length) {
      footerHomes.forEach(function (row) {
        row.hidden = false;
      });
    } else {
      var footer = document.querySelector(".footer-cta");
      if (footer) {
        var homeRow = document.createElement("p");
        homeRow.className = "footer-cta__studio-home";
        homeRow.innerHTML =
          '<a class="footer-cta__studio-home-link" href="/">← 返回 Studio 首页</a>';
        footer.insertBefore(homeRow, footer.firstChild);
      }
    }
  }

  function ensureCoverMobileFootnote() {
    if (isSharePreview()) return;
    if (document.getElementById("preview-toolbar-cover-footnote")) return;
    var note = document.createElement("p");
    note.id = "preview-toolbar-cover-footnote";
    note.className = "preview-toolbar__cover-footnote";
    note.setAttribute("role", "note");
    note.textContent = "手机预览封面版式与电脑不同，以手机效果为准";
    document.body.appendChild(note);
  }

  function init() {
    if (isSharePreview()) {
      initShareMinimal();
      return;
    }

    document.documentElement.setAttribute("data-preview-toolbar", "on");

    var root = document.createElement("div");
    root.className = "preview-toolbar preview-toolbar--v4";
    root.innerHTML =
      '<nav class="preview-toolbar__dock" aria-label="预览快捷操作">' +
      '<a class="preview-toolbar__dock-btn preview-toolbar__dock-btn--back preview-toolbar__ctl" href="/" aria-label="返回" title="返回 Studio 首页">' +
      dockIconSvg("back") +
      "</a>" +
      '<span class="preview-toolbar__dock-divider" aria-hidden="true"></span>' +
      '<div class="preview-toolbar__menu-wrap">' +
      '<button type="button" class="preview-toolbar__menu-btn preview-toolbar__dock-btn preview-toolbar__dock-btn--menu preview-toolbar__dock-btn--folio" aria-haspopup="dialog" aria-expanded="false" aria-label="编辑与设置" title="编辑与设置">' +
      dockIconSvg("settings") +
      "</button>" +
      "</div>" +
      "</nav>";

    document.body.insertBefore(root, document.body.firstChild);
    ensureCoverMobileFootnote();
    var tripId = tripIdFromPath();
    if (!tripId) return;
    initToolbarV3(root, tripId);
  }

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
