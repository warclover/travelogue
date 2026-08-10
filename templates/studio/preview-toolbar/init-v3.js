/**
 * Preview toolbar · v3 init (bridges, sheet, dock, longshot mount).
 */
"use strict";

import { mountPreviewTaskDock } from "../preview-toolbar-v3-task-dock.js";
import { mountPreviewUnifiedSheet } from "../preview-toolbar-v3-sheet.js";
import {
  insertScreenplayControl,
  isPreviewToolbarV4,
  dockLongshotIconHtml,
  dockIconSvg,
  initDockTooltips,
  initDockScrollFade,
} from "./dock.js";
import { mountAiSurface } from "./ai-sheet.js";
import { isSharePreview } from "./share.js";
import {
  ensurePreviewRefineDefault,
  setPreviewRefineMode,
  syncInspectChromeVisibility,
  isPreviewRefineOn,
  syncRefineDockChrome,
  maybeShowRefineStarTip,
  maybeShowBookTabMigrateTip,
} from "./preview-mode.js";
import { trackStudioEvent } from "../js/analytics.js";
import { HELP_COPY, maybeShowStubNarrateTip } from "../js/help-onboarding.js";
import {
  ensureAiSurfaceHydrated,
  isAiSurfaceEnabled,
} from "../js/ai-surface.js";
import { studioAuthHeaders } from "../js/http.js";
import { DARK_COPY } from "../js/ai-surface-dark-copy.js";
import { requestExitStudio } from "../js/studio-exit.js";
import {
  registerInlineEditBridge,
  initCoverTitleEdit,
} from "./inline-edit.js";
import {
  registerLongshotBridge,
  cancelPreviewLongshotExport,
  startLongshot,
  offerSwitchShareMethod,
  setLongshotExportState,
  readLongshotExportPrefs,
  writeStoredLongshotPrefs,
  exportZip,
  revealTripPath,
  isReaderSurfaceMode,
  refreshStaleHint,
  applyToolbarCopyPreset,
  toggleToolbarCaptions,
  toggleToolbarNarrative,
  applyLongshot2Config,
  syncLongshotCtaLabel,
  openLongshotExportOptions,
  refreshLongshotExportMeta,
  consumeExportAfterLayout,
  consumeAutoExport,
  shouldShowExportPulse,
  maybeShowLongshotHelp,
  onLongshotHelpTargetClick,
  queueLongshotHelpIdleEval,
} from "./longshot.js";
import {
  tripIdFromPath,
  tripApiBase,
  toolbarConfirm,
  toolbarAlert,
  showToolbarToast,
  maybeShowCoverOpeningStyleToast,
  reloadPreviewAfterLayout,
  setSlowHint,
  syncToolbarHeight,
  setToolbarCollapsed,
  toolbarBody,
} from "./shell.js";
import {
  registerDrawersBridge,
  initPreviewDrawers,
  trapDrawerFocus,
} from "./drawers.js";
import {
  getLayoutPending,
  getSourceMissing,
  setSourceMissing,
  dismissSourceMissingDock,
  setLayoutPendingMessage,
  clearSheetEditDirty,
  dismissPendingDock,
  dismissG1Dock,
  markSheetEditBaseline,
  wireSheetEditDirty,
  refreshTaskDockState,
  setLayoutPending,
  startLlmNarrate,
  applyLayoutRerender,
  fetchEntry,
  currentChapterId,
  refreshPreviewCover,
} from "./core.js";
import {
  initTitleEdit,
  initDisplayedAestheticTitles,
  initG1V3,
  startFeaturedPresent,
  initCollageMediaControls,
  initFeaturedStars,
  revealTripFolder,
  mountCoverStyleControls,
  mountLayoutVibeControls,
  maybeShowLayoutVibeImportHint,
  mountTemplateControls,
  snapshotReadingPayload,
  applyReaderSurfaceMode,
  runFeaturedRerank,
} from "./features.js";
import { mountBookendsPanel } from "./bookends.js";
import {
  configureHelpDrawer,
  createHelpOpenButton,
  openHelpDrawer,
  closeHelpDrawer,
  isHelpDrawerOpen,
  maybeInjectRefineSaveHint,
  maybeOpenHelpFromDeepLink,
} from "../js/help-drawer.js";
import {
  mountChapterPanel,
  maybeShowChapterHintTip,
} from "./chapter-panel.js";

