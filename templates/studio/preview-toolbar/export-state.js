/**
 * Preview toolbar · longshot export state (M-P2b).
 */
"use strict";

import { buildLongshotRequest, resolveCopyDisplayFromDom } from "../js/longshot-client.js";
import { readLongshotMode, readLongshotScale } from "./store.js";
import { toolbarBody } from "./shell.js";

export { hideLongshotDrawer, openLongshotResultDrawer, showLongshotDrawer } from "./export-drawer.js";

export function longshotApi() {
  return window.TravelogueLongshot || null;
}

export function readLongshotExportPrefs() {
  var ls = longshotApi();
  var scale =
    ls && typeof ls.getUserSelectedScale === "function"
      ? ls.getUserSelectedScale()
      : readLongshotScale();
  var mode =
    ls && typeof ls.getUserSelectedMode === "function"
      ? ls.getUserSelectedMode()
      : readLongshotMode();
  var captions =
    ls && typeof ls.areCaptionsVisible === "function"
      ? ls.areCaptionsVisible()
      : document.documentElement.getAttribute("data-caption-display") !== "off";
  return {
    scale: scale,
    mode: mode,
    captions: captions,
    copyDisplay: resolveCopyDisplayFromDom(document),
  };
}

export function formatLongshotExportMetaLabel() {
  var prefs = readLongshotExportPrefs();
  var modeLabel = prefs.mode === "full" ? "完整" : "按章";
  var copyLabel = prefs.copyDisplay === "photos" ? "纯照片" : "完整文案";
  var capLabel = prefs.captions ? "" : " · 无图注";
  return "导出设置：" + modeLabel + " · " + prefs.scale + "× · " + copyLabel + capLabel;
}

export function refreshLongshotExportMeta(root) {
  setLongshotExportMeta(root, formatLongshotExportMetaLabel());
}

export function normalizeSegmentMode(mode) {
  if (mode === "full" || mode === "chapter") return mode;
  return "auto";
}

export function buildLongshotRequestFromPage(tripId) {
  var prefs = readLongshotExportPrefs();
  return buildLongshotRequest(tripId, {
    scale: prefs.scale,
    format: "png",
    copyDisplay: prefs.copyDisplay,
    segmentMode: normalizeSegmentMode(prefs.mode),
  });
}

export function syncLongshotPreviewRowVisibility(root) {
  if (!root) return;
  var row = root.querySelector(".preview-toolbar__longshot-preview-row");
  if (row) row.hidden = true;
}

