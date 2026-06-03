/**
 * 首页 v2 · 工作台高级分析选项（Popover + 复用 advanced.js 配置绑定）。
 */
import { bindAdvancedConfigControls } from "../js/advanced.js";
import { $, V2 } from "./store.js";

var _open = false;
var _bound = null;
var _anchor = null;
var _scrim = null;
var _focusTrapHandler = null;
var _focusRestoreEl = null;
var POPOVER_FOCUSABLE = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(",");

function focusableEls(container) {
  if (!container) return [];
  return Array.prototype.filter.call(container.querySelectorAll(POPOVER_FOCUSABLE), function (el) {
    if (el.getAttribute("aria-hidden") === "true") return false;
    if (el.closest("[hidden]")) return false;
    return true;
  });
}

function trapFocus(popover) {
  releaseFocusTrap(popover);
  _focusTrapHandler = function (e) {
    if (e.key !== "Tab") return;
    var els = focusableEls(popover);
    if (!els.length) return;
    var first = els[0];
    var last = els[els.length - 1];
    if (e.shiftKey) {
      if (document.activeElement === first) {
        e.preventDefault();
        last.focus();
      }
      return;
    }
    if (document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  };
  popover.addEventListener("keydown", _focusTrapHandler);
}

function releaseFocusTrap(popover) {
  if (_focusTrapHandler && popover) popover.removeEventListener("keydown", _focusTrapHandler);
  _focusTrapHandler = null;
}

function ensureScrim() {
  if (_scrim) return _scrim;
  _scrim = document.createElement("div");
  _scrim.id = "v2-advanced-scrim";
  _scrim.className = "v2-advanced-scrim";
  _scrim.hidden = true;
  _scrim.addEventListener("click", closePopover);
  document.body.appendChild(_scrim);
  return _scrim;
}

function ensurePopoverPortaled(popover) {
  if (!popover || popover.dataset.portaled === "1") return;
  document.body.appendChild(popover);
  popover.dataset.portaled = "1";
}

function positionPopover(popover, toggle) {
  var rect = toggle.getBoundingClientRect();
  var gap = 8;
  var margin = 12;
  var width = Math.min(320, window.innerWidth - margin * 2);
  popover.style.width = width + "px";
  popover.style.left = "auto";
  popover.style.right = Math.max(margin, window.innerWidth - rect.right) + "px";
  var maxH = Math.min(window.innerHeight * 0.7, 420);
  popover.style.maxHeight = maxH + "px";
  popover.hidden = false;
  var popH = popover.offsetHeight;
  var spaceAbove = rect.top - margin;
  var spaceBelow = window.innerHeight - rect.bottom - margin;
  if (spaceAbove >= popH + gap || spaceAbove >= spaceBelow) {
    popover.style.top = "auto";
    popover.style.bottom = (window.innerHeight - rect.top + gap) + "px";
  } else {
    popover.style.bottom = "auto";
    popover.style.top = (rect.bottom + gap) + "px";
  }
}

function closePopover() {
  var popover = $("v2-advanced-popover");
  var toggle = $("v2-advanced-toggle");
  if (!popover || !toggle) return;
  _open = false;
  popover.hidden = true;
  releaseFocusTrap(popover);
  toggle.setAttribute("aria-expanded", "false");
  if (_scrim) _scrim.hidden = true;
  var restore = _focusRestoreEl;
  _focusRestoreEl = null;
  if (restore && typeof restore.focus === "function") restore.focus();
}

function openPopover(fetchConfig) {
  var popover = $("v2-advanced-popover");
  var toggle = $("v2-advanced-toggle");
  if (!popover || !toggle || V2.state === "Importing") return;
  ensurePopoverPortaled(popover);
  if (fetchConfig) fetchConfig();
  _focusRestoreEl = document.activeElement;
  _open = true;
  positionPopover(popover, toggle);
  var scrim = ensureScrim();
  scrim.hidden = false;
  toggle.setAttribute("aria-expanded", "true");
  trapFocus(popover);
  var first = focusableEls(popover)[0];
  if (first && typeof first.focus === "function") first.focus();
  else {
    popover.tabIndex = -1;
    popover.focus();
  }
}

export function syncAdvancedOptionsLock() {
  var toggle = $("v2-advanced-toggle");
  if (!toggle) return;
  var locked = V2.state === "Importing";
  toggle.disabled = locked;
  if (locked) closePopover();
}

export function initAdvancedOptionsPanel() {
  var toggle = $("v2-advanced-toggle");
  var popover = $("v2-advanced-popover");
  if (!toggle || !popover) return;

  _bound = bindAdvancedConfigControls();
  if (!_bound) return;

  syncAdvancedOptionsLock();
  _anchor = toggle;

  window.addEventListener("resize", function () {
    if (!_open) return;
    var pop = $("v2-advanced-popover");
    if (pop && _anchor) positionPopover(pop, _anchor);
  });

  toggle.addEventListener("click", function (e) {
    e.stopPropagation();
    if (toggle.disabled) return;
    if (_open) {
      closePopover();
      return;
    }
    openPopover(_bound.fetchConfig);
  });

  document.addEventListener("click", function (e) {
    if (!_open) return;
    var t = e.target;
    if (popover.contains(t) || toggle.contains(t)) return;
    closePopover();
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && _open) closePopover();
  });
}
