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
import { dockIconSvg } from "./dock.js";
import { fetchEntry, startLlmNarrate } from "./core.js";
import { closeStudioExportPopover } from "./longshot.js";
import {
  reloadPreviewAfterLayout,
  showToolbarToast,
  tripApiBase,
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

function showAdvancedSection() {
  try {
    var h = location.hostname || "";
    return h === "127.0.0.1" || h === "localhost" || h === "::1";
  } catch (_e) {
    return false;
  }
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
  closeStudioExportPopover();
  if (typeof isHelpDrawerOpen === "function" && isHelpDrawerOpen()) {
    closeHelpDrawer();
  }
  if (root._chapterPanel && root._chapterPanel.isOpen()) {
    root._chapterPanel.close();
  }
  if (root._sheet && typeof root._sheet.isOpen === "function" && root._sheet.isOpen()) {
    root._sheet.close("ai_sheet");
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
  var titleArtEnabled = false;
  var titleArtRouteCEnabled = false;
  var titleArtBusy = false;
  var intentBusy = false;
  var entryCache = null;
  var pendingFocus = null;
  var hasBadge = false;

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
      '<p class="preview-ai-sheet__sub" data-ai-sheet-sub>本册智能动作 · 不自动消耗额度</p>' +
      "</div>" +
      '<button type="button" class="preview-ai-sheet__close" data-ai-sheet-close aria-label="关闭">×</button>' +
      "</header>" +
      '<div class="preview-ai-sheet__body" data-ai-sheet-body></div>' +
      "</aside>";
    document.body.appendChild(shell);

    shell.querySelector("[data-ai-sheet-scrim]").addEventListener("click", function () {
      close("scrim");
    });
    shell.querySelector("[data-ai-sheet-close]").addEventListener("click", function () {
      close("close_btn");
    });
    return shell;
  }

  function renderBody() {
    var body = shell.querySelector("[data-ai-sheet-body]");
    var sub = shell.querySelector("[data-ai-sheet-sub]");
    var surfaceOn = isAiSurfaceEnabled();
    if (sub) {
      sub.textContent = surfaceOn
        ? "本册智能动作 · 不自动消耗额度"
        : "本环境未开启智能能力";
    }

    if (!surfaceOn) {
      body.innerHTML =
        '<div class="preview-ai-sheet__block preview-ai-sheet__block--gate">' +
        "<h3>智能动作暂不可用</h3>" +
        "<p>装帧标题、杂志文案等需开启 AI 能力后使用。出图与导出不受影响。</p>" +
        '<p class="preview-ai-sheet__hint">内测可先展开下方「本机连接」预配 Key。</p>' +
        '<details class="preview-ai-sheet__details" data-ai-help-gate>' +
        "<summary>了解如何开启</summary>" +
        '<div class="preview-ai-sheet__details-body">' +
        '<p class="preview-ai-sheet__hint">内测：启动 Studio 前设置环境变量 <code>TRAVELOGUE_AI_SURFACE=1</code>，再打开预览。</p>' +
        '<p class="preview-ai-sheet__hint">Key 可在下方「本机连接」预先配置；未开启智能能力时也可保存，不影响出图与导出。</p>' +
        "</div></details>" +
        "</div>" +
        connectionDetailsHtml() +
        advancedDetailsHtml();
      bindGateHelp(body);
      bindConnection(body);
      bindAdvanced(body);
      return;
    }

    body.innerHTML =
      titleArtBlockHtml() +
      narrateBlockHtml() +
      intentBlockHtml() +
      suggestionsBlockHtml() +
      connectionDetailsHtml() +
      advancedDetailsHtml();
    bindTitleArt(body);
    bindNarrate(body);
    bindIntent(body);
    bindSuggestions(body);
    bindConnection(body);
    bindAdvanced(body);
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
        "<h3>装帧标题</h3>" +
        '<p class="preview-ai-sheet__desc">当前环境未开启装帧标题能力。</p>' +
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
        '<p class="preview-ai-sheet__hint">勾选只表示优先走手写体，不会自动开跑。未通过自动用字库 · 约十几秒。</p>'
      : '<p class="preview-ai-sheet__hint">将使用字库路线生成装帧标题。</p>';

    return (
      '<div class="preview-ai-sheet__block" data-ai-title-art-block>' +
      "<h3>装帧标题</h3>" +
      '<p class="preview-ai-sheet__desc">点一次才生成。勾选只表示优先走 AI 手写体，不会自动开跑。</p>' +
      routeCRow +
      '<div class="preview-ai-sheet__row">' +
      '<span class="preview-ai-sheet__status" data-ai-title-art-status>尚未生成</span>' +
      '<button type="button" class="preview-ai-sheet__btn" data-ai-title-art-btn>生成装帧标题</button>' +
      "</div>" +
      "</div>"
    );
  }

  function narrateBlockHtml() {
    var g1Pending = !!(entryCache && entryCache.g1Pending);
    var status = g1Pending
      ? "待分章确认"
      : llmAvailable
        ? "可生成"
        : "未配置";
    var cta = g1Pending
      ? "请先确认分章"
      : llmAvailable
        ? "生成杂志感文案"
        : "配置写作引擎";
    return (
      '<div class="preview-ai-sheet__block" data-ai-narrate-block>' +
      "<h3>杂志文案</h3>" +
      '<p class="preview-ai-sheet__desc">重写封面钩子与章节导语等版心文字；照片仍留在本机。导入默认仍用本机文案。</p>' +
      (g1Pending
        ? '<p class="preview-ai-sheet__hint">请先在分章确认结构，再生成杂志感文案。</p>'
        : "") +
      '<div class="preview-ai-sheet__row">' +
      '<span class="preview-ai-sheet__status" data-ai-narrate-status>' +
      escapeHtml(status) +
      "</span>" +
      '<button type="button" class="preview-ai-sheet__btn" data-ai-narrate-btn' +
      (g1Pending ? " disabled" : "") +
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

  function connectionDetailsHtml() {
    return (
      '<details class="preview-ai-sheet__details" data-ai-connection>' +
      "<summary>本机连接</summary>" +
      '<div class="preview-ai-sheet__details-body">' +
      '<div class="preview-ai-sheet__row">' +
      '<span class="preview-ai-sheet__status" data-ai-conn-status>' +
      (llmAvailable ? "已就绪" : "未测通") +
      "</span>" +
      '<button type="button" class="preview-ai-sheet__btn preview-ai-sheet__btn--ghost" data-ai-conn-btn>配置 / 测试</button>' +
      "</div>" +
      '<p class="preview-ai-sheet__hint">本地 Key · 失败不影响出图与导出。</p>' +
      "</div></details>"
    );
  }

  function advancedDetailsHtml() {
    if (!showAdvancedSection()) return "";
    return (
      '<details class="preview-ai-sheet__details" data-ai-advanced>' +
      "<summary>高级</summary>" +
      '<div class="preview-ai-sheet__details-body">' +
      '<p class="preview-ai-sheet__hint">工程观测与预算（内部）。普通用户可忽略。</p>' +
      '<a class="preview-ai-sheet__link" data-ai-ops-link href="/ai-ops-admin" target="_blank" rel="noopener">打开 AI 运维台 →</a>' +
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
        showToolbarToast("无法打开写作引擎设置", { error: true });
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

  function bindAdvanced(body) {
    var link = body.querySelector("[data-ai-ops-link]");
    if (!link) return;
    link.addEventListener("click", function () {
      trackAction("open_ops");
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
      if (!llmAvailable) {
        trackAction("open_settings", { reason: "narrate_no_key" });
        openLlmSettingsFromSheet("ai_sheet_narrate");
        return;
      }
      trackAction("narrate");
      var started = Date.now();
      startLlmNarrate(root, tripId, narrateBtn, {
        source: "ai_sheet",
        confirmTitle: DARK_COPY.narrateConfirmTitle || "生成杂志感文案",
        confirmBody:
          "将调用写作引擎重写文案；照片仍留在本机。将重写版心文案（可能包括你改过的句子）。",
        confirmText: "生成杂志感文案",
        busyHint: DARK_COPY.narrateBusy,
      }).then(function () {
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
      postJson(tripApiBase(tripId) + "/ai/intent-brief", { force: true })
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
          postJsonConflictRetry(tripApiBase(tripId) + "/ai/layout-critic/accept", {
            chapterId: sug.chapterId,
            suggestedPatternId: sug.suggestedPatternId || undefined,
          })
            .then(function (res) {
              if (!res || res.status < 200 || res.status >= 300) {
                showToolbarToast(
                  (res && res.body && res.body.message) || "采纳失败",
                  { error: true }
                );
                trackResult("suggestion_accept", false, {
                  latency_ms: Date.now() - started,
                });
                return;
              }
              showToolbarToast("已采纳建议（下次重生时参考）");
              trackResult("suggestion_accept", true, {
                latency_ms: Date.now() - started,
              });
              return loadEntry().then(function () {
                if (isOpen()) renderBody();
              });
            })
            .catch(function () {
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
          postJsonConflictRetry(tripApiBase(tripId) + "/ai/layout-feedback", {
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
            showToolbarToast(
              (res && res.body && res.body.message) ||
                "装帧标题暂时不可用，可稍后重试",
              { error: true }
            );
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
          if (statusEl) statusEl.textContent = "已有结果";
          showToolbarToast("装帧标题已更新");
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
          showToolbarToast("装帧标题请求失败", { error: true });
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
          llmAvailable = !!(st && st.llmAvailable);
        })
        .catch(function () {
          llmAvailable = false;
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
    ensureAiSurfaceHydrated().then(function () {
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
        trackStudioEvent("ai_sheet_open", {
          source: openOpts.source || "dock",
          has_badge: openHadBadge,
        });
        trackStudioEvent("ai_sheet_gate_view", {
          surfaceOn: isAiSurfaceEnabled(),
          keyOk: llmAvailable,
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