export function syncLongshotPreviewChips(root) {
  if (!root) return;
  var html = document.documentElement;
  var photosOnly = html.getAttribute("data-photos-only") === "on";
  var narrativeHidden = html.getAttribute("data-copy-display") === "photos";
  var captionsOn = html.getAttribute("data-caption-display") !== "off";

  root.querySelectorAll("[data-copy-preset]").forEach(function (btn) {
    var on = photosOnly
      ? btn.getAttribute("data-copy-preset") === "photos"
      : btn.getAttribute("data-copy-preset") === "full";
    btn.classList.toggle("is-selected", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  });

  var captionChip = root.querySelector('[data-preview-chip="caption"]');
  if (captionChip) {
    captionChip.setAttribute("aria-pressed", captionsOn ? "true" : "false");
    captionChip.textContent = captionsOn ? "图注：开" : "图注：关";
    captionChip.disabled = photosOnly;
  }

  var narrativeChip = root.querySelector('[data-preview-chip="narrative"]');
  if (narrativeChip) {
    var showNarrative = !narrativeHidden;
    narrativeChip.setAttribute("aria-pressed", showNarrative ? "true" : "false");
    narrativeChip.textContent = showNarrative ? "导语：显" : "导语：隐";
    narrativeChip.disabled = photosOnly;
  }

  refreshLongshotExportMeta(root);
}

export function longshotProgressPct(job) {
  if (!job || job.status !== "running") return null;
  var cur = Number(job.stageIndex);
  var total = Number(job.stageCount);
  if (!isFinite(cur) || !isFinite(total) || total < 1) return null;
  var hint = String(job.stageHint || "");
  var isChapter = /第\s*\d+\s*\/\s*\d+\s*段/.test(hint);
  if (total === 1 && !isChapter) return 10;
  if (cur <= 0 && total > 1) return 5;
  return Math.min(100, Math.max(0, Math.round((cur / total) * 100)));
}

function exportZoneEl(root) {
  return root.querySelector(".preview-toolbar__export-zone");
}

export function longshotBtnEl(root) {
  return (
    root.querySelector(".preview-toolbar__longshot--main") ||
    root.querySelector(".preview-toolbar__longshot")
  );
}

function longshotCaretEl(root) {
  return root.querySelector(".preview-toolbar__export-settings-trigger");
}

function setLongshotControlsDisabled(root, disabled) {
  var main = longshotBtnEl(root);
  var caret = longshotCaretEl(root);
  if (main) main.disabled = !!disabled;
  if (caret) caret.disabled = !!disabled;
}

function setLongshotExportMeta(root, text, opts) {
  opts = opts || {};
  var trigger = root.querySelector(".preview-toolbar__export-settings-trigger");
  var meta = root.querySelector(".preview-toolbar__export-meta");
  if (!meta) return;
  var actionable = !!opts.actionable;
  if (actionable) {
    meta.textContent = text || "点击查看详情";
    if (trigger) {
      trigger.classList.add("preview-toolbar__export-settings-trigger--result");
      trigger.setAttribute("aria-label", "查看保存结果");
      trigger.title = opts.title || "展开保存结果";
    }
    return;
  }
  if (trigger) {
    trigger.classList.remove("preview-toolbar__export-settings-trigger--result");
    trigger.setAttribute("aria-label", "导出设置");
    trigger.removeAttribute("title");
  }
  if (text && String(text).indexOf("导出设置：") === 0) {
    meta.textContent = text;
  } else if (text) {
    meta.textContent = "导出设置：" + text;
  } else {
    meta.textContent = formatLongshotExportMetaLabel();
  }
}

function setLongshotExportProgress(root, visible, pct) {
  var prog = root.querySelector(".preview-toolbar__export-progress");
  var fill = root.querySelector(".preview-toolbar__export-progress-fill");
  if (prog) prog.hidden = !visible;
  if (fill && typeof pct === "number") fill.style.width = pct + "%";
}

function setLongshotSplitState(root, state) {
  var zone = exportZoneEl(root);
  if (!zone) return;
  ["idle", "running", "done"].forEach(function (s) {
    zone.classList.remove("preview-toolbar__export-zone--split-" + s);
  });
  if (state === "running") {
    zone.classList.add("preview-toolbar__export-zone--split-running");
  } else if (state === "done") {
    zone.classList.add("preview-toolbar__export-zone--split-done");
  } else {
    zone.classList.add("preview-toolbar__export-zone--split-idle");
  }
}

export function setLongshotExportState(root, state, opts) {
  opts = opts || {};
  var zone = exportZoneEl(root);
  var btn = longshotBtnEl(root);
  if (!btn) return;
  ["idle", "running", "done", "error"].forEach(function (s) {
    btn.classList.remove("preview-toolbar__longshot--" + s);
  });
  btn.classList.remove("preview-toolbar__longshot--primary");
  if (zone) {
    zone.classList.remove("preview-toolbar__export-zone--stale");
    zone.classList.remove("preview-toolbar__export-zone--running");
  }
  var badge = root.querySelector(".preview-toolbar__export-stale");

  if (state === "running") {
    btn.classList.add("preview-toolbar__longshot--running");
    setLongshotSplitState(root, "running");
    if (zone) zone.classList.add("preview-toolbar__export-zone--running");
    setLongshotControlsDisabled(root, true);
    btn.innerHTML =
      '<span class="preview-toolbar__longshot__spinner" aria-hidden="true"></span> 正在保存…';
    setLongshotExportMeta(root, opts.hint || "生成长图中", { actionable: false });
    var pct = typeof opts.pct === "number" ? opts.pct : 8;
    setLongshotExportProgress(root, true, pct);
    if (badge) badge.hidden = true;
    return;
  }
  if (state === "done") {
    btn.classList.add("preview-toolbar__longshot--done");
    setLongshotSplitState(root, "done");
    setLongshotControlsDisabled(root, false);
    btn.textContent = "✓ 已保存";
    setLongshotExportMeta(root, "点击查看详情", { actionable: true });
    setLongshotExportProgress(root, false);
    if (badge) badge.hidden = true;
    return;
  }
  if (state === "error") {
    btn.classList.add("preview-toolbar__longshot--idle");
    setLongshotSplitState(root, "idle");
    setLongshotControlsDisabled(root, false);
    btn.textContent = "保存长图";
    setLongshotExportMeta(root, opts.hint || "保存失败，请重试", { actionable: false });
    setLongshotExportProgress(root, false);
    if (badge) badge.hidden = true;
    return;
  }
  if (state === "stale") {
    btn.classList.add("preview-toolbar__longshot--idle");
    setLongshotSplitState(root, "idle");
    setLongshotControlsDisabled(root, false);
    btn.textContent = "保存长图";
    if (zone) zone.classList.add("preview-toolbar__export-zone--stale");
    if (badge) badge.hidden = false;
    setLongshotExportMeta(root, "内容已更新", { actionable: false });
    setLongshotExportProgress(root, false);
    return;
  }
  btn.classList.add("preview-toolbar__longshot--idle");
  btn.classList.add("preview-toolbar__longshot--primary");
  setLongshotSplitState(root, "idle");
  setLongshotControlsDisabled(root, false);
  btn.textContent = "保存长图";
  if (badge) badge.hidden = true;
  refreshLongshotExportMeta(root);
  setLongshotExportProgress(root, false);
}

export function showStaleHint(root) {
  setLongshotExportState(root, "stale");
}

export function hideStaleHint(root) {
  var btn = longshotBtnEl(root);
  if (btn && btn.classList.contains("preview-toolbar__longshot--done")) return;
  setLongshotExportState(root, "idle");
}

export function refreshPreviewCover(root) {
  var body = toolbarBody(root);
  var card = body.querySelector(".preview-toolbar__preview-card");
  if (card) card.remove();
}
