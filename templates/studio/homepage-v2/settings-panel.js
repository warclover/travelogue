/**
 * 首页 v2 · 设置 Popover（手风琴五区 · D-DLLM-03 AI zone→Modal）。
 */
import { trackStudioEvent } from "../js/analytics.js";
import { bindAdvancedConfigControls } from "../js/advanced.js";
import { openHelpDrawer } from "../js/help-drawer.js";
import { isCapabilityCardSeen } from "../js/help-onboarding.js";
import { harnessEnabled } from "./harness.js";
import { openDevPanelFromSettings } from "./dev-panel.js";
import { requestExitStudio } from "../js/studio-exit.js";
import { bindStorageSettings } from "./storage-settings.js";
import { $, V2, V2_THEME_LABELS } from "./store.js";
import { studioAuthHeaders } from "../js/http.js";
import { isAiSurfaceEnabled } from "../js/ai-surface.js";
import { DARK_COPY } from "../js/ai-surface-dark-copy.js";

var SETTINGS_HINT_KEY = "travelogue.studio.v2.settingsMovedHint";

var _open = false;
var _bound = null;
var _storageBound = null;
var _scrim = null;
var _focusTrapHandler = null;
var _focusRestoreEl = null;
var _repositionHandler = null;
var _popoverResizeObserver = null;
var _llmStatusHandler = null;
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
    if (el.classList && el.classList.contains("v2-settings-native-select")) return false;
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

function syncSegFromSelect(select) {
  if (!select || !select.id) return;
  var group = document.querySelector('[data-seg-for="' + select.id + '"]');
  if (!group) return;
  var val = select.value;
  Array.prototype.forEach.call(group.querySelectorAll(".v2-settings-seg__btn"), function (btn) {
    btn.classList.toggle("is-on", btn.getAttribute("data-value") === val);
  });
}

function syncAllSegs(root) {
  var scope = root || document;
  Array.prototype.forEach.call(scope.querySelectorAll("[data-seg-for]"), function (group) {
    var select = document.getElementById(group.getAttribute("data-seg-for"));
    syncSegFromSelect(select);
  });
}

function shortClustering(v) {
  if (v === "true") return "开";
  if (v === "false") return "关";
  return "自动";
}

function shortVision(v) {
  if (v === "true") return "开";
  if (v === "auto") return "自动";
  return "关";
}

export function syncImportMeta() {
  var meta = $("v2-settings-meta-import");
  var clu = $("studio-cfg-clustering");
  var vis = $("studio-cfg-vision");
  if (!meta || !clu || !vis) return;
  meta.textContent =
    "行程·" + shortClustering(clu.value) + " · 场景·" + shortVision(vis.value);
}

export function syncAppearanceMeta() {
  var meta = $("v2-settings-meta-appearance");
  var select = $("v2-theme-select");
  if (!meta || !select) return;
  var key = select.value;
  meta.textContent = (V2_THEME_LABELS && V2_THEME_LABELS[key]) || select.options[select.selectedIndex].text || key;
}

function bindSegControls(root) {
  if (!root) return;
  Array.prototype.forEach.call(root.querySelectorAll("[data-seg-for]"), function (group) {
    if (group.dataset.segBound === "1") return;
    var id = group.getAttribute("data-seg-for");
    var select = document.getElementById(id);
    if (!select) return;
    group.dataset.segBound = "1";
    group.addEventListener("click", function (e) {
      var btn = e.target && e.target.closest ? e.target.closest(".v2-settings-seg__btn") : null;
      if (!btn || !group.contains(btn)) return;
      var val = btn.getAttribute("data-value");
      if (val == null) return;
      if (select.value !== val) {
        select.value = val;
        select.dispatchEvent(new Event("change", { bubbles: true }));
      }
      syncSegFromSelect(select);
      syncImportMeta();
    });
    select.addEventListener("change", function () {
      syncSegFromSelect(select);
      syncImportMeta();
    });
    syncSegFromSelect(select);
  });
}

