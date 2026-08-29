/**
 * LIVE · Preview toolbar dock (icons, screenplay, dock UX).
 * Loaded by: init-v3.js. S-09 · mount + journalDockLogic / portfolioDockLogic.
 * Do not grow is_portfolio / edition product branches in this file.
 */
"use strict";

import {
  isConfirmedExportTarget,
  readExportPrefs,
} from "../js/longshot-export-panel.js";
import { applyJournalDockLogic, journalDockCta } from "../js/journal-dock-logic.js";
import {
  applyPortfolioDockLogic,
  resolveTripEdition,
  syncPortfolioFlagOffBanner,
  syncPortfolioOverflowBadge,
} from "../js/portfolio-dock-logic.js";
import {
  isPortfolioEdition,
  portfolioDockCta,
} from "../js/portfolio-export-logic.js";

export { syncPortfolioFlagOffBanner, syncPortfolioOverflowBadge };

export function presentPreviewUrl() {
  return document.documentElement.getAttribute("data-present-preview-url") || "";
}

export function presentAutoplayHref(opts) {
  var url = presentPreviewUrl();
  if (!url) return "";
  var href = url;
  if (opts && opts.featured) {
    href += (href.indexOf("?") >= 0 ? "&" : "?") + "presentFeatured=1";
  }
  return href + "#present/1";
}

/**
 * DIG · Dock 线图标（对齐效果图：返回圈箭 / 播放三角 / 分章列表 /
 * 精修滑杆 / AI 星芒 / 文件夹 / 导出下行 / 帮助圈问号）。
 */
export function dockIconSvg(name) {
  var attrs =
    'class="preview-toolbar__dock-icon" viewBox="0 0 24 24" ' +
    'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" ' +
    'stroke-linejoin="round" aria-hidden="true" focusable="false"';
  switch (name) {
    case "help":
      return (
        "<svg " +
        attrs +
        ">" +
        '<circle cx="12" cy="12" r="9"/>' +
        '<path d="M9.6 9.4a2.4 2.4 0 0 1 4.6 1.1c0 1.6-2.2 2.1-2.2 3.5"/>' +
        '<circle cx="12" cy="17.2" r="0.85" fill="currentColor" stroke="none"/>' +
        "</svg>"
      );
    case "back":
      // 无外圈，避免被误认成「选中芯片」
      return (
        "<svg " +
        attrs +
        ">" +
        '<path d="M15 6.5L9 12l6 5.5"/>' +
        '<path d="M9.5 12H19"/>' +
        "</svg>"
      );
    case "play":
      return (
        "<svg " +
        attrs +
        ">" +
        '<path d="M9 7.2v9.6L18 12z"/>' +
        "</svg>"
      );
    case "refine":
      // 效果图：三档滑杆（精修）
      return (
        "<svg " +
        attrs +
        ">" +
        '<path d="M5 7h14"/>' +
        '<circle cx="9" cy="7" r="1.7" fill="currentColor" stroke="none"/>' +
        '<path d="M5 12h14"/>' +
        '<circle cx="14" cy="12" r="1.7" fill="currentColor" stroke="none"/>' +
        '<path d="M5 17h14"/>' +
        '<circle cx="11" cy="17" r="1.7" fill="currentColor" stroke="none"/>' +
        "</svg>"
      );
    case "settings":
      // 设置齿轮（caret / 兼容别名；精修请用 refine）
      return (
        "<svg " +
        attrs +
        ">" +
        '<circle cx="12" cy="12" r="3"/>' +
        '<path d="M12 3.5v2.2M12 18.3v2.2M3.5 12h2.2M18.3 12h2.2M6 6l1.6 1.6M16.4 16.4L18 18M18 6l-1.6 1.6M7.6 16.4L6 18"/>' +
        "</svg>"
      );
    case "scroll":
      return (
        "<svg " +
        attrs +
        ">" +
        '<rect x="7.5" y="3" width="9" height="13" rx="1.8"/>' +
        '<path d="M12 11.5v8"/>' +
        '<path d="M9.2 17.2L12 20l2.8-2.8"/>' +
        "</svg>"
      );
    case "chapters":
      // 效果图：条目列表
      return (
        "<svg " +
        attrs +
        ">" +
        '<circle cx="5.5" cy="7" r="1.2" fill="currentColor" stroke="none"/>' +
        '<path d="M9 7h10"/>' +
        '<circle cx="5.5" cy="12" r="1.2" fill="currentColor" stroke="none"/>' +
        '<path d="M9 12h10"/>' +
        '<circle cx="5.5" cy="17" r="1.2" fill="currentColor" stroke="none"/>' +
        '<path d="M9 17h10"/>' +
        "</svg>"
      );
    case "folder":
      return (
        "<svg " +
        attrs +
        ">" +
        '<path d="M3.5 8.2V18a2 2 0 0 0 2 2h13a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2h-6.3L10.2 5.8H5.5a2 2 0 0 0-2 2.4z"/>' +
        "</svg>"
      );
    case "ai":
      // 效果图：单颗四角星芒
      return (
        "<svg " +
        attrs +
        ">" +
        '<path d="M12 3.2l1.85 5.05L19 10.1l-5.15 1.85L12 17.1l-1.85-5.15L5 10.1l5.15-1.85L12 3.2z"/>' +
        "</svg>"
      );
    default:
      return "";
  }
}

