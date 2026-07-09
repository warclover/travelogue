/**
 * Preview toolbar · longshot export (AC-ARC-14c).
 */
"use strict";

import {
  postJson,
  postJsonBusyRetry,
  isJobBusyResponse,
} from "../js/http.js";
import { startJobPollInterval, pollJobUntilDone } from "../js/job-poll.js";
import {
  buildLongshotRequest,
  resolveCopyDisplayFromDom,
} from "../js/longshot-client.js";
import {
  bindPanelDraft,
  buildPanelHtml,
  ctaLabelForPlatform,
  enabledPlatformsFromConfig,
  estimatePhotoCountFromDom,
  isSmartCropUiEnabled,
  markMomentsCoachSeen,
  readExportPrefs,
  shouldHintSparseMoments,
  sparseMomentsHintMessage,
  writeExportPrefs,
} from "../js/longshot-export-panel.js";
import { trackStudioEvent } from "../js/analytics.js";
import {
  applyDockLongshotIdle,
  dockLongshotContentHtml,
  dockLongshotIconHtml,
  isPreviewToolbarV3,
  isPreviewToolbarV4,
  setDockLongshotAria,
  updateDockTip,
} from "./dock.js";

var isJobBusy409 = isJobBusyResponse;
var LONGSHOT_MODE_KEY = "travelogue:longshotMode";
var LONGSHOT_SCALE_KEY = "travelogue:longshotScale";
var SLOW_JOB_MS = 30000;
var LONGSHOT_DRAWER_AUTO_MS = 3000;

var longshotPollCancel = null;
var narratePollCancel = null;
var longshotJobId = null;
var _longshotDrawerTimer = null;
var _studioExportPopoverClose = null;
var _longshot2PlatformIds = ["wechat_chat", "wechat_moments"];
var _longshot2SmartCrop = false;
var _sparseMomentsToastAt = 0;

var _showToolbarToast = function (_message, _opts) {};
var _toolbarConfirm = function (_opts) {
  return Promise.resolve(false);
};
var _toolbarAlert = function (_message, _opts) {};
var _setSlowHint = function (_root, _text, _visible) {};
var _setToolbarCollapsed = function (_root, _collapsed, _persist) {};
var _syncToolbarHeight = function (_root) {};
var _refreshTaskDockState = function (_root) {};
var _getLayoutPending = function () {
  return false;
};
var _tripIdFromPath = function () {
  return "";
};
var _toolbarBody = function (root) {
  return root;
};
var _setLayoutPending = function (_on) {};
var _setLayoutPendingMessage = function (_msg) {};

export function registerLongshotBridge(api) {
  if (typeof api.showToolbarToast === "function") _showToolbarToast = api.showToolbarToast;
  if (typeof api.toolbarConfirm === "function") _toolbarConfirm = api.toolbarConfirm;
  if (typeof api.toolbarAlert === "function") _toolbarAlert = api.toolbarAlert;
  if (typeof api.setSlowHint === "function") _setSlowHint = api.setSlowHint;
  if (typeof api.setToolbarCollapsed === "function") {
    _setToolbarCollapsed = api.setToolbarCollapsed;
  }
  if (typeof api.syncToolbarHeight === "function") _syncToolbarHeight = api.syncToolbarHeight;
  if (typeof api.refreshTaskDockState === "function") {
    _refreshTaskDockState = api.refreshTaskDockState;
  }
  if (typeof api.getLayoutPending === "function") _getLayoutPending = api.getLayoutPending;
  if (typeof api.tripIdFromPath === "function") _tripIdFromPath = api.tripIdFromPath;
  if (typeof api.toolbarBody === "function") _toolbarBody = api.toolbarBody;
  if (typeof api.setLayoutPending === "function") _setLayoutPending = api.setLayoutPending;
  if (typeof api.setLayoutPendingMessage === "function") {
    _setLayoutPendingMessage = api.setLayoutPendingMessage;
  }
}

