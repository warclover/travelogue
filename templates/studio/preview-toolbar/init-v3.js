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
  initDockTooltips,
  initDockScrollFade,
} from "./dock.js";
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
import { HELP_COPY } from "../js/help-onboarding.js";
import {
  registerInlineEditBridge,
  initCoverTitleEdit,
} from "./inline-edit.js";
import {
  registerLongshotBridge,
  cancelPreviewLongshotExport,
  startLongshot,
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

var READER_VIEW_KEY = "travelogue.studio.readerView";
var EXPORT_HINT_KEY = "travelogue.studio.exportHintSeen"; // legacy; pulse 现用 shouldShowExportPulse

export function initToolbarV3(root, tripId) {
  ensurePreviewRefineDefault();

  var helpBtn = createHelpOpenButton({
    id: "studio-help-open-preview",
    className: "studio-help-open studio-help-open--ghost studio-help-open--preview",
  });
  document.body.appendChild(helpBtn);

  configureHelpDrawer({
    getOpenButton: function () {
      return document.getElementById("studio-help-open-preview");
    },
    showToast: showToolbarToast,
    isHelpOpen: isHelpDrawerOpen,
    beforeOpen: function (done) {
      // MF-HELP-06 / AC-16 · 精修面板开着 → 先关面板保模式，再开帮助
      var sheet = root._sheet;
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

  var sheetHooks = {
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
            (typeof hooks.featuredPresentEmptyText === "string" &&
              hooks.featuredPresentEmptyText) ||
            "先在正文点 ★";
        }
      });
      var llmBtn = panel.querySelector('[data-action="llm"]');
      var llmHint = panel.querySelector(".preview-sheet__llm-unavailable");
      var llmSetup = panel.querySelector(".preview-sheet__llm-setup");
      function setLlmAvailable(ok) {
        if (llmBtn) {
          llmBtn.disabled = !ok;
          llmBtn.setAttribute("aria-disabled", ok ? "false" : "true");
        }
        if (llmHint) llmHint.hidden = !!ok;
        if (llmSetup) llmSetup.hidden = !!ok;
      }
      setLlmAvailable(false);
      function refreshLlmStatus() {
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
      window.addEventListener("travelogue:llm-status", function (ev) {
        var d = ev && ev.detail;
        if (d && typeof d.llmAvailable === "boolean") {
          setLlmAvailable(d.llmAvailable);
        } else {
          refreshLlmStatus();
        }
      });
      if (llmSetup && llmSetup.dataset.bound !== "1") {
        llmSetup.dataset.bound = "1";
        var setupBtn = llmSetup.querySelector('[data-action="llm-setup"]');
        if (setupBtn) {
          setupBtn.addEventListener("click", function () {
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
    },
  };

  fetch("/__travelogue/config")
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (cfg) {
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
      root._exportDockActive = false;
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
    onDismissStale: function () {
      root._staleDockDismissed = true;
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
  caretBtn.textContent = "▾";

  split.appendChild(longshotBtn);
  split.appendChild(caretBtn);
  exportZone.appendChild(split);
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
  syncToolbarHeight(root);

  // 「更新并导出」：版面刷新后自动续导出
  requestAnimationFrame(function () {
    consumeExportAfterLayout(root, tripId);
  });
}