/**
 * @returns {(HTMLElement & { _dockCta?: { short?: string, aria?: string } }) | null}
 */
function _dockRoot() {
  if (typeof document === "undefined") return null;
  return /** @type {(HTMLElement & { _dockCta?: { short?: string, aria?: string } }) | null} */ (
    document.querySelector(".preview-toolbar")
  );
}

function _htmlEditionIsPortfolio() {
  try {
    return isPortfolioEdition(
      typeof document !== "undefined" && document.documentElement
        ? document.documentElement.getAttribute("data-edition")
        : ""
    );
  } catch (_eEd) {
    return false;
  }
}

function idleExportShortLabel() {
  // 只读 edition 做 idle 标签兜底；行为差异改 *-dock-logic.js。
  try {
    var root = _dockRoot();
    if (root && root._dockCta && root._dockCta.short) return root._dockCta.short;
    if (_htmlEditionIsPortfolio()) return portfolioDockCta().short;
    var prefs = readExportPrefs();
    if (isConfirmedExportTarget(prefs)) {
      return journalDockCta().short;
    }
  } catch (_eIdle) {}
  return journalDockCta().short;
}

export function idleExportAriaLabel() {
  try {
    var root = _dockRoot();
    if (root && root._dockCta && root._dockCta.aria) return root._dockCta.aria;
    if (_htmlEditionIsPortfolio()) return portfolioDockCta().aria;
  } catch (_eAria) {}
  return journalDockCta().aria;
}

export function dockLongshotContentHtml(state) {
  if (state === "running") {
    return (
      '<span class="preview-toolbar__dock-export-inner preview-toolbar__dock-export-inner--running">' +
      '<span class="preview-toolbar__longshot__spinner" aria-hidden="true"></span>' +
      '<span class="preview-toolbar__dock-export-label">导出中</span></span>'
    );
  }
  if (state === "done") {
    return (
      '<span class="preview-toolbar__dock-export-inner preview-toolbar__dock-export-inner--done">' +
      '<span class="preview-toolbar__dock-export-label" aria-hidden="true">✓</span>' +
      '<span class="preview-toolbar__dock-export-label">已保存</span></span>'
    );
  }
  return (
    '<span class="preview-toolbar__dock-export-inner">' +
    dockIconSvg("scroll") +
    '<span class="preview-toolbar__dock-export-label">' +
    idleExportShortLabel() +
    "</span></span>"
  );
}

