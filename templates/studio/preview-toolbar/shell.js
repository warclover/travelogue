/**
 * Preview toolbar · shared chrome (toast, collapse, layout height).
 */
"use strict";

import { trackStudioEvent } from "../js/analytics.js";
import { isPreviewToolbarV3, isPreviewToolbarV4 } from "./dock.js";

var COLLAPSE_KEY = "travelogue.studio.previewToolbar.collapsed";
var COVER_STYLE_TOAST_KEY = "travelogue.coverStyleToast.";
var COVER_LEGACY_NOTICE_KEY = "travelogue.coverLegacyNotice.";
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
    var style = section.getAttribute("data-cover-opening") || "veil-footer";
    var storageKey = COVER_STYLE_TOAST_KEY + tripId;
    var legacyKey = COVER_LEGACY_NOTICE_KEY + tripId;

    fetchEntrySafe(tripId).then(function (data) {
      if (!data) return;
      syncCoverPlaceholderBadge(!!data.coverIsPlaceholder);
      syncCoverExplainLine(data);

      // §7.4 · legacy V5 notice once
      try {
        if (data.coverLegacyMapped && !localStorage.getItem(legacyKey)) {
          localStorage.setItem(legacyKey, "1");
          var raw = data.coverOpeningStyleRaw || "";
          var extra =
            raw === "split-mat" || raw === "magazine-head"
              ? "原先两款编辑向版式，现统一呈现为「对页叠印」。"
              : "";
          showToolbarToast(
            "封面已按新画册风格呈现；你的原始设定未改写。" + (extra ? " " + extra : ""),
            { duration: 5200 }
          );
          trackStudioEvent("cover_opening_style_render", {
            tripId: tripId,
            coverOpeningStyle: style,
            legacyMapped: true,
          });
          return;
        }
      } catch (e) {}

      // §7.2 · joint toast once per trip (after lock)
      if (!data.coverJointLocked) return;
      try {
        if (localStorage.getItem(storageKey)) return;
        localStorage.setItem(storageKey, "1");
      } catch (e) {
        return;
      }
      var label = data.coverStyleLabel || style;
      trackStudioEvent("cover_opening_style_render", {
        tripId: tripId,
        coverOpeningStyle: style,
        source: (data.coverStyleExplain && data.coverStyleExplain.source) || "joint-v6",
      });
      showToolbarToast(
        "已为这本游记选了「" + label + "」，并配了更合适的封面图。可在「排版」中更换。",
        { duration: 4200 }
      );
    });
  }

  function fetchEntrySafe(tripId) {
    return fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry")
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; });
  }

export function syncCoverPlaceholderBadge(isPlaceholder) {
    var cover = document.querySelector(".cover-opening");
    if (!cover) return;
    var badge = cover.querySelector(".cover-opening__placeholder-badge");
    if (isPlaceholder) {
      if (!badge) {
        badge = document.createElement("p");
        badge.className = "cover-opening__placeholder-badge";
        badge.setAttribute("role", "status");
        cover.appendChild(badge);
      }
      badge.hidden = false;
      badge.textContent = "临时预览 · 精选后更新";
    } else if (badge) {
      badge.hidden = true;
    }
  }

export function syncCoverExplainLine(data) {
    var cover = document.querySelector(".cover-opening");
    if (!cover || !data) return;
    var line = cover.querySelector(".cover-opening__explain-line");
    var text = explainToHuman(data.coverStyleExplain);
    if (!text) {
      if (line) line.hidden = true;
      return;
    }
    if (!line) {
      line = document.createElement("p");
      line.className = "cover-opening__explain-line";
      cover.appendChild(line);
    }
    line.hidden = false;
    line.textContent = text;
  }

function explainToHuman(explain) {
    if (!explain || typeof explain !== "object") return "";
    if (explain.lowConfidence) return "备选有限，已选相对最合适的一款";
    if (explain.source === "manual") return "由你手动选定";
    var styleId = explain.styleId || "";
    if (styleId === "cameo-aperture") return "主体较居中，适合圆窗";
    if (styleId === "band-cut") return "避开了题带压到人物";
    if (styleId === "veil-footer") return "主体偏上，适合雾底题签";
    if (styleId === "folio-overlap") return "右侧有景，适合对页叠印";
    if (styleId === "type-monument") return "氛围底图，适合海报巨字";
    if (explain.source === "joint-v6") return "已按版式与封面图联合精选";
    return "";
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
