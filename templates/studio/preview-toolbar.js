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

var isJobBusy409 = isJobBusyResponse;
var HINT_KEY = "travelogue.studio.editHint.dismissed";
var COLLAPSE_KEY = "travelogue.studio.previewToolbar.collapsed";
var READER_VIEW_KEY = "travelogue.studio.readerView";
var LONGSHOT_MODE_KEY = "travelogue:longshotMode";
var LONGSHOT_SCALE_KEY = "travelogue:longshotScale";
var SLOW_JOB_MS = 30000;
var longshotPollCancel = null;
var narratePollCancel = null;
var longshotJobId = null;
var narrateJobId = null;
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

  var _layoutPending = false;
  function setLayoutPending(on) {
    _layoutPending = !!on;
    document.querySelectorAll(".preview-toolbar__apply-layout").forEach(function (btn) {
      btn.hidden = !_layoutPending;
    });
    document.querySelectorAll(".preview-toolbar__pending-row").forEach(function (row) {
      row.hidden = !_layoutPending;
    });
    var toolbar = document.querySelector(".preview-toolbar");
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
      btn.innerHTML =
        '<span class="preview-toolbar__longshot__spinner" aria-hidden="true"></span> 正在保存…';
      setLongshotExportMeta(root, opts.hint || "生成长图中", { actionable: false });
      var pct = typeof opts.pct === "number" ? opts.pct : 8;
      setLongshotExportProgress(root, true, pct);
      if (badge) badge.hidden = true;
      return;
    }
    if (state === "done") {
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
      btn.textContent = "保存长图";
      setLongshotExportMeta(root, opts.hint || "保存失败，请重试", { actionable: false });
      setLongshotExportProgress(root, false);
      if (badge) badge.hidden = true;
      return;
    }
    if (state === "stale") {
      btn.classList.add("preview-toolbar__longshot--idle");
      setLongshotSplitState(root, "idle");
      setLongshotControlsDisabled(root, false);
      btn.textContent = "保存长图";
      if (zone) zone.classList.add("preview-toolbar__export-zone--stale");
      if (badge) badge.hidden = false;
      setLongshotExportMeta(root, "内容已更新", { actionable: false });
      setLongshotExportProgress(root, false);
      return;
    }
    btn.classList.add("preview-toolbar__longshot--idle");
    setLongshotSplitState(root, "idle");
    setLongshotControlsDisabled(root, false);
    btn.textContent = "保存长图";
    if (badge) badge.hidden = true;
    refreshLongshotExportMeta(root);
    setLongshotExportProgress(root, false);
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
          var pendingText = root.querySelector(".preview-toolbar__pending-text");
          if (pendingText) {
            pendingText.textContent = "布局 CSS 已过期，请应用排版重新渲染";
          }
          setLayoutPending(true);
          return;
        }
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
        postJson(tripApiBase(tripId) + "/save-copy", {
          patches: [{ path: "meta.title", value: next }],
        })
          .then(function (res) {
            display.classList.remove("preview-toolbar__title--saving");
            if (res.status !== 200 || !res.body.ok) {
              showToolbarToast((res.body && res.body.error) || "保存失败", { error: true });
              return;
            }
            setTitle(next);
            showToolbarToast("杂志名已保存");
            try {
              window.dispatchEvent(new CustomEvent("travelogue:copy-saved"));
            } catch (e) {}
            if (res.body.rendered && res.body.rendered.length) {
              window.location.reload();
            }
          })
          .catch(function () {
            display.classList.remove("preview-toolbar__title--saving");
            showToolbarToast("保存失败", { error: true });
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
            " 张 · 成册中各图 top-3 维度",
          details: [],
        });
        assets.forEach(function (row) {
          var block = document.createElement("div");
          block.className = "preview-drawer__aesthetic-asset";
          var head = document.createElement("p");
          head.className = "preview-drawer__aesthetic-head";
          var overall =
            row.overall != null ? Math.round(Number(row.overall) * 100) + " 分" : "—";
          head.textContent = (row.id || "?") + " · overall " + overall;
          block.appendChild(head);
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
            img.setAttribute(
              "title",
              (pct != null ? "审美 " + pct + " · " : "") + tips
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
    var scrim = shell.querySelector(".preview-drawer__scrim");
    var closeBtn = shell.querySelector(".preview-drawer__close");
    var entryCache = null;
    var drawerFocusRelease = null;
    var drawerPreviousFocus = null;

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
      var inputs = bodyEl.querySelectorAll(".preview-drawer__anchor");
      var row = chapterRow(chId);
      var anchors = (row && row.memoryAnchors) || [];
      for (var i = 0; i < inputs.length; i++) {
        inputs[i].value = anchors[i] || "";
      }
      var nameEl = bodyEl.querySelector(".preview-drawer__chapter-name");
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
      bodyEl.querySelectorAll(".preview-drawer__chip-mood").forEach(function (btn) {
        var on = btn.getAttribute("data-value") === intent.mood;
        btn.classList.toggle("is-selected", on);
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
      bodyEl.querySelectorAll(".preview-drawer__chip-focus").forEach(function (btn) {
        var on = btn.getAttribute("data-value") === intent.focus;
        btn.classList.toggle("is-selected", on);
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
      var noteInp = bodyEl.querySelector(".preview-drawer__copy-intent-note");
      if (noteInp) noteInp.value = intent.note || "";
      updateCopyIntentVisibility(chId);
    }

    function chapterHasVoice(chId) {
      var row = chapterRow(chId);
      return !!(row && row.hasVoice);
    }

    function updateCopyIntentVisibility(chId) {
      var details = bodyEl.querySelector(".preview-drawer__copy-intent");
      var skipNote = bodyEl.querySelector(".preview-drawer__copy-intent-voice-skip");
      var hint = bodyEl.querySelector(".preview-drawer__copy-intent-hint");
      var applyLabel = bodyEl.querySelector(".preview-drawer__copy-intent-apply");
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
      var moodBtn = bodyEl.querySelector(".preview-drawer__chip-mood.is-selected");
      var focusBtn = bodyEl.querySelector(".preview-drawer__chip-focus.is-selected");
      var noteInp = bodyEl.querySelector(".preview-drawer__copy-intent-note");
      var subsequent = bodyEl.querySelector(".preview-drawer__copy-intent-subsequent");
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
      shell.hidden = false;
      drawer.hidden = false;
      document.body.classList.add("preview-drawer-open");
      setToolbarCollapsed(root, false, false);
      requestAnimationFrame(activateDrawerFocus);

      if (mode === "edit") {
        titleEl.textContent = "编辑";
        bodyEl.innerHTML = editTpl;
        var titleInput = bodyEl.querySelector(".preview-drawer__title-input");
        var notes = bodyEl.querySelector(".preview-drawer__notes");
        if (titleInput && entryCache.intentSummary) {
          titleInput.value = entryCache.intentSummary.title || "";
        }
        if (notes && entryCache.intentSummary) {
          notes.value = entryCache.intentSummary.userNotes || "";
        }
        fillChapterFields(currentChapterId());
        wireChipGroup(bodyEl.querySelector(".preview-drawer__chips--mood"), "preview-drawer__chip-mood");
        wireChipGroup(bodyEl.querySelector(".preview-drawer__chips--focus"), "preview-drawer__chip-focus");

        function persistEditDrawer(btn, opts) {
          opts = opts || {};
          var chId = currentChapterId();
          var titleVal = (titleInput && titleInput.value || "").trim();
          var notesVal = (notes.value || "").trim();
          var anchorInputs = bodyEl.querySelectorAll(".preview-drawer__anchor");
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
                    ? "编辑已保存。可在 ⋯ 菜单中重新生成文案以写入锚点与点缀。"
                    : "编辑已保存"
                );
              }
              return true;
            })
            .catch(function () {
              btn.disabled = false;
              showToolbarToast("保存失败", { error: true });
              return false;
            });
        }

        bodyEl.querySelector(".preview-drawer__save-edit").addEventListener("click", function () {
          var btn = this;
          persistEditDrawer(btn).then(function (ok) {
            if (ok) closeDrawer();
          });
        });
        var narrateAnchorsBtn = bodyEl.querySelector(".preview-drawer__narrate-anchors");
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
        titleEl.textContent = "旅行主角 · 同框";
        bodyEl.innerHTML = "";
        mountCohortDrawer({
          tripId: tripId,
          bodyEl: bodyEl,
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

      titleEl.textContent = "结构";
      bodyEl.innerHTML = structTpl;
      var g1 = bodyEl.querySelector(".preview-drawer__g1");
      var g1Actions = bodyEl.querySelector(".preview-drawer__g1-actions");
      var status = entryCache.pipelineStatus || "";
      var pending = entryCache.g1Pending || status === "structure_draft";
      if (pending) {
        g1.className = "preview-drawer__g1 preview-drawer__g1--warn";
        g1.textContent = "章节结构待确认：请浏览各章顺序，确认后将生成文案并完成排版。";
        if (g1Actions) g1Actions.hidden = false;
        var confirmBtn = bodyEl.querySelector(".preview-drawer__g1-confirm");
        var regenBtn = bodyEl.querySelector(".preview-drawer__g1-regenerate");
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
      loadChapterExplain(tripId, bodyEl.querySelector(".preview-drawer__explain"));
      loadAestheticExplain(tripId, bodyEl.querySelector(".preview-drawer__aesthetic"));
      var applyBtn = bodyEl.querySelector(".preview-drawer__apply-layout");
      applyBtn.hidden = !_layoutPending;
      applyBtn.addEventListener("click", function () {
        closeDrawer();
        applyLayoutRerender(tripId, root);
      });
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
    var toggle = document.getElementById("featured-present-toggle");
    var start = document.getElementById("screenplay-start");
    if (!start) {
      showToolbarToast("当前页面不支持放映", { error: true });
      return;
    }
    if (toggle && toggle.getAttribute("aria-pressed") !== "true") {
      toggle.click();
    }
    start.click();
    showToolbarToast("精选放映已开始");
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

  function initTemplateBadge(root, tripId) {
    var bar = root.querySelector(".preview-toolbar__bar");
    var cluster = bar && bar.querySelector(".preview-toolbar__cluster");
    if (!cluster || cluster.querySelector(".preview-toolbar__template")) return;
    fetchEntry(tripId).then(function (data) {
      var t = data && data.template;
      if (!t) return;
      var pill = document.createElement("span");
      pill.className = "preview-toolbar__template";
      pill.setAttribute("title", t.feedbackMessage || "");
      var label = t.sourceLabel || "模板";
      if (t.locked) label += " · 已锁定";
      pill.textContent = label + " · " + (t.resolvedTemplateId || "visual-journal");
      cluster.insertBefore(pill, cluster.firstChild);
      trackStudioEvent("template_selector_impression", { surface: "preview", tripId: tripId });
      if (!t.locked) {
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
            .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
            .then(function (res) {
              if (!res.ok) {
                showToolbarToast((res.j && res.j.message) || "模板调整失败", { error: true });
                return;
              }
              showToolbarToast("模板策略已更新", { duration: 2000 });
              pill.textContent = (res.j.template && res.j.template.sourceLabel) || "已更新";
            })
            .catch(function () {
              showToolbarToast("模板调整失败", { error: true });
            });
        });
        wrap.appendChild(sel);
        wrap.appendChild(btn);
        cluster.insertBefore(wrap, pill.nextSibling);
      }
    }).catch(function () { /* ignore */ });
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

  function initToolbar(root) {
    var tripId = tripIdFromPath();
    if (!tripId) return;

    var bar = root.querySelector(".preview-toolbar__bar");
    var actions = root.querySelector(".preview-toolbar__actions") || bar;
    initPreviewModeSeg(root, actions);
    var menuBtn = root.querySelector(".preview-toolbar__menu-btn");
    var menu = root.querySelector(".preview-toolbar__more-menu");
    var revealBtn = root.querySelector(".preview-toolbar__reveal-folder");

    initTemplateBadge(root, tripId);
    var drawers = initPreviewDrawers(root, tripId);
    initG1Banner(root, tripId, drawers);
    initDisplayedAestheticTitles(tripId);

    var exportWrap = document.createElement("div");
    exportWrap.className = "preview-toolbar__export-zone-wrap";

    var exportZone = document.createElement("div");
    exportZone.className = "preview-toolbar__export-zone";

    var longshotSplit = document.createElement("div");
    longshotSplit.className =
      "preview-toolbar__longshot-split preview-toolbar__longshot-split--idle";

    var longshotBtn = document.createElement("button");
    longshotBtn.type = "button";
    longshotBtn.className =
      "preview-toolbar__longshot preview-toolbar__longshot--main preview-toolbar__longshot--idle";
    longshotBtn.textContent = "保存长图";

    var longshotCaret = document.createElement("button");
    longshotCaret.type = "button";
    longshotCaret.className = "preview-toolbar__longshot-caret";
    longshotCaret.setAttribute("aria-label", "导出选项");
    longshotCaret.title = "导出选项";
    longshotCaret.innerHTML =
      '<span class="preview-toolbar__icon-btn__glyph" aria-hidden="true">▾</span>';

    longshotSplit.appendChild(longshotBtn);
    longshotSplit.appendChild(longshotCaret);

    var staleBadge = document.createElement("span");
    staleBadge.className = "preview-toolbar__export-stale";
    staleBadge.hidden = true;
    staleBadge.textContent = "内容已更新";

    var exportMeta = document.createElement("span");
    exportMeta.className = "preview-toolbar__export-meta";
    exportMeta.textContent = "按章 · 2× · 完整文案";

    exportZone.appendChild(longshotSplit);
    exportZone.appendChild(staleBadge);
    exportZone.appendChild(exportMeta);

    var progress = document.createElement("div");
    progress.className = "preview-toolbar__export-progress";
    progress.hidden = true;
    progress.innerHTML = '<div class="preview-toolbar__export-progress-fill"></div>';

    exportWrap.appendChild(exportZone);
    exportWrap.appendChild(progress);
    actions.appendChild(exportWrap);
    setLongshotExportState(root, "idle");

    if (document.documentElement.getAttribute("data-screenplay") === "on") {
      var screenplayBtn = document.createElement("button");
      screenplayBtn.type = "button";
      screenplayBtn.className = "preview-toolbar__ctl preview-toolbar__screenplay";
      screenplayBtn.setAttribute("data-screenplay-trigger", "start");
      screenplayBtn.setAttribute("data-screenplay-label", "▶ 放映");
      screenplayBtn.setAttribute("data-screenplay-busy", "退出放映");
      screenplayBtn.setAttribute("aria-pressed", "false");
      screenplayBtn.setAttribute("aria-label", "放映，全屏逐屏展示");
      screenplayBtn.textContent = "▶ 放映";
      actions.insertBefore(screenplayBtn, exportWrap);
    }

    bindLongshotExportMeta(root);

    longshotBtn.addEventListener("click", function () {
      if (longshotBtn.classList.contains("preview-toolbar__longshot--done")) {
        openLongshotResultDrawer(root);
        return;
      }
      startLongshot(root, tripId);
    });
    longshotCaret.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (longshotCaret.disabled) return;
      openLongshotExportOptions(root);
    });

    initLongshotPreviewRow(root);
    (function waitLongshotApi(attempts) {
      if (longshotApi() || attempts <= 0) {
        syncLongshotPreviewChips(root);
        return;
      }
      window.setTimeout(function () {
        waitLongshotApi(attempts - 1);
      }, 150);
    })(24);

    var pendingApply = root.querySelector(".preview-toolbar__pending-apply");
    if (pendingApply) {
      pendingApply.addEventListener("click", function () {
        applyLayoutRerender(tripId, root);
      });
    }

    if (revealBtn) {
      revealBtn.addEventListener("click", function () {
        revealTripFolder(tripId);
      });
    }

    if (window.location.search.indexOf("focus=longshot") >= 0) {
      setToolbarCollapsed(root, false, false);
      requestAnimationFrame(function () {
        exportWrap.scrollIntoView({ behavior: "smooth", block: "center" });
        longshotBtn.focus();
        longshotBtn.classList.add("preview-toolbar__longshot--focus");
      });
    }

    if (menu && menuBtn) {
      var applyBtn = menu.querySelector(".preview-toolbar__apply-layout");
      var editBtn = menu.querySelector(".preview-toolbar__open-edit");
      var cohortBtn = menu.querySelector(".preview-toolbar__open-cohort");
      var structBtn = menu.querySelector(".preview-toolbar__open-structure");
      var presentBtn = menu.querySelector(".preview-toolbar__present-featured");
      var llmSlot = menu.querySelector(".preview-toolbar__llm-slot");
      var zipBtn = menu.querySelector(".preview-toolbar__export-zip");

      function closeMenu() {
        menu.hidden = true;
        menuBtn.setAttribute("aria-expanded", "false");
      }

      menuBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        var willOpen = menu.hidden;
        menu.hidden = !willOpen;
        menuBtn.setAttribute("aria-expanded", willOpen ? "true" : "false");
      });

      if (applyBtn) {
        applyBtn.hidden = true;
        applyBtn.addEventListener("click", function () {
          closeMenu();
          applyLayoutRerender(tripId, root);
        });
      }
      if (editBtn) {
        editBtn.addEventListener("click", function () {
          closeMenu();
          drawers.openEdit();
        });
      }
      if (cohortBtn) {
        fetch("/__travelogue/config")
          .then(function (r) {
            return r.ok ? r.json() : null;
          })
          .then(function (cfg) {
            if (cfg && cfg.cohort && cfg.cohort.enabled) cohortBtn.hidden = false;
          })
          .catch(function () {});
        cohortBtn.addEventListener("click", function () {
          closeMenu();
          drawers.openCohort();
        });
      }
      if (structBtn) {
        structBtn.addEventListener("click", function () {
          closeMenu();
          drawers.openStructure();
        });
      }
      if (presentBtn) {
        drawers.refreshEntry().then(function (data) {
          var count = (data && data.intentSummary && data.intentSummary.featuredCount) || 0;
          presentBtn.hidden = count < 1;
        });
        presentBtn.addEventListener("click", function () {
          closeMenu();
          startFeaturedPresent();
        });
      }
      if (zipBtn) {
        zipBtn.addEventListener("click", function () {
          closeMenu();
          exportZip(tripId);
        });
      }

      fetch("/__travelogue/config")
        .then(function (resp) { return resp.json(); })
        .then(function (cfg) {
          if (!cfg.llmAvailable || !llmSlot) return;
          var llmBtn = document.createElement("button");
          llmBtn.type = "button";
          llmBtn.className = "preview-toolbar__llm";
          llmBtn.textContent = "生成杂志感文案";
          llmBtn.addEventListener("click", function () {
            closeMenu();
            startLlmNarrate(root, tripId, llmBtn);
          });
          llmSlot.appendChild(llmBtn);
        })
        .catch(function () {});

      document.addEventListener("click", function (ev) {
        if (!menu.contains(ev.target) && !menuBtn.contains(ev.target)) {
          closeMenu();
        }
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

    if (document.documentElement.getAttribute("data-screenplay") === "on") {
      var cluster = root.querySelector(".preview-toolbar__cluster");
      if (cluster) {
        var screenplayBtn = document.createElement("button");
        screenplayBtn.type = "button";
        screenplayBtn.className = "preview-toolbar__ctl preview-toolbar__screenplay";
        screenplayBtn.setAttribute("data-screenplay-trigger", "start");
        screenplayBtn.setAttribute("data-screenplay-label", "▶ 放映");
        screenplayBtn.setAttribute("data-screenplay-busy", "退出放映");
        screenplayBtn.setAttribute("aria-pressed", "false");
        screenplayBtn.setAttribute("aria-label", "放映，全屏逐屏展示");
        screenplayBtn.textContent = "▶ 放映";
        cluster.insertBefore(screenplayBtn, cluster.firstChild);
      }
    }

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

  function init() {
    if (isSharePreview()) {
      initShareMinimal();
      return;
    }

    document.documentElement.setAttribute("data-preview-toolbar", "on");

    var root = document.createElement("div");
    root.className = "preview-toolbar";
    root.innerHTML =
      '<div class="preview-toolbar__collapsed-strip">' +
      '<div class="preview-toolbar__spacer preview-toolbar__spacer--strip" aria-hidden="true"></div>' +
      '<button type="button" class="preview-toolbar__handle" aria-expanded="false">' +
      '<span class="preview-toolbar__handle-icon" aria-hidden="true">▾</span>' +
      '<span class="preview-toolbar__handle-label">显示工具栏</span>' +
      "</button>" +
      '<a class="preview-toolbar__back preview-toolbar__back--strip preview-toolbar__ctl" href="/" title="返回 Studio 首页">' +
      '<span class="preview-toolbar__ctl__glyph" aria-hidden="true">←</span>返回</a>' +
      "</div>" +
      '<div class="preview-toolbar__body">' +
      '<div class="preview-toolbar__bar preview-toolbar__bar--minimal">' +
      '<div class="preview-toolbar__spacer" aria-hidden="true"></div>' +
      '<div class="preview-toolbar__cluster">' +
      '<div class="preview-toolbar__ops-group">' +
      '<div class="preview-toolbar__actions"></div>' +
      '<button type="button" class="preview-toolbar__reveal-folder preview-toolbar__ctl" title="在文件夹中显示">文件夹</button>' +
      '<button type="button" class="preview-toolbar__menu-btn preview-toolbar__icon-btn" aria-haspopup="true" aria-expanded="false" aria-label="更多编辑" title="更多编辑">' +
      '<span class="preview-toolbar__icon-btn__glyph preview-toolbar__icon-btn__glyph--more" aria-hidden="true">⋯</span></button>' +
      '<div class="preview-toolbar__more-menu" hidden role="menu">' +
      '<button type="button" class="preview-toolbar__open-edit" role="menuitem">编辑感受与锚点</button>' +
      '<button type="button" class="preview-toolbar__open-cohort" role="menuitem" hidden>旅行主角 · 同框</button>' +
      '<button type="button" class="preview-toolbar__open-structure" role="menuitem">结构与分章</button>' +
      '<button type="button" class="preview-toolbar__apply-layout" role="menuitem" hidden>应用排版</button>' +
      '<button type="button" class="preview-toolbar__present-featured" role="menuitem" hidden>放映精选</button>' +
      '<span class="preview-toolbar__llm-slot" role="none"></span>' +
      '<button type="button" class="preview-toolbar__export-zip" role="menuitem">导出 zip（自行托管）</button>' +
      "</div>" +
      "</div>" +
      '<button type="button" class="preview-toolbar__collapse preview-toolbar__icon-btn" aria-expanded="true" aria-label="收起工具栏">' +
      '<span class="preview-toolbar__icon-btn__glyph" aria-hidden="true">▴</span>' +
      "</button>" +
      '<a class="preview-toolbar__back preview-toolbar__ctl" href="/" title="返回 Studio 首页">' +
      '<span class="preview-toolbar__ctl__glyph" aria-hidden="true">←</span>返回</a>' +
      "</div>" +
      '<div class="preview-toolbar__longshot-preview-row" hidden>' +
      '<div class="preview-toolbar__longshot-preview-banner">' +
      '<div class="preview-toolbar__chip-seg" role="group" aria-label="文案范围">' +
      '<button type="button" class="preview-toolbar__chip-seg-btn" data-copy-preset="photos" aria-pressed="false">纯照片</button>' +
      '<button type="button" class="preview-toolbar__chip-seg-btn is-selected" data-copy-preset="full" aria-pressed="true">完整文案</button>' +
      "</div>" +
      '<button type="button" class="preview-toolbar__chip" data-preview-chip="caption" aria-pressed="true">图注：开</button>' +
      '<button type="button" class="preview-toolbar__chip" data-preview-chip="narrative" aria-pressed="true">导语：显</button>' +
      "</div>" +
      "</div>" +
      '<div class="preview-toolbar__pending-row" hidden>' +
      '<div class="preview-toolbar__pending-banner">' +
      '<span class="preview-toolbar__pending-text">有编辑尚未应用排版</span>' +
      '<button type="button" class="preview-toolbar__pending-apply">应用排版</button>' +
      "</div>" +
      "</div>" +
      '<div class="preview-toolbar__drawer" id="preview-toolbar-longshot-drawer" hidden></div>' +
      "</div>" +
      "</div>";

    document.body.insertBefore(root, document.body.firstChild);
    bindToolbarCollapse(root);
    initToolbar(root);

    var startCollapsed = false;
    try {
      startCollapsed = localStorage.getItem(COLLAPSE_KEY) === "1";
    } catch (e3) {}
    if (window.location.search.indexOf("focus=longshot") >= 0) {
      startCollapsed = false;
    }
    setToolbarCollapsed(root, startCollapsed, false);
  }

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
