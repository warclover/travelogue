/**
 * Preview mode · Trust V1 refine / inspect chrome authority.
 * html[data-preview-refine="off"|"on"] — default off (验货壳).
 *
 * V1.1 · 精修模式可独立于面板存在（模式 ≠ 面板）。
 */
"use strict";

var REFINE_STAR_TIP_KEY = "travelogue.preview.refineStarTipSeen.v2";
var BOOK_TAB_MIGRATE_TIP_KEY = "travelogue.preview.bookTabMigrateTipSeen";

export function getPreviewRefineMode() {
  var v = document.documentElement.getAttribute("data-preview-refine");
  return v === "on" ? "on" : "off";
}

export function isPreviewRefineOn() {
  return getPreviewRefineMode() === "on";
}

export function isPreviewShareOn() {
  return document.documentElement.getAttribute("data-preview-share") === "on";
}

/**
 * @param {boolean} on
 */
export function setPreviewRefineMode(on) {
  document.documentElement.setAttribute("data-preview-refine", on ? "on" : "off");
  syncInspectChromeVisibility();
  if (!on) {
    hideRefineModeChip();
  }
}

/** Hide + disable ★ / collage when refine=off (CSS + interaction). */
export function syncInspectChromeVisibility() {
  var on = isPreviewRefineOn();
  document
    .querySelectorAll(
      ".preview-toolbar__featured-star, .preview-toolbar__collage-ctrl"
    )
    .forEach(function (el) {
      el.hidden = !on;
      el.setAttribute("aria-hidden", on ? "false" : "true");
      if (el.tagName === "BUTTON" || el.tagName === "SELECT") {
        el.disabled = !on;
      }
      el.querySelectorAll("button, select").forEach(function (ctl) {
        ctl.disabled = !on;
      });
      if (!on) {
        el.style.pointerEvents = "none";
      } else {
        el.style.pointerEvents = "";
      }
    });
}

export function ensurePreviewRefineDefault() {
  if (!document.documentElement.hasAttribute("data-preview-refine")) {
    document.documentElement.setAttribute("data-preview-refine", "off");
  }
  syncDebugAttrFromUrl();
  syncInspectChromeVisibility();
}

/** FE-SFI-02 · ``?debug=1`` → html[data-debug="1"]（Plate 门禁） */
export function syncDebugAttrFromUrl() {
  try {
    var q = new URLSearchParams(window.location.search || "");
    if (q.get("debug") === "1") {
      document.documentElement.setAttribute("data-debug", "1");
    } else {
      document.documentElement.removeAttribute("data-debug");
    }
  } catch (_e) {
    /* ignore */
  }
}

/**
 * Sync Dock「精修/完成」文案与 a11y（SF-04：pressed=模式 · expanded=面板）.
 * @param {HTMLElement | null} root
 * @param {{ panelOpen?: boolean }} [opts]
 */
export function syncRefineDockChrome(root, opts) {
  opts = opts || {};
  var menuBtn =
    (root && root.querySelector(".preview-toolbar__menu-btn")) ||
    document.querySelector(".preview-toolbar__menu-btn");
  if (!menuBtn) return;

  var on = isPreviewRefineOn();
  var panelOpen = !!opts.panelOpen;
  var showDone = on && !panelOpen;
  var label = showDone ? "完成" : "精修";

  menuBtn.setAttribute("aria-expanded", panelOpen ? "true" : "false");
  menuBtn.setAttribute("aria-pressed", on ? "true" : "false");
  menuBtn.setAttribute("aria-label", label);
  menuBtn.classList.toggle("preview-toolbar__dock-btn--done", showDone);

  var labelEl = menuBtn.querySelector(".preview-toolbar__dock-label");
  if (labelEl) labelEl.textContent = label;

  if (on) {
    ensureRefineModeChip();
  } else {
    hideRefineModeChip();
  }
}

function ensureRefineModeChip() {
  var chip = document.getElementById("preview-refine-mode-chip");
  if (!chip) {
    chip = document.createElement("div");
    chip.id = "preview-refine-mode-chip";
    chip.className = "preview-toolbar__refine-chip";
    chip.setAttribute("role", "status");
    document.body.appendChild(chip);
  }
  chip.textContent = "精修中";
  chip.hidden = false;
}

function hideRefineModeChip() {
  var chip = document.getElementById("preview-refine-mode-chip");
  if (chip) chip.hidden = true;
}

/**
 * 首次收起面板后一次性 tip（MF-04b）。
 * @param {(msg: string, opts?: object) => void} [showToast]
 */
export function maybeShowRefineStarTip(showToast) {
  try {
    if (localStorage.getItem(REFINE_STAR_TIP_KEY) === "1") return;
    localStorage.setItem(REFINE_STAR_TIP_KEY, "1");
  } catch (_e) {
    /* ignore */
  }
  if (typeof showToast === "function") {
    // FE-DFX-46 / MF-04 · 含「点完成退出」
    showToast("可在照片上点 ★ 标精选；点「完成」退出精修", { duration: 4200 });
  }
}

/**
 * 字段迁出后首次打开「画册」的一次性 tip（SF-01 / AC-REFUX-16）。
 * @param {(msg: string, opts?: object) => void} [showToast]
 * @param {(event: string, meta?: object) => void} [track]
 * @returns {boolean} 是否本次展示
 */
export function maybeShowBookTabMigrateTip(showToast, track) {
  try {
    if (localStorage.getItem(BOOK_TAB_MIGRATE_TIP_KEY) === "1") return false;
    localStorage.setItem(BOOK_TAB_MIGRATE_TIP_KEY, "1");
  } catch (_e) {
    /* ignore */
  }
  if (typeof showToast === "function") {
    showToast("章节锚点与意图已移到「页面」", { duration: 4200 });
  }
  if (typeof track === "function") {
    track("book_tab_migrate_tip_show", { once: true });
  }
  return true;
}
