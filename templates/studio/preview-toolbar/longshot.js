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
  exportSummaryLine,
  batchChecklistItems,
  batchChecklistItemsFromResult,
  batchOverallProgressRatio,
  ctaLabelForPlatform,
  ctaLabelForPlatforms,
  detectPlatformFromProgressHint,
  enabledPlatformsFromConfig,
  estimatePhotoCountFromDom,
  formatBatchSuccess,
  isComposePlatform,
  isSmartCropUiEnabled,
  markMomentsCoachSeen,
  normalizePlatformList,
  progressSynthesizingTitleForPlatform,
  progressTitleForPlatform,
  readExportPrefs,
  shortCtaLabelForPlatform,
  shortCtaLabelForPlatforms,
  shouldHintSparseMoments,
  sparseMomentsHintMessage,
  writeExportPrefs,
} from "../js/longshot-export-panel.js";
import { openDualPreview } from "./dual-preview.js";
import {
  applyOutputRecipeConfig,
  clearSessionIntent,
  fetchServerRecipe,
  getCachedKeptN,
  INTENT_TO_PLATFORM,
  isOutputRecipeEnabled,
  needsFullExportConfirm,
  PLATFORM_TO_INTENT,
  RECIPE_API_FAIL_TOAST,
  readSessionIntent,
  resolveClientRecipe,
  showAmbiguousIntentCard,
  trackRecipeResolve,
  writeSessionIntent,
} from "../js/output-recipe.js";
import { trackStudioEvent } from "../js/analytics.js";
import { markLongshotReady } from "../js/longshot-ready.js";
import {
  applyDockLongshotIdle,
  dockLongshotContentHtml,
  dockLongshotIconHtml,
  isPreviewToolbarV3,
  isPreviewToolbarV4,
  setDockLongshotAria,
  updateDockTip,
} from "./dock.js";
import { saveMagazineTitleValue } from "./inline-edit.js";
import {
  HELP_COPY,
  hasLongshotHelpSeen,
  markLongshotHelpSeen,
  maybeShowLongshotHelp,
  onLongshotHelpTargetClick,
  queueLongshotHelpIdleEval,
  resolvePublishGuide,
  shouldShowExportPulse,
  markExportPulseSeen,
  maybeShowPlatformPickTip,
} from "../js/help-onboarding.js";
import { runClientLongshotFallback } from "./longshot-client-fallback.js";
import {
  assessMagazineTitleRisk as assessMagazineTitleRiskLogic,
  disconnectExportFeedback as disconnectExportFeedbackLogic,
  isFlagExpired as isFlagExpiredLogic,
  isExportSideEffectActiveFor,
  shouldShowLongshotStale,
} from "./longshot-logic.js";

export {
  shouldShowExportPulse,
  markExportPulseSeen,
  maybeShowLongshotHelp,
  queueLongshotHelpIdleEval,
  onLongshotHelpTargetClick,
  hasLongshotHelpSeen,
  resolvePublishGuide,
  HELP_COPY,
  maybeShowPlatformPickTip,
};

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
/** Active openStudioLongshotExportPanel settle(ok) — Escape/outside close must call this (CQA D-10). */
var _activeExportPanelFinish = null;
var _longshot2PlatformIds = ["wechat_chat", "wechat_moments"];
var _longshot2SmartCrop = false;
var _sparseMomentsToastAt = 0;

var _showToolbarToast = function (_message, _opts) {};
/** @type {(opts?: any) => Promise<any>} */
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
var _getSourceMissing = function () {
  return false;
};
var _setSourceMissing = function (_on) {};
var _dismissSourceMissingDock = function () {};
var _tripIdFromPath = function () {
  return "";
};
var _toolbarBody = function (root) {
  return root;
};
var _setLayoutPending = function (_on) {};
var _setLayoutPendingMessage = function (_msg) {};
/** @type {(tripId: string, root: any, opts?: any) => Promise<any>} */
var _applyLayoutRerender = function (_tripId, _root, _opts) {
  return Promise.resolve(false);
};

var EXPORT_AFTER_LAYOUT_KEY = "travelogue.studio.exportAfterLayout";
var EXPORT_RESUME_PLATFORM_KEY = "travelogue.studio.exportResumePlatform";
var LAYOUT_UPDATING_KEY = "travelogue.studio.layoutUpdating";
var EXPECT_LAYOUT_RELOAD_KEY = "travelogue.studio.expectLayoutReload";
var UPDATE_ONLY_HINT_KEY = "travelogue.studio.updateOnlyHint";
var EXPORT_SIDE_EFFECT_KEY = "travelogue.studio.exportSideEffect";
var AUTO_EXPORT_KEY = "travelogue.studio.autoExport";
var COPY_GATE_SEVERE_KEY = "travelogue.studio.copyGateSevere.";
var EXPORT_AFTER_TTL_MS = 10 * 60 * 1000;
var EXPORT_SIDE_EFFECT_MS = 60 * 1000;
var AUTO_EXPORT_TTL_MS = 5 * 60 * 1000;
var _exportStartFrom = "direct";
var _pagehideBound = false;
var _copyGateBypassTitle = null;
var _pendingExportPlatform = null;

function _readJsonStorage(store, key) {
  try {
    var raw = store.getItem(key);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (eRead) {
    return null;
  }
}

function _writeJsonStorage(store, key, value) {
  try {
    store.setItem(key, JSON.stringify(value));
    return true;
  } catch (eWrite) {
    return false;
  }
}

function _removeStorage(store, key) {
  try {
    store.removeItem(key);
  } catch (eRm) {}
}

function clearExportAfterLayoutFlag(reason, extra) {
  var prev = _readJsonStorage(sessionStorage, EXPORT_AFTER_LAYOUT_KEY);
  _removeStorage(sessionStorage, EXPORT_AFTER_LAYOUT_KEY);
  if (prev || reason) {
    trackStudioEvent(
      "export_after_layout_cleared",
      Object.assign(
        {
          reason: reason || "clear",
          trip_id: (prev && prev.tripId) || null,
        },
        extra || {}
      )
    );
  }
}

function clearLayoutUpdatingFlag() {
  _removeStorage(sessionStorage, LAYOUT_UPDATING_KEY);
}

function notifyHelpL1Idle(root) {
  if (!root) return;
  try {
    queueLongshotHelpIdleEval(root, _tripIdFromPath(), {
      isLayoutPending: _getLayoutPending,
    });
  } catch (_eHelp) {}
}

function markExpectLayoutReload() {
  _writeJsonStorage(sessionStorage, EXPECT_LAYOUT_RELOAD_KEY, { ts: Date.now() });
}

function resolveExportPlatform() {
  var pop = document.querySelector(".preview-toolbar__export-popover");
  if (pop && pop._panelDraft && typeof pop._panelDraft.getDraft === "function") {
    try {
      var draft = pop._panelDraft.getDraft();
      if (draft && draft.platform) return String(draft.platform);
    } catch (eDraft) {}
  }
  var prefs = readLongshotExportPrefs();
  return (prefs && prefs.platform) || "wechat_chat";
}

function writeResumePlatform(tripId, platform) {
  return _writeJsonStorage(sessionStorage, EXPORT_RESUME_PLATFORM_KEY, {
    tripId: String(tripId || ""),
    platform: String(platform || "wechat_chat"),
    ts: Date.now(),
  });
}

function readResumePlatform(tripId) {
  var data = _readJsonStorage(sessionStorage, EXPORT_RESUME_PLATFORM_KEY);
  if (!data) return null;
  if (String(data.tripId || "") !== String(tripId || "")) return null;
  if (data.ts && Date.now() - Number(data.ts) > EXPORT_AFTER_TTL_MS) {
    _removeStorage(sessionStorage, EXPORT_RESUME_PLATFORM_KEY);
    return null;
  }
  return data.platform ? String(data.platform) : null;
}

function clearResumePlatform() {
  _removeStorage(sessionStorage, EXPORT_RESUME_PLATFORM_KEY);
}

function syncPrefsPlatform(platform) {
  if (!platform) return;
  try {
    var prefs = readExportPrefs();
    // PRD-BATCH-EXPORT-MULTISELECT-V1 · 2026-08-06 Playwright 走查发现的真实
    // 回归：batch 态下点导出 → startLongshotWithRecipe 的 Output Recipe「猜
    // 单一平台意图」（早于多选功能存在，不知道 platforms 数组）会在
    // runLongshotExport 判断 batch 之前先调这里，把刚多选好的 platforms 坍缩
    // 成单元素，导致批量选择形同摆设。所有调用方（tipRecipe / resume / 换种
    // 分享方式…）本意都是「猜/强制收敛到单一平台」，这类启发式不该覆盖用户
    // 刚做出的显式多选——统一在这里拦截，不逐个排查调用方。
    if (Array.isArray(prefs.platforms) && prefs.platforms.length > 1) return;
    // 单选态下调用方本意是「把确认平台强制收敛回这一个」，`platforms` 数组
    // 须同步折叠成单元素，避免与 `platform` 单值字段互相矛盾（同一类 bug 见
    // §pop._applyDraft）。
    writeExportPrefs(
      Object.assign({}, prefs, {
        platform: platform,
        platforms: [platform],
      })
    );
  } catch (eSync) {}
}

function writeExportAfterLayout(tripId) {
  var platform = resolveExportPlatform();
  // AC-TRU-07 · 双写：flag + resume key，防止消费后 prefs 被默认值覆盖
  writeResumePlatform(tripId, platform);
  syncPrefsPlatform(platform);
  return _writeJsonStorage(sessionStorage, EXPORT_AFTER_LAYOUT_KEY, {
    tripId: String(tripId || ""),
    ts: Date.now(),
    platform: platform,
  });
}

function writeExportSideEffect(tripId) {
  return _writeJsonStorage(sessionStorage, EXPORT_SIDE_EFFECT_KEY, {
    tripId: String(tripId || ""),
    ts: Date.now(),
    until: Date.now() + EXPORT_SIDE_EFFECT_MS,
  });
}

function isExportSideEffectActive(tripId) {
  var data = _readJsonStorage(sessionStorage, EXPORT_SIDE_EFFECT_KEY);
  if (!data) return false;
  if (String(data.tripId || "") !== String(tripId || "")) return false;
  if (!isExportSideEffectActiveFor(data, tripId, Date.now())) {
    _removeStorage(sessionStorage, EXPORT_SIDE_EFFECT_KEY);
    return false;
  }
  return true;
}

function clearExportSideEffect() {
  _removeStorage(sessionStorage, EXPORT_SIDE_EFFECT_KEY);
}

function readMagazineTitleFromDom() {
  var el = document.querySelector(".cover-opening__title");
  if (el) {
    return String(el.dataset.title || el.textContent || "").trim();
  }
  return String(document.title || "").trim();
}

/**
 * Trust V1 附录 D · 可读性启发式
 * @returns {null|{level:"soft"|"severe", reason:string}}
 */
export function assessMagazineTitleRisk(title) {
  return assessMagazineTitleRiskLogic(title);
}

/** Trust V1 · F-TRU-EXP-04 / 附录 C.2 · 断服反馈 */
export function disconnectExportFeedback(tripId) {
  var pathname =
    (typeof window !== "undefined" && window.location && window.location.pathname) || "/";
  return disconnectExportFeedbackLogic(tripId, pathname);
}

function applyDisconnectExportError(root, tripId) {
  clearExportAfterLayoutFlag("disconnect");
  clearLayoutUpdatingFlag();
  var fb = disconnectExportFeedback(tripId);
  setLongshotExportState(root, "error", fb);
}

function writeLayoutUpdating(tripId) {
  return _writeJsonStorage(sessionStorage, LAYOUT_UPDATING_KEY, {
    tripId: String(tripId || ""),
    ts: Date.now(),
  });
}

function readExportAfterLayout() {
  var data = _readJsonStorage(sessionStorage, EXPORT_AFTER_LAYOUT_KEY);
  if (!data) return null;
  if (typeof data === "string") {
    return { tripId: data, ts: Date.now() };
  }
  return data;
}

function readLayoutUpdating() {
  return _readJsonStorage(sessionStorage, LAYOUT_UPDATING_KEY);
}

function isFlagExpired(data) {
  return isFlagExpiredLogic(data, Date.now(), EXPORT_AFTER_TTL_MS);
}

function bindExportAfterLayoutPagehide() {
  if (_pagehideBound || typeof window === "undefined") return;
  _pagehideBound = true;
  window.addEventListener("pagehide", function () {
    var expecting = _readJsonStorage(sessionStorage, EXPECT_LAYOUT_RELOAD_KEY);
    if (expecting) return;
    clearExportAfterLayoutFlag("leave");
    clearLayoutUpdatingFlag();
  });
}

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
  if (typeof api.getSourceMissing === "function") _getSourceMissing = api.getSourceMissing;
  if (typeof api.setSourceMissing === "function") _setSourceMissing = api.setSourceMissing;
  if (typeof api.dismissSourceMissingDock === "function") {
    _dismissSourceMissingDock = api.dismissSourceMissingDock;
  }
  if (typeof api.tripIdFromPath === "function") _tripIdFromPath = api.tripIdFromPath;
  if (typeof api.toolbarBody === "function") _toolbarBody = api.toolbarBody;
  if (typeof api.setLayoutPending === "function") _setLayoutPending = api.setLayoutPending;
  if (typeof api.setLayoutPendingMessage === "function") {
    _setLayoutPendingMessage = api.setLayoutPendingMessage;
  }
  if (typeof api.applyLayoutRerender === "function") {
    _applyLayoutRerender = api.applyLayoutRerender;
  }
}