var READER_VIEW_KEY = "travelogue.studio.readerView";
var EXPORT_HINT_KEY = "travelogue.studio.exportHintSeen"; // legacy; pulse 现用 shouldShowExportPulse

export function initToolbarV3(root, tripId) {
  ensurePreviewRefineDefault();
  // NAS · 尽早水合，供 Sheet/抽屉运行时门控（AC-NAS-09）
  ensureAiSurfaceHydrated();

  var dock = root.querySelector(".preview-toolbar__dock");
  var helpBtn = createHelpOpenButton({
    id: "studio-help-open-preview",
    className:
      "studio-help-open studio-help-open--ghost studio-help-open--dock preview-toolbar__dock-btn",
  });
  helpBtn.setAttribute("aria-label", "使用帮助");
  if (dock && dock.firstChild) {
    dock.insertBefore(helpBtn, dock.firstChild);
  } else if (dock) {
    dock.appendChild(helpBtn);
  } else {
    document.body.appendChild(helpBtn);
  }

  configureHelpDrawer({
    getOpenButton: function () {
      return document.getElementById("studio-help-open-preview");
    },
    showToast: showToolbarToast,
    isHelpOpen: isHelpDrawerOpen,
    beforeOpen: function (done) {
      // MF-HELP-06 / AC-16 · 精修面板开着 → 先关面板保模式，再开帮助
      var sheet = root._sheet;
      if (root._aiSheet && root._aiSheet.isOpen && root._aiSheet.isOpen()) {
        root._aiSheet.close("help");
      }
      if (root._chapterPanel && root._chapterPanel.isOpen()) {
        root._chapterPanel.close();
      }
      if (sheet && typeof sheet.isOpen === "function" && sheet.isOpen()) {
        sheet.close("help", function () {
          done(true);
        });
        return;
      }
      done(true);
    },
  });
  maybeOpenHelpFromDeepLink();

  registerLongshotBridge({
    showToolbarToast: showToolbarToast,
    toolbarConfirm: toolbarConfirm,
    toolbarAlert: toolbarAlert,
    setSlowHint: setSlowHint,
    setToolbarCollapsed: setToolbarCollapsed,
    syncToolbarHeight: syncToolbarHeight,
    refreshTaskDockState: refreshTaskDockState,
    getLayoutPending: getLayoutPending,
    getSourceMissing: getSourceMissing,
    setSourceMissing: setSourceMissing,
    dismissSourceMissingDock: dismissSourceMissingDock,
    tripIdFromPath: tripIdFromPath,
    toolbarBody: toolbarBody,
    setLayoutPending: setLayoutPending,
    setLayoutPendingMessage: setLayoutPendingMessage,
    applyLayoutRerender: applyLayoutRerender,
  });
  registerDrawersBridge({
    fetchEntry: fetchEntry,
    currentChapterId: currentChapterId,
    markSheetEditBaseline: markSheetEditBaseline,
    wireSheetEditDirty: wireSheetEditDirty,
    startLlmNarrate: startLlmNarrate,
    applyLayoutRerender: applyLayoutRerender,
    getLayoutPending: getLayoutPending,
  });
  registerInlineEditBridge({
    tripApiBase: tripApiBase,
    reloadPreviewAfterLayout: reloadPreviewAfterLayout,
    showToolbarToast: showToolbarToast,
    isSharePreview: isSharePreview,
  });
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

  function exitRefineMode(opts) {
    opts = opts || {};
    if (getLayoutPending()) {
      showToolbarToast("版面还没更新，可稍后在下方更新", { duration: 4000 });
    }
    setPreviewRefineMode(false);
    syncRefineDockChrome(root, { panelOpen: false });
    trackStudioEvent("refine_mode_exit", {
      source: opts.source || "done",
    });
  }

  // CQA AC-18 · sheet llm-status listener is singular + removed on close/tab switch
  var _sheetLlmStatusHandler = null;
  function unbindSheetLlmStatus() {
    if (_sheetLlmStatusHandler) {
      window.removeEventListener("travelogue:llm-status", _sheetLlmStatusHandler);
      _sheetLlmStatusHandler = null;
    }
  }
  function bindSheetLlmStatus(setLlmAvailable, refreshLlmStatus) {
    unbindSheetLlmStatus();
    _sheetLlmStatusHandler = function (ev) {
      var d = ev && ev.detail;
      if (d && typeof d.llmAvailable === "boolean") {
        setLlmAvailable(d.llmAvailable);
      } else {
        refreshLlmStatus();
      }
    };
    window.addEventListener("travelogue:llm-status", _sheetLlmStatusHandler);
  }

  var sheetHooks = {
    tripId: tripId,
    drawers: drawers,
    get cohortEnabled() { return cohortEnabled; },
    isLayoutPending: getLayoutPending,
    isRefineModeOn: isPreviewRefineOn,
    isHelpOpen: isHelpDrawerOpen,
    maybeInjectRefineSaveHint: maybeInjectRefineSaveHint,
    onExitRefineMode: exitRefineMode,
    confirmLeaveCurrentTab: function (tabId, done) {
      // D-REF-05 · 文案立即自动保存；切 Tab 不再弹「未保存将丢弃」
      clearSheetEditDirty(root);
      done(true);
    },
    onSheetTabShown: function (tabId) {
      unbindSheetLlmStatus();
      if (tabId !== "book" && tabId !== "edit") {
        clearSheetEditDirty(root);
      }
    },
    onBookTabRendered: function () {
      maybeShowBookTabMigrateTip(showToolbarToast, trackStudioEvent);
    },
    onSheetOpened: function (meta) {
      meta = meta || {};
      var entering = !isPreviewRefineOn();
      // Trust V1 + V1.1 · 打开精修 → refine=on；面板开
      setPreviewRefineMode(true);
      syncRefineDockChrome(root, { panelOpen: true });
      if (entering) {
        trackStudioEvent("refine_mode_enter", {
          source: meta.source || "dock",
        });
      }
    },
    onSheetClosed: function (meta) {
      meta = meta || {};
      unbindSheetLlmStatus();
      // V1.1 MF-01 · 关面板不退出模式
      syncRefineDockChrome(root, { panelOpen: false });
      if (isPreviewRefineOn()) {
        trackStudioEvent("refine_panel_close", {
          keep_mode: true,
          via: meta.via || "close",
        });
        maybeShowRefineStarTip(showToolbarToast);
      }
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
    onFeaturedRerank: function () {
      runFeaturedRerank(tripId, root);
    },
    featuredPresentEmptyText: HELP_COPY.featuredPresentEmpty || "先在正文点 ★",
    mountTemplateControls: function (slot) {
      mountTemplateControls(slot, tripId, { inSheet: true });
    },
    mountCoverStyleControls: function (slot) {
      mountCoverStyleControls(slot, tripId);
    },
    mountLayoutVibeControls: function (slot) {
      mountLayoutVibeControls(slot, tripId, { root: root });
    },
    mountBookendsPanel: function (slot) {
      mountBookendsPanel(slot, tripId, {
        mountCoverStyleControls: function (inner, styleOpts) {
          mountCoverStyleControls(inner, tripId, styleOpts || {});
        },
      });
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
      drawers.refreshEntry().then(function (/** @type {{ intentSummary?: { featuredCount?: number } }} */ data) {
        var count = (data && data.intentSummary && data.intentSummary.featuredCount) || 0;
        var presentLi = panel.querySelector('[data-tool="present"]');
        if (!presentLi) return;
        presentLi.hidden = false;
        var presentBtn = presentLi.querySelector('[data-action="present"]');
        var emptyHint = presentLi.querySelector(".preview-sheet__present-empty");
        var empty = count < 1;
        if (presentBtn) {
          presentBtn.disabled = empty;
          presentBtn.hidden = empty;
          presentBtn.setAttribute("aria-disabled", empty ? "true" : "false");
        }
        if (emptyHint) {
          emptyHint.hidden = !empty;
          emptyHint.textContent =
            (typeof sheetHooks.featuredPresentEmptyText === "string" &&
              sheetHooks.featuredPresentEmptyText) ||
            HELP_COPY.featuredPresentEmpty ||
            "先在正文点 ★";
        }
      });
      // NAS · FE-NAS-09/13：等门控水合后再决定是否挂 llm 状态机
      root._copyRefreshHint = false;
      ensureAiSurfaceHydrated().then(function () {
        if (!isAiSurfaceEnabled()) {
          try {
            trackStudioEvent("refine_copy_branch", {
              copy_branch: "nas_hidden",
              trip_id: tripId || null,
            });
          } catch (_eNas) {}
          return;
        }
        var llmBtn = panel.querySelector('[data-action="llm"]');
        var llmHint = panel.querySelector(".preview-sheet__llm-unavailable");
        var llmSetup = panel.querySelector(".preview-sheet__llm-setup");
        var llmExpect = panel.querySelector(".preview-sheet__llm-expect");
        var _wantStubTip = false;
        var _stubTipTries = 0;
        var _stubTipTimer = null;
        function scheduleStubNarrateTip() {
          if (!_wantStubTip || _stubTipTries > 10) return;
          if (_stubTipTimer) return;
          _stubTipTries += 1;
          _stubTipTimer = window.setTimeout(function () {
            _stubTipTimer = null;
            if (!_wantStubTip) return;
            if (maybeShowStubNarrateTip(showToolbarToast)) return;
            scheduleStubNarrateTip();
          }, _stubTipTries === 1 ? 1800 : 1600);
        }
        function setLlmAvailable(ok) {
          if (!isAiSurfaceEnabled()) {
            root._copyRefreshHint = false;
            return;
          }
          llmBtn = panel.querySelector('[data-action="llm"]');
          llmHint = panel.querySelector(".preview-sheet__llm-unavailable");
          llmSetup = panel.querySelector(".preview-sheet__llm-setup");
          llmExpect = panel.querySelector(".preview-sheet__llm-expect");
          if (llmBtn) {
            llmBtn.disabled = !ok;
            llmBtn.setAttribute("aria-disabled", ok ? "false" : "true");
          }
          if (llmHint) llmHint.hidden = !!ok;
          if (llmSetup) llmSetup.hidden = !!ok;
          if (llmExpect) {
            llmExpect.hidden = !ok;
            if (ok) {
              llmExpect.textContent = DARK_COPY.llmExpectReady;
            } else {
              llmExpect.textContent = DARK_COPY.llmExpectStub;
            }
          }
          _wantStubTip = !ok;
          if (!ok) scheduleStubNarrateTip();
          root._copyRefreshHint = !!ok;
          try {
            var dismissKey = "travelogue.copyRefreshDismiss." + tripId;
            root._copyRefreshDismissed = localStorage.getItem(dismissKey) === "1";
          } catch (_e) {
            root._copyRefreshDismissed = false;
          }
          if (typeof refreshTaskDockState === "function") {
            refreshTaskDockState(root);
          }
          try {
            var branch = ok ? "l1_ready" : "l0_degraded";
            if (root._pmxCopyBranch !== branch) {
              root._pmxCopyBranch = branch;
              trackStudioEvent("refine_copy_branch", {
                copy_branch: branch,
                trip_id: tripId || null,
              });
            }
          } catch (_eTrack) {}
        }
        setLlmAvailable(false);
        function refreshLlmStatus() {
          if (!isAiSurfaceEnabled()) return;
          fetch("/__travelogue/llm/status")
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (cfg) {
              setLlmAvailable(!!(cfg && cfg.llmAvailable));
            })
            .catch(function () {
              setLlmAvailable(false);
            });
        }
        refreshLlmStatus();
        bindSheetLlmStatus(setLlmAvailable, refreshLlmStatus);
        panel.dataset.nasLlmStatusBound = "1";
        llmSetup = panel.querySelector(".preview-sheet__llm-setup");
        if (llmSetup && llmSetup.dataset.bound !== "1") {
          llmSetup.dataset.bound = "1";
          var setupBtn = llmSetup.querySelector('[data-action="llm-setup"]');
          if (setupBtn) {
            setupBtn.addEventListener("click", function () {
              // @ts-expect-error runtime Studio absolute URL (not a TS-resolvable module path)
              import("/__studio/js/llm-settings.js").then(function (mod) {
                if (mod && typeof mod.openLlmSettings === "function") {
                  mod.openLlmSettings({
                    source: "preview",
                    onChange: function (st) {
                      setLlmAvailable(!!(st && st.llmAvailable));
                    },
                  });
                }
              });
            });
          }
        }
      });
    },
  };

  fetch("/__travelogue/config", {
    headers: studioAuthHeaders({}),
  })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (cfg) {
      // AI 门控只经 ensureAiSurfaceHydrated（已在上方调用）；此处只消费非 LLM 业务字段
      cohortEnabled = !!(cfg && cfg.cohort && cfg.cohort.enabled);
      if (cfg && cfg.studio) {
        applyLongshot2Config(cfg.studio);
        syncLongshotCtaLabel(root);
        refreshLongshotExportMeta(root);
      }
    })
    .catch(function () {});

  root._taskDock = mountPreviewTaskDock(root, {
    onCancelExport: function () {
      cancelPreviewLongshotExport(root);
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
    onFeaturedRerank: function () {
      runFeaturedRerank(tripId, root);
    },
    onDismissPending: function () {
      dismissPendingDock();
      refreshTaskDockState(root);
    },
    onReExport: function () {
      startLongshot(root, tripId);
    },
    onSwitchShareMethod: function () {
      offerSwitchShareMethod(root, tripId);
    },
    onDismissStale: function () {
      root._staleDockDismissed = true;
      refreshTaskDockState(root);
    },
    onCopyRefresh: function () {
      // NAS · M11：默认面切断 Dock → narrate
      if (!isAiSurfaceEnabled()) return;
      var btn =
        (root._sheet &&
          root._sheet.el &&
          root._sheet.el.querySelector('[data-action="llm"]')) ||
        root.querySelector('[data-action="llm"]');
      startLlmNarrate(root, tripId, btn || document.createElement("button"));
    },
    onDismissCopyRefresh: function () {
      root._copyRefreshDismissed = true;
      try {
        localStorage.setItem("travelogue.copyRefreshDismiss." + tripId, "1");
      } catch (_e) {
        /* ignore */
      }
      refreshTaskDockState(root);
    },
    onOpenStructure: function () {
      if (root._sheet) root._sheet.open("book");
    },
    onConfirmStructure: function () {
      drawers.confirmStructure();
    },
    onDismissG1: function () {
      dismissG1Dock();
      refreshTaskDockState(root);
    },
    onResultDismissed: function () {
      root._exportResultShowing = false;
      refreshTaskDockState(root);
    },
  });

  root._sheet = mountPreviewUnifiedSheet(root, sheetHooks);
  root._chapterPanel = mountChapterPanel(root, tripId, drawers, root._sheet);
  root._openChapterPanel = function (opts) {
    root._chapterPanel.open(opts || {});
  };
  root._maybeShowChapterHint = function () {
    maybeShowChapterHintTip(root, tripId);
  };
  initG1V3(root, tripId, drawers, root._sheet);
  initDisplayedAestheticTitles(tripId);

  var exportWrap = document.createElement("div");
  exportWrap.className = "preview-toolbar__export-zone-wrap";

  var exportZone = document.createElement("div");
  exportZone.className = "preview-toolbar__export-zone";

  // Split control: main = one-click export (default 1.x); caret = Longshot 2.0 settings.
  var split = document.createElement("div");
  split.className = "preview-toolbar__longshot-split preview-toolbar__longshot-split--idle";

  var longshotBtn = document.createElement("button");
  longshotBtn.type = "button";
  longshotBtn.className =
    "preview-toolbar__longshot preview-toolbar__longshot--main preview-toolbar__longshot--v3 preview-toolbar__longshot--idle";
  if (isPreviewToolbarV4(root)) {
    longshotBtn.className +=
      " preview-toolbar__dock-btn preview-toolbar__dock-btn--export";
    longshotBtn.innerHTML = dockLongshotIconHtml("idle");
    longshotBtn.setAttribute("aria-label", "导出长图");
  } else {
    // F-EXP-09 · 可见「长图」；完整动作名放 aria
    longshotBtn.textContent = "长图";
    longshotBtn.setAttribute("aria-label", "导出长图");
  }

  var caretBtn = document.createElement("button");
  caretBtn.type = "button";
  caretBtn.className = "preview-toolbar__longshot-caret";
  caretBtn.setAttribute("aria-label", "导出设置");
  caretBtn.setAttribute("aria-haspopup", "dialog");
  // 可见短标「设置」；完整动作名放 aria（避免与主钮「小红书」抢权）
  caretBtn.innerHTML =
    '<span class="preview-toolbar__longshot-caret-label">设置</span>' +
    '<span class="preview-toolbar__longshot-caret-chevron" aria-hidden="true">▾</span>';

  split.appendChild(longshotBtn);
  split.appendChild(caretBtn);
  exportZone.appendChild(split);
  exportWrap.appendChild(exportZone);
  var menuWrap = actions.querySelector(".preview-toolbar__menu-wrap");
  if (isPreviewToolbarV4(root)) {
    insertScreenplayControl(actions, menuWrap, { label: "▶", v3: true, dock: true });

    // D-CHAP · 分章（播放与精修之间）
    var chapBtn = document.createElement("button");
    chapBtn.type = "button";
    chapBtn.className =
      "preview-toolbar__dock-btn preview-toolbar__dock-btn--chapters preview-toolbar__dock-btn--labeled preview-toolbar__ctl";
    chapBtn.setAttribute("aria-label", "分章");
    chapBtn.setAttribute("aria-pressed", "false");
    chapBtn.innerHTML =
      dockIconSvg("chapters") +
      '<span class="preview-toolbar__dock-label">分章</span>';
    chapBtn.addEventListener("click", function () {
      if (root._chapterPanel) root._chapterPanel.toggle();
    });
    actions.insertBefore(chapBtn, menuWrap);

    // D-STAT · 管道状态槽
    var dockStat = document.createElement("span");
    dockStat.id = "preview-dock-stat";
    dockStat.className = "preview-toolbar__dock-stat";
    dockStat.setAttribute("role", "status");
    dockStat.setAttribute("aria-live", "polite");
    dockStat.hidden = true;
    actions.insertBefore(dockStat, menuWrap.nextSibling);

    var exportDivider = document.createElement("span");
    exportDivider.className = "preview-toolbar__dock-divider";
    exportDivider.setAttribute("aria-hidden", "true");
    actions.appendChild(exportDivider);

    // SAS · D-SAS-02：AI 插在精修之后、导出区之前（divider / 文件夹 / 导出之前）
    mountAiSurface(root, tripId, { insertBefore: exportDivider });

    // 打开画册文件夹（常驻；成功面 Task Dock 仍保留「在文件夹中显示」）
    var folderBtn = document.createElement("button");
    folderBtn.type = "button";
    folderBtn.className =
      "preview-toolbar__dock-btn preview-toolbar__dock-btn--folder preview-toolbar__dock-btn--labeled preview-toolbar__ctl preview-toolbar__reveal-folder";
    folderBtn.setAttribute("aria-label", "打开文件夹");
    folderBtn.innerHTML =
      dockIconSvg("folder") +
      '<span class="preview-toolbar__dock-label">文件夹</span>';
    folderBtn.addEventListener("click", function () {
      try {
        trackStudioEvent("ftue_reveal_folder", {
          tripId: tripId || null,
          source: "preview_dock",
        });
        trackStudioEvent("export_open_folder_clicked", {
          tripId: tripId || null,
          source: "preview_dock",
        });
      } catch (_e) {}
      revealTripFolder(tripId);
    });
    actions.appendChild(folderBtn);
    actions.appendChild(exportWrap);
  } else {
    actions.insertBefore(exportWrap, menuWrap);
    insertScreenplayControl(actions, menuWrap, { label: "放映", v3: true });
  }

  setLongshotExportState(root, "idle");
  syncLongshotCtaLabel(root);
  refreshLongshotExportMeta(root);

  try {
    // D-HELP-03′ / 08′ · 首访脉冲+可见 tip；忙碌则排队 idle 补评估
    if (longshotBtn && shouldShowExportPulse(tripId)) {
      maybeShowLongshotHelp(root, tripId, {
        delayMs: 450,
        isLayoutPending: getLayoutPending,
      });
    }
  } catch (eExportHint) {}

  longshotBtn.addEventListener("click", function () {
    try {
      sessionStorage.setItem(EXPORT_HINT_KEY, "1");
      onLongshotHelpTargetClick(root);
      trackStudioEvent("help_funnel_longshot_click", { tripId: tripId || null });
    } catch (eSeen) {}
    longshotBtn.classList.remove("preview-toolbar__dock-btn--pulse");
    longshotBtn.classList.remove("preview-toolbar__menu-btn--pulse");
    longshotBtn.classList.remove("preview-toolbar__dock-btn--pulse-static");
    startLongshot(root, tripId);
  });
  caretBtn.addEventListener("click", function (e) {
    e.preventDefault();
    e.stopPropagation();
    // 打开导出选项不停止脉冲、不标记已学会
    openLongshotExportOptions(root);
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
    syncInspectChromeVisibility();
  });

  // V1.1 MF-01d · 返回首页强制退出精修
  var backBtn = root.querySelector(".preview-toolbar__dock-btn--back");
  if (backBtn) {
    backBtn.addEventListener("click", function () {
      if (isPreviewRefineOn()) {
        trackStudioEvent("refine_mode_exit", { source: "home_nav" });
      }
      setPreviewRefineMode(false);
      syncRefineDockChrome(root, { panelOpen: false });
    });
  }

  // M-INS-0c · desktop exit (only when capabilities.desktopExit)
  fetch("/__travelogue/config")
    .then(function (r) {
      return r.ok ? r.json() : null;
    })
    .then(function (cfg) {
      var caps = (cfg && cfg.capabilities) || {};
      if (!caps.desktopExit) return;
      var dock = root.querySelector(".preview-toolbar__dock-rail") || root;
      if (root.querySelector("[data-studio-exit]")) return;
      var exitBtn = document.createElement("button");
      exitBtn.type = "button";
      exitBtn.className = "preview-toolbar__dock-btn preview-toolbar__dock-btn--exit";
      exitBtn.setAttribute("data-studio-exit", "1");
      exitBtn.setAttribute("aria-label", "退出 Studio");
      exitBtn.title = "退出 Studio";
      exitBtn.textContent = "退出";
      exitBtn.addEventListener("click", function () {
        requestExitStudio({ surface: "preview_dock" }).then(function (res) {
          if (res && res.ok === false && !res.cancelled && res.message) {
            showToolbarToast(res.message);
          }
        });
      });
      if (backBtn && backBtn.parentNode) {
        backBtn.parentNode.insertBefore(exitBtn, backBtn.nextSibling);
      } else {
        dock.appendChild(exitBtn);
      }
    })
    .catch(function () {});

  syncRefineDockChrome(root, { panelOpen: false });

  // Trust V1 · 文案保存不升 longshotStale（废止 copy-saved → showStaleHint）
  window.addEventListener("travelogue:copy-saved", function () {
    /* no-op: F-TRU-STALE-05 / F-TRU-EDIT-NAME-04 */
  });

  if (isPreviewToolbarV4(root)) {
    initDockTooltips(root);
    initDockScrollFade(root);
    initCoverTitleEdit(tripId);
  }

  maybeShowCoverOpeningStyleToast(tripId);
  maybeShowLayoutVibeImportHint(tripId, function () {
    if (root._sheet) root._sheet.open("book");
  });
  syncToolbarHeight(root);

  // 「更新并导出」：版面刷新后自动续导出；FTUE「保存长图」query/session 续跑
  requestAnimationFrame(function () {
    if (consumeExportAfterLayout(root, tripId)) return;
    consumeAutoExport(root, tripId);
  });
}
