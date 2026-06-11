/**
 * Preview toolbar · export popover + copy chips (M-P2b).
 */
"use strict";

import { trackStudioEvent } from "../js/analytics.js";
import { tripIdFromPath } from "./toolbar-ui.js";
import {
  applyExportCaptions,
  applyExportCopyPreset,
  applyExportDraft,
  applyExportNarrative,
  getPreviewStore,
} from "./store.js";
import {
  longshotApi,
  readLongshotExportPrefs,
  formatLongshotExportMetaLabel,
  refreshLongshotExportMeta,
  syncLongshotPreviewChips,
  syncLongshotPreviewRowVisibility,
} from "./export-state.js";

export function applyToolbarCopyPreset(root, preset) {
  applyExportCopyPreset(preset);
  syncLongshotPreviewChips(root);
}

export function toggleToolbarNarrative(root) {
  if (getPreviewStore().exportPrefs.copy === "photos") return;
  var prefs = getPreviewStore().exportPrefs;
  applyExportNarrative(!prefs.narrative);
  syncLongshotPreviewChips(root);
}

export function toggleToolbarCaptions(root) {
  if (getPreviewStore().exportPrefs.copy === "photos") return;
  var prefs = getPreviewStore().exportPrefs;
  var ls = longshotApi();
  var next =
    ls && typeof ls.areCaptionsVisible === "function"
      ? !ls.areCaptionsVisible()
      : !prefs.captions;
  applyExportCaptions(next);
  syncLongshotPreviewChips(root);
}

export function initLongshotPreviewRow(root) {
  var row = root.querySelector(".preview-toolbar__longshot-preview-row");
  if (!row || row.dataset.bound === "1") return;
  row.dataset.bound = "1";

  row.querySelectorAll("[data-copy-preset]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      applyToolbarCopyPreset(root, btn.getAttribute("data-copy-preset"));
    });
  });

  var captionChip = row.querySelector('[data-preview-chip="caption"]');
  if (captionChip) {
    captionChip.addEventListener("click", function () {
      toggleToolbarCaptions(root);
    });
  }

  var narrativeChip = row.querySelector('[data-preview-chip="narrative"]');
  if (narrativeChip) {
    narrativeChip.addEventListener("click", function () {
      toggleToolbarNarrative(root);
    });
  }

  syncLongshotPreviewChips(root);
  syncLongshotPreviewRowVisibility(root);
}

var _studioExportPopoverClose = null;

function closeStudioExportPopover() {
  document.querySelectorAll(".preview-toolbar__export-popover").forEach(function (pop) {
    pop.hidden = true;
  });
  if (_studioExportPopoverClose) {
    document.removeEventListener("click", _studioExportPopoverClose, true);
    _studioExportPopoverClose = null;
  }
}

