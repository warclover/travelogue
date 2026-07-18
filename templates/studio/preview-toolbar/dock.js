/**
 * Preview toolbar · dock icons, screenplay control, dock UX.
 */
"use strict";

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

/** Folio / editorial-room SVG glyphs for v4 icon dock (PRD §6.1.1). */
export function dockIconSvg(name) {
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
        '<path d="M19 12H7"/>' +
        '<path d="M11 7l-5 5 5 5"/>' +
        "</svg>"
      );
    case "play":
      return (
        "<svg " +
        attrs +
        ">" +
        '<rect x="3" y="5" width="18" height="14" rx="2.5"/>' +
        '<path d="M10 9.2v5.6L15.8 12z" ' +
        accent +
        "/>" +
        "</svg>"
      );
    case "refine":
    case "settings": // 短暂别名兼容（settings → refine）
      return (
        "<svg " +
        attrs +
        ">" +
        '<path d="M13.2 5.2l5.6 5.6"/>' +
        '<path d="M4 20l1.6-5.4L15.8 4.4a2 2 0 0 1 2.8 0l1 1a2 2 0 0 1 0 2.8L9.4 18.4 4 20z"/>' +
        '<path d="M12.2 7.2l4.6 4.6"/>' +
        "</svg>"
      );
    case "scroll":
      return (
        "<svg " +
        attrs +
        ">" +
        '<rect x="8" y="2.5" width="8" height="12.5" rx="1.6"/>' +
        '<path d="M12 11.5v9"/>' +
        '<path d="M9 17.5l3 3 3-3"/>' +
        "</svg>"
      );
    default:
      return "";
  }
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
    '<span class="preview-toolbar__dock-export-label">长图</span></span>'
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
      btn.setAttribute("aria-label", "已保存到此游记文件夹");
      updateDockTip(btn, "已保存");
    } else {
      btn.setAttribute("aria-label", "导出长图");
      updateDockTip(btn, "导出长图");
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