export function insertScreenplayControl(parent, beforeNode, opts) {
  if (!parent) return null;
  opts = opts || {};
  var label = opts.label != null ? opts.label : "▶ 全屏放映";
  if (opts.dock) label = "播放";
  var v3Class = opts.v3 ? " preview-toolbar__screenplay--v3" : "";
  var dockClass = opts.dock
    ? " preview-toolbar__dock-btn preview-toolbar__dock-btn--screenplay preview-toolbar__dock-btn--folio preview-toolbar__dock-btn--labeled"
    : "";
  if (document.documentElement.getAttribute("data-screenplay") === "on") {
    var screenplayBtn = document.createElement("button");
    screenplayBtn.type = "button";
    screenplayBtn.className =
      "preview-toolbar__ctl preview-toolbar__screenplay" + v3Class + dockClass;
    screenplayBtn.setAttribute("data-screenplay-trigger", "start");
    screenplayBtn.setAttribute("data-screenplay-label", label);
    screenplayBtn.setAttribute("data-screenplay-busy", "退出放映");
    screenplayBtn.setAttribute("aria-pressed", "false");
    screenplayBtn.setAttribute("aria-label", "播放");
    if (opts.dock) {
      screenplayBtn.innerHTML =
        dockIconSvg("play") +
        '<span class="preview-toolbar__dock-label">播放</span>';
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
    autoplayLink.innerHTML =
      dockIconSvg("play") +
      '<span class="preview-toolbar__dock-label">播放</span>';
  } else {
    autoplayLink.textContent = label;
  }
  autoplayLink.setAttribute("aria-label", "播放");
  parent.insertBefore(autoplayLink, beforeNode || null);
  return autoplayLink;
}

export function isPreviewToolbarV4(root) {
    return !!(root && root.classList.contains("preview-toolbar--v4"));
  }

export function isPreviewToolbarV3(root) {
    return !!(
      root &&
      (root.classList.contains("preview-toolbar--v3") ||
        root.classList.contains("preview-toolbar--v4"))
    );
  }

export function dockLongshotIconHtml(state) {
    return dockLongshotContentHtml(state);
  }

export function setDockLongshotAria(btn, state) {
    if (!btn) return;
    if (state === "running") {
      btn.setAttribute("aria-label", "导出中");
      updateDockTip(btn, "导出中…");
    } else if (state === "done") {
      btn.setAttribute("aria-label", "已保存到此画册文件夹");
      updateDockTip(btn, "已保存");
    } else {
      var idleAria = idleExportAriaLabel();
      btn.setAttribute("aria-label", idleAria);
      updateDockTip(btn, idleAria);
    }
  }

export function applyDockLongshotIdle(btn) {
    if (!btn) return;
    btn.innerHTML = dockLongshotIconHtml("idle");
    setDockLongshotAria(btn, "idle");
  }

export function updateDockTip(btn, text) {
    if (btn && btn._dockTipEl) {
      btn._dockTipEl.textContent = text;
    }
  }

export function ensureDockTooltip(btn, label) {
    if (!btn || btn.querySelector(".preview-toolbar__dock-tip")) return;
    btn.classList.add("preview-toolbar__dock-btn--has-tip");
    var tip = document.createElement("span");
    tip.className = "preview-toolbar__dock-tip";
    tip.setAttribute("role", "tooltip");
    tip.textContent = label;
    btn.appendChild(tip);
    btn._dockTipEl = tip;
  }

export function syncDockScreenplayTip(btn) {
    if (!btn || !btn._dockTipEl) return;
    btn._dockTipEl.textContent =
      btn.getAttribute("aria-pressed") === "true" ? "退出放映" : "放映";
  }

export function initDockTooltips(root) {
    // 底栏按钮已有可见文字标签，不再挂悬浮 tip / 原生 title
    if (!isPreviewToolbarV4(root)) return;
    var dock = root.querySelector(".preview-toolbar__dock");
    if (!dock) return;
    var caretBtn = dock.querySelector(".preview-toolbar__longshot-caret");
    if (caretBtn) caretBtn.removeAttribute("title");
  }

export function applyTripEdition(root, entry) {
  var edition = resolveTripEdition(root, entry);
  if (root) {
    root._edition = edition;
    if (entry) {
      root._portfolio = entry.portfolio || null;
      root._pipelineEnabled = entry.portfolioPipelineEnabled === true;
      root._layoutVibeVisible = entry.layoutVibeVisible !== false;
      root._dockCta = entry.dockCta || null;
      root._overflowLine = entry.overflowLine || "";
      root._overflowDetail = entry.overflowDetail || "";
      root._overflowCta = entry.overflowCta || "";
      root._previewUrl = String(
        (entry.scrollShareUrl || entry.previewUrl) || ""
      ).trim();
    }
  }
  // S-09 · 身份只在此处分发一次。新业务写 journal-dock-logic / portfolio-dock-logic。
  var isPortfolio = edition === "portfolio";
  try {
    if (typeof document !== "undefined" && document.documentElement) {
      if (isPortfolio) {
        document.documentElement.setAttribute("data-edition", "portfolio");
      } else {
        document.documentElement.removeAttribute("data-edition");
      }
    }
  } catch (_eAttr) {}
  if (isPortfolio) {
    applyPortfolioDockLogic(root, entry);
  } else {
    applyJournalDockLogic(root, entry);
  }
}

export function initDockScrollFade(root) {
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

