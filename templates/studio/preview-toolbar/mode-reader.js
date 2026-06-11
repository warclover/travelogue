/**
 * Preview toolbar · reader/present mode + G1 hints (§6.1).
 */
"use strict";

import { trackStudioEvent } from "../js/analytics.js";
import {
  applySurfaceReaderMode,
  getPreviewStore,
  setPreviewStore,
  loadPreviewMode,
  persistPreviewMode,
  hasSeenEditModeHint,
  markEditModeHintSeen,
} from "./store.js";
import { presentAutoplayHref } from "./share-mode.js";
import { tripIdFromPath, showToolbarToast } from "./toolbar-ui.js";
import { refreshPendingUi } from "./pending.js";
import { fetchEntry } from "./drawer-support.js";

export function initG1Banner(root, tripId, drawers) {
  Promise.all([
    fetch("/__travelogue/config").then(function (r) { return r.ok ? r.json() : null; }),
    fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry").then(function (r) {
      return r.ok ? r.json() : null;
    }),
  ])
    .then(function (rows) {
      var cfg = rows[0];
      var entry = rows[1];
      if (!cfg || !entry || !entry.g1Pending) return;
      if (!(cfg.studio && cfg.studio.g1ConfirmStructure)) return;
      if (document.querySelector(".preview-toolbar__g1-banner")) return;

      var banner = document.createElement("div");
      banner.className = "preview-toolbar__g1-banner";
      banner.setAttribute("role", "status");
      banner.innerHTML =
        '<p class="preview-toolbar__g1-banner-text">章节结构待确认（G1 已开启）</p>' +
        '<div class="preview-toolbar__g1-banner-actions">' +
        '<button type="button" class="preview-toolbar__g1-banner-open">查看结构</button>' +
        '<button type="button" class="preview-toolbar__g1-banner-confirm">确认并继续</button>' +
        "</div>";
      var anchor =
        document.querySelector(".travelogue-scroll") ||
        document.querySelector(".layout-root") ||
        document.querySelector("main") ||
        document.body;
      anchor.insertBefore(banner, anchor.firstChild);
      banner.querySelector(".preview-toolbar__g1-banner-open").addEventListener("click", function () {
        drawers.openStructure();
      });
      banner.querySelector(".preview-toolbar__g1-banner-confirm").addEventListener("click", function () {
        drawers.confirmStructure();
      });
      if (getPreviewStore().mode === "reader") {
        banner.hidden = true;
      }
    })
    .catch(function () {});
}

export function initG1ReaderPill(root, tripId) {
  var identity = root.querySelector(".preview-toolbar__identity");
  if (!identity || identity.querySelector(".preview-toolbar__g1-pill")) return;
  Promise.all([
    fetch("/__travelogue/config").then(function (r) { return r.ok ? r.json() : null; }),
    fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry").then(function (r) {
      return r.ok ? r.json() : null;
    }),
  ])
    .then(function (rows) {
      var cfg = rows[0];
      var entry = rows[1];
      if (!cfg || !entry || !entry.g1Pending) return;
      if (!(cfg.studio && cfg.studio.g1ConfirmStructure)) return;
      var pill = document.createElement("button");
      pill.type = "button";
      pill.className = "preview-toolbar__g1-pill";
      pill.textContent = "章节结构待确认 → 去编辑";
      pill.addEventListener("click", function () {
        if (typeof root._setPreviewMode === "function") {
          root._setPreviewMode("edit");
        }
      });
      identity.appendChild(pill);
      pill.hidden = getPreviewStore().mode !== "reader";
    })
    .catch(function () {});
}

function startFeaturedPresent() {
  var featuredHref = presentAutoplayHref({ featured: true });
  if (featuredHref) {
    window.location.href = featuredHref;
    showToolbarToast("精选全屏放映已开始");
    return;
  }
  var toggle = document.getElementById("featured-present-toggle");
  var start = document.getElementById("screenplay-start");
  if (!start) {
    showToolbarToast("当前页面不支持全屏放映", { error: true });
    return;
  }
  if (toggle && toggle.getAttribute("aria-pressed") !== "true") {
    toggle.click();
  }
  start.click();
  showToolbarToast("精选全屏放映已开始");
}

export function snapshotReadingPayload() {
  var reading = window.__TRAVELOGUE_READING__;
  if (!reading || typeof reading !== "object") return null;
  try {
    return JSON.parse(JSON.stringify(reading));
  } catch (e) {
    return null;
  }
}

export function applyReaderSurfaceMode(readerMode) {
  applySurfaceReaderMode(readerMode);
  var reading = window.__TRAVELOGUE_READING__ || {};
  if (readerMode) {
    reading.profile = "reader_immersive";
    reading.scroll = reading.scroll || {};
    reading.scroll.folio = "off";
  } else {
    reading.profile = "studio_preview";
    reading.scroll = reading.scroll || {};
    reading.scroll.folio = "lite";
  }
  window.__TRAVELOGUE_READING__ = reading;
  if (window.TravelogueBreath && typeof window.TravelogueBreath.destroy === "function") {
    window.TravelogueBreath.destroy();
  }
  if (window.TravelogueBreath && typeof window.TravelogueBreath.init === "function") {
    window.TravelogueBreath.init();
  }
}