function syncStudioExportPopoverUI(pop) {
  var prefs = readLongshotExportPrefs();
  var html = document.documentElement;
  var photosOnly = html.getAttribute("data-photos-only") === "on";
  var narrativeHidden = html.getAttribute("data-copy-display") === "photos";
  var captionsOn = html.getAttribute("data-caption-display") !== "off";

  pop.querySelectorAll("[data-studio-copy-preset]").forEach(function (btn) {
    var preset = btn.getAttribute("data-studio-copy-preset");
    var on = photosOnly ? preset === "photos" : preset === "full";
    btn.classList.toggle("is-selected", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  });

  var captionBtn = pop.querySelector('[data-studio-preview-chip="caption"]');
  if (captionBtn) {
    captionBtn.setAttribute("aria-pressed", captionsOn ? "true" : "false");
    captionBtn.textContent = captionsOn ? "图注：开" : "图注：关";
    captionBtn.disabled = photosOnly;
  }

  var narrativeBtn = pop.querySelector('[data-studio-preview-chip="narrative"]');
  if (narrativeBtn) {
    var showNarrative = !narrativeHidden;
    narrativeBtn.setAttribute("aria-pressed", showNarrative ? "true" : "false");
    narrativeBtn.textContent = showNarrative ? "导语：显" : "导语：隐";
    narrativeBtn.disabled = photosOnly;
  }

  pop.querySelectorAll("[data-studio-longshot-mode]").forEach(function (btn) {
    var on = btn.getAttribute("data-studio-longshot-mode") === prefs.mode;
    btn.classList.toggle("is-selected", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  });
  pop.querySelectorAll("[data-studio-longshot-scale]").forEach(function (btn) {
    var on = String(btn.getAttribute("data-studio-longshot-scale")) === String(prefs.scale);
    btn.classList.toggle("is-selected", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  });

  var summary = pop.querySelector(".preview-toolbar__export-popover-summary");
  if (summary) {
    summary.textContent = formatLongshotExportMetaLabel();
  }
}

function ensureStudioExportPopover(root) {
  var wrap = root.querySelector(".preview-toolbar__export-zone-wrap");
  if (!wrap) return null;
  var pop = wrap.querySelector(".preview-toolbar__export-popover");
  if (pop) return pop;

  pop = document.createElement("div");
  pop.className = "preview-toolbar__export-popover";
  pop.hidden = true;
  pop.setAttribute("role", "dialog");
  pop.setAttribute("aria-label", "导出设置");
  pop.innerHTML =
    '<p class="preview-toolbar__export-popover-title">导出设置</p>' +
    '<p class="preview-toolbar__export-popover-note">调整长图内容与清晰度；点「保存长图」开始导出。</p>' +
    '<div class="preview-toolbar__export-popover-field">' +
    '<span class="preview-toolbar__export-popover-label">内容</span>' +
    '<div class="preview-toolbar__export-popover-seg" role="group" aria-label="文案范围">' +
    '<button type="button" data-studio-copy-preset="full">完整文案</button>' +
    '<button type="button" data-studio-copy-preset="photos">纯照片</button>' +
    "</div></div>" +
    '<div class="preview-toolbar__export-popover-field preview-toolbar__export-popover-field--inline">' +
    '<button type="button" class="preview-toolbar__export-popover-chip" data-studio-preview-chip="caption">图注：开</button>' +
    '<button type="button" class="preview-toolbar__export-popover-chip" data-studio-preview-chip="narrative">导语：显</button>' +
    "</div>" +
    '<div class="preview-toolbar__export-popover-field">' +
    '<span class="preview-toolbar__export-popover-label">范围</span>' +
    '<div class="preview-toolbar__export-popover-seg" role="group">' +
    '<button type="button" data-studio-longshot-mode="chapter">按章</button>' +
    '<button type="button" data-studio-longshot-mode="full">完整一张</button>' +
    "</div></div>" +
    '<div class="preview-toolbar__export-popover-field">' +
    '<span class="preview-toolbar__export-popover-label">清晰度</span>' +
    '<div class="preview-toolbar__export-popover-seg" role="group">' +
    '<button type="button" data-studio-longshot-scale="2">2×</button>' +
    '<button type="button" data-studio-longshot-scale="3">3×</button>' +
    "</div></div>" +
    '<p class="preview-toolbar__export-popover-summary" aria-live="polite"></p>' +
    '<div class="preview-toolbar__export-popover-actions">' +
    '<button type="button" class="preview-toolbar__export-popover-ok" data-action="ok">确定</button>' +
    '<button type="button" class="preview-toolbar__export-popover-cancel" data-action="cancel">取消</button>' +
    "</div>";

  var draftMode = "chapter";
  var draftScale = 2;
  var draftCopyPreset = "full";
  var draftCaptionsOn = true;
  var draftNarrativeOn = true;

  function refreshPopoverSummary() {
    var summary = pop.querySelector(".preview-toolbar__export-popover-summary");
    if (!summary) return;
    var modeLabel = draftMode === "full" ? "完整" : "按章";
    var copyLabel = draftCopyPreset === "photos" ? "纯照片" : "完整文案";
    var capLabel = draftCaptionsOn ? "" : " · 无图注";
    summary.textContent = "导出设置：" + modeLabel + " · " + draftScale + "× · " + copyLabel + capLabel;
  }

  function syncDraftChipsUI() {
    var photosOnly = draftCopyPreset === "photos";
    pop.querySelectorAll("[data-studio-copy-preset]").forEach(function (btn) {
      var on = btn.getAttribute("data-studio-copy-preset") === draftCopyPreset;
      btn.classList.toggle("is-selected", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
    var captionBtn = pop.querySelector('[data-studio-preview-chip="caption"]');
    if (captionBtn) {
      captionBtn.setAttribute("aria-pressed", draftCaptionsOn ? "true" : "false");
      captionBtn.textContent = draftCaptionsOn ? "图注：开" : "图注：关";
      captionBtn.disabled = photosOnly;
    }
    var narrativeBtn = pop.querySelector('[data-studio-preview-chip="narrative"]');
    if (narrativeBtn) {
      narrativeBtn.setAttribute("aria-pressed", draftNarrativeOn ? "true" : "false");
      narrativeBtn.textContent = draftNarrativeOn ? "导语：显" : "导语：隐";
      narrativeBtn.disabled = photosOnly;
    }
    refreshPopoverSummary();
  }

  pop.querySelectorAll("[data-studio-copy-preset]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      draftCopyPreset = btn.getAttribute("data-studio-copy-preset") || "full";
      if (draftCopyPreset === "photos") {
        draftCaptionsOn = false;
        draftNarrativeOn = false;
      }
      syncDraftChipsUI();
    });
  });

  var captionChip = pop.querySelector('[data-studio-preview-chip="caption"]');
  if (captionChip) {
    captionChip.addEventListener("click", function () {
      if (draftCopyPreset === "photos") return;
      draftCaptionsOn = !draftCaptionsOn;
      syncDraftChipsUI();
    });
  }

  var narrativeChip = pop.querySelector('[data-studio-preview-chip="narrative"]');
  if (narrativeChip) {
    narrativeChip.addEventListener("click", function () {
      if (draftCopyPreset === "photos") return;
      draftNarrativeOn = !draftNarrativeOn;
      syncDraftChipsUI();
    });
  }

  pop.querySelectorAll("[data-studio-longshot-mode]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      draftMode = btn.getAttribute("data-studio-longshot-mode") || "chapter";
      pop.querySelectorAll("[data-studio-longshot-mode]").forEach(function (b) {
        var on = b === btn;
        b.classList.toggle("is-selected", on);
        b.setAttribute("aria-pressed", on ? "true" : "false");
      });
      refreshPopoverSummary();
    });
  });
  pop.querySelectorAll("[data-studio-longshot-scale]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      draftScale = parseInt(btn.getAttribute("data-studio-longshot-scale"), 10) || 2;
      pop.querySelectorAll("[data-studio-longshot-scale]").forEach(function (b) {
        var on = b === btn;
        b.classList.toggle("is-selected", on);
        b.setAttribute("aria-pressed", on ? "true" : "false");
      });
      refreshPopoverSummary();
    });
  });

  pop.addEventListener("click", function (e) {
    e.stopPropagation();
  });

  pop._applyDraft = function () {
    applyExportDraft({
      mode: draftMode,
      scale: draftScale,
      copy: draftCopyPreset,
      narrative: draftNarrativeOn,
      captions: draftCaptionsOn,
    });
    var toolbar = document.querySelector(".preview-toolbar");
    if (toolbar) {
      syncLongshotPreviewChips(toolbar);
      refreshLongshotExportMeta(toolbar);
    }
  };
  pop._readDraftFromPrefs = function () {
    var prefs = readLongshotExportPrefs();
    var html = document.documentElement;
    draftMode = prefs.mode;
    draftScale = prefs.scale;
    draftCopyPreset = prefs.copyDisplay === "photos" ? "photos" : "full";
    draftCaptionsOn = prefs.captions;
    draftNarrativeOn = html.getAttribute("data-copy-display") !== "photos";
    syncDraftChipsUI();
    syncStudioExportPopoverUI(pop);
  };

  wrap.appendChild(pop);
  return pop;
}

