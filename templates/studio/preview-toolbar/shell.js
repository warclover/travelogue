/**
 * Preview toolbar · shared chrome (toast, collapse, layout height).
 */
"use strict";

import { trackStudioEvent } from "../js/analytics.js";
import { isPreviewToolbarV3, isPreviewToolbarV4 } from "./dock.js";

var COLLAPSE_KEY = "travelogue.studio.previewToolbar.collapsed";
var COVER_STYLE_TOAST_KEY = "travelogue.coverStyleToast.";
var _toastTimer = null;


export function tripIdFromPath() {
    var parts = window.location.pathname.replace(/^\/+|\/+$/g, "").split("/");
    return parts[0] || "";
  }


export function tripApiBase(tripId) {
    return "/" + encodeURIComponent(tripId) + "/__travelogue";
  }


export function toolbarConfirm(opts) {
    if (typeof studioModal === "function") {
      return studioModal(opts);
    }
    var msg = (opts.title ? opts.title + "\n\n" : "") + (opts.body || "");
    return Promise.resolve(window.confirm(msg));
  }


export function toolbarAlert(message, opts) {
    opts = opts || {};
    if (message) showToolbarToast(message, { error: !!opts.error });
  }


export function showToolbarToast(message, opts) {
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


export function maybeShowCoverOpeningStyleToast(tripId) {
    if (!tripId) return;
    var section = document.querySelector(".cover-opening[data-cover-opening]");
    if (!section) return;
    var style = section.getAttribute("data-cover-opening") || "card-br";
    var storageKey = COVER_STYLE_TOAST_KEY + tripId;
    try {
      if (localStorage.getItem(storageKey)) return;
      localStorage.setItem(storageKey, "1");
    } catch (e) {
      return;
    }
    trackStudioEvent("cover_opening_style_render", {
      tripId: tripId,
      coverOpeningStyle: style,
    });
    showToolbarToast(
      "这本游记的封面版式已为你选定（电脑与手机版式不同），可在「排版」设置中更换",
      { duration: 4200 }
    );
  }

  var _layoutPending = false;
  var _pendingDockDismissed = false;
  var _layoutPendingMessage = "";
  var _g1Pending = false;
  var _g1DockDismissed = false;
  var _sheetEditDirty = false;
  var _sheetEditBaseline = "";



export function reloadPreviewAfterLayout() {
    var url = new URL(window.location.href);
    url.searchParams.set("_preview", String(Date.now()));
    window.location.replace(url.toString());
  }


export function setSlowHint(root, text, visible) {
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


export function toolbarBody(root) {
    return root.querySelector(".preview-toolbar__body") || root;
  }


export function syncToolbarHeight(root) {
    if (isPreviewToolbarV4(root)) {
      root.style.height = "";
      document.documentElement.style.setProperty("--preview-toolbar-h", "0px");
      return;
    }
    if (isPreviewToolbarV3(root)) {
      root.style.height = "";
      document.documentElement.style.setProperty("--preview-toolbar-h", "48px");
      return;
    }
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


export function setToolbarCollapsed(root, collapsed, persist) {
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


export function toggleToolbarCollapsed(root) {
    setToolbarCollapsed(root, !root.classList.contains("preview-toolbar--collapsed"));
  }


export function bindToolbarCollapse(root) {
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
