/**
 * Studio AI Surface V1 (SAS) · preview Dock「AI」+ Sheet
 * PRD-STUDIO-AI-SURFACE-V1 · W1：壳 / 未开闸 / 装帧标题 / 杂志文案 / 本机连接
 */
"use strict";

import { trackStudioEvent } from "../js/analytics.js";
import {
  ensureAiSurfaceHydrated,
  isAiSurfaceEnabled,
} from "../js/ai-surface.js";
import { DARK_COPY } from "../js/ai-surface-dark-copy.js";
import { closeHelpDrawer, isHelpDrawerOpen } from "../js/help-drawer.js";
import { postJson, studioAuthHeaders } from "../js/http.js";
import { dockIconSvg } from "./dock.js";
import { startLlmNarrate } from "./core.js";
import { closeStudioExportPopover } from "./longshot.js";
import {
  reloadPreviewAfterLayout,
  showToolbarToast,
  tripIdFromPath,
} from "./shell.js";

var TITLE_ART_ROUTE_C_PREF_KEY = "travelogue.studio.titleArtRouteC";
var BODY_OPEN_CLASS = "preview-ai-sheet-open";

function escapeHtml(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function showAdvancedSection() {
  try {
    var h = location.hostname || "";
    return h === "127.0.0.1" || h === "localhost" || h === "::1";
  } catch (_e) {
    return false;
  }
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
        "</div>" +
        connectionDetailsHtml() +
        advancedDetailsHtml();
      bindConnection(body);
      bindAdvanced(body);
      return;
    }

    body.innerHTML =
      titleArtBlockHtml() +
      narrateBlockHtml() +
      connectionDetailsHtml() +
      advancedDetailsHtml();
    bindTitleArt(body);
    bindNarrate(body);
    bindConnection(body);
    bindAdvanced(body);
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
    var status = llmAvailable ? "可生成" : "未配置";
    var cta = llmAvailable ? "生成杂志感文案" : "配置写作引擎";
    return (
      '<div class="preview-ai-sheet__block" data-ai-narrate-block>' +
      "<h3>杂志文案</h3>" +
      '<p class="preview-ai-sheet__desc">重写封面钩子与章节导语等版心文字；照片仍留在本机。导入默认仍用本机文案。</p>' +
      '<div class="preview-ai-sheet__row">' +
      '<span class="preview-ai-sheet__status" data-ai-narrate-status>' +
      escapeHtml(status) +
      "</span>" +
      '<button type="button" class="preview-ai-sheet__btn" data-ai-narrate-btn>' +
      escapeHtml(cta) +
      "</button>" +
      "</div>" +
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
    ]);
  }

  function open(openOpts) {
    openOpts = openOpts || {};
    ensureAiSurfaceHydrated().then(function () {
      closePeers(root);
      ensureShell();
      refreshLlmAndConfig().then(function () {
        renderBody();
        shell.hidden = false;
        requestAnimationFrame(function () {
          shell.classList.add("preview-ai-sheet-root--open");
        });
        document.body.classList.add(BODY_OPEN_CLASS);
        document.body.classList.add("preview-sheet-open");
        setBtnActive(true);
        openAt = Date.now();
        trackStudioEvent("ai_sheet_open", {
          source: openOpts.source || "dock",
          has_badge: false,
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
    if (!root._sheet || !root._sheet.isOpen || !root._sheet.isOpen()) {
      document.body.classList.remove("preview-sheet-open");
    }
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
