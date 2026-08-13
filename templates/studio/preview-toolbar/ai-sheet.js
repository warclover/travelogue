/**
 * Studio AI Surface V1 (SAS) · preview Dock「AI」+ Sheet
 * PRD-STUDIO-AI-SURFACE-V1 · W1 壳/杂志/装帧 · W2 意图/建议/徽标/旧入口深链
 */
"use strict";

import { trackStudioEvent } from "../js/analytics.js";
import {
  ensureAiSurfaceHydrated,
  isAiSurfaceEnabled,
} from "../js/ai-surface.js";
import { DARK_COPY } from "../js/ai-surface-dark-copy.js";
import { closeHelpDrawer, isHelpDrawerOpen } from "../js/help-drawer.js";
import { postJson, postJsonConflictRetry, studioAuthHeaders } from "../js/http.js";
import { pollJobUntilDone } from "../js/job-poll.js";
import { dockIconSvg } from "./dock.js";
import { fetchEntry, startLlmNarrate } from "./core.js";
import { closeStudioExportPopover } from "./longshot.js";
import {
  reloadPreviewAfterLayout,
  showToolbarToast,
  tripApiBase,
  tripRestBase,
  tripIdFromPath,
} from "./shell.js";

var TITLE_ART_ROUTE_C_PREF_KEY = "travelogue.studio.titleArtRouteC";
var BODY_OPEN_CLASS = "preview-ai-sheet-open";
var DISMISS_KEY_PREFIX = "travelogue.studio.aiSheet.dismissed.";
var BADGE_SEEN_KEY_PREFIX = "travelogue.studio.aiSheet.badgeSeen.";

