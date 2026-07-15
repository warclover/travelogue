/**
 * 首页 v2 · 设置 Popover（外层「设置」· 内含导入偏好 · D-DLLM-03）。
 */
import { trackStudioEvent } from "../js/analytics.js";
import { bindAdvancedConfigControls } from "../js/advanced.js";
import { isCapabilityCardSeen } from "../js/help-onboarding.js";
import { harnessEnabled } from "./harness.js";
import { openDevPanelFromSettings } from "./dev-panel.js";
import { requestExitStudio } from "../js/studio-exit.js";
import { $, V2 } from "./store.js";

var SETTINGS_HINT_KEY = "travelogue.studio.v2.settingsMovedHint";

var _open = false;
var _bound = null;
var _scrim = null;
var _focusTrapHandler = null;
var _focusRestoreEl = null;
var _repositionHandler = null;
var _popoverResizeObserver = null;
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
  _scrim.id = "v2-settings-scrim";
  _scrim.className = "v2-settings-scrim";
  _scrim.hidden = true;
  _scrim.addEventListener("click", closeSettings);
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
  var width = Math.min(340, window.innerWidth - margin * 2);
  popover.style.width = width + "px";
  popover.style.left = "auto";
  popover.style.right = Math.max(margin, window.innerWidth - rect.right) + "px";

  var spaceAbove = Math.max(0, rect.top - margin);
  var spaceBelow = Math.max(0, window.innerHeight - rect.bottom - margin);
  var placeAbove = spaceAbove >= spaceBelow;
  var avail = placeAbove ? spaceAbove : spaceBelow;
  var maxH = Math.min(window.innerHeight * 0.78, 520, Math.max(avail - gap, 160));
  popover.style.maxHeight = maxH + "px";
  popover.hidden = false;

  if (placeAbove) {
    popover.style.top = "auto";
    popover.style.bottom = (window.innerHeight - rect.top + gap) + "px";
  } else {
    popover.style.bottom = "auto";
    popover.style.top = (rect.bottom + gap) + "px";
  }
}

function schedulePositionPopover() {
  requestAnimationFrame(function () {
    requestAnimationFrame(function () {
      if (!_open) return;
      var popover = $("v2-settings-popover");
      var toggle = $("v2-settings-toggle");
      if (popover && toggle) positionPopover(popover, toggle);
    });
  });
}

function releasePopoverResizeObserver() {
  if (_popoverResizeObserver) {
    _popoverResizeObserver.disconnect();
    _popoverResizeObserver = null;
  }
}

function bindRepositionWhileOpen() {
  releaseRepositionWhileOpen();
  _repositionHandler = function () {
    if (!_open) return;
    var popover = $("v2-settings-popover");
    var toggle = $("v2-settings-toggle");
    if (popover && toggle) positionPopover(popover, toggle);
  };
  window.addEventListener("resize", _repositionHandler);
  window.addEventListener("scroll", _repositionHandler, true);
  if (typeof ResizeObserver === "function") {
    var toggle = $("v2-settings-toggle");
    if (toggle) {
      _popoverResizeObserver = new ResizeObserver(_repositionHandler);
      _popoverResizeObserver.observe(toggle);
    }
  }
}

function releaseRepositionWhileOpen() {
  if (_repositionHandler) {
    window.removeEventListener("resize", _repositionHandler);
    window.removeEventListener("scroll", _repositionHandler, true);
    _repositionHandler = null;
  }
  releasePopoverResizeObserver();
}

function syncDevSection() {
  var section = $("v2-settings-dev-section");
  if (!section) return;
  section.hidden = !harnessEnabled();
}

export function closeSettings() {
  var popover = $("v2-settings-popover");
  var toggle = $("v2-settings-toggle");
  if (!popover || !toggle) return;
  _open = false;
  popover.hidden = true;
  releaseFocusTrap(popover);
  releaseRepositionWhileOpen();
  toggle.setAttribute("aria-expanded", "false");
  if (_scrim) _scrim.hidden = true;
  var restore = _focusRestoreEl;
  _focusRestoreEl = null;
  if (restore && typeof restore.focus === "function") restore.focus();
}

