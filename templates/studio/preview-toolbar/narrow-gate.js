/**
 * PMX FE-PMX-20 · 预览窄屏诚实门面（与首页同一断点）。
 * Share 只读预览不拦截；Studio 工作台预览禁止近黑屏无说明。
 * QFX D-QFX-12 · 复制三态。
 */
"use strict";

import {
  classifyViewport,
  isSupported,
  unsupportedCopy,
} from "../homepage-v2/viewport-logic.js";
import { trackStudioEvent } from "../js/analytics.js";
import { bindCopyPageUrlControl } from "../js/copy-page-url.js";
import { readEditionFromDom } from "../js/portfolio-export-logic.js";
import { resolvePreviewNarrowGateCopy } from "./narrow-gate-logic.js";

var GATE_ID = "preview-narrow-gate";
var _lastLayout = null;
var _wired = false;

function coarsePointer() {
  try {
    return window.matchMedia("(pointer: coarse)").matches;
  } catch (_e) {
    return false;
  }
}

function currentLayout() {
  var w = window.innerWidth || document.documentElement.clientWidth || 0;
  var h = window.innerHeight || document.documentElement.clientHeight || 0;
  return classifyViewport(w, h, coarsePointer());
}

function pageUrl() {
  return window.location.origin + window.location.pathname + window.location.search;
}

function ensureGateEl() {
  var el = document.getElementById(GATE_ID);
  if (el) return el;
  el = document.createElement("section");
  el.id = GATE_ID;
  el.className = "preview-narrow-gate";
  el.setAttribute("hidden", "");
  el.setAttribute("role", "dialog");
  el.setAttribute("aria-modal", "true");
  el.setAttribute("aria-labelledby", "preview-narrow-gate-title");
  el.innerHTML =
    '<div class="preview-narrow-gate__card">' +
    '<p class="preview-narrow-gate__brand">TRAVELOGUE · STUDIO</p>' +
    '<h1 class="preview-narrow-gate__title" id="preview-narrow-gate-title"></h1>' +
    '<p class="preview-narrow-gate__lead" id="preview-narrow-gate-lead"></p>' +
    '<div class="preview-narrow-gate__actions">' +
    '<a class="preview-narrow-gate__btn preview-narrow-gate__btn--primary" href="/">返回首页制作</a>' +
    '<button type="button" class="preview-narrow-gate__btn" id="preview-narrow-gate-copy">复制电脑打开地址</button>' +
    "</div>" +
    '<input id="preview-narrow-gate-url" class="preview-narrow-gate__url" type="text" readonly hidden aria-label="电脑打开地址" />' +
    "</div>";
  document.body.appendChild(el);
  var copyBtn = /** @type {HTMLElement|null} */ (el.querySelector("#preview-narrow-gate-copy"));
  var urlInput = /** @type {HTMLInputElement|null} */ (
    el.querySelector("#preview-narrow-gate-url")
  );
  bindCopyPageUrlControl({
    button: copyBtn,
    urlInput: urlInput,
    getUrl: pageUrl,
    defaultLabel: "复制电脑打开地址",
    onTrack: function (result) {
      trackStudioEvent("preview_narrow_gate_action", {
        action: "copy_link",
        result: result,
      });
    },
  });
  return el;
}

function showGate(layout) {
  var base = unsupportedCopy(layout, {
    width: window.innerWidth || document.documentElement.clientWidth || 0,
    miniappQrAvailable: false,
  });
  var copy = resolvePreviewNarrowGateCopy(
    layout,
    readEditionFromDom(document),
    base
  );
  var el = ensureGateEl();
  var title = el.querySelector("#preview-narrow-gate-title");
  var lead = el.querySelector("#preview-narrow-gate-lead");
  if (title) title.textContent = copy.title;
  if (lead) lead.textContent = copy.lead;
  el.removeAttribute("hidden");
  document.documentElement.setAttribute("data-preview-narrow-gate", "1");
  if (_lastLayout !== layout) {
    _lastLayout = layout;
    trackStudioEvent("preview_narrow_gate_view", {
      layout: String(layout || "").replace(/^unsupported_/, "") || "unknown",
    });
  }
}

function hideGate() {
  var el = document.getElementById(GATE_ID);
  if (el) el.setAttribute("hidden", "");
  document.documentElement.removeAttribute("data-preview-narrow-gate");
  _lastLayout = null;
}

function apply() {
  var layout = currentLayout();
  if (isSupported(layout)) {
    hideGate();
    return;
  }
  showGate(layout);
}

/**
 * Share 只读预览跳过；Studio 预览挂载后启用。
 */
export function refreshPreviewNarrowGate() {
  apply();
}

export function initPreviewNarrowGate() {
  if (_wired) {
    apply();
    return;
  }
  _wired = true;
  apply();
  window.addEventListener("resize", apply);
  try {
    window.matchMedia("(orientation: portrait)").addEventListener("change", apply);
  } catch (_e) {}
}