function syncMoreZone() {
  var more = $("v2-settings-zone-more");
  var dev = $("v2-settings-dev-section");
  var exit = $("v2-settings-exit-section");
  var meta = $("v2-settings-meta-more");
  if (!more) return;
  var showDev = !!(dev && !dev.hidden);
  var showExit = !!(exit && !exit.hidden);
  more.hidden = !(showDev || showExit);
  if (meta) {
    var bits = [];
    if (showDev) bits.push("开发者");
    if (showExit) bits.push("退出");
    meta.textContent = bits.join(" · ");
  }
}

function syncDevSection() {
  var section = $("v2-settings-dev-section");
  if (!section) return;
  section.hidden = !harnessEnabled();
  syncMoreZone();
}

function applyAiStatus(st) {
  var meta = $("v2-settings-meta-ai");
  var badge = $("studio-llm-settings-badge");
  var entry = $("studio-llm-settings-entry");
  var readiness =
    (st && st.readiness) ||
    (st && (st.connectionOk === true || st.lastPingOk === true)
      ? "已就绪"
      : st && st.configured
        ? "已保存未验证"
        : "未配置");
  var metaText = readiness;
  if (readiness === "已就绪") metaText = "已连接通义百炼";
  if (meta) {
    meta.textContent = metaText;
    meta.classList.toggle("is-ok", readiness === "已就绪");
    meta.classList.toggle(
      "is-warn",
      readiness === "连接失败" || readiness === "未配置" || readiness === "已保存未验证"
    );
  }
  if (badge) {
    badge.textContent = readiness;
    badge.classList.toggle("is-ready", readiness === "已就绪");
    badge.classList.toggle("is-fail", readiness === "连接失败");
    badge.classList.toggle(
      "is-warn",
      readiness === "已保存未验证" || readiness === "未配置"
    );
  }
  if (entry) {
    entry.textContent =
      readiness === "已就绪" ? DARK_COPY.settingsManage : DARK_COPY.settingsConfigure;
  }
}

function refreshAiStatus() {
  // NAS · S3：默认面不请求 /llm/status
  if (!isAiSurfaceEnabled()) {
    return Promise.resolve();
  }
  return fetch("/__travelogue/llm/status", { headers: studioAuthHeaders({}) })
    .then(function (r) {
      return r.ok ? r.json() : null;
    })
    .then(function (st) {
      applyAiStatus(st || {});
    })
    .catch(function () {
      applyAiStatus({});
    });
}

/** NAS · FE-NAS-03：默认隐藏 AI zone；dark ON 再显示并恢复文案 */
export function syncAiSettingsZone() {
  var zone = $("v2-settings-zone-ai");
  if (!zone) return;
  var on = isAiSurfaceEnabled();
  zone.hidden = !on;
  zone.setAttribute("aria-hidden", on ? "false" : "true");
  if (!on) {
    try {
      zone.open = false;
    } catch (_e) {
      /* ignore */
    }
  }
}

function expandZone(zone) {
  if (!zone) return;
  try {
    zone.open = true;
  } catch (_e) {
    /* ignore */
  }
  if (typeof zone.scrollIntoView === "function") {
    zone.scrollIntoView({ block: "nearest" });
  }
}