function openSettings() {
  var popover = $("v2-settings-popover");
  var toggle = $("v2-settings-toggle");
  if (!popover || !toggle || toggle.disabled || V2.state === "Importing") return;
  ensurePopoverPortaled(popover);
  syncDevSection();
  if (_bound && _bound.fetchConfig) _bound.fetchConfig();
  _focusRestoreEl = document.activeElement;
  _open = true;
  positionPopover(popover, toggle);
  schedulePositionPopover();
  bindRepositionWhileOpen();
  var scrim = ensureScrim();
  scrim.hidden = false;
  toggle.setAttribute("aria-expanded", "true");
  trapFocus(popover);
  trackStudioEvent("settings_open", { source: "toolbar" });
  var first = focusableEls(popover)[0];
  if (first && typeof first.focus === "function") first.focus();
  else {
    popover.tabIndex = -1;
    popover.focus();
  }
}

export function syncSettingsLock() {
  var toggle = $("v2-settings-toggle");
  if (!toggle) return;
  var locked = V2.state === "Importing";
  toggle.disabled = locked;
  if (locked) closeSettings();
}

export function maybeShowSettingsMovedHint() {
  try {
    if (localStorage.getItem(SETTINGS_HINT_KEY) === "1") return;
    // 能力卡未见过：等首启卡结束（travelogue:capability-card-done）后再提示设置入口
    // 不读 shouldDeferHomeHelpL1：该门禁只压制 Help L1，能力卡关闭后仍应允许设置 tip
    if (!isCapabilityCardSeen()) return;
    localStorage.setItem(SETTINGS_HINT_KEY, "1");
  } catch (e) {
    return;
  }
  if (typeof studioToast === "function") {
    studioToast("导入与外观选项在这里", { duration: 3200 });
  }
}

export function initSettingsPanel() {
  var toggle = $("v2-settings-toggle");
  var popover = $("v2-settings-popover");
  if (!toggle || !popover) return;

  _bound = bindAdvancedConfigControls();
  syncSettingsLock();
  syncDevSection();
  ensurePopoverPortaled(popover);
  maybeShowSettingsMovedHint();
  try {
    window.addEventListener("travelogue:capability-card-done", function () {
      maybeShowSettingsMovedHint();
    });
  } catch (_e) {
    /* ignore */
  }

  toggle.addEventListener("click", function (e) {
    e.stopPropagation();
    if (toggle.disabled) return;
    if (_open) {
      closeSettings();
      return;
    }
    openSettings();
  });

  popover.addEventListener("mousedown", function (e) {
    e.stopPropagation();
  });

  popover.addEventListener("click", function (e) {
    e.stopPropagation();
  });

  var closeBtn = $("v2-settings-close");
  if (closeBtn) {
    closeBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      if (_open) closeSettings();
    });
  }

  var devBtn = $("v2-settings-dev-toggle");
  if (devBtn) {
    devBtn.addEventListener("click", function () {
      closeSettings();
      openDevPanelFromSettings();
    });
  }

  var exitSection = $("v2-settings-exit-section");
  var exitBtn = $("v2-settings-exit-studio");
  if (exitSection && exitBtn) {
    fetch("/__travelogue/config")
      .then(function (r) {
        return r.ok ? r.json() : null;
      })
      .then(function (cfg) {
        var caps = (cfg && cfg.capabilities) || {};
        if (caps.desktopExit) {
          exitSection.hidden = false;
        }
      })
      .catch(function () {});
    exitBtn.addEventListener("click", function () {
      closeSettings();
      requestExitStudio({ surface: "homepage_settings" }).then(function (res) {
        if (res && res.ok === false && !res.cancelled && res.message) {
          window.alert(res.message);
        }
      });
    });
  }

  document.addEventListener("mousedown", function (e) {
    if (!_open) return;
    var t = e.target;
    if (popover.contains(t) || toggle.contains(t)) return;
    closeSettings();
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && _open) closeSettings();
  });
}