function openStudioLongshotExportPanel(root) {
  return new Promise(function (resolve, reject) {
    var pop = ensureStudioExportPopover(root);
    if (!pop) {
      reject(new Error("no popover"));
      return;
    }
    closeStudioExportPopover();
    pop._readDraftFromPrefs();
    pop.hidden = false;
    trackStudioEvent("export_settings_open", { tripId: tripIdFromPath() });

    function finish(ok) {
      closeStudioExportPopover();
      if (ok) resolve();
      else reject(new Error("cancelled"));
    }

    var okBtn = pop.querySelector('[data-action="ok"]');
    var cancelBtn = pop.querySelector('[data-action="cancel"]');

    function onOk() {
      pop._applyDraft();
      finish(true);
    }
    function onCancel() {
      finish(false);
    }

    okBtn.addEventListener("click", onOk, { once: true });
    cancelBtn.addEventListener("click", onCancel, { once: true });

    _studioExportPopoverClose = function (e) {
      if (pop.contains(e.target)) return;
      if (root.querySelector(".preview-toolbar__export-settings-trigger") === e.target) return;
      okBtn.removeEventListener("click", onOk);
      cancelBtn.removeEventListener("click", onCancel);
      finish(false);
    };
    window.setTimeout(function () {
      document.addEventListener("click", _studioExportPopoverClose, true);
    }, 0);
  });
}

export function bindLongshotExportMeta(root) {
  var trigger = root.querySelector(".preview-toolbar__export-settings-trigger");
  if (!trigger || trigger.dataset.bound === "1") return;
  trigger.dataset.bound = "1";
  trigger.addEventListener("click", function (e) {
    e.preventDefault();
    e.stopPropagation();
    if (trigger.disabled) return;
    if (trigger.classList.contains("preview-toolbar__export-settings-trigger--result")) {
      import("./export-drawer.js").then(function (drawer) {
        drawer.openLongshotResultDrawer(root);
      });
      return;
    }
    openLongshotExportOptions(root);
  });
}

export function openLongshotExportOptions(root) {
  var ls = longshotApi();
  if (ls && typeof ls.openExportPanel === "function") {
    ls
      .openExportPanel()
      .then(function () {
        refreshLongshotExportMeta(root);
        syncLongshotPreviewChips(root);
      })
      .catch(function () {});
    return;
  }
  openStudioLongshotExportPanel(root)
    .then(function () {
      refreshLongshotExportMeta(root);
      syncLongshotPreviewChips(root);
    })
    .catch(function () {});
}
