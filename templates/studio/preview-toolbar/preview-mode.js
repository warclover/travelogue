/**
 * Preview mode · Trust V1 refine / inspect chrome authority.
 * html[data-preview-refine="off"|"on"] — default off (验货壳).
 */
"use strict";

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
  syncInspectChromeVisibility();
}