export function cancelPreviewLongshotExport(root) {
  if (longshotPollCancel) {
    longshotPollCancel();
    longshotPollCancel = null;
  }
  if (longshotJobId) {
    postJson("/__travelogue/cancel", { jobId: longshotJobId }).catch(function () {});
    longshotJobId = null;
  }
  setLongshotExportState(root, "idle");
}


  export function clearLongshotDrawerTimer() {
    if (_longshotDrawerTimer) {
      clearTimeout(_longshotDrawerTimer);
      _longshotDrawerTimer = null;
    }
  }

  export function scheduleLongshotDrawerAutoHide(root) {
    clearLongshotDrawerTimer();
    _longshotDrawerTimer = setTimeout(function () {
      _longshotDrawerTimer = null;
      hideLongshotDrawer(root);
    }, LONGSHOT_DRAWER_AUTO_MS);
  }

  export function longshotApi() {
    return window.TravelogueLongshot || null;
  }

  export function readStoredLongshotScale() {
    try {
      var s = parseInt(localStorage.getItem(LONGSHOT_SCALE_KEY), 10);
      if (s === 2 || s === 3) return s;
    } catch (e) {}
    return 2;
  }

  export function readStoredLongshotMode() {
    try {
      var m = localStorage.getItem(LONGSHOT_MODE_KEY);
      if (m === "full" || m === "chapter") return m;
    } catch (e2) {}
    return "chapter";
  }

  export function writeStoredLongshotPrefs(mode, scale) {
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

  export function applyLongshot2Config(studioCfg) {
    _longshot2PlatformIds = enabledPlatformsFromConfig(studioCfg || {});
    _longshot2SmartCrop = isSmartCropUiEnabled(studioCfg || {});
  }

  export function syncLongshotCtaLabel(root) {
    if (!root) return;
    var btn = longshotBtnEl(root);
    if (!btn) return;
    if (btn.getAttribute("data-label-locked") === "1") return;
    var prefs = readExportPrefs();
    var platform = prefs.platform || "wechat_chat";
    var label = ctaLabelForPlatform(platform);
    var isDock = isPreviewToolbarV4(root);
    if (isDock) {
      // Compact dock: short chip text; full CTA on aria/tooltip.
      var short =
        platform === "wechat_moments"
          ? "朋友圈"
          : platform === "xiaohongshu"
            ? "小红书"
            : "长图";
      var labelEl = btn.querySelector(".preview-toolbar__dock-export-label");
      if (labelEl && !btn.classList.contains("preview-toolbar__longshot--running")) {
        labelEl.textContent = short;
      }
      btn.setAttribute("aria-label", label);
      updateDockTip(btn, label);
      return;
    }
    btn.textContent = label;
  }

  function maybeToastSparseMoments() {
    var n = estimatePhotoCountFromDom(document);
    if (!shouldHintSparseMoments(n)) return;
    var now = Date.now();
    if (now - _sparseMomentsToastAt < 2500) return;
    _sparseMomentsToastAt = now;
    _showToolbarToast(sparseMomentsHintMessage());
  }

  export function readLongshotExportPrefs() {
    var ls = longshotApi();
    var stored = readExportPrefs();
    var scale =
      ls && typeof ls.getUserSelectedScale === "function"
        ? ls.getUserSelectedScale()
        : stored.scale || readStoredLongshotScale();
    var mode =
      ls && typeof ls.getUserSelectedMode === "function"
        ? ls.getUserSelectedMode()
        : stored.mode || readStoredLongshotMode();
    var captions =
      ls && typeof ls.areCaptionsVisible === "function"
        ? ls.areCaptionsVisible()
        : document.documentElement.getAttribute("data-caption-display") !== "off";
    return {
      scale: scale,
      mode: mode,
      captions: captions,
      copyDisplay: resolveCopyDisplayFromDom(document),
      platform: stored.platform || "wechat_chat",
      slideCount: stored.slideCount,
      padMode: stored.padMode || "letterbox",
    };
  }

  export function formatLongshotExportMetaLabel() {
    var prefs = readLongshotExportPrefs();
    var platform = prefs.platform || "wechat_chat";
    if (platform === "wechat_moments") {
      return "朋友圈 · " + prefs.scale + "×";
    }
    if (platform === "xiaohongshu") {
      var n = prefs.slideCount == null ? "auto" : String(prefs.slideCount);
      return "小红书 · " + n + " 张 · " + prefs.scale + "×";
    }
    var modeLabel = prefs.mode === "full" ? "完整" : "按章";
    var copyLabel = prefs.copyDisplay === "photos" ? "纯照片" : "完整文案";
    var capLabel = prefs.captions ? "" : " · 无图注";
    return modeLabel + " · " + prefs.scale + "× · " + copyLabel + capLabel;
  }

  export function refreshLongshotExportMeta(root) {
    setLongshotExportMeta(root, formatLongshotExportMetaLabel());
  }

  export function normalizeSegmentMode(mode) {
    if (mode === "full" || mode === "chapter") return mode;
    return "auto";
  }

  export function buildLongshotRequestFromPage(tripId) {
    var prefs = readLongshotExportPrefs();
    var platform = prefs.platform || "wechat_chat";
    return buildLongshotRequest(tripId, {
      scale: prefs.scale,
      format: "png",
      copyDisplay: prefs.copyDisplay,
      segmentMode: normalizeSegmentMode(prefs.mode),
      platform: platform,
      slideCount: prefs.slideCount,
      padMode: prefs.padMode,
    });
  }

  export function isReaderSurfaceMode() {
    return document.documentElement.getAttribute("data-surface-mode") === "reader";
  }

  export function syncLongshotPreviewRowVisibility(root) {
    if (!root) return;
    var row = root.querySelector(".preview-toolbar__longshot-preview-row");
    if (!row) return;
    row.hidden = isReaderSurfaceMode() || _getLayoutPending();
    requestAnimationFrame(function () {
      _syncToolbarHeight(root);
    });
  }

  export function syncLongshotPreviewChips(root) {
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

  export function applyToolbarCopyPreset(root, preset) {
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

  export function toggleToolbarNarrative(root) {
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

  export function toggleToolbarCaptions(root) {
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

  export function initLongshotPreviewRow(root) {
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

  export function closeStudioExportPopover() {
    document.querySelectorAll(".preview-toolbar__export-popover").forEach(function (pop) {
      pop.hidden = true;
    });
    if (_studioExportPopoverClose) {
      document.removeEventListener("click", _studioExportPopoverClose, true);
      _studioExportPopoverClose = null;
    }
  }

  export function syncStudioExportPopoverUI(pop) {
    if (!pop || !pop._panelDraft) return;
    pop._panelDraft.setUiOpts({
      smartCropEnabled: _longshot2SmartCrop,
      photoCount: estimatePhotoCountFromDom(document),
    });
  }

  export function ensureStudioExportPopover(root) {
    var wrap = root.querySelector(".preview-toolbar__export-zone-wrap");
    if (!wrap) return null;
    var pop = wrap.querySelector(".preview-toolbar__export-popover");
    if (pop) return pop;

    pop = document.createElement("div");
    pop.className = "preview-toolbar__export-popover";
    pop.hidden = true;
    pop.setAttribute("role", "dialog");
    pop.setAttribute("aria-label", "导出设置");
    pop.innerHTML = buildPanelHtml(_longshot2PlatformIds);

    var prefs0 = readLongshotExportPrefs();
    var panel = bindPanelDraft(
      pop,
      {
        platform: prefs0.platform,
        mode: prefs0.mode,
        scale: prefs0.scale,
        slideCount: prefs0.slideCount,
        padMode: prefs0.padMode,
      },
      {
        smartCropEnabled: _longshot2SmartCrop,
        photoCount: estimatePhotoCountFromDom(document),
      }
    );
    pop._panelDraft = panel;

    pop.addEventListener("click", function (e) {
      e.stopPropagation();
    });

    pop.querySelectorAll("[data-studio-longshot-platform]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var pid = btn.getAttribute("data-studio-longshot-platform") || "wechat_chat";
        var prev = readExportPrefs().platform || "wechat_chat";
        if (pid !== prev) {
          trackStudioEvent("longshot_platform_change", { from: prev, to: pid });
        }
        if (pid === "wechat_moments") {
          maybeToastSparseMoments();
        }
      });
    });

    pop._applyDraft = function () {
      var draft = panel.getDraft();
      writeStoredLongshotPrefs(draft.mode, draft.scale);
      writeExportPrefs({
        platform: draft.platform,
        mode: draft.mode,
        scale: draft.scale,
        slideCount: draft.slideCount,
        padMode: draft.padMode,
      });
      if (draft.platform === "wechat_moments") {
        markMomentsCoachSeen();
        maybeToastSparseMoments();
      }
      syncLongshotCtaLabel(root);
      refreshLongshotExportMeta(root);
    };
    pop._readDraftFromPrefs = function () {
      var prefs = readLongshotExportPrefs();
      if (panel.setDraft) {
        panel.setDraft({
          platform: prefs.platform,
          mode: prefs.mode,
          scale: prefs.scale,
          slideCount: prefs.slideCount,
          padMode: prefs.padMode,
        });
      }
      syncStudioExportPopoverUI(pop);
    };

    wrap.appendChild(pop);
    return pop;
  }

  export function openStudioLongshotExportPanel(root) {
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

  export function openLongshotExportOptions(root) {
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

  export function revealTripPath(tripId, relPath) {
    return postJson("/__travelogue/reveal", { tripId: tripId, relPath: relPath });
  }

  export function longshotProgressPct(job) {
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

  export function pollJob(jobId, root, onDone, onSlow, kind) {
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

  export function exportZoneEl(root) {
    return root.querySelector(".preview-toolbar__export-zone");
  }

  export function longshotBtnEl(root) {
    return (
      root.querySelector(".preview-toolbar__longshot--main") ||
      root.querySelector(".preview-toolbar__longshot")
    );
  }

  export function longshotCaretEl(root) {
    return root.querySelector(".preview-toolbar__longshot-caret");
  }

  export function setLongshotControlsDisabled(root, disabled) {
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

  export function setLongshotExportMeta(root, text, opts) {
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

  export function openLongshotResultDrawer(root) {
    if (isPreviewToolbarV3(root)) {
      if (root._lastLongshotJob && root._taskDock) {
        root._taskDock.showSuccess(root._lastLongshotJob, _tripIdFromPath());
      }
      return;
    }
    _setToolbarCollapsed(root, false, false);
    clearLongshotDrawerTimer();
    var drawer = root.querySelector(".preview-toolbar__drawer");
    if (!drawer) return;
    if (root._lastLongshotJob && drawer.childElementCount === 0) {
      showLongshotDrawer(root, root._lastLongshotJob, { autoHide: false });
      return;
    }
    drawer.hidden = false;
    requestAnimationFrame(function () {
      _syncToolbarHeight(root);
    });
  }

  export function bindLongshotExportMeta(root) {
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

  export function setLongshotExportProgress(root, visible, pct) {
    var prog = root.querySelector(".preview-toolbar__export-progress");
    var fill = root.querySelector(".preview-toolbar__export-progress-fill");
    if (prog) prog.hidden = !visible;
    if (fill && typeof pct === "number") fill.style.width = pct + "%";
  }

  export function longshotSplitEl(root) {
    return root.querySelector(".preview-toolbar__longshot-split");
  }

  export function setLongshotSplitState(root, state) {
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

  export function setLongshotExportState(root, state, opts) {
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
      setLongshotSplitState(root, "running");
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
        setLongshotSplitState(root, "idle");
        setLongshotControlsDisabled(root, false);
        if (isDock) {
          btn.innerHTML = dockLongshotIconHtml("idle");
          setDockLongshotAria(btn, "idle");
        }
        syncLongshotCtaLabel(root);
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
      setLongshotSplitState(root, "idle");
      setLongshotControlsDisabled(root, false);
      if (isDock) {
        applyDockLongshotIdle(btn);
      }
      syncLongshotCtaLabel(root);
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
      setLongshotSplitState(root, "idle");
      setLongshotControlsDisabled(root, false);
      if (isDock) {
        applyDockLongshotIdle(btn);
      }
      syncLongshotCtaLabel(root);
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
    setLongshotSplitState(root, "idle");
    setLongshotControlsDisabled(root, false);
    if (isDock) {
      applyDockLongshotIdle(btn);
    }
    syncLongshotCtaLabel(root);
    btn.classList.remove("preview-toolbar__longshot--stale");
    root._exportDockActive = false;
    if (badge) badge.hidden = true;
    refreshLongshotExportMeta(root);
    if (!isV3) {
      setLongshotExportProgress(root, false);
    }
  }

  export function hideLongshotDrawer(root) {
    clearLongshotDrawerTimer();
    var drawer = root.querySelector(".preview-toolbar__drawer");
    if (!drawer) return;
    drawer.hidden = true;
    requestAnimationFrame(function () {
      _syncToolbarHeight(root);
    });
  }

  export function getLongshotDrawer(root) {
    var drawer = root.querySelector(".preview-toolbar__drawer");
    if (drawer) return drawer;
    drawer = document.createElement("div");
    drawer.className = "preview-toolbar__drawer";
    drawer.id = "preview-toolbar-longshot-drawer";
    drawer.setAttribute("role", "status");
    drawer.hidden = true;
    var body = _toolbarBody(root);
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

  export function showLongshotDrawer(root, job, opts) {
    opts = opts || {};
    root._lastLongshotJob = job;
    if (isPreviewToolbarV3(root)) {
      hideLongshotDrawer(root);
      root._exportResultShowing = true;
      if (root._taskDock) {
        root._taskDock.showSuccess(job, _tripIdFromPath());
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
    var tripId = _tripIdFromPath();
    var drawer = getLongshotDrawer(root);
    _setToolbarCollapsed(root, false, false);
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
        _syncToolbarHeight(root);
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
      _syncToolbarHeight(root);
    });
  }

  export function showStaleHint(root) {
    setLongshotExportState(root, "stale");
  }

  export function hideStaleHint(root) {
    var btn = longshotBtnEl(root);
    if (btn && btn.classList.contains("preview-toolbar__longshot--done")) return;
    setLongshotExportState(root, "idle");
  }

  export function refreshStaleHint(root, tripId) {
    fetch("/__travelogue/trips")
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        var trips = data.trips || [];
        var trip = trips.filter(function (t) { return t.tripId === tripId; })[0];
        if (!trip) return;
        if (trip.layoutCssStale || trip.renderBundleStale) {
          var pendingMsg = trip.renderBundleStale
            ? "预览产物已过期，请重新渲染"
            : "布局 CSS 已过期，请应用排版重新渲染";
          if (trip.layoutCssStale && trip.renderBundleStale) {
            pendingMsg = "预览产物与布局 CSS 已过期，请重新渲染";
          }
          _setLayoutPendingMessage(pendingMsg);
          var pendingText = root.querySelector(".preview-toolbar__pending-text");
          if (pendingText) {
            pendingText.textContent = pendingMsg;
          }
          _setLayoutPending(true);
          return;
        }
        _setLayoutPendingMessage("");
        if (trip.longshotStale) {
          showStaleHint(root);
        }
      })
      .catch(function () {});
  }

  export function exportZip(tripId) {
    _toolbarConfirm({
      title: "导出 zip",
      body: "导出 zip 包用于自行托管或备份，不是微信分享主路径。继续？",
      confirmText: "继续",
    }).then(function (ok) {
      if (!ok) return;
      return postJson("/__travelogue/export", { tripId: tripId, confirmPrivacy: true });
    }).then(function (res) {
      if (!res) return;
      if (res.status !== 200 || !res.body.ok) {
        _toolbarAlert((res.body && res.body.message) || "导出失败", { error: true });
        return;
      }
      var zipRel = res.body.zipRelPath;
      if (!zipRel) return;
      return _toolbarConfirm({
        title: "zip 已生成",
        body: "是否在文件夹中显示？",
        confirmText: "显示",
        cancelText: "关闭",
      }).then(function (reveal) {
        if (reveal) revealTripPath(tripId, zipRel);
      });
    }).catch(function () {
      _toolbarAlert("导出失败", { error: true });
    });
  }

  export function startLongshot(root, tripId) {
    var btn = longshotBtnEl(root);
    if (!btn || btn.disabled) return;
    _setToolbarCollapsed(root, false, false);
    hideLongshotDrawer(root);
    setLongshotExportState(root, "running", { hint: "正在保存…" });
    _setSlowHint(root, "", false);

    var prefs = readLongshotExportPrefs();
    var platform = prefs.platform || "wechat_chat";
    var t0 = Date.now();
    trackStudioEvent("longshot_export_start", {
      platform: platform,
      scale: prefs.scale,
      slide_count: prefs.slideCount == null ? null : prefs.slideCount,
      photo_count: estimatePhotoCountFromDom(document),
      trip_id: tripId,
      surface: "preview",
    });

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
          trackStudioEvent("longshot_export_fail", {
            platform: platform,
            error_code: (res.body && res.body.error) || "E_STUDIO_JOB_BUSY",
            trip_id: tripId,
            surface: "preview",
          });
          setLongshotExportState(root, "error", {
            hint: (res.body && res.body.message) || "请稍候再试",
          });
          return;
        }
        if (res.status !== 202 || !res.body.jobId) {
          trackStudioEvent("longshot_export_fail", {
            platform: platform,
            error_code: "E_LNG2_START_FAILED",
            trip_id: tripId,
            surface: "preview",
          });
          setLongshotExportState(root, "error", { hint: "无法开始导出" });
          return;
        }
        longshotJobId = res.body.jobId;
        pollJob(
          res.body.jobId,
          root,
          function (job) {
            _setSlowHint(root, "", false);
            if (job.status === "succeeded") {
              var result = job.result || {};
              trackStudioEvent("longshot_export_success", {
                platform: result.platform || platform,
                output_count: (result.outputs && result.outputs.length) || 0,
                target_page_count: result.pageCount != null ? result.pageCount : null,
                duration_ms: Date.now() - t0,
                trip_id: tripId,
                surface: "preview",
              });
              setLongshotExportState(root, "done");
              showLongshotDrawer(root, job);
            } else if (job.status === "failed") {
              var err = job.error || {};
              trackStudioEvent("longshot_export_fail", {
                platform: platform,
                error_code: err.code || "E_EXPORT_LONGSHOT",
                trip_id: tripId,
                surface: "preview",
              });
              setLongshotExportState(root, "error");
              showLongshotDrawer(root, job);
            } else {
              setLongshotExportState(root, "idle");
            }
          },
          function () {
            _setSlowHint(root, "比预期久一些，请耐心等待…", true);
          }
        );
      })
      .catch(function () {
        trackStudioEvent("longshot_export_fail", {
          platform: platform,
          error_code: "network",
          trip_id: tripId,
          surface: "preview",
        });
        setLongshotExportState(root, "error", { hint: "网络错误" });
      });
  }