function focusZoneControl(focusKey) {
  if (focusKey === "storage") {
    var storageSec = $("v2-settings-storage-section");
    expandZone(storageSec);
    var copyOn =
      storageSec &&
      storageSec.querySelector('[data-seg-for="studio-cfg-copy-source"] .v2-settings-seg__btn.is-on');
    if (copyOn && typeof copyOn.focus === "function") {
      try {
        copyOn.focus();
      } catch (_e) {
        /* ignore */
      }
      return true;
    }
    return !!storageSec;
  }
  if (focusKey === "ai") {
    // NAS · 默认面忽略 focus=ai
    if (!isAiSurfaceEnabled()) return false;
    var aiZone = $("v2-settings-zone-ai");
    expandZone(aiZone);
    var entry = $("studio-llm-settings-entry");
    if (entry && typeof entry.focus === "function") {
      try {
        entry.focus();
      } catch (_e2) {
        /* ignore */
      }
      return true;
    }
    return !!aiZone;
  }
  if (focusKey === "import") {
    expandZone($("v2-settings-zone-import"));
    return true;
  }
  if (focusKey === "appearance") {
    expandZone($("v2-settings-zone-appearance"));
    return true;
  }
  if (focusKey === "more") {
    expandZone($("v2-settings-zone-more"));
    return true;
  }
  return false;
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

/**
 * @param {{ focus?: "storage"|"ai"|"import"|"appearance"|"more", source?: string }} [opts]
 */
export function openSettings(opts) {
  opts = opts || {};
  var popover = $("v2-settings-popover");
  var toggle = $("v2-settings-toggle");
  if (!popover || !toggle || toggle.disabled || V2.state === "Importing") return;
  ensurePopoverPortaled(popover);
  syncDevSection();
  syncAppearanceMeta();
  if (_bound && _bound.fetchConfig) {
    Promise.resolve(_bound.fetchConfig()).then(function () {
      syncAllSegs(popover);
      syncImportMeta();
    });
  }
  if (_storageBound && _storageBound.fetchConfig) _storageBound.fetchConfig();
  refreshAiStatus();
  trackStudioEvent("storage_settings_open", { source: opts.source || "toolbar" });
  _focusRestoreEl = document.activeElement;
  _open = true;
  positionPopover(popover, toggle);
  schedulePositionPopover();
  bindRepositionWhileOpen();
  var scrim = ensureScrim();
  scrim.hidden = false;
  toggle.setAttribute("aria-expanded", "true");
  trapFocus(popover);
  trackStudioEvent("settings_open", { source: opts.source || "toolbar" });
  // 默认全部折叠，避免一打开就见导入实验区 / 开发者
  try {
    popover.querySelectorAll("details.v2-settings-zone, details.v2-settings-sub").forEach(function (d) {
      d.open = false;
    });
  } catch (_e) {}
  // ?dev=1 / harness：展开「更多」，避免 Dev 入口藏在折叠区内不可见
  if (harnessEnabled()) {
    expandZone($("v2-settings-zone-more"));
  }
  if (opts.focus && focusZoneControl(opts.focus)) return;
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
  _storageBound = bindStorageSettings();
  bindSegControls(popover);
  syncAllSegs(popover);
  syncImportMeta();
  syncAppearanceMeta();
  syncSettingsLock();
  syncDevSection();
  ensurePopoverPortaled(popover);
  maybeShowSettingsMovedHint();

  // CSC F-CSC-3 · Happy Path 短文可从设置常用区发现（不抢主 CTA）
  var cscHelp = popover.querySelector('[data-help-item="H0"]');
  if (cscHelp && !cscHelp.dataset.cscHelpBound) {
    cscHelp.dataset.cscHelpBound = "1";
    cscHelp.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      openHelpDrawer({ source: "settings_csc", itemId: "H0" });
    });
  }

  try {
    window.addEventListener("travelogue:capability-card-done", function () {
      maybeShowSettingsMovedHint();
    });
    // CQA AC-18 · bind once (initSettingsPanel may re-enter in harness)
    if (!_llmStatusHandler) {
      _llmStatusHandler = function (ev) {
        applyAiStatus((ev && ev.detail) || {});
      };
      window.addEventListener("travelogue:llm-status", _llmStatusHandler);
    }
  } catch (_e) {
    /* ignore */
  }

  var themeSelect = $("v2-theme-select");
  if (themeSelect) {
    themeSelect.addEventListener("change", syncAppearanceMeta);
  }

  toggle.addEventListener("click", function (e) {
    e.stopPropagation();
    if (toggle.disabled) return;
    if (_open) {
      closeSettings();
      return;
    }
    openSettings({ source: "toolbar" });
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
          syncMoreZone();
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
    // AI Modal 叠在设置上时，点击 Modal 不应关掉设置（关闭 Modal 后继续改偏好）
    var llmRoot = document.getElementById("studio-llm-settings-root");
    if (llmRoot && !llmRoot.hidden) return;
    var t = e.target;
    if (popover.contains(t) || toggle.contains(t)) return;
    closeSettings();
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape" || !_open) return;
    var llmRoot = document.getElementById("studio-llm-settings-root");
    if (llmRoot && !llmRoot.hidden) return; // Modal 自管 Esc
    closeSettings();
  });
}
