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

/** Folio / editorial-room SVG glyphs for v4 icon dock. */
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
        '<path d="M3.5 3.5h10.2L20.5 7.2V20a1.4 1.4 0 0 1-1.4 1.4H5.4A1.4 1.4 0 0 1 4 20V3.5h-.5z"/>' +
        '<path d="M13.7 3.5V7.4H20.5"/>' +
        '<path d="M13.7 3.5H20.5" ' +
        accent +
        "/>" +
        '<path d="M8 12.2 4.8 12l3.2-2.8"/>' +
        '<path d="M4.8 12h6.8" stroke-width="2"/>' +
        "</svg>"
      );
    case "play":
      return (
        "<svg " +
        attrs +
        ">" +
        '<rect x="2.5" y="2.5" width="19" height="19" rx="2"/>' +
        '<circle cx="5.2" cy="6.8" r="1.05" fill="currentColor" stroke="none"/>' +
        '<circle cx="5.2" cy="12" r="1.05" fill="currentColor" stroke="none"/>' +
        '<circle cx="5.2" cy="17.2" r="1.05" fill="currentColor" stroke="none"/>' +
        '<circle cx="18.8" cy="6.8" r="1.05" fill="currentColor" stroke="none"/>' +
        '<circle cx="18.8" cy="12" r="1.05" fill="currentColor" stroke="none"/>' +
        '<circle cx="18.8" cy="17.2" r="1.05" fill="currentColor" stroke="none"/>' +
        '<polygon points="9,7.5 9,16.5 17.5,12" ' +
        accent +
        "/>" +
        "</svg>"
      );
    case "settings":
      return (
        "<svg " +
        attrs +
        ' stroke-width="1.9">' +
        '<path d="M12 2.3L15.65 5.68L20.41 7.15L19.3 12L20.41 16.85L15.65 18.32L12 21.7L8.35 18.32L3.59 16.85L4.7 12L3.59 7.15L8.35 5.68Z"/>' +
        '<circle cx="12" cy="12" r="3.4"/>' +
        "</svg>"
      );
    case "scroll":
      return (
        "<svg " +
        attrs +
        ">" +
        '<rect x="7" y="2" width="10" height="5.2" rx="0.9" opacity="0.42"/>' +
        '<rect x="5" y="7.2" width="14" height="5.6" rx="0.9" opacity="0.68"/>' +
        '<rect x="3" y="12.8" width="18" height="8.2" rx="1"/>' +
        '<path d="M6.5 20.8h11" stroke-dasharray="2.2 1.6" opacity="0.8" stroke-width="1.6"/>' +
        '<path d="M3 13.8h18" ' +
        accent +
        ' stroke-width="1.45"/>' +
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
  if (opts.dock) label = "▶";
  var v3Class = opts.v3 ? " preview-toolbar__screenplay--v3" : "";
  var dockClass = opts.dock ? " preview-toolbar__dock-btn preview-toolbar__dock-btn--screenplay preview-toolbar__dock-btn--folio" : "";
  if (document.documentElement.getAttribute("data-screenplay") === "on") {
    var screenplayBtn = document.createElement("button");
    screenplayBtn.type = "button";
    screenplayBtn.className =
      "preview-toolbar__ctl preview-toolbar__screenplay" + v3Class + dockClass;
    screenplayBtn.setAttribute("data-screenplay-trigger", "start");
    screenplayBtn.setAttribute("data-screenplay-label", label);
    screenplayBtn.setAttribute("data-screenplay-busy", "退出放映");
    screenplayBtn.setAttribute("aria-pressed", "false");
    screenplayBtn.setAttribute("aria-label", "全屏放映，逐屏展示");
    screenplayBtn.title = "全屏逐屏放映";
    if (opts.dock) {
      screenplayBtn.innerHTML = dockIconSvg("play");
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
    autoplayLink.innerHTML = dockIconSvg("play");
  } else {
    autoplayLink.textContent = label;
  }
  autoplayLink.setAttribute("aria-label", "全屏放映，逐屏展示");
  autoplayLink.title = "全屏逐屏放映";
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
    if (!isPreviewToolbarV4(root)) return;
    var dock = root.querySelector(".preview-toolbar__dock");
    if (!dock) return;

    ensureDockTooltip(
      dock.querySelector(".preview-toolbar__dock-btn--back"),
      "返回"
    );
    ensureDockTooltip(dock.querySelector(".preview-toolbar__menu-btn"), "编辑与设置");

    var exportBtn = dock.querySelector(".preview-toolbar__dock-btn--export");
    ensureDockTooltip(exportBtn, "导出长图");

    var screenplayBtn = dock.querySelector(".preview-toolbar__screenplay--v3");
    ensureDockTooltip(screenplayBtn, "放映");
    if (screenplayBtn && typeof MutationObserver !== "undefined") {
      syncDockScreenplayTip(screenplayBtn);
      var spObs = new MutationObserver(function () {
        syncDockScreenplayTip(screenplayBtn);
      });
      spObs.observe(screenplayBtn, {
        attributes: true,
        attributeFilter: ["aria-pressed"],
      });
      root._dockScreenplayTipObs = spObs;
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