function escapeHtml(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function clipSuggestion(text) {
  var t = String(text || "").trim();
  if (t.length <= 28) return t;
  if (t.length <= 36) return t;
  return t.slice(0, 36);
}

function suggestionKey(s) {
  if (!s) return "";
  return (
    String(s.chapterId || "") +
    "|" +
    String(s.suggestedPatternId || s.suggestion || "")
  );
}

function readJsonList(storageKey) {
  try {
    var raw = localStorage.getItem(storageKey);
    if (!raw) return [];
    var parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.map(String) : [];
  } catch (_e) {
    return [];
  }
}

function writeJsonList(storageKey, list) {
  try {
    localStorage.setItem(storageKey, JSON.stringify(list || []));
  } catch (_e) {}
}

function closePeers(root) {
  var closed = [];
  try {
    var pop = document.querySelector(".preview-export-popover:not([hidden])");
    if (pop) closed.push("export");
  } catch (_ePop) {}
  closeStudioExportPopover();
  if (typeof isHelpDrawerOpen === "function" && isHelpDrawerOpen()) {
    closeHelpDrawer();
    closed.push("help");
  }
  if (root._chapterPanel && root._chapterPanel.isOpen()) {
    root._chapterPanel.close();
    closed.push("chapter");
  }
  if (root._sheet && typeof root._sheet.isOpen === "function" && root._sheet.isOpen()) {
    root._sheet.close("ai_sheet");
    closed.push("refine");
  }
  if (closed.length) {
    trackStudioEvent("snr_panel_mutex", {
      opened: "ai_sheet",
      closed: closed,
    });
  }
}

/**
 * @param {HTMLElement} root preview-toolbar root
 * @param {string} tripId
 * @param {{ insertBefore?: HTMLElement|null }} opts
 */
export function mountAiSurface(root, tripId, opts) {
  opts = opts || {};
  if (!root || root._aiSheet) return root._aiSheet || null;
  tripId = tripId || tripIdFromPath();
  var dock = root.querySelector(".preview-toolbar__dock") || root;
  var openAt = 0;
  var shell = null;
  var btn = null;
  var llmAvailable = false;
  /** @type {boolean | null} */
  var lastPingOk = null;
  var llmConfigured = false;
  var connectionOk = false;
  var copyReady = false;
  var titleArtEnabled = false;
  var titleArtRouteCEnabled = false;
  var titleArtBusy = false;
  var intentBusy = false;
  /** @type {Record<string, any> | null} */
  var entryCache = null;
  var pendingFocus = null;
  var hasBadge = false;
  /** SNR COPY-SNR-S01 · 运行时覆盖：生成中 / 失败可重试（成功后由 posture 接管） */
  var narrateRuntimeStatus = "";

  btn = document.createElement("button");
  btn.type = "button";
  btn.className =
    "preview-toolbar__dock-btn preview-toolbar__dock-btn--ai preview-toolbar__dock-btn--labeled preview-toolbar__ctl";
  btn.setAttribute("aria-label", "AI");
  btn.setAttribute("aria-haspopup", "dialog");
  btn.setAttribute("aria-expanded", "false");
  btn.innerHTML =
    dockIconSvg("ai") + '<span class="preview-toolbar__dock-label">AI</span>';

  var before = opts.insertBefore || null;
  if (before && before.parentNode === dock) {
    dock.insertBefore(btn, before);
  } else {
    dock.appendChild(btn);
  }

  function dismissKey() {
    return DISMISS_KEY_PREFIX + String(tripId || "global");
  }

  function badgeSeenKey() {
    return BADGE_SEEN_KEY_PREFIX + String(tripId || "global");
  }

  function dismissedSet() {
    var out = {};
    readJsonList(dismissKey()).forEach(function (k) {
      out[k] = true;
    });
    return out;
  }

  function badgeSeenSet() {
    var out = {};
    readJsonList(badgeSeenKey()).forEach(function (k) {
      out[k] = true;
    });
    return out;
  }

  function markDismissed(key) {
    if (!key) return;
    var list = readJsonList(dismissKey());
    if (list.indexOf(key) < 0) list.push(key);
    writeJsonList(dismissKey(), list);
  }

  function markBadgeSeen(keys) {
    var list = readJsonList(badgeSeenKey());
    (keys || []).forEach(function (k) {
      if (k && list.indexOf(k) < 0) list.push(k);
    });
    writeJsonList(badgeSeenKey(), list);
  }

  function pendingSuggestions(entry) {
    var dismissed = dismissedSet();
    var list = (entry && entry.layoutSuggestions) || [];
    return list.filter(function (s) {
      if (!s || !s.suggestion || s.accepted) return false;
      return !dismissed[suggestionKey(s)];
    });
  }

  function computeBadge(entry) {
    var pending = pendingSuggestions(entry);
    if (!pending.length) return false;
    var seen = badgeSeenSet();
    return pending.some(function (s) {
      return !seen[suggestionKey(s)];
    });
  }

  function setBadge(on) {
    hasBadge = !!on;
    btn.classList.toggle("has-badge", hasBadge);
    btn.setAttribute("data-has-badge", hasBadge ? "1" : "0");
  }

  function refreshBadgeFromEntry(entry) {
    entryCache = entry || entryCache;
    setBadge(computeBadge(entryCache));
  }

  function loadEntry() {
    return fetchEntry(tripId).then(function (entry) {
      entryCache = entry || {};
      refreshBadgeFromEntry(entryCache);
      return entryCache;
    });
  }

  function isOpen() {
    return !!(shell && !shell.hidden);
  }

  function setBtnActive(on) {
    btn.classList.toggle("is-active", !!on);
    btn.setAttribute("aria-expanded", on ? "true" : "false");
  }

  function trackAction(action, extra) {
    var meta = Object.assign({ action: action }, extra || {});
    trackStudioEvent("ai_sheet_action_click", meta);
  }

  function trackResult(action, ok, extra) {
    var meta = Object.assign(
      { action: action, ok: !!ok },
      extra || {}
    );
    trackStudioEvent("ai_sheet_action_result", meta);
  }

  function chapterTitle(chapterId) {
    var chapters = (entryCache && entryCache.chapters) || [];
    for (var i = 0; i < chapters.length; i++) {
      if (chapters[i] && chapters[i].id === chapterId) {
        return chapters[i].title || chapterId;
      }
    }
    return chapterId || "某章";
  }

  function ensureShell() {
    if (shell) return shell;
    shell = document.createElement("div");
    shell.className = "preview-ai-sheet-root";
    shell.hidden = true;
    shell.innerHTML =
      '<div class="preview-ai-sheet__scrim" data-ai-sheet-scrim></div>' +
      '<aside class="preview-ai-sheet" role="dialog" aria-modal="true" aria-labelledby="preview-ai-sheet-title">' +
      '<header class="preview-ai-sheet__head">' +
      '<div class="preview-ai-sheet__head-text">' +
      '<h2 id="preview-ai-sheet-title" class="preview-ai-sheet__title">AI</h2>' +
      '<p class="preview-ai-sheet__sub" data-ai-sheet-sub>AI能力 · 需配置模型API后方可使用</p>' +
      "</div>" +
      '<button type="button" class="preview-ai-sheet__close" data-ai-sheet-close aria-label="关闭">×</button>' +
      "</header>" +
      '<div class="preview-ai-sheet__body" data-ai-sheet-body></div>' +
      "</aside>";
    document.body.appendChild(shell);

    shell.querySelector("[data-ai-sheet-scrim]").addEventListener("click", function () {
      close("scrim");
    });
    shell.querySelector("[data-ai-sheet-close]").addEventListener("click", function (e) {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }
      close("close_btn");
    });
    return shell;
  }

  function onDocKeydown(e) {
    if (!e || e.key !== "Escape") return;
    if (!isOpen()) return;
    e.preventDefault();
    close("escape");
  }

  function renderBody() {
    var body = shell.querySelector("[data-ai-sheet-body]");
    var sub = shell.querySelector("[data-ai-sheet-sub]");
    var surfaceOn = isAiSurfaceEnabled();
    if (sub) {
      sub.textContent = surfaceOn
        ? "AI能力 · 需配置模型API后方可使用"
        : "本环境未开启智能能力";
    }

    if (!surfaceOn) {
      // 关闸态：API 配置置顶并默认展开（未就绪）
      body.innerHTML =
        connectionDetailsHtml({ ready: false }) +
        '<div class="preview-ai-sheet__block preview-ai-sheet__block--gate">' +
        "<h3>智能动作暂不可用</h3>" +
        "<p>封面字体、杂志文案等需先开启智能能力。仅填写 API Key <strong>不会</strong>自动开启。</p>" +
        '<p class="preview-ai-sheet__hint">出图与导出不受影响。</p>' +
        '<details class="preview-ai-sheet__details" data-ai-help-gate>' +
        "<summary>了解如何开启</summary>" +
        '<div class="preview-ai-sheet__details-body">' +
        '<p class="preview-ai-sheet__hint">任选其一后<strong>重启 Studio</strong>并刷新预览：</p>' +
        '<p class="preview-ai-sheet__hint">1）在 <code>config.yaml</code> 设置 <code>studio.ai_surface_enabled: true</code></p>' +
        '<p class="preview-ai-sheet__hint">2）启动前设置环境变量 <code>TRAVELOGUE_AI_SURFACE=1</code></p>' +
        '<p class="preview-ai-sheet__hint">开启后，再用上方「模型API 配置」测试 Key。</p>' +
        "</div></details>" +
        "</div>";
      bindGateHelp(body);
      bindConnection(body);
      return;
    }

    var actionsHtml =
      narrateBlockHtml() +
      titleArtBlockHtml() +
      intentBlockHtml() +
      suggestionsBlockHtml();
    var connReady = connectionOk === true;
    var connHtml = connectionDetailsHtml({
      ready: connReady,
      configured: llmConfigured,
      pingFailed: lastPingOk === false,
    });
    // 未测通：API配置置顶并展开；已就绪：沉底折叠
    body.innerHTML = connReady ? actionsHtml + connHtml : connHtml + actionsHtml;
    bindTitleArt(body);
    bindNarrate(body);
    bindIntent(body);
    bindSuggestions(body);
    bindConnection(body);
    applyPendingFocus();
  }

  function applyPendingFocus() {
    if (!pendingFocus || !shell) return;
    var sel =
      pendingFocus === "narrate"
        ? "[data-ai-narrate-block]"
        : pendingFocus === "intent"
          ? "[data-ai-intent-block]"
          : pendingFocus === "suggestions"
            ? "[data-ai-suggestions-block]"
            : null;
    pendingFocus = null;
    if (!sel) return;
    var el = shell.querySelector(sel);
    if (el && typeof el.scrollIntoView === "function") {
      try {
        el.scrollIntoView({ block: "nearest", behavior: "smooth" });
      } catch (_e) {
        el.scrollIntoView(true);
      }
    }
  }

  function titleArtBlockHtml() {
    if (!titleArtEnabled) {
      return (
        '<div class="preview-ai-sheet__block preview-ai-sheet__block--muted">' +
        "<h3>封面字体</h3>" +
        '<p class="preview-ai-sheet__desc">当前环境未开启封面字体能力。</p>' +
        "</div>"
      );
    }
    if (!connectionOk) {
      return (
        '<div class="preview-ai-sheet__block" data-ai-title-art-block>' +
        "<h3>封面字体</h3>" +
        '<p class="preview-ai-sheet__desc">封面手写体需要通义百炼；未连接时使用本机字库</p>' +
        '<div class="preview-ai-sheet__row">' +
        '<span class="preview-ai-sheet__status">未连接</span>' +
        '<button type="button" class="preview-ai-sheet__btn" data-ai-title-art-connect>去连接</button>' +
        "</div>" +
        "</div>"
      );
    }
    var pref = "1";
    try {
      pref = localStorage.getItem(TITLE_ART_ROUTE_C_PREF_KEY);
      if (pref == null) pref = "1";
    } catch (_e) {
      pref = "1";
    }
    var checked = pref !== "0";
    var routeCRow = titleArtRouteCEnabled
      ? '<label class="preview-ai-sheet__check">' +
        '<input type="checkbox" data-ai-title-art-routec' +
        (checked ? " checked" : "") +
        " />" +
        "<span>优先 AI 手写体</span>" +
        "</label>" +
        '<p class="preview-ai-sheet__hint">优先尝试AI字体，耗时约几十秒</p>'
      : '<p class="preview-ai-sheet__hint">将使用字库路线生成封面字体。</p>';

    var taUi = (entryCache && entryCache.titleArtUi) || {};
    var statusLabel =
      typeof taUi.statusLabel === "string" && taUi.statusLabel
        ? taUi.statusLabel
        : "尚未生成";
    var btnLabel = taUi.ready ? "重新生成字体" : "生成字体";

    return (
      '<div class="preview-ai-sheet__block" data-ai-title-art-block>' +
      "<h3>封面字体</h3>" +
      routeCRow +
      '<div class="preview-ai-sheet__row">' +
      '<span class="preview-ai-sheet__status" data-ai-title-art-status>' +
      escapeHtml(statusLabel) +
      "</span>" +
      '<button type="button" class="preview-ai-sheet__btn" data-ai-title-art-btn>' +
      escapeHtml(btnLabel) +
      "</button>" +
      "</div>" +
      '<button type="button" class="preview-ai-sheet__link-btn" data-ai-goto-cover-name">去精修 · 杂志名</button>' +
      "</div>"
    );
  }

  function narrateBlockHtml() {
    var g1Pending = !!(entryCache && entryCache.g1Pending);
    var posture = (entryCache && entryCache.narrativePosture) || "";
    // SNR COPY-SNR-S01 · 未配置 / 可生成 / 生成中 / 已是杂志文案 / 失败可重试
    // 「可生成」不得暗示预览已是杂志感；禁止「杂志文案已完成」
    var status = "未配置";
    var cta = "去连接";
    var disableBtn = false;
    if (g1Pending) {
      status = "待分章确认";
      cta = "请先确认分章";
      disableBtn = true;
    } else if (narrateRuntimeStatus === "生成中") {
      status = "生成中";
      cta = "正在生成…";
      disableBtn = true;
    } else if (narrateRuntimeStatus === "失败可重试") {
      status = "失败可重试";
      cta = copyReady ? "重试生成" : "去连接";
    } else if (posture === "narrative_ready") {
      status = "已是杂志文案";
      cta = copyReady ? "再生成一版" : "已是杂志文案";
      disableBtn = !copyReady;
    } else if (copyReady) {
      status = "可生成";
      cta = "生成杂志感文案";
    } else {
      status = "连接通义百炼后可生成杂志文案";
      cta = "去连接";
    }
    return (
      '<div class="preview-ai-sheet__block" data-ai-narrate-block>' +
      "<h3>杂志文案</h3>" +
      '<p class="preview-ai-sheet__desc">尝试AI文案</p>' +
      (g1Pending
        ? '<p class="preview-ai-sheet__hint">请先在分章确认结构，再生成杂志感文案。</p>'
        : "") +
      '<div class="preview-ai-sheet__row">' +
      '<span class="preview-ai-sheet__status" data-ai-narrate-status>' +
      escapeHtml(status) +
      "</span>" +
      '<button type="button" class="preview-ai-sheet__btn" data-ai-narrate-btn' +
      (disableBtn ? " disabled" : "") +
      ">" +
      escapeHtml(cta) +
      "</button>" +
      "</div>" +
      "</div>"
    );
  }

  function intentBlockHtml() {
    var ui = (entryCache && entryCache.intentBriefUi) || {};
    var status = ui.statusLabel || "尚未解析";
    var detail = ui.detail
      ? '<p class="preview-ai-sheet__hint">' + escapeHtml(ui.detail) + "</p>"
      : "";
    return (
      '<div class="preview-ai-sheet__block" data-ai-intent-block>' +
      "<h3>旅行意图</h3>" +
      '<p class="preview-ai-sheet__desc">重新理解这趟旅行的节奏与篇幅偏好（影响后续建议，不直接改已锁定结构）。</p>' +
      detail +
      '<div class="preview-ai-sheet__row">' +
      '<span class="preview-ai-sheet__status" data-ai-intent-status>' +
      escapeHtml(status) +
      "</span>" +
      '<button type="button" class="preview-ai-sheet__btn preview-ai-sheet__btn--ghost" data-ai-intent-btn' +
      (intentBusy ? " disabled" : "") +
      ">" +
      (intentBusy ? "解析中…" : "重新解析") +
      "</button>" +
      "</div>" +
      "</div>"
    );
  }

  function suggestionsBlockHtml() {
    var pending = pendingSuggestions(entryCache);
    var all = ((entryCache && entryCache.layoutSuggestions) || []).filter(function (s) {
      return s && s.suggestion;
    });
    var cards = "";
    if (!pending.length) {
      cards =
        '<p class="preview-ai-sheet__hint" data-ai-suggestions-empty>' +
        (all.length
          ? "当前没有待处理建议。"
          : "成册后若有可改点，会出现在这里；届时顶部 AI 会亮提示点。") +
        "</p>";
    } else {
      cards = pending
        .map(function (s, idx) {
          var text = clipSuggestion(s.suggestion);
          var chTitle = chapterTitle(s.chapterId);
          return (
            '<div class="preview-ai-sheet__sug" data-ai-sug-idx="' +
            idx +
            '" data-chapter-id="' +
            escapeHtml(s.chapterId || "") +
            '">' +
            '<p class="preview-ai-sheet__sug-meta">' +
            escapeHtml(chTitle) +
            "</p>" +
            '<p class="preview-ai-sheet__sug-text">' +
            escapeHtml(text) +
            "</p>" +
            '<div class="preview-ai-sheet__sug-actions">' +
            '<button type="button" class="preview-ai-sheet__btn" data-ai-sug-accept>采纳</button>' +
            '<button type="button" class="preview-ai-sheet__btn preview-ai-sheet__btn--ghost" data-ai-sug-dismiss>忽略</button>' +
            '<button type="button" class="preview-ai-sheet__link-btn" data-ai-sug-feedback>这章不对</button>' +
            "</div></div>"
          );
        })
        .join("");
    }
    return (
      '<div class="preview-ai-sheet__block" data-ai-suggestions-block>' +
      "<h3>排版建议</h3>" +
      '<p class="preview-ai-sheet__desc">只读建议；采纳后才写入。</p>' +
      cards +
      "</div>"
    );
  }

  /**
   * @param {{ ready?: boolean, configured?: boolean, pingFailed?: boolean }} [opts]
   * ready = connectionOk===true → 折叠；否则默认展开
   */
  function connectionDetailsHtml(opts) {
    opts = opts || {};
    var ready = !!opts.ready;
    var summary = ready ? "模型API 配置 · 已连接" : "模型API 配置";
    var status = "未配置 / 未测通";
    if (ready) status = "已连接";
    else if (opts.pingFailed) status = "连接失败 · 请重试";
    else if (opts.configured) status = "已保存未验证";
    return (
      '<details class="preview-ai-sheet__details" data-ai-connection' +
      (ready ? "" : " open") +
      ">" +
      "<summary>" +
      summary +
      "</summary>" +
      '<div class="preview-ai-sheet__details-body">' +
      '<div class="preview-ai-sheet__row">' +
      '<span class="preview-ai-sheet__status" data-ai-conn-status>' +
      status +
      "</span>" +
      '<button type="button" class="preview-ai-sheet__btn preview-ai-sheet__btn--ghost" data-ai-conn-btn>' +
      (ready ? "管理连接" : "去连接") +
      "</button>" +
      "</div>" +
      '<p class="preview-ai-sheet__hint">密钥只保存在本机。失败不影响出图与导出。</p>' +
      "</div></details>"
    );
  }

  function openLlmSettingsFromSheet(source) {
    // @ts-expect-error Studio absolute URL
    return import("/__studio/js/llm-settings.js")
      .then(function (mod) {
        if (!mod || typeof mod.openLlmSettings !== "function") return;
        mod.openLlmSettings({
          source: source || "ai_sheet",
          allowWhenSurfaceOff: true,
          onChange: function () {
            refreshLlmAndConfig().then(function () {
              if (isOpen()) renderBody();
            });
          },
        });
      })
      .catch(function () {
        showToolbarToast("无法打开模型API 配置", { error: true });
      });
  }

  function bindGateHelp(body) {
    var help = body.querySelector("[data-ai-help-gate]");
    if (!help) return;
    help.addEventListener("toggle", function () {
      if (help.open) trackAction("open_help", { topic: "gate" });
    });
  }

  function bindConnection(body) {
    var connBtn = body.querySelector("[data-ai-conn-btn]");
    if (!connBtn) return;
    connBtn.addEventListener("click", function () {
      trackAction("open_settings");
      openLlmSettingsFromSheet("ai_sheet");
    });
  }

  function bindNarrate(body) {
    var narrateBtn = body.querySelector("[data-ai-narrate-btn]");
    if (!narrateBtn) return;
    narrateBtn.addEventListener("click", function () {
      if (entryCache && entryCache.g1Pending) {
        showToolbarToast("请先在分章确认结构");
        return;
      }
      if (!copyReady) {
        trackAction("open_settings", { reason: "narrate_no_key" });
        openLlmSettingsFromSheet("ai_sheet_copy");
        return;
      }
      trackAction("narrate");
      trackStudioEvent("snr_upgrade_cta_click", {
        source: "ai_sheet",
        tripId: tripId || null,
      });
      var started = Date.now();
      var wasGenerating = false;
      startLlmNarrate(root, tripId, narrateBtn, {
        source: "ai_sheet",
        confirmTitle: DARK_COPY.narrateConfirmTitle || "生成杂志感文案",
        confirmBody:
          "将调用写作引擎重写文案；照片仍留在本机。将重写版心文案（可能包括你改过的句子）。",
        confirmText: "生成杂志感文案",
        // SNR · 生成中状态人话（对齐 COPY-SNR-S01）
        busyHint: "正在生成杂志感文案…",
        onStatus: function (label) {
          if (label === "生成中") {
            narrateRuntimeStatus = "生成中";
            wasGenerating = true;
          } else if (label === "失败可重试") {
            narrateRuntimeStatus = "失败可重试";
          } else if (label === "已是杂志文案") {
            narrateRuntimeStatus = "";
          }
          var el = document.querySelector("[data-ai-narrate-status]");
          if (el && label) el.textContent = label;
          if (label === "失败可重试" && narrateBtn) {
            narrateBtn.textContent = "重试生成";
            narrateBtn.disabled = false;
          }
        },
      }).then(function () {
        // 用户取消确认时不会进入 run()，勿残留「生成中」
        if (!wasGenerating && narrateRuntimeStatus === "生成中") {
          narrateRuntimeStatus = "";
        }
        trackResult("narrate", true, {
          latency_ms: Date.now() - started,
        });
      });
    });
  }

  function bindIntent(body) {
    var intentBtn = body.querySelector("[data-ai-intent-btn]");
    var statusEl = body.querySelector("[data-ai-intent-status]");
    if (!intentBtn) return;
    intentBtn.addEventListener("click", function () {
      if (intentBusy) return;
      trackAction("intent");
      intentBusy = true;
      intentBtn.disabled = true;
      intentBtn.textContent = "解析中…";
      if (statusEl) statusEl.textContent = "解析中…";
      var started = Date.now();
      postJson(tripRestBase(tripId) + "/ai/intent-brief", { force: true })
        .then(function (res) {
          intentBusy = false;
          if (!res || res.status !== 200 || !res.body || !res.body.ok) {
            if (statusEl) statusEl.textContent = "暂时不可用";
            intentBtn.disabled = false;
            intentBtn.textContent = "重新解析";
            showToolbarToast(
              (res && res.body && res.body.message) || "意图解析暂时不可用",
              { error: true }
            );
            trackResult("intent", false, {
              latency_ms: Date.now() - started,
              error_code: "fail",
            });
            return;
          }
          trackResult("intent", true, {
            latency_ms: Date.now() - started,
            source: res.body.source || null,
          });
          showToolbarToast("意图已更新");
          return loadEntry().then(function () {
            if (isOpen()) renderBody();
          });
        })
        .catch(function () {
          intentBusy = false;
          intentBtn.disabled = false;
          intentBtn.textContent = "重新解析";
          if (statusEl) statusEl.textContent = "网络错误";
          showToolbarToast("意图解析请求失败", { error: true });
          trackResult("intent", false, {
            latency_ms: Date.now() - started,
            error_code: "network",
          });
        });
    });
  }

  function bindSuggestions(body) {
    var pending = pendingSuggestions(entryCache);
    body.querySelectorAll("[data-ai-sug-idx]").forEach(function (card) {
      var idx = parseInt(card.getAttribute("data-ai-sug-idx") || "-1", 10);
      var sug = pending[idx];
      if (!sug) return;
      var acceptBtn = card.querySelector("[data-ai-sug-accept]");
      var dismissBtn = card.querySelector("[data-ai-sug-dismiss]");
      var feedbackBtn = card.querySelector("[data-ai-sug-feedback]");
      if (acceptBtn) {
        acceptBtn.addEventListener("click", function () {
          trackAction("suggestion_accept", { chapterId: sug.chapterId });
          var started = Date.now();
          acceptBtn.disabled = true;
          postJsonConflictRetry(tripRestBase(tripId) + "/ai/layout-critic/accept", {
            chapterId: sug.chapterId,
            suggestedPatternId: sug.suggestedPatternId || undefined,
          })
            .then(function (res) {
              if (!res || res.status < 200 || res.status >= 300) {
                acceptBtn.disabled = false;
                showToolbarToast(
                  (res && res.body && res.body.message) || "采纳失败",
                  { error: true }
                );
                trackResult("suggestion_accept", false, {
                  latency_ms: Date.now() - started,
                });
                return;
              }
              // ACP §5.3 · 202 + jobId → 章级重排；200 skipReplan → 仅标记
              if (res.status === 202 && res.body && res.body.jobId) {
                showToolbarToast("正在按建议更新该章版面…");
                return pollJobUntilDone(res.body.jobId, { intervalMs: 800 }).then(
                  function (job) {
                    if (!job || job.status !== "succeeded") {
                      showToolbarToast("建议已记下，版面更新未完成", {
                        error: true,
                      });
                      trackResult("suggestion_accept", false, {
                        latency_ms: Date.now() - started,
                        error_code: "replan_job",
                      });
                      return loadEntry().then(function () {
                        if (isOpen()) renderBody();
                      });
                    }
                    showToolbarToast("已按建议更新该章版面");
                    trackResult("suggestion_accept", true, {
                      latency_ms: Date.now() - started,
                      replan: true,
                    });
                    reloadPreviewAfterLayout();
                    return loadEntry().then(function () {
                      if (isOpen()) renderBody();
                    });
                  }
                );
              }
              showToolbarToast(
                res.body && res.body.replan === false
                  ? "已采纳建议"
                  : "已按建议更新该章版面"
              );
              trackResult("suggestion_accept", true, {
                latency_ms: Date.now() - started,
              });
              reloadPreviewAfterLayout();
              return loadEntry().then(function () {
                if (isOpen()) renderBody();
              });
            })
            .catch(function () {
              acceptBtn.disabled = false;
              showToolbarToast("采纳失败", { error: true });
              trackResult("suggestion_accept", false, {
                latency_ms: Date.now() - started,
                error_code: "network",
              });
            });
        });
      }
      if (dismissBtn) {
        dismissBtn.addEventListener("click", function () {
          trackAction("suggestion_dismiss", { chapterId: sug.chapterId });
          markDismissed(suggestionKey(sug));
          trackResult("suggestion_dismiss", true, {});
          refreshBadgeFromEntry(entryCache);
          if (isOpen()) renderBody();
        });
      }
      if (feedbackBtn) {
        feedbackBtn.addEventListener("click", function () {
          trackAction("suggestion_feedback", { chapterId: sug.chapterId });
          var reason = window.prompt(
            "这章哪里不对？\n1 图太多\n2 图太少\n3 顺序不对\n4 风格不搭\n5 其他\n请输入编号：",
            "1"
          );
          if (reason == null) return;
          var map = {
            "1": "too_many_photos",
            "2": "too_few_photos",
            "3": "wrong_order",
            "4": "style_mismatch",
            "5": "other",
          };
          var code = map[String(reason).trim()] || "other";
          postJsonConflictRetry(tripRestBase(tripId) + "/ai/layout-feedback", {
            chapterId: sug.chapterId,
            reason: code,
          })
            .then(function (res) {
              if (!res || res.status < 200 || res.status >= 300) {
                showToolbarToast(
                  (res && res.body && res.body.message) || "反馈未保存"
                );
                trackResult("suggestion_feedback", false, {});
                return;
              }
              showToolbarToast("已记下，下次排版建议会参考");
              trackResult("suggestion_feedback", true, {});
            })
            .catch(function () {
              showToolbarToast("反馈未保存");
              trackResult("suggestion_feedback", false, {
                error_code: "network",
              });
            });
        });
      }
    });
  }

  function bindTitleArt(body) {
    var check = body.querySelector("[data-ai-title-art-routec]");
    var artBtn = body.querySelector("[data-ai-title-art-btn]");
    var statusEl = body.querySelector("[data-ai-title-art-status]");
    var gotoName = body.querySelector("[data-ai-goto-cover-name]");
    if (gotoName && !gotoName._rciWired) {
      gotoName._rciWired = true;
      gotoName.addEventListener("click", function () {
        close("deep_link");
        if (root._sheet && typeof root._sheet.open === "function") {
          root._sheet.open("cover", {
            coverSeg: "name",
            bookendsFocus: "opening",
            scrollToBookends: false,
            source: "ai_sheet",
          });
        }
      });
    }
    if (check) {
      check.addEventListener("change", function () {
        try {
          localStorage.setItem(
            TITLE_ART_ROUTE_C_PREF_KEY,
            check.checked ? "1" : "0"
          );
        } catch (_e) {}
      });
    }
    var connectBtn = body.querySelector("[data-ai-title-art-connect]");
    if (connectBtn) {
      connectBtn.addEventListener("click", function () {
        trackAction("open_settings", { reason: "title_art_no_key" });
        openLlmSettingsFromSheet("ai_sheet_image");
      });
    }
    if (!artBtn) return;
    artBtn.addEventListener("click", function () {
      if (titleArtBusy) return;
      trackAction("title_art");
      var wantRouteC = !!(check && check.checked && titleArtRouteCEnabled);
      var bodyPayload = { force: true };
      if (wantRouteC) bodyPayload.routeC = true;
      titleArtBusy = true;
      artBtn.disabled = true;
      if (statusEl) statusEl.textContent = "生成中…";
      var started = Date.now();
      postJson(
        "/__travelogue/trips/" + encodeURIComponent(tripId) + "/title-art/resolve",
        bodyPayload
      )
        .then(function (res) {
          titleArtBusy = false;
          artBtn.disabled = false;
          if (!res || res.status !== 200 || !res.body || !res.body.ok) {
            if (statusEl) statusEl.textContent = "生成失败";
            var failMsg =
              (res && res.body && res.body.message) ||
              "封面字体暂时不可用，可稍后重试";
            // 禁止把 E_SERVER 等工程码直接展示
            if (failMsg.indexOf("E_") === 0) {
              failMsg = "封面字体暂时不可用，可稍后重试";
            }
            showToolbarToast(failMsg, { error: true });
            trackResult("title_art", false, {
              latency_ms: Date.now() - started,
              routeCRequested: wantRouteC,
            });
            trackStudioEvent("title_art_resolve", {
              outcome: "error",
              source: "ai_sheet",
              routeCRequested: wantRouteC,
            });
            return;
          }
          if (!res.body.enabled) {
            if (statusEl) statusEl.textContent = "暂不支持";
            showToolbarToast("此版式或标题暂不支持艺术字，已保持默认样式");
            trackResult("title_art", false, {
              latency_ms: Date.now() - started,
              error_code: "disabled",
            });
            trackStudioEvent("title_art_resolve", {
              outcome: "disabled",
              source: "ai_sheet",
              routeCRequested: !!res.body.routeCRequested,
            });
            return;
          }
          var engineLabel =
            res.body.engine === "diffusion-fixed-prompt-v1"
              ? "AI 手写体"
              : "字库合成";
          var readyLabel = "已生成 · " + engineLabel;
          if (res.body.fallbackFrom) {
            readyLabel += "（已回退字库）";
          }
          if (statusEl) statusEl.textContent = readyLabel;
          artBtn.textContent = "重新生成";
          // 预览整页重载后靠 entry.titleArtUi 回填；此处先写入 cache 防中途 re-render
          entryCache = entryCache || {};
          entryCache.titleArtUi = {
            ready: true,
            stale: false,
            engine: res.body.engine || null,
            statusLabel: readyLabel,
          };
          showToolbarToast("封面字体已更新");
          trackResult("title_art", true, {
            latency_ms: Date.now() - started,
            routeCRequested: wantRouteC,
          });
          trackStudioEvent("title_art_resolve", {
            outcome: "success",
            source: "ai_sheet",
            routeCRequested: !!res.body.routeCRequested,
            routeCAllowedByConfig: !!res.body.routeCAllowedByConfig,
            fallback: !!res.body.fallbackFrom,
            ocrVerified:
              typeof res.body.ocrVerified === "boolean"
                ? res.body.ocrVerified
                : null,
          });
          reloadPreviewAfterLayout();
        })
        .catch(function () {
          titleArtBusy = false;
          artBtn.disabled = false;
          if (statusEl) statusEl.textContent = "网络错误";
          showToolbarToast("封面字体请求失败", { error: true });
          trackResult("title_art", false, {
            latency_ms: Date.now() - started,
            error_code: "network",
          });
          trackStudioEvent("title_art_resolve", {
            outcome: "network",
            source: "ai_sheet",
            routeCRequested: wantRouteC,
          });
        });
    });
  }

  function refreshLlmAndConfig() {
    return Promise.all([
      fetch("/__travelogue/llm/status", {
        headers: studioAuthHeaders({}),
      })
        .then(function (r) {
          return r && r.ok ? r.json() : null;
        })
        .then(function (st) {
          lastPingOk =
            st && typeof st.lastPingOk === "boolean" ? st.lastPingOk : null;
          llmConfigured = !!(st && st.configured);
          connectionOk = !!(st && st.connectionOk === true);
          copyReady = !!(st && (st.copyReady === true || st.connectionOk === true));
          // 封面字体禁止再用单一 llmAvailable；W1a copyReady ≡ connectionOk
          llmAvailable = copyReady;
        })
        .catch(function () {
          llmAvailable = false;
          lastPingOk = null;
          llmConfigured = false;
          connectionOk = false;
          copyReady = false;
        }),
      fetch("/__travelogue/config", {
        headers: studioAuthHeaders({}),
      })
        .then(function (r) {
          return r && r.ok ? r.json() : null;
        })
        .then(function (cfg) {
          var ta = (cfg && cfg.titleArt) || {};
          titleArtEnabled = !!ta.enabled;
          titleArtRouteCEnabled = !!ta.routeCEnabled;
        })
        .catch(function () {
          titleArtEnabled = false;
          titleArtRouteCEnabled = false;
        }),
      loadEntry(),
    ]);
  }

  function open(openOpts) {
    openOpts = openOpts || {};
    pendingFocus = openOpts.focus || null;
    // force：避免曾以关闸态缓存后，本机改开闸仍显示「暂不可用」
    ensureAiSurfaceHydrated({ force: true }).then(function () {
      closePeers(root);
      ensureShell();
      refreshLlmAndConfig().then(function () {
        var openHadBadge = computeBadge(entryCache);
        var pending = pendingSuggestions(entryCache);
        if (pending.length) {
          markBadgeSeen(
            pending.map(function (s) {
              return suggestionKey(s);
            })
          );
          refreshBadgeFromEntry(entryCache);
        }
        renderBody();
        shell.hidden = false;
        requestAnimationFrame(function () {
          shell.classList.add("preview-ai-sheet-root--open");
        });
        document.body.classList.add(BODY_OPEN_CLASS);
        setBtnActive(true);
        openAt = Date.now();
        document.addEventListener("keydown", onDocKeydown, true);
        trackStudioEvent("ai_sheet_open", {
          source: openOpts.source || "dock",
          has_badge: openHadBadge,
        });
        trackStudioEvent("ai_sheet_gate_view", {
          surfaceOn: isAiSurfaceEnabled(),
          keyOk: connectionOk,
        });
        if (titleArtEnabled) {
          trackStudioEvent("title_art_impression", {
            source: "ai_sheet",
            routeCShown: titleArtRouteCEnabled,
          });
        }
      });
    });
  }

  function close(reason) {
    if (!isOpen()) return;
    var dwell = openAt ? Date.now() - openAt : 0;
    shell.classList.remove("preview-ai-sheet-root--open");
    shell.hidden = true;
    document.body.classList.remove(BODY_OPEN_CLASS);
    setBtnActive(false);
    document.removeEventListener("keydown", onDocKeydown, true);
    trackStudioEvent("ai_sheet_close", {
      reason: reason || "unknown",
      dwell_ms: dwell,
    });
  }

  function toggle() {
    if (isOpen()) close("dock_toggle");
    else open({ source: "dock" });
  }

  btn.addEventListener("click", function (e) {
    e.stopPropagation();
    toggle();
  });

  // 初次挂载拉建议徽标（不自动开 Sheet）
  ensureAiSurfaceHydrated().then(function () {
    if (isAiSurfaceEnabled()) loadEntry();
  });

  var api = {
    open: open,
    close: close,
    isOpen: isOpen,
    toggle: toggle,
    btn: btn,
    refresh: function () {
      return refreshLlmAndConfig().then(function () {
        if (isOpen()) renderBody();
      });
    },
  };
  root._aiSheet = api;
  return api;
}