export function syncPreviewSurface(root, mode) {
  if (!root) return;
  var isReader = mode === "reader";
  root.setAttribute("data-preview-mode", mode);
  document.documentElement.setAttribute("data-preview-mode", mode);
  applyReaderSurfaceMode(isReader);
  var readerZone = root.querySelector(".preview-toolbar__reader-zone");
  var editZone = root.querySelector(".preview-toolbar__edit-zone");
  if (readerZone) readerZone.hidden = !isReader;
  if (editZone) editZone.hidden = isReader;
  refreshPendingUi(root);
  document.querySelectorAll(".preview-toolbar__g1-banner").forEach(function (el) {
    el.hidden = isReader;
  });
  document.querySelectorAll(".preview-toolbar__g1-pill").forEach(function (el) {
    el.hidden = !isReader;
  });
  document.querySelectorAll(".preview-toolbar__featured-star").forEach(function (el) {
    el.hidden = isReader;
  });
  document.querySelectorAll(".preview-toolbar__collage-ctrl").forEach(function (el) {
    el.hidden = isReader;
  });
}

export function startPresentMode(root, opts) {
  opts = opts || {};
  if (document.documentElement.getAttribute("data-screenplay") === "on") {
    var trigger = document.querySelector("[data-screenplay-trigger='start']");
    if (trigger && typeof trigger.click === "function") {
      trigger.click();
      return;
    }
  }
  if (opts.featured) {
    startFeaturedPresent();
    return;
  }
  var href = presentAutoplayHref(opts);
  if (href) window.location.href = href;
}

export function initPreviewModeSeg(root, actions, drawers) {
  var baseline = snapshotReadingPayload();
  var seg = document.createElement("div");
  seg.className = "preview-toolbar__mode-seg";
  seg.setAttribute("role", "group");
  seg.setAttribute("aria-label", "预览模式");

  var readerBtn = document.createElement("button");
  readerBtn.type = "button";
  readerBtn.textContent = "阅读";
  var editBtn = document.createElement("button");
  editBtn.type = "button";
  editBtn.textContent = "编辑";
  var presentBtn = document.createElement("button");
  presentBtn.type = "button";
  presentBtn.className = "preview-toolbar__mode-present";
  presentBtn.textContent = "▶ 放映";
  presentBtn.title = "全屏逐屏放映";
  seg.appendChild(readerBtn);
  seg.appendChild(editBtn);
  seg.appendChild(presentBtn);
  actions.insertBefore(seg, actions.firstChild);

  var mode = loadPreviewMode();
  if (baseline && baseline.profile === "reader_immersive") {
    mode = "reader";
  }

  function syncSeg() {
    var current = getPreviewStore().mode;
    readerBtn.classList.toggle("is-selected", current === "reader");
    editBtn.classList.toggle("is-selected", current === "edit");
    readerBtn.setAttribute("aria-pressed", current === "reader" ? "true" : "false");
    editBtn.setAttribute("aria-pressed", current === "edit" ? "true" : "false");
    presentBtn.classList.remove("is-selected");
    presentBtn.setAttribute("aria-pressed", "false");
  }

  function setPreviewMode(next, opts) {
    opts = opts || {};
    if (next !== "reader" && next !== "edit") return;
    var prev = getPreviewStore().mode;
    setPreviewStore({ mode: next });
    persistPreviewMode(next);
    syncPreviewSurface(root, next);
    syncSeg();
    if (next === "edit" && !hasSeenEditModeHint()) {
      markEditModeHintSeen();
      showToolbarToast("编辑模式：标记精选与媒资后，点「应用排版」生效", { duration: 5200 });
    }
    if (!opts.silent) {
      trackStudioEvent("preview_mode_switch", {
        from: prev,
        to: next,
        tripId: tripIdFromPath(),
      });
    }
  }

  readerBtn.addEventListener("click", function () {
    setPreviewMode("reader");
  });
  editBtn.addEventListener("click", function () {
    setPreviewMode("edit");
  });
  presentBtn.addEventListener("click", function () {
    if (drawers && typeof drawers.refreshEntry === "function") {
      drawers.refreshEntry().then(function (data) {
        var count = (data && data.intentSummary && data.intentSummary.featuredCount) || 0;
        if (count > 0 && typeof studioModal === "function") {
          studioModal({
            title: "全屏放映",
            body: "选择放映范围",
            confirmLabel: "从头放映",
            cancelLabel: "仅放映精选",
          }).then(function (ok) {
            startPresentMode(root, { featured: !ok });
          });
          return;
        }
        startPresentMode(root);
      });
      return;
    }
    startPresentMode(root);
  });

  setPreviewStore({ mode: mode });
  syncPreviewSurface(root, mode);
  syncSeg();
  root._setPreviewMode = setPreviewMode;
}