export function cancelPreviewLongshotExport(root) {
  var jobId = longshotJobId;
  if (!jobId && !longshotPollCancel) {
    setLongshotExportState(root, "idle");
    return Promise.resolve(false);
  }
  return _toolbarConfirm({
    title: "停止导出？",
    body: "已生成的本轮图片将丢弃。",
    confirmText: "停止",
    cancelText: "继续导出",
  }).then(function (ok) {
    if (!ok) return false;
    // OQ-LCC-04 · 清续跑 flag，避免取消后幽灵「更新并导出」
    clearLayoutUpdatingFlag();
    try {
      sessionStorage.removeItem(EXPORT_AFTER_LAYOUT_KEY);
      sessionStorage.removeItem(EXPECT_LAYOUT_RELOAD_KEY);
    } catch (e) {}
    clearResumePlatform();
    trackStudioEvent("longshot_export_cancel", {
      trip_id: (_tripIdFromPath && _tripIdFromPath()) || undefined,
      surface: "preview",
    });
    if (longshotPollCancel) {
      longshotPollCancel();
      longshotPollCancel = null;
    }
    var pending = jobId
      ? postJson("/__travelogue/cancel", { jobId: jobId })
      : Promise.resolve({ status: 200, body: { ok: true } });
    longshotJobId = null;
    return pending
      .catch(function () {
        return { status: 0, body: {} };
      })
      .then(function () {
        setLongshotExportState(root, "idle");
        if (root && root._taskDock && typeof root._taskDock.hide === "function") {
          root._taskDock.hide();
        }
        root._exportDockActive = false;
        _showToolbarToast("已取消导出");
        return true;
      });
  });
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
    applyOutputRecipeConfig(studioCfg || {});
  }

  /** D-OR-27 · CTA / Band 用缓存服务端 kept_n；无缓存再 DOM 估（仅非裁决提示）。 */
  function keptNForRecipe(tripId) {
    var cached = getCachedKeptN(tripId);
    if (cached != null) return cached;
    return estimatePhotoCountFromDom(document);
  }

  /**
   * FE-SR-07 / D-SR-07 · 进度第一行人话；参数进次行。
   * P0 · 按 platform 区分文案（禁止 Compose 平台回落到「可发微信的长图」）：
   * 平台优先取 hint 里的即时信号（stageHint 可能比本地 prefs 更新），
   * 兜底才用 confirmed prefs.platform（AC-DFX-02 SSOT）。
   * @returns {{ title: string, subtitle: string }}
   */
  function humanExportProgress(opts) {
    opts = opts || {};
    var hint = String(opts.hint || "");
    var pct = typeof opts.pct === "number" ? opts.pct : null;
    var prefs = readLongshotExportPrefs();
    var platform =
      detectPlatformFromProgressHint(hint) || prefs.platform || "wechat_chat";
    var composeMode = isComposePlatform(platform);

    var scale = Number(prefs.scale) || 2;
    var quality = scale >= 3 ? "超清" : scale >= 2 ? "高清" : "标准";
    // Compose 平台没有「按章/一整张」概念；副标题改用拼贴描述，避免误导。
    var subtitle = composeMode
      ? "3:4 拼贴 · " + quality
      : (prefs.mode === "full" ? "完整导出" : "按章导出") + " · " + quality;

    var title = progressTitleForPlatform(platform);
    if (/更新版面/.test(hint)) {
      title = "正在更新版面…";
      subtitle = /自动导出/.test(hint) ? "完成后将自动导出" : "完成后可再点导出";
    } else if (/排队/.test(hint)) {
      // busyHint 已按平台写好文案（如「小红书海报排队中…」），直接沿用。
      title = hint;
    } else if (/兼容模式/.test(hint)) {
      title = "正在保存到本机…";
    } else if (
      /打开浏览器|准备长图组件|preparing_browser/i.test(hint) ||
      (pct != null && pct < 25)
    ) {
      title = progressTitleForPlatform(platform);
    } else if (pct != null && pct >= 70) {
      title = "正在保存到本机…";
    } else if (/保存|合成|拼贴页|拼贴导出/.test(hint) || (pct != null && pct >= 25)) {
      title = progressSynthesizingTitleForPlatform(platform);
    }
    return { title: title, subtitle: subtitle };
  }

  export function syncLongshotCtaLabel(root) {
    if (!root) return;
    var btn = longshotBtnEl(root);
    if (!btn) return;
    if (btn.getAttribute("data-label-locked") === "1") return;
    var prefs = readExportPrefs();
    // PRD-BATCH-EXPORT-MULTISELECT-V1 · 多选（2+ 个平台）走独立的批量 CTA
    // 文案（「导出 N 个模式」），不进入下方任何单平台 Output Recipe / tipRecipe
    // 逻辑——那套「猜意图」机制天然假设只有一个确认平台，批量场景下用户已
    // 显式多选，无需再猜。
    var batchPlatforms = Array.isArray(prefs.platforms) ? prefs.platforms : [];
    if (batchPlatforms.length > 1) {
      var batchLabel = ctaLabelForPlatforms(batchPlatforms);
      var batchShort = shortCtaLabelForPlatforms(batchPlatforms);
      btn.removeAttribute("data-recipe-subtitle");
      if (isPreviewToolbarV4(root)) {
        var batchLabelEl = btn.querySelector(".preview-toolbar__dock-export-label");
        if (batchLabelEl && !btn.classList.contains("preview-toolbar__longshot--running")) {
          batchLabelEl.textContent = batchShort;
        }
        btn.setAttribute("aria-label", batchLabel);
        updateDockTip(btn, batchLabel);
        return;
      }
      if (!btn.classList.contains("preview-toolbar__longshot--running")) {
        btn.textContent = batchShort;
      }
      btn.setAttribute("aria-label", batchLabel);
      return;
    }
    // AC-DFX-02 · confirmed prefs 为 CTA SSOT；tipRecipe 不得覆盖用户已确认平台
    var platform = prefs.platform || "wechat_chat";
    var tipRecipe = null;
    var tripId = root._tripId || "";
    if (isOutputRecipeEnabled()) {
      var keptN = keptNForRecipe(tripId);
      tipRecipe = resolveClientRecipe(keptN, tripId, "preview");
    }
    var label;
    if (tipRecipe && tipRecipe.needsIntent) {
      label = tipRecipe.ctaLabel || "选择并导出";
    } else if (
      tipRecipe &&
      tipRecipe.ctaLabel &&
      tipRecipe.platform &&
      tipRecipe.platform === platform
    ) {
      label = tipRecipe.ctaLabel;
    } else {
      label = ctaLabelForPlatform(platform);
    }
    // deepHint.subtitle · Narrative≥50 副文（H-A-07）；仅当配方平台与 confirmed 一致
    if (tipRecipe && tipRecipe.subtitle && tipRecipe.platform === platform) {
      btn.setAttribute("data-recipe-subtitle", tipRecipe.subtitle);
    } else {
      btn.removeAttribute("data-recipe-subtitle");
    }
    // PMX D8 · by_chapter / 「按章」配方：可见短标签保留按章语义
    function shortLabelForCta() {
      if (tipRecipe && tipRecipe.needsIntent) return "选择分享";
      if (/按章/.test(label || "")) return "按章导出";
      return shortCtaLabelForPlatform(platform);
    }
    var isDock = isPreviewToolbarV4(root);
    if (isDock) {
      var short = shortLabelForCta();
      var labelEl = btn.querySelector(".preview-toolbar__dock-export-label");
      if (labelEl && !btn.classList.contains("preview-toolbar__longshot--running")) {
        labelEl.textContent = short;
      }
      btn.setAttribute("aria-label", label);
      updateDockTip(btn, label);
      return;
    }
    var shortBar = shortLabelForCta();
    if (!btn.classList.contains("preview-toolbar__longshot--running")) {
      btn.textContent = shortBar;
    }
    btn.setAttribute("aria-label", label);
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
      // PRD-BATCH-EXPORT-MULTISELECT-V1 · 多选态真实来源；单选时长度恒为 1，
      // 与既有 `platform` 单值字段完全一致（零回归）。
      platforms:
        Array.isArray(stored.platforms) && stored.platforms.length
          ? stored.platforms
          : [stored.platform || "wechat_chat"],
      slideCount: stored.slideCount,
      padMode: stored.padMode || "letterbox",
      includeAppendix: stored.includeAppendix === true,
      density: stored.density === "compact" ? "compact" : "default",
    };
  }

  function estimateAppendixCountFromDom(doc) {
    doc = doc || document;
    var ch = doc.querySelector("section.chapter--appendix");
    if (!ch) return 0;
    var n = ch.querySelectorAll(
      '.layout-slot__img, [data-block="media-card"], .media-card img'
    ).length;
    return n >= 2 ? n : 2;
  }

  export function formatLongshotExportMetaLabel() {
    var prefs = readLongshotExportPrefs();
    var platform = prefs.platform || "wechat_chat";
    if (platform === "wechat_moments") {
      return "朋友圈连读 · " + prefs.scale + "×";
    }
    if (platform === "xiaohongshu") {
      var n = prefs.slideCount == null ? "auto" : String(prefs.slideCount);
      return "小红书海报 · " + n + " 张 · " + prefs.scale + "×";
    }
    if (platform === "wechat_official") {
      var nMp = prefs.slideCount == null ? "auto" : String(prefs.slideCount);
      return "公众号配图 · " + nMp + " 张 · " + prefs.scale + "×";
    }
    if (platform === "poster_bric") {
      return "单张海报 · " + prefs.scale + "×";
    }
    if (platform === "album_spread") {
      return "画册跨页 · " + prefs.scale + "×";
    }
    if (platform === "moments_grid") {
      // CLI / 旧 prefs 残留；Studio 已无入口
      return "九宫格(CLI) · " + prefs.scale + "×";
    }
    var modeLabel = prefs.mode === "full" ? "完整" : "按章";
    var copyLabel = prefs.copyDisplay === "photos" ? "纯照片" : "带文字";
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
    // AC-DFX-01 · confirmed platform → intent；禁止陈旧 session intent 覆盖（如 chat 盖住 poster）
    var mappedIntent = PLATFORM_TO_INTENT[platform] || null;
    var sessionIntent = readSessionIntent(tripId);
    if (mappedIntent && sessionIntent && sessionIntent !== mappedIntent) {
      writeSessionIntent(tripId, mappedIntent);
    } else if (mappedIntent && !sessionIntent) {
      writeSessionIntent(tripId, mappedIntent);
    }
    var intent = mappedIntent || sessionIntent || null;
    return buildLongshotRequest(tripId, {
      scale: prefs.scale,
      format: "png",
      copyDisplay: prefs.copyDisplay,
      segmentMode: normalizeSegmentMode(prefs.mode),
      platform: platform,
      intent: intent,
      entrypoint: "preview",
      slideCount: prefs.slideCount,
      padMode: prefs.padMode,
      includeAppendix: prefs.includeAppendix === true,
    });
  }

  /** Fail-closed：confirmed prefs 与即将提交的 platform 必须一致 */
  function assertConfirmedPlatformPayload(prefsPlatform, payloadPlatform) {
    var a = String(prefsPlatform || "wechat_chat");
    var b = String(payloadPlatform || "wechat_chat");
    if (a !== b) {
      trackStudioEvent("export_platform_mismatch", {
        confirmed: a,
        payload: b,
      });
      return false;
    }
    return true;
  }

  function isExportAfterLayoutActive(tripId) {
    var data = _readJsonStorage(sessionStorage, EXPORT_AFTER_LAYOUT_KEY);
    if (!data) return false;
    if (String(data.tripId || "") !== String(tripId || "")) return false;
    if (data.ts && Date.now() - Number(data.ts) > EXPORT_AFTER_TTL_MS) {
      _removeStorage(sessionStorage, EXPORT_AFTER_LAYOUT_KEY);
      return false;
    }
    return true;
  }

  function syncConfirmedExportSummary(pop, draftPlatform) {
    if (!pop) return;
    var el = pop.querySelector("[data-export-confirmed-summary]");
    if (!el) return;
    var prefs = readExportPrefs();
    var confirmed = prefs.platform || "wechat_chat";
    var draft = draftPlatform;
    if (draft == null && pop._panelDraft && typeof pop._panelDraft.getDraft === "function") {
      var d = pop._panelDraft.getDraft();
      draft = d && d.platform;
    }
    el.textContent = exportSummaryLine(confirmed, draft || confirmed);
    el.setAttribute(
      "data-export-summary-pending",
      draft && draft !== confirmed ? "1" : "0"
    );
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

  function _closeStudioExportPopoverUi() {
    document.querySelectorAll(".preview-toolbar__export-popover").forEach(function (pop) {
      releaseExportPopoverFocus(pop);
      pop.hidden = true;
      pop.classList.remove("preview-toolbar__export-popover--sheet");
    });
    if (_studioExportPopoverClose) {
      document.removeEventListener("click", _studioExportPopoverClose, true);
      _studioExportPopoverClose = null;
    }
    try {
      document.documentElement.classList.remove("preview-export-popover-open");
    } catch (eLock) {}
  }

  export function closeStudioExportPopover() {
    if (typeof _activeExportPanelFinish === "function") {
      _activeExportPanelFinish(false);
      return;
    }
    _closeStudioExportPopoverUi();
  }

  export function syncStudioExportPopoverUI(pop) {
    if (!pop || !pop._panelDraft) return;
    pop._panelDraft.setUiOpts({
      smartCropEnabled: _longshot2SmartCrop,
      photoCount: estimatePhotoCountFromDom(document),
      appendixCount: estimateAppendixCountFromDom(document),
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
    var dualBtn = pop.querySelector("[data-ltn-dual-preview]");
    if (dualBtn && !dualBtn._ltnBound) {
      dualBtn._ltnBound = true;
      dualBtn.addEventListener("click", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        openDualPreview(_tripIdFromPath());
      });
    }

    var prefs0 = readLongshotExportPrefs();
    var panel = bindPanelDraft(
      pop,
      {
        platform: prefs0.platform,
        mode: prefs0.mode,
        scale: prefs0.scale,
        slideCount: prefs0.slideCount,
        padMode: prefs0.padMode,
        includeAppendix: prefs0.includeAppendix === true,
        density: prefs0.density === "compact" ? "compact" : "default",
      },
      {
        smartCropEnabled: _longshot2SmartCrop,
        photoCount: estimatePhotoCountFromDom(document),
        appendixCount: estimateAppendixCountFromDom(document),
        onDraftChange: function (draft) {
          syncConfirmedExportSummary(pop, draft && draft.platform);
        },
      }
    );
    pop._panelDraft = panel;

    pop.addEventListener("click", function (e) {
      e.stopPropagation();
    });

    function syncExportPopoverCopyUi() {
      var html = document.documentElement;
      var photosOnly = html.getAttribute("data-photos-only") === "on";
      var narrativeHidden = html.getAttribute("data-copy-display") === "photos";
      var captionsOn = html.getAttribute("data-caption-display") !== "off";
      pop.querySelectorAll("[data-copy-preset]").forEach(function (btn) {
        var on = photosOnly
          ? btn.getAttribute("data-copy-preset") === "photos"
          : btn.getAttribute("data-copy-preset") === "full";
        btn.classList.toggle("is-selected", on);
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
      var captionChip = pop.querySelector('[data-preview-chip="caption"]');
      if (captionChip) {
        captionChip.classList.toggle("is-selected", captionsOn && !photosOnly);
        captionChip.setAttribute("aria-pressed", captionsOn ? "true" : "false");
        captionChip.textContent = captionsOn ? "图注：开" : "图注：关";
        captionChip.disabled = photosOnly;
      }
      var narrativeChip = pop.querySelector('[data-preview-chip="narrative"]');
      if (narrativeChip) {
        var showNarrative = !narrativeHidden && !photosOnly;
        narrativeChip.classList.toggle("is-selected", showNarrative);
        narrativeChip.setAttribute("aria-pressed", showNarrative ? "true" : "false");
        narrativeChip.textContent = !narrativeHidden ? "导语：显" : "导语：隐";
        narrativeChip.disabled = photosOnly;
      }
      syncLongshotPreviewChips(root);
    }
    pop._syncCopyUi = syncExportPopoverCopyUi;

    pop.querySelectorAll("[data-copy-preset]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        applyToolbarCopyPreset(root, btn.getAttribute("data-copy-preset"));
        syncExportPopoverCopyUi();
      });
    });
    var popCaption = pop.querySelector('[data-preview-chip="caption"]');
    if (popCaption) {
      popCaption.addEventListener("click", function () {
        toggleToolbarCaptions(root);
        syncExportPopoverCopyUi();
      });
    }
    var popNarrative = pop.querySelector('[data-preview-chip="narrative"]');
    if (popNarrative) {
      popNarrative.addEventListener("click", function () {
        toggleToolbarNarrative(root);
        syncExportPopoverCopyUi();
      });
    }

    pop.querySelectorAll("[data-studio-longshot-platform]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var pid = btn.getAttribute("data-studio-longshot-platform") || "wechat_chat";
        var prev = readExportPrefs().platform || "wechat_chat";
        if (pid !== prev) {
          trackStudioEvent("longshot_platform_change", { from: prev, to: pid });
          // T-PLATFORM-PICK · 首次从微信群切到其他平台
          maybeShowPlatformPickTip(prev, pid, _showToolbarToast);
        }
        if (pid === "wechat_moments") {
          maybeToastSparseMoments();
        }
      });
    });

    var zipMoreBtn = pop.querySelector('[data-action="export-zip"]');
    if (zipMoreBtn) {
      zipMoreBtn.addEventListener("click", function () {
        closeStudioExportPopover();
        exportZip(_tripIdFromPath());
      });
    }
    var revealMoreBtn = pop.querySelector('[data-action="reveal-folder"]');
    if (revealMoreBtn) {
      revealMoreBtn.addEventListener("click", function () {
        closeStudioExportPopover();
        revealTripFolderQuick(_tripIdFromPath());
      });
    }

    // SFP D-SFP-11 · 小红书设置内「复制文案包」（成功前可达）
    var xhsPackBtn = pop.querySelector('[data-action="copy-xhs-pack"]');
    if (xhsPackBtn && !xhsPackBtn._sfpWired) {
      xhsPackBtn._sfpWired = true;
      xhsPackBtn.addEventListener("click", function () {
        var tid = _tripIdFromPath() || root._tripId || "";
        if (!tid) {
          _showToolbarToast("先打开一本画册");
          return;
        }
        xhsPackBtn.disabled = true;
        fetch("/__travelogue/trips/" + encodeURIComponent(tid) + "/entry")
          .then(function (r) {
            return r.ok ? r.json() : null;
          })
          .then(function (entry) {
            xhsPackBtn.disabled = false;
            var pack = (entry && entry.shareCopyPack) || {};
            var title = String(pack.title || "").trim();
            if (!title) {
              _showToolbarToast("先给画册起个名字");
              return;
            }
            var body = String(pack.body || "").trim();
            var topics = String(pack.topics || "#旅行日记").trim();
            var blob = title + "\n\n" + (body ? body + "\n\n" : "") + topics;
            var hint = pop.querySelector("[data-xhs-copy-hint]");
            if (hint) {
              hint.textContent = body
                ? "标题、正文与话题已备好"
                : "标题和话题已备好 · 正文可粘贴后自填";
            }
            if (navigator.clipboard && navigator.clipboard.writeText) {
              navigator.clipboard.writeText(blob).then(
                function () {
                  trackStudioEvent("sfp_xhs_copy_pack_copied", {
                    tripId: tid,
                    bodyEmpty: !body,
                    surface: "export_settings",
                  });
                  _showToolbarToast("文案包已复制");
                },
                function () {
                  _showToolbarToast("复制失败，请手动选中");
                }
              );
            } else {
              _showToolbarToast("当前环境无法复制，请手动选中");
            }
          })
          .catch(function () {
            xhsPackBtn.disabled = false;
            _showToolbarToast("文案包加载失败");
          });
      });
    }

    pop._applyDraft = function () {
      var draft = panel.getDraft();
      var prevPlatform = readExportPrefs().platform || "wechat_chat";
      var prevDensity = readExportPrefs().density || "default";
      var confirmedPlatform = draft.platform || "wechat_chat";
      // PRD-BATCH-EXPORT-MULTISELECT-V1 · draft.platforms 是多选真实来源，
      // 这里若漏写会导致确认后 localStorage 里只剩单值 platform，多选形同
      // 摆设（2026-08-06 Playwright 走查发现的回归，务必带上）。
      var confirmedPlatforms = normalizePlatformList(draft.platforms, confirmedPlatform);
      var nextDensity = draft.density === "compact" ? "compact" : "default";
      writeStoredLongshotPrefs(draft.mode, draft.scale);
      writeExportPrefs({
        platform: confirmedPlatform,
        platforms: confirmedPlatforms,
        mode: draft.mode,
        scale: draft.scale,
        slideCount: draft.slideCount,
        padMode: draft.padMode,
        includeAppendix: draft.includeAppendix === true,
        density: nextDensity,
      });
      // FE-SFI-09 · 密度档写入 trip 并走「更新版面」
      if (nextDensity !== prevDensity) {
        var tidDensity = _tripIdFromPath() || root._tripId || "";
        if (tidDensity) {
          postJson(
            "/" + encodeURIComponent(tidDensity) + "/__travelogue/save-copy",
            {
              patches: [{ path: "export.longshotDensity", value: nextDensity }],
            }
          )
            .then(function (res) {
              if (!res || res.status < 200 || res.status >= 300) {
                _showToolbarToast("密度未保存，请稍后重试");
                return;
              }
              _showToolbarToast(
                nextDensity === "compact"
                  ? "已切换紧凑档 · 长图已更新"
                  : "已切回默认密度 · 长图已更新"
              );
            })
            .catch(function () {
              _showToolbarToast("密度未保存，请稍后重试");
            });
        }
      }
      // Confirmed platform SSOT · 同步 session intent，清陈旧续跑 pending
      var mappedIntent = PLATFORM_TO_INTENT[confirmedPlatform] || null;
      var tripIdApply = _tripIdFromPath() || root._tripId || "";
      if (mappedIntent) {
        writeSessionIntent(tripIdApply, mappedIntent);
      } else {
        clearSessionIntent(tripIdApply);
      }
      _pendingExportPlatform = null;
      clearResumePlatform();
      if (confirmedPlatform && confirmedPlatform !== "wechat_chat") {
        maybeShowPlatformPickTip(prevPlatform, confirmedPlatform, _showToolbarToast);
        markMomentsCoachSeen();
      }
      if (confirmedPlatform === "wechat_moments") {
        maybeToastSparseMoments();
      }
      syncConfirmedExportSummary(pop);
      syncLongshotCtaLabel(root);
      refreshLongshotExportMeta(root);
    };

    // 永久确定处理器（不依赖 Promise once），保证 JS/辅助点击也能落盘 confirmed
    var okBtnAlways = pop.querySelector('[data-action="ok"]');
    if (okBtnAlways) {
      okBtnAlways.addEventListener("click", function () {
        if (typeof pop._applyDraft === "function") pop._applyDraft();
      });
    }
    pop._readDraftFromPrefs = function () {
      var prefs = readLongshotExportPrefs();
      if (panel.setDraft) {
        panel.setDraft({
          platform: prefs.platform,
          mode: prefs.mode,
          scale: prefs.scale,
          slideCount: prefs.slideCount,
          padMode: prefs.padMode,
          includeAppendix: prefs.includeAppendix === true,
        });
      }
      syncStudioExportPopoverUI(pop);
      syncExportPopoverCopyUi();
      syncConfirmedExportSummary(pop);
    };

    wrap.appendChild(pop);
    return pop;
  }

  function applyExportPopoverLayoutMode(pop) {
    if (!pop) return;
    var sheet = typeof window !== "undefined" && window.innerHeight < 560;
    pop.classList.toggle("preview-toolbar__export-popover--sheet", sheet);
    if (sheet) {
      pop.setAttribute("data-export-sheet", "1");
    } else {
      pop.removeAttribute("data-export-sheet");
    }
  }

  function trapExportPopoverFocus(pop) {
    if (!pop) return;
    var focusables = pop.querySelectorAll(
      'button:not([disabled]), [href], input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (!focusables.length) return;
    var first = focusables[0];
    var last = focusables[focusables.length - 1];
    function onKey(e) {
      if (e.key === "Escape") {
        e.preventDefault();
        if (typeof _activeExportPanelFinish === "function") {
          _activeExportPanelFinish(false);
        } else {
          _closeStudioExportPopoverUi();
        }
        return;
      }
      if (e.key !== "Tab" || focusables.length < 2) return;
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
    pop._focusTrapHandler = onKey;
    pop.addEventListener("keydown", onKey);
    window.setTimeout(function () {
      var ok = pop.querySelector('[data-action="ok"]');
      if (ok && typeof ok.focus === "function") ok.focus();
      else if (typeof first.focus === "function") first.focus();
    }, 0);
  }

  function releaseExportPopoverFocus(pop) {
    if (!pop || !pop._focusTrapHandler) return;
    pop.removeEventListener("keydown", pop._focusTrapHandler);
    pop._focusTrapHandler = null;
  }

  export function openStudioLongshotExportPanel(root) {
    return new Promise(function (resolve, reject) {
      var pop = ensureStudioExportPopover(root);
      if (!pop) {
        reject(new Error("no popover"));
        return;
      }
      // SFP D-SFP-10 · 浮层互斥：打开导出设置前关掉分章面板
      try {
        if (root && root._chapterPanel && typeof root._chapterPanel.close === "function") {
          root._chapterPanel.close();
        }
      } catch (_eChap) {
        /* ignore */
      }
      // Close any prior session without double-settle
      if (typeof _activeExportPanelFinish === "function") {
        _activeExportPanelFinish(false);
      } else {
        _closeStudioExportPopoverUi();
      }
      pop._readDraftFromPrefs();
      applyExportPopoverLayoutMode(pop);
      pop.hidden = false;
      try {
        document.documentElement.classList.add("preview-export-popover-open");
      } catch (eOpen) {}
      trapExportPopoverFocus(pop);

      var settled = false;
      var okBtn = pop.querySelector('[data-action="ok"]');
      var cancelBtn = pop.querySelector('[data-action="cancel"]');

      function finish(ok) {
        if (settled) return;
        settled = true;
        _activeExportPanelFinish = null;
        if (okBtn) okBtn.removeEventListener("click", onOk);
        if (cancelBtn) cancelBtn.removeEventListener("click", onCancel);
        _closeStudioExportPopoverUi();
        if (ok) resolve();
        else reject(new Error("cancelled"));
      }
      _activeExportPanelFinish = finish;

      function onOk() {
        // Draft apply is owned by the permanent OK listener — settle only (CQA D-10).
        finish(true);
      }
      function onCancel() {
        finish(false);
      }

      if (okBtn) okBtn.addEventListener("click", onOk);
      if (cancelBtn) cancelBtn.addEventListener("click", onCancel);

      _studioExportPopoverClose = function (e) {
        if (pop.contains(e.target)) return;
        if (root.querySelector(".preview-toolbar__longshot-caret") === e.target) return;
        finish(false);
      };
      window.setTimeout(function () {
        document.addEventListener("click", _studioExportPopoverClose, true);
      }, 0);
    });
  }

  export function openLongshotExportOptions(root) {
    // SFI FE-09 · ▾ 优先 Studio 面板（密度 / 双预览 / 平台 / 诚实标宽）；
    // 勿先走 TravelogueLongshot.openExportPanel，否则紧凑档入口不可达。
    openStudioLongshotExportPanel(root)
      .then(function () {
        refreshLongshotExportMeta(root);
        syncLongshotPreviewChips(root);
      })
      .catch(function () {
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
      });
  }

  export function revealTripPath(tripId, relPath) {
    return postJson("/__travelogue/reveal", { tripId: tripId, relPath: relPath });
  }

  /** ▾「更多输出」· 打开当前预览所在文件夹（避免 circular import features.js） */
  function revealTripFolderQuick(tripId) {
    if (!tripId) {
      _showToolbarToast("无法打开文件夹", { error: true });
      return;
    }
    fetch("/__travelogue/trips")
      .then(function (resp) {
        return resp.json();
      })
      .then(function (data) {
        var trips = data.trips || [];
        var trip = trips.filter(function (t) {
          return t.tripId === tripId;
        })[0];
        var rel = (trip && trip.previewRelPath) || "index.html";
        return revealTripPath(tripId, rel);
      })
      .catch(function () {
        _showToolbarToast("无法打开文件夹", { error: true });
      });
  }

  // FE-FST-05 / D-FST-13 · 禁止自动 reveal（成功后仅点击「在文件夹中显示」）

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

  export function pollJob(jobId, root, onDone, onSlow, kind, onTick) {
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
            // FE-SR-07 · stageHint 只作分类信号，不进第一行
            hint: job.stageHint || "正在合成长图…",
            pct: pct,
          });
        }
        // PRD-BATCH-EXPORT-MULTISELECT-V1 Stage 3 · 批量清单化进度，由调用方
        // （runBatchExport）自行决定怎么渲染，此处只做无条件转发。
        if (typeof onTick === "function") onTick(job);
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
      onError: function () {
        if (kind === "narrate") {
          narratePollCancel = null;
          return;
        }
        longshotPollCancel = null;
        if (jobId === longshotJobId) longshotJobId = null;
        // F-TRU-EXP-04 · 轮询断服
        applyDisconnectExportError(root, _tripIdFromPath());
        trackStudioEvent("longshot_export_fail", {
          error_code: "disconnect",
          trip_id: _tripIdFromPath(),
          surface: "preview",
          from: "poll",
        });
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
    if (prog) {
      prog.hidden = !visible;
      prog.classList.toggle(
        "preview-toolbar__export-progress--indeterminate",
        visible && typeof pct !== "number"
      );
    }
    if (fill && typeof pct === "number") fill.style.width = pct + "%";
    else if (fill && typeof pct !== "number") fill.style.width = "";
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
    btn.classList.remove("preview-toolbar__longshot--stale");
    if (zone) {
      zone.classList.remove("preview-toolbar__export-zone--stale");
      zone.classList.remove("preview-toolbar__export-zone--running");
    }
    var badge = root.querySelector(".preview-toolbar__export-stale");

    if (state === "running") {
      root._longshotStale = false;
      window.clearTimeout(root._longshotDoneIdleTimer);
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
          var human = humanExportProgress(opts);
          root._taskDock.updateExporting({
            title: human.title,
            subtitle: human.subtitle,
            // FE-FST-03 · null → indeterminate，勿假进度
            pct: typeof opts.pct === "number" ? opts.pct : null,
          });
        }
      } else {
        btn.innerHTML =
          '<span class="preview-toolbar__longshot__spinner" aria-hidden="true"></span> 正在保存…';
        setLongshotExportMeta(root, opts.hint || "正在生成可发微信的长图…", {
          actionable: false,
        });
        var pctRun = typeof opts.pct === "number" ? opts.pct : null;
        setLongshotExportProgress(root, true, pctRun);
      }
      if (badge) badge.hidden = true;
      return;
    }
    if (state === "done") {
      root._longshotStale = false;
      if (isV3) {
        // FE-DFX-30 · 稳定成功态：主钮短暂 done，Dock 为权威成功面
        btn.classList.add("preview-toolbar__longshot--done");
        setLongshotSplitState(root, "done");
        setLongshotControlsDisabled(root, false);
        if (isDock) {
          btn.innerHTML = dockLongshotIconHtml("done");
          setDockLongshotAria(btn, "done");
        } else {
          btn.textContent = "✓ 已保存";
        }
        root._exportDockActive = true;
        if (badge) badge.hidden = true;
        notifyHelpL1Idle(root);
        window.clearTimeout(root._longshotDoneIdleTimer);
        root._longshotDoneIdleTimer = window.setTimeout(function () {
          if (!btn.isConnected) return;
          btn.classList.remove("preview-toolbar__longshot--done");
          btn.classList.add("preview-toolbar__longshot--idle");
          setLongshotSplitState(root, "idle");
          if (isDock) {
            btn.innerHTML = dockLongshotIconHtml("idle");
            setDockLongshotAria(btn, "idle");
          }
          syncLongshotCtaLabel(root);
          root._exportDockActive = false;
        }, 8000);
        return;
      }
      btn.classList.add("preview-toolbar__longshot--done");
      setLongshotSplitState(root, "done");
      setLongshotControlsDisabled(root, false);
      btn.textContent = "✓ 已保存";
      setLongshotExportMeta(root, "点击查看详情", { actionable: true });
      setLongshotExportProgress(root, false);
      if (badge) badge.hidden = true;
      notifyHelpL1Idle(root);
      return;
    }
    if (state === "error") {
      root._longshotStale = false;
      btn.classList.add("preview-toolbar__longshot--idle");
      setLongshotSplitState(root, "idle");
      setLongshotControlsDisabled(root, false);
      if (isDock) {
        applyDockLongshotIdle(btn);
      }
      syncLongshotCtaLabel(root);
      var errPayload =
        opts.title || opts.linkHref
          ? {
              title: opts.title || opts.hint || "保存失败，请重试",
              subtitle: opts.subtitle || "",
              linkHref: opts.linkHref || "",
              linkText: opts.linkText || "",
            }
          : opts.hint || "保存失败，请重试";
      if (isV3) {
        root._exportDockActive = false;
        if (root._taskDock) root._taskDock.showError(errPayload);
        notifyHelpL1Idle(root);
      } else {
        var metaHint =
          typeof errPayload === "string"
            ? errPayload
            : errPayload.title +
              (errPayload.subtitle ? " · " + errPayload.subtitle : "");
        setLongshotExportMeta(root, metaHint, { actionable: false });
        setLongshotExportProgress(root, false);
        notifyHelpL1Idle(root);
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
        root._longshotStale = true;
        root._staleDockDismissed = false;
        if (badge) badge.hidden = true;
        _refreshTaskDockState(root);
      } else {
        if (badge) badge.hidden = false;
        setLongshotExportMeta(root, "内容已更新", { actionable: false });
        setLongshotExportProgress(root, false);
      }
      return;
    }
    root._longshotStale = false;
    btn.classList.add("preview-toolbar__longshot--idle");
    setLongshotSplitState(root, "idle");
    setLongshotControlsDisabled(root, false);
    if (isDock) {
      applyDockLongshotIdle(btn);
    }
    syncLongshotCtaLabel(root);
    root._exportDockActive = false;
    if (badge) badge.hidden = true;
    refreshLongshotExportMeta(root);
    if (!isV3) {
      setLongshotExportProgress(root, false);
    } else {
      _refreshTaskDockState(root);
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
        var resultV3 = job.result || {};
        var outsV3 = resultV3.outputs || [];
        trackStudioEvent("longshot_success_share_hint_shown", {
          trip_id: _tripIdFromPath(),
          segment_count: outsV3.length || 0,
        });
        // FE-FST-05 / D-FST-13 · 禁止自动 reveal；仅点击「在文件夹中显示」
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
    homeHint.className = "preview-toolbar__longshot-compat preview-toolbar__longshot-share-hint";
    var resultPlatform = result.platform || "wechat_chat";
    if (resultPlatform === "wechat_moments") {
      homeHint.textContent =
        "已保存 " +
        (outputs.length || 0) +
        " 张朋友圈长图连读 · 按 01→顺序发";
    } else if (resultPlatform === "xiaohongshu") {
      homeHint.textContent =
        "已保存 " +
        (outputs.length || 0) +
        " 张竖版拼贴海报（3:4）· 可发小红书";
    } else if (resultPlatform === "wechat_official") {
      homeHint.textContent =
        "已保存 " +
        (outputs.length || 0) +
        " 张竖版拼贴配图（3:4）· 可插入公众号图文";
    } else if (resultPlatform === "poster_bric") {
      homeHint.textContent = "已保存 1 张 3:4 拼贴海报";
    } else if (resultPlatform === "album_spread") {
      homeHint.textContent =
        "已保存 " +
        (outputs.length || 0) +
        " 张画册跨页（两卡 3:4+3:4+中缝，约 1.53:1）· 可预览或送印";
    } else {
      // FE-FST-04 · 默认成功面：已保存确认，不塞发群教学
      var drawerTitle = String(result.displayTitle || result.title || "").trim();
      homeHint.textContent = drawerTitle
        ? "《" + drawerTitle + "》长图已保存"
        : "长图已保存";
    }
    drawer.appendChild(homeHint);
    if (_copyGateBypassTitle) {
      var echo = document.createElement("p");
      echo.className = "preview-toolbar__longshot-compat";
      echo.textContent =
        "标题仍是「" + _copyGateBypassTitle + "」· 可回预览改";
      drawer.appendChild(echo);
      _copyGateBypassTitle = null;
    }
    trackStudioEvent("longshot_success_share_hint_shown", {
      trip_id: tripId,
      segment_count: outputs.length || 0,
    });

    if (segmented && outputs.length > 1) {
      var segEl = document.createElement("p");
      segEl.className = "preview-toolbar__longshot-compat";
      segEl.textContent =
        result.userHint ||
        "共 " + outputs.length + " 张，可按章发送";
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
        trackStudioEvent("ftue_reveal_folder", {
          tripId: tripId,
          source: "preview_drawer",
        });
        revealTripPath(tripId, outputs[0]);
      });
      actions.appendChild(revealBtn);
      // FE-FST-05 / D-FST-13 · 禁止自动 reveal
    }

    // FE-SR-08 / USR-03 · 非 Dock 成功面也提供换种分享
    var switchShareBtn = document.createElement("button");
    switchShareBtn.type = "button";
    switchShareBtn.className = "preview-toolbar__drawer-secondary";
    switchShareBtn.setAttribute("data-share-ready-switch", "1");
    switchShareBtn.textContent = "换种分享方式";
    switchShareBtn.addEventListener("click", function () {
      hideLongshotDrawer(root);
      offerSwitchShareMethod(root, tripId);
    });
    actions.appendChild(switchShareBtn);

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
    if (
      !shouldShowLongshotStale({
        layoutPending: !!_getLayoutPending(),
        sourceMissing: !!_getSourceMissing(),
        sideEffectActive: isExportSideEffectActive(_tripIdFromPath()),
        exportResultShowing: !!(root && root._exportResultShowing),
        longshotStale: true,
      })
    ) {
      return;
    }
    setLongshotExportState(root, "stale");
  }

  function fetchSourceStatus(tripId) {
    return fetch(
      "/__travelogue/trips/" + encodeURIComponent(tripId) + "/source-status"
    )
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        var missing = !!(data && data.ok !== false && data.sourceMissing);
        _setSourceMissing(missing);
        return data;
      })
      .catch(function () {
        return { ok: true, sourceMissing: false };
      });
  }

  function remountAlbumThenContinue(root, tripId, continueFn) {
    return postJson("/__travelogue/pick-folder", {})
      .then(function (res) {
        var data = (res && res.body) || {};
        if (data.cancelled) return false;
        if (!res || res.status >= 400 || data.ok === false || !data.albumPath) {
          _toolbarAlert(
            (data && data.message) || "无法打开文件夹选择器",
            { error: true }
          );
          return false;
        }
        return postJson("/__travelogue/storage/remount", {
          tripId: tripId,
          albumPath: data.albumPath,
        }).then(function (rem) {
          var body = (rem && rem.body) || {};
          var contentChanged = Number(body.contentChanged) || 0;
          trackStudioEvent("storage_remount_album", {
            trip_id: tripId,
            matched: body.matched || 0,
            unmatched: body.missing || 0,
            content_changed: contentChanged,
            ok: !!(body && body.ok),
          });
          if (!rem || rem.status >= 400 || body.ok === false) {
            _toolbarAlert(
              (body && body.message) || "重新指定相册失败",
              { error: true }
            );
            return false;
          }
          // AC-MRS-13 · partial match + content_changed: warn, do not silent continue
          if (contentChanged > 0) {
            _toolbarAlert(
              (body && body.message) ||
                "照片内容已变化，无法自动关联；请重新导入或跳过",
              { error: true }
            );
            return false;
          }
          _setSourceMissing(false);
          if (typeof continueFn === "function") continueFn();
          return true;
        });
      })
      .catch(function () {
        _toolbarAlert("重新指定相册失败", { error: true });
        return false;
      });
  }

  function maybeSourceMissingGate(root, tripId, continueFn) {
    return fetchSourceStatus(tripId).then(function (data) {
      if (!data || !data.sourceMissing) {
        continueFn();
        return;
      }
      trackStudioEvent("export_blocked_source_missing", { trip_id: tripId });
      return _toolbarConfirm({
        title: "原相册无法访问",
        body: "原相册已不存在或无法访问。请重新指定相册目录后，再继续导出。",
        confirmText: "重新指定相册目录",
        cancelText: "稍后",
        stacked: true,
      }).then(function (ok) {
        if (!ok) {
          _dismissSourceMissingDock();
          if (_refreshTaskDockState) _refreshTaskDockState(root);
          return;
        }
        return remountAlbumThenContinue(root, tripId, continueFn);
      });
    });
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
        // Trust V1 · 导出副作用窗口：忽略 renderBundleStale / longshotStale 升主警告
        if (isExportSideEffectActive(tripId)) {
          trackStudioEvent("stale_warned_within_60s_of_success", {
            trip_id: tripId,
            suppressed: true,
            render_bundle_stale: !!trip.renderBundleStale,
            longshot_stale: !!trip.longshotStale,
          });
          return;
        }
        if (trip.layoutCssStale || trip.renderBundleStale) {
          // SFC · 禁「产物/过期」工程腔；与 stale 主词「分享图需更新」同族
          var pendingMsg = trip.renderBundleStale
            ? "预览需更新，请重新渲染后再分享"
            : "版面需更新，请先更新版面再导出";
          if (trip.layoutCssStale && trip.renderBundleStale) {
            pendingMsg = "预览与版面需更新，请重新渲染后再分享";
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
        return fetchSourceStatus(tripId).then(function () {
          if (trip.longshotStale) {
            showStaleHint(root);
          }
        });
      })
      .catch(function () {});
  }

  export function exportZip(tripId) {
    var root = document.querySelector(".preview-toolbar");
    maybeSourceMissingGate(root, tripId, function () {
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
    });
  }

  export function startLongshot(root, tripId) {
    var btn = longshotBtnEl(root);
    if (!btn || btn.disabled) return;
    bindExportAfterLayoutPagehide();

    // MF-01 / MF-06 · layoutPending 时拦截，禁止静默导出旧长图
    if (_getLayoutPending()) {
      trackStudioEvent("longshot_export_blocked_pending", { trip_id: tripId });
      _toolbarConfirm({
        title: "导出前先更新一下",
        body: "你改过拼图或版式相关设置，导出前需先更新版面，否则长图仍是旧版。",
        confirmText: "更新并导出",
        secondaryText: "仅更新版面",
        cancelText: "取消",
        stacked: true,
        helpItemId: "H3",
        helpLinkText: "「分享图需更新」是什么意思 →",
      }).then(function (choice) {
        if (!choice) {
          trackStudioEvent("longshot_export_block_dismissed", {
            trip_id: tripId,
            via: "cancel",
          });
          return;
        }
        var thenExport = choice === true || choice === "confirm";
        var intent = thenExport ? "and_export" : "only";
        trackStudioEvent(
          thenExport ? "layout_update_and_export" : "layout_update_only",
          { trip_id: tripId }
        );

        var storageOk = writeLayoutUpdating(tripId);
        if (thenExport) {
          storageOk = writeExportAfterLayout(tripId) && storageOk;
        }
        if (!storageOk) {
          trackStudioEvent("export_after_layout_cleared", {
            reason: "storage_fail",
            trip_id: tripId,
          });
          _showToolbarToast("无法自动续导出，请更新版面后再点「长图」", {
            error: true,
            duration: 4000,
          });
        }

        setLongshotExportState(root, "running", { hint: "正在更新版面…" });
        if (root._taskDock) {
          var pendingPlatform = readExportPrefs().platform || "wechat_chat";
          root._taskDock.updateExporting({
            title: "正在更新版面…",
            subtitle: thenExport
              ? "完成后将自动导出"
              : "完成后可再点「" + shortCtaLabelForPlatform(pendingPlatform) + "」",
            pct: 6,
          });
          root._exportDockActive = true;
        }

        return _applyLayoutRerender(tripId, root, {
          intent: intent,
          busyMessage: "正在更新版面…",
          failMessage: thenExport
            ? "版面没有更新成功，长图尚未开始"
            : "版面没有更新成功，请重试",
          beforeReload: function () {
            markExpectLayoutReload();
            if (!thenExport) {
              _writeJsonStorage(sessionStorage, UPDATE_ONLY_HINT_KEY, {
                tripId: String(tripId || ""),
                ts: Date.now(),
              });
              clearLayoutUpdatingFlag();
              clearExportAfterLayoutFlag("update_only_ok");
            }
          },
          onFail: function (errorCode) {
            trackStudioEvent("layout_update_failed", {
              trip_id: tripId,
              intent: intent,
              error_code: errorCode || null,
            });
          },
        }).then(function (ok) {
          if (ok) {
            // 成功会整页刷新；仅更新的下一步提示见 consume / init
            return;
          }
          clearLayoutUpdatingFlag();
          _removeStorage(sessionStorage, UPDATE_ONLY_HINT_KEY);
          if (thenExport) {
            clearExportAfterLayoutFlag("layout_update_failed", { intent: intent });
          }
          setLongshotExportState(root, "error", {
            hint: thenExport
              ? "版面没有更新成功，长图尚未开始"
              : "版面没有更新成功，请重试",
          });
        });
      });
      return;
    }

    maybeSourceMissingGate(root, tripId, function () {
      startLongshotWithRecipe(root, tripId);
    });
  }

  function startLongshotWithRecipe(root, tripId) {
    if (!isOutputRecipeEnabled()) {
      maybeCopyGateThenExport(root, tripId);
      return;
    }
    fetchServerRecipe(tripId, "preview").then(function (res) {
      var tipRecipe;
      var keptN;
      if (res && res.ok && res.tipRecipe) {
        tipRecipe = res.tipRecipe;
        keptN = res.keptN;
        var domN = estimatePhotoCountFromDom(document);
        if (domN != null && keptN != null && Number(domN) !== Number(keptN)) {
          trackStudioEvent("recipe_keptn_dom_mismatch", {
            trip_id: tripId,
            server_kept_n: keptN,
            dom_estimate: domN,
          });
        }
      } else {
        // D-SR-13 · API 失败：降级 chat + 冻结 toast
        keptN = keptNForRecipe(tripId);
        tipRecipe = resolveClientRecipe(keptN, tripId, "preview");
        if (tipRecipe.needsIntent) {
          tipRecipe = resolveClientRecipe(keptN, tripId, "shelf");
        }
        _showToolbarToast(RECIPE_API_FAIL_TOAST, { duration: 4200 });
      }
      trackRecipeResolve({
        band: tipRecipe.band,
        needs_intent: tipRecipe.needsIntent,
        intent: tipRecipe.intent,
        platform: tipRecipe.platform,
        kept_n: keptN,
        source: tipRecipe.source,
      });
      syncLongshotCtaLabel(root);
      if (tipRecipe.needsIntent) {
        showAmbiguousIntentCard(keptN, tipRecipe.userHints).then(function (choice) {
          if (!choice || !choice.intent) return;
          writeSessionIntent(tripId, choice.intent);
          var platform = INTENT_TO_PLATFORM[choice.intent] || "wechat_chat";
          _pendingExportPlatform = platform;
          syncPrefsPlatform(platform);
          syncLongshotCtaLabel(root);
          if (!choice.exportNow) {
            _showToolbarToast("已记住分享方式 · 再点导出即可", { duration: 3200 });
            return;
          }
          maybeConfirmFullExportThen(root, tripId, function () {
            maybeCopyGateThenExport(root, tripId);
          });
        });
        return;
      }
      if (tipRecipe.platform) {
        _pendingExportPlatform = tipRecipe.platform;
        syncPrefsPlatform(tipRecipe.platform);
      }
      maybeConfirmFullExportThen(root, tripId, function () {
        maybeCopyGateThenExport(root, tripId);
      });
    });
  }

  function maybeConfirmFullExportThen(root, tripId, next) {
    var prefs = readExportPrefs();
    // CQA D-03 · prefs SSOT is `mode` (not segmentMode)
    var mode = prefs.mode === "full" ? "full" : "chapter";
    var platform =
      _pendingExportPlatform || prefs.platform || "wechat_chat";
    var keptN = keptNForRecipe(tripId);
    if (!needsFullExportConfirm(keptN, mode, platform)) {
      next();
      return;
    }
    _toolbarConfirm({
      title: "照片较多，确认导出整卷？",
      body: "建议按章导出，方便发送。整卷会合成一张很长的图。",
      confirmText: "仍导出整卷",
      secondaryText: "改用按章导出",
      cancelText: "取消",
      stacked: true,
    }).then(function (choice) {
      if (!choice) return;
      if (choice === "secondary") {
        try {
          var nextPrefs = readExportPrefs();
          nextPrefs.mode = "chapter";
          writeExportPrefs(nextPrefs);
        } catch (_e) {}
      }
      next();
    });
  }

  export function offerSwitchShareMethod(root, tripId) {
    clearSessionIntent(tripId);
    _pendingExportPlatform = null;
    if (!isOutputRecipeEnabled()) {
      _showToolbarToast("可在导出面板改选平台", { duration: 2800 });
      return;
    }
    fetchServerRecipe(tripId, "preview").then(function (res) {
      var keptN =
        res && res.ok && res.keptN != null ? res.keptN : keptNForRecipe(tripId);
      var hints =
        res && res.ok && res.tipRecipe ? res.tipRecipe.userHints : null;
      showAmbiguousIntentCard(keptN, hints).then(function (choice) {
        if (!choice || !choice.intent) return;
        writeSessionIntent(tripId, choice.intent);
        var platform = INTENT_TO_PLATFORM[choice.intent] || "wechat_chat";
        _pendingExportPlatform = platform;
        syncPrefsPlatform(platform);
        syncLongshotCtaLabel(root);
        if (choice.exportNow) {
          maybeConfirmFullExportThen(root, tripId, function () {
            maybeCopyGateThenExport(root, tripId);
          });
        } else {
          _showToolbarToast("已换种分享方式", { duration: 2800 });
        }
      });
    });
  }

  function copyGateSevereKey(tripId) {
    return COPY_GATE_SEVERE_KEY + String(tripId || "");
  }

  function maybeCopyGateThenExport(root, tripId) {
    var title = readMagazineTitleFromDom();
    var risk = assessMagazineTitleRisk(title);
    if (!risk) {
      _copyGateBypassTitle = null;
      runLongshotExport(root, tripId);
      return;
    }

    var severeForced = false;
    if (risk.level === "severe") {
      try {
        if (sessionStorage.getItem(copyGateSevereKey(tripId)) !== "1") {
          severeForced = true;
        }
      } catch (eSev) {
        severeForced = true;
      }
    }

    trackStudioEvent("copy_gate_shown", {
      trip_id: tripId,
      reason: risk.reason,
      level: risk.level,
      severe_forced: !!severeForced,
    });

    // F-TRU-COPY-06b · 首次出示即记 seen，再次同 trip 放宽 bypass（含取消后再点）
    if (severeForced) {
      try {
        sessionStorage.setItem(copyGateSevereKey(tripId), "1");
      } catch (eSeen) {}
    }

    var displayTitle = title || "（空）";
    var modalOpts = {
      title: "这个标题不太合适",
      body:
        "现在的标题：「" +
        displayTitle +
        "」。发群前建议改一下，朋友一眼能看懂。",
      confirmText: "改标题并导出",
      cancelText: "取消",
      stacked: true,
    };
    if (!severeForced) {
      modalOpts.secondaryText = "暂时不改，继续导出";
    }

    _toolbarConfirm(modalOpts).then(function (choice) {
      if (!choice) {
        trackStudioEvent("copy_gate_dismissed", { trip_id: tripId });
        return;
      }
      if (choice === "secondary") {
        trackStudioEvent("copy_gate_bypass", {
          trip_id: tripId,
          reason: risk.reason,
        });
        _copyGateBypassTitle = displayTitle;
        runLongshotExport(root, tripId);
        return;
      }
      // confirm / true → 改标题并导出
      var next = window.prompt("改成新的标题", title || "");
      if (next == null) return;
      next = String(next).trim();
      if (!next) {
        _showToolbarToast("标题不能为空", { error: true });
        return;
      }
      saveMagazineTitleValue(tripId, next).then(function (ok) {
        if (!ok) return;
        trackStudioEvent("copy_gate_fix", {
          trip_id: tripId,
          reason: risk.reason,
        });
        _copyGateBypassTitle = null;
        runLongshotExport(root, tripId);
      });
    });
  }

  function showUpdateOnlyNextStep(root) {
    if (root && root._taskDock && typeof root._taskDock.showNextStepHint === "function") {
      root._exportResultShowing = true;
      root._taskDock.showNextStepHint({
        title: "版面已更新",
        subtitle: "再点「长图」即可导出",
      });
      var hintBtn = longshotBtnEl(root);
      if (hintBtn) {
        hintBtn.classList.add("preview-toolbar__dock-btn--next-hint");
        window.setTimeout(function () {
          hintBtn.classList.remove("preview-toolbar__dock-btn--next-hint");
        }, 6000);
      }
      return;
    }
    _showToolbarToast("版面已更新 · 再点「长图」即可导出", { duration: 4000 });
  }

  /**
   * PRD-BATCH-EXPORT-MULTISELECT-V1 · 多选（2+ 个平台）批量提交/轮询/完成
   * 提示。所有平台统一走「自动」设置（无手风琴逐平台自定义，见该 PRD
   * D-BEX-01 的 v1 简化范围）。
   *
   * Stage 3 · Task Dock 清单化：有 `root._taskDock.showBatchChecklist` 时
   * （V3 Dock UI）用「批量导出中（i/N）+ 逐平台状态」清单替代单行 hint，
   * 完成时同一清单切到成功/部分失败态（不冒泡进 `showLongshotDrawer`——
   * 那是单结果形状的成功面，与 batch 的多结果形状不兼容）。旧版工具栏
   * （无 `_taskDock`）走原有单行 hint + toast 兜底，行为不变。
   */
  function runBatchExport(root, tripId, prefs, platforms) {
    var t0 = Date.now();
    var from = _exportStartFrom || "direct";
    _exportStartFrom = "direct";
    var itemLabels = platforms.map(function (id) {
      return shortCtaLabelForPlatform(id);
    });
    function hasChecklistDock() {
      return !!(root._taskDock && typeof root._taskDock.showBatchChecklist === "function");
    }

    /**
     * cur1Based：当前第几个平台在跑（1-based）；仅用于展示，不代表已知成败
     * （逐项真实成败要等 job 完成才拿到 `result.items`，见完成分支）。
     * `titleOverride` 用于「提交排队中」等尚未真正开始跑平台的过渡态文案。
     * `itemProgress`（2026-08-06 进度条增强）：`{cur, total}`，来自后端
     * `job.itemStageIndex`/`itemStageCount`——当前平台内部真实渲染进度（如
     * 拼贴页 3/5）；驱动总进度条 + 单项细进度条，让清单在长耗时任务里也能
     * 看到"活的"进展，而不是卡在同一个百分比不动。
     */
    function renderBatchProgress(cur1Based, titleOverride, itemProgress) {
      var cur = Math.max(1, Number(cur1Based) || 1);
      var total = platforms.length;
      var defaultTitle = "批量导出中（" + cur + "/" + total + "）";
      setLongshotExportState(root, "running", {
        hint: titleOverride || defaultTitle + " · " + (itemLabels[cur - 1] || ""),
      });
      if (hasChecklistDock()) {
        root._taskDock.showBatchChecklist({
          title: titleOverride || defaultTitle,
          items: batchChecklistItems(platforms, cur, itemProgress),
          overallProgress: batchOverallProgressRatio(platforms, cur, itemProgress),
          done: false,
        });
      }
    }

    renderBatchProgress(1);
    _setSlowHint(root, "", false);

    trackStudioEvent("longshot_export_start", {
      platform: "batch:" + platforms.join(","),
      scale: prefs.scale,
      slide_count: null,
      photo_count: estimatePhotoCountFromDom(document),
      trip_id: tripId,
      surface: "preview",
      from: from,
    });

    var req = {
      tripId: tripId,
      scale: prefs.scale,
      format: "png",
      copyDisplay: prefs.copyDisplay,
      segmentMode: normalizeSegmentMode(prefs.mode),
      entrypoint: "preview",
      includeAppendix: prefs.includeAppendix === true,
      platforms: platforms.map(function (id) {
        return { platform: id };
      }),
    };

    function trackBatchFail(errorCode, hint) {
      trackStudioEvent("longshot_export_fail", {
        platform: "batch:" + platforms.join(","),
        error_code: errorCode,
        trip_id: tripId,
        surface: "preview",
        from: from,
      });
      // hint === null → 调用方（如断连分支）自行接管 setLongshotExportState。
      if (hint != null) {
        setLongshotExportState(root, "error", { hint: hint });
      }
    }

    postJsonBusyRetry("/__travelogue/longshot", req, {
      onBusy: function () {
        renderBatchProgress(1, "批量导出排队中，请稍候…");
      },
    })
      .then(function (res) {
        if (isJobBusy409(res)) {
          trackBatchFail("E_STUDIO_JOB_BUSY", "导出排队超时，请稍后再试");
          return;
        }
        if (res.status === 400) {
          var msg400 = (res.body && res.body.message) || "批量导出提交失败";
          trackBatchFail((res.body && res.body.error) || "E_LNG2_INVALID_BATCH_ITEM", msg400);
          _showToolbarToast(msg400, { error: true });
          return;
        }
        if (res.status === 409) {
          trackBatchFail(
            (res.body && res.body.error) || "E_STUDIO_JOB_BUSY",
            (res.body && res.body.message) || "请稍候再试"
          );
          return;
        }
        if (res.status !== 202 || !res.body.jobId) {
          trackBatchFail("E_LNG2_START_FAILED", "无法开始批量导出");
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
              markExportPulseSeen(tripId);
              writeExportSideEffect(tripId);
              var summary = formatBatchSuccess(result);
              trackStudioEvent("longshot_export_success", {
                platform: "batch:" + platforms.join(","),
                output_count: (result.items || []).reduce(function (n, it) {
                  return n + ((it.outputs && it.outputs.length) || 0);
                }, 0),
                target_page_count: null,
                duration_ms: Date.now() - t0,
                trip_id: tripId,
                surface: "preview",
                from: from,
                batch_succeeded: result.succeededCount,
                batch_failed: result.failedCount,
              });
              setLongshotExportState(root, "done");
              try {
                markLongshotReady(tripId);
              } catch (_readyErr) {}
              if (hasChecklistDock()) {
                // Stage 3 · 清单化完成面：逐项 ✅/✗ + 各自 detail（张数/失败原因）。
                var firstOutput = null;
                (result.items || []).some(function (it) {
                  if (it.ok && it.outputs && it.outputs.length) {
                    firstOutput = it.outputs[0];
                    return true;
                  }
                  return false;
                });
                root._taskDock.showBatchChecklist({
                  title: summary.title,
                  items: batchChecklistItemsFromResult(result),
                  done: true,
                  tripId: tripId,
                  firstOutput: firstOutput,
                });
              } else {
                try {
                  var toastMsg =
                    summary.title +
                    (summary.lines.length ? " · " + summary.lines.join("；") : "");
                  if (typeof studioToast === "function") {
                    studioToast(toastMsg, { duration: 6000 });
                  } else {
                    _showToolbarToast(toastMsg, { error: summary.failedCount > 0 });
                  }
                } catch (_toastErr) {}
              }
              try {
                trackStudioEvent("export_ok_toast_shown", {
                  platform: "batch:" + platforms.join(","),
                  output_count: summary.succeededCount,
                  trip_id: tripId,
                });
              } catch (_toastErr2) {}
              try {
                window.dispatchEvent(
                  new CustomEvent("travelogue:longshot-export-ready", {
                    detail: { tripId: tripId, platform: platforms[0], batch: true },
                  })
                );
              } catch (_evErr) {}
            } else if (job.status === "failed") {
              var err = job.error || {};
              trackBatchFail(err.code || "E_EXPORT_LONGSHOT", err.message || "批量导出失败");
            } else if (job.status === "cancelled") {
              trackStudioEvent("longshot_export_cancel", {
                trip_id: tripId,
                surface: "preview",
                from: from,
                source: "poll",
              });
              setLongshotExportState(root, "idle");
              _showToolbarToast("已取消导出");
            } else {
              setLongshotExportState(root, "idle");
            }
          },
          function () {
            _setSlowHint(root, "比预期久一些，请耐心等待…", true);
          },
          "batch",
          function (job) {
            if (job.status !== "running") return;
            // 后端 stageHint 形如「[1/2] xiaohongshu · 正在合成拼贴…」，英文平台
            // id 不适合直接展示；这里只取 stageIndex 驱动清单态，展示文案统一
            // 由 renderBatchProgress 用 itemLabels 生成，保持可读一致。
            var cur = Number(job.stageIndex);
            // itemStageIndex/itemStageCount：当前平台自己内部的真实渲染进度
            // （如拼贴页 cur/total），与 stageIndex（第几个平台）语义正交。
            var itemCur = Number(job.itemStageIndex);
            var itemTotal = Number(job.itemStageCount);
            var itemProgress =
              isFinite(itemTotal) && itemTotal > 0 && isFinite(itemCur) && itemCur >= 0
                ? { cur: itemCur, total: itemTotal }
                : null;
            renderBatchProgress(isFinite(cur) && cur > 0 ? cur : 1, null, itemProgress);
          }
        );
      })
      .catch(function () {
        trackBatchFail("disconnect", null);
        applyDisconnectExportError(root, tripId);
      });
  }

  function runLongshotExport(root, tripId) {
    var btn = longshotBtnEl(root);
    if (!btn || btn.disabled) return;
    _setToolbarCollapsed(root, false, false);
    hideLongshotDrawer(root);

    var prefs = readLongshotExportPrefs();
    // PRD-BATCH-EXPORT-MULTISELECT-V1 · 多选（2+ 个平台）走独立的批量分支，
    // 完全不进入下方任何单平台专属逻辑（resume-after-layout / intent 映射 /
    // Task Dock 抽屉渲染等），避免混用两套结果形状（single vs `{batch:true}`）。
    if (prefs.platforms && prefs.platforms.length > 1) {
      runBatchExport(root, tripId, prefs, prefs.platforms);
      return;
    }
    // AC-DFX-01 · confirmed prefs 为默认权威；resume 仅在「更新版面后续跑」激活时优先
    var prefsPlatform = prefs.platform || "wechat_chat";
    var afterLayout = isExportAfterLayoutActive(tripId);
    var platform =
      _pendingExportPlatform ||
      (afterLayout ? readResumePlatform(tripId) : null) ||
      prefsPlatform;
    _pendingExportPlatform = null;
    if (platform !== prefsPlatform) {
      syncPrefsPlatform(platform);
    }
    var runningHint =
      platform === "moments_grid"
        ? "正在导出九宫格（CLI）…"
        : platform === "wechat_moments"
          ? "正在导出朋友圈长图连读…"
          : platform === "xiaohongshu"
            ? "正在导出小红书竖版拼贴海报…"
            : platform === "wechat_official"
              ? "正在导出公众号竖版拼贴配图…"
              : platform === "poster_bric"
                ? "正在导出单张海报…"
                : platform === "album_spread"
                  ? "正在导出画册跨页…"
                  : "正在保存…";
    setLongshotExportState(root, "running", { hint: runningHint });
    _setSlowHint(root, "", false);

    var t0 = Date.now();
    var from = _exportStartFrom || "direct";
    _exportStartFrom = "direct";
    trackStudioEvent("longshot_export_start", {
      platform: platform,
      scale: prefs.scale,
      slide_count: prefs.slideCount == null ? null : prefs.slideCount,
      photo_count: estimatePhotoCountFromDom(document),
      trip_id: tripId,
      surface: "preview",
      from: from,
    });

    var req = buildLongshotRequestFromPage(tripId);
    if (req && platform) {
      req.platform = platform;
      var mapped = PLATFORM_TO_INTENT[platform];
      if (mapped) req.intent = mapped;
    }
    if (!assertConfirmedPlatformPayload(readExportPrefs().platform || prefsPlatform, req && req.platform)) {
      setLongshotExportState(root, "idle");
      _showToolbarToast("导出目标不一致，请重新在导出设置里确认", { error: true });
      return;
    }

    function finishClientFallback() {
      setLongshotExportState(root, "running", { hint: "正在使用兼容模式保存…" });
      return runClientLongshotFallback(root, tripId, {
        platform: platform,
        prefs: prefs,
      }).then(function (job) {
        _setSlowHint(root, "", false);
        if (job.status === "succeeded") {
          markExportPulseSeen(tripId);
          writeExportSideEffect(tripId);
          trackStudioEvent("longshot_export_success", {
            platform: (job.result && job.result.platform) || platform,
            output_count: (job.result && job.result.outputs && job.result.outputs.length) || 0,
            target_page_count: job.result && job.result.pageCount != null ? job.result.pageCount : null,
            duration_ms: Date.now() - t0,
            trip_id: tripId,
            surface: "preview",
            from: from,
            capture_method: "p2",
          });
          setLongshotExportState(root, "done");
          showLongshotDrawer(root, job);
        } else {
          trackStudioEvent("longshot_export_fail", {
            platform: platform,
            error_code: (job.error && job.error.code) || "E_LNG_CAPTURE_FAILED",
            trip_id: tripId,
            surface: "preview",
            from: from,
            capture_method: "p2",
          });
          setLongshotExportState(root, "error");
          showLongshotDrawer(root, job);
        }
      });
    }

    postJsonBusyRetry("/__travelogue/longshot", req, {
      onBusy: function () {
        var busyHint =
          platform === "wechat_moments"
            ? "朋友圈连读排队中，请稍候…"
            : platform === "xiaohongshu"
              ? "小红书海报排队中，请稍候…"
              : platform === "wechat_official"
                ? "公众号配图排队中，请稍候…"
                : platform === "poster_bric"
                  ? "单张海报排队中，请稍候…"
                  : platform === "album_spread"
                    ? "画册跨页排队中，请稍候…"
                    : "排队中，请稍候…";
        setLongshotExportState(root, "running", { hint: busyHint });
      },
    })
      .then(function (res) {
        if (isJobBusy409(res)) {
          trackStudioEvent("longshot_export_fail", {
            platform: platform,
            error_code: "E_STUDIO_JOB_BUSY",
            trip_id: tripId,
            surface: "preview",
            from: from,
          });
          clearResumePlatform();
          setLongshotExportState(root, "error", {
            hint:
              from === "after_layout"
                ? "版面已更新，长图还在排队，请稍后再点「长图」"
                : "导出排队超时，请稍后再试",
          });
          return;
        }
        var failHint =
          from === "after_layout"
            ? "版面已更新，长图没有保存成功，可再点「长图」"
            : null;
        if (res.status === 409) {
          var errCode = (res.body && res.body.error) || "E_STUDIO_JOB_BUSY";
          trackStudioEvent("longshot_export_fail", {
            platform: platform,
            error_code: errCode,
            trip_id: tripId,
            surface: "preview",
            from: from,
          });
          clearResumePlatform();
          // D-PCU-10 · 结构未确认：引导打开分章面板
          if (errCode === "E_PIPELINE_ORDER") {
            if (typeof root._openChapterPanel === "function") {
              root._openChapterPanel({ pending: true });
            }
            _showToolbarToast(
              (res.body && res.body.message) || "请先在「分章」中确认章节顺序",
              { error: true }
            );
            setLongshotExportState(root, "idle");
            return;
          }
          setLongshotExportState(root, "error", {
            hint: failHint || (res.body && res.body.message) || "请稍候再试",
          });
          return;
        }
        // M-INS-0c · server asks client to run html2canvas track
        if (res.status === 200 && res.body && res.body.fallback === "client") {
          clearResumePlatform();
          return finishClientFallback();
        }
        if (res.status !== 202 || !res.body.jobId) {
          trackStudioEvent("longshot_export_fail", {
            platform: platform,
            error_code: "E_LNG2_START_FAILED",
            trip_id: tripId,
            surface: "preview",
            from: from,
          });
          clearResumePlatform();
          setLongshotExportState(root, "error", {
            hint: failHint || "无法开始导出",
          });
          return;
        }
        clearResumePlatform();
        longshotJobId = res.body.jobId;
        pollJob(
          res.body.jobId,
          root,
          function (job) {
            _setSlowHint(root, "", false);
            if (job.status === "succeeded") {
              var result = job.result || {};
              markExportPulseSeen(tripId);
              writeExportSideEffect(tripId);
              trackStudioEvent("longshot_export_success", {
                platform: result.platform || platform,
                output_count: (result.outputs && result.outputs.length) || 0,
                target_page_count: result.pageCount != null ? result.pageCount : null,
                duration_ms: Date.now() - t0,
                trip_id: tripId,
                surface: "preview",
                from: from,
              });
              setLongshotExportState(root, "done");
              showLongshotDrawer(root, job);
              // FE-DFX-30 / D5 · 书架「分享图已就绪」会话标记
              try {
                markLongshotReady(tripId);
              } catch (_readyErr) {}
              // FE-DFX-30 · Dock 为主；toast 短提示叠加
              try {
                var nOut = (result.outputs && result.outputs.length) || 0;
                var toastLabel = shortCtaLabelForPlatform(
                  result.platform || platform || "wechat_chat"
                );
                var toastMsg =
                  nOut > 1
                    ? "已导出 " + nOut + " 张 · " + toastLabel
                    : "已导出 · " + toastLabel;
                if (typeof studioToast === "function") {
                  studioToast(toastMsg, { duration: 4000 });
                } else {
                  _showToolbarToast(toastMsg);
                }
                trackStudioEvent("export_ok_toast_shown", {
                  platform: result.platform || platform,
                  output_count: nOut,
                  trip_id: tripId,
                });
              } catch (_toastErr) {}
              try {
                window.dispatchEvent(
                  new CustomEvent("travelogue:longshot-export-ready", {
                    detail: { tripId: tripId, platform: result.platform || platform },
                  })
                );
              } catch (_evErr) {}
            } else if (job.status === "failed") {
              var err = job.error || {};
              // Playwright missing mid-job → auto client track (non-terminal).
              if (err.code === "E_LNG_PLAYWRIGHT") {
                finishClientFallback();
                return;
              }
              trackStudioEvent("longshot_export_fail", {
                platform: platform,
                error_code: err.code || "E_EXPORT_LONGSHOT",
                trip_id: tripId,
                surface: "preview",
                from: from,
              });
              if (from === "after_layout") {
                setLongshotExportState(root, "error", {
                  hint: "版面已更新，长图没有保存成功，可再点「长图」",
                });
              } else {
                setLongshotExportState(root, "error");
                showLongshotDrawer(root, job);
              }
            } else if (job.status === "cancelled") {
              trackStudioEvent("longshot_export_cancel", {
                trip_id: tripId,
                surface: "preview",
                from: from,
                source: "poll",
              });
              setLongshotExportState(root, "idle");
              _showToolbarToast("已取消导出");
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
          error_code: "disconnect",
          trip_id: tripId,
          surface: "preview",
          from: from,
        });
        clearResumePlatform();
        // F-TRU-EXP-04 · 启动请求断服
        applyDisconnectExportError(root, tripId);
      });
  }

  /** FE-DFX-43 · FTUE「保存长图」续跑：query/session → 默认 wechat_chat 导出 */
  export function consumeAutoExport(root, tripId) {
    var platform = null;
    try {
      var q = new URLSearchParams(location.search || "").get("autoExport");
      if (q) platform = String(q).trim() || "wechat_chat";
    } catch (_q) {}
    var flagged = _readJsonStorage(sessionStorage, AUTO_EXPORT_KEY);
    if (flagged) {
      _removeStorage(sessionStorage, AUTO_EXPORT_KEY);
      if (
        flagged.ts &&
        Date.now() - Number(flagged.ts) <= AUTO_EXPORT_TTL_MS &&
        String(flagged.tripId || "") === String(tripId || "")
      ) {
        platform = String(flagged.platform || platform || "wechat_chat");
      }
    }
    if (!platform) return false;
    if (platform !== "wechat_chat" && platform !== "chat_longshot") {
      platform = "wechat_chat";
    } else {
      platform = "wechat_chat";
    }
    try {
      if (location.search && /(?:^|[?&])autoExport=/.test(location.search)) {
        var url = new URL(location.href);
        url.searchParams.delete("autoExport");
        history.replaceState(null, "", url.pathname + url.search + url.hash);
      }
    } catch (_hist) {}
    _exportStartFrom = "ftue_save_longshot";
    _pendingExportPlatform = platform;
    writeResumePlatform(tripId, platform);
    syncPrefsPlatform(platform);
    maybeCopyGateThenExport(root, tripId);
    return true;
  }

  export function consumeExportAfterLayout(root, tripId) {
    bindExportAfterLayoutPagehide();
    _removeStorage(sessionStorage, EXPECT_LAYOUT_RELOAD_KEY);

    var updating = readLayoutUpdating();
    if (updating && String(updating.tripId || "") === String(tripId || "")) {
      if (isFlagExpired(updating)) {
        clearLayoutUpdatingFlag();
      } else {
        setLongshotExportState(root, "running", { hint: "正在更新版面…" });
        if (root._taskDock) {
          root._exportDockActive = true;
          root._taskDock.updateExporting({
            title: "正在更新版面…",
            subtitle: "即将开始导出",
            pct: 12,
          });
        }
      }
    }

    var flagged = readExportAfterLayout();
    if (!flagged) {
      clearLayoutUpdatingFlag();
      var onlyHint = _readJsonStorage(sessionStorage, UPDATE_ONLY_HINT_KEY);
      if (
        onlyHint &&
        String(onlyHint.tripId || "") === String(tripId || "") &&
        !isFlagExpired(onlyHint)
      ) {
        _removeStorage(sessionStorage, UPDATE_ONLY_HINT_KEY);
        showUpdateOnlyNextStep(root);
      } else {
        _removeStorage(sessionStorage, UPDATE_ONLY_HINT_KEY);
      }
      return false;
    }

    var flaggedId = String(flagged.tripId || "");
    var currentId = String(tripId || "");

    clearExportAfterLayoutFlag("consume", { flagged_id: flaggedId });
    _removeStorage(sessionStorage, UPDATE_ONLY_HINT_KEY);

    if (isFlagExpired(flagged)) {
      clearLayoutUpdatingFlag();
      trackStudioEvent("export_after_layout_expired", { trip_id: currentId });
      return false;
    }
    if (!flaggedId || flaggedId !== currentId) {
      clearLayoutUpdatingFlag();
      trackStudioEvent("export_after_layout_trip_mismatch", {
        flagged_id: flaggedId,
        current_id: currentId,
      });
      return false;
    }
    if (_getLayoutPending()) {
      clearLayoutUpdatingFlag();
      return false;
    }

    clearLayoutUpdatingFlag();
    var latencyMs =
      flagged.ts && Number(flagged.ts) ? Date.now() - Number(flagged.ts) : null;
    trackStudioEvent("export_after_layout_consumed", {
      trip_id: currentId,
      latency_ms: latencyMs,
      platform: flagged.platform || null,
    });
    _exportStartFrom = "after_layout";
    var resumePlatform =
      flagged.platform || readResumePlatform(currentId) || resolveExportPlatform();
    if (resumePlatform) {
      _pendingExportPlatform = resumePlatform;
      writeResumePlatform(currentId, resumePlatform);
      syncPrefsPlatform(resumePlatform);
    }
    // 续跑后若仍有标题风险，再跑门禁；否则直接导出
    maybeCopyGateThenExport(root, tripId);
    return true;
  }
