/**
 * SNR · AI 杂志文案生成后 diff 条（D-SNR-06 · COPY-SNR-D*）。
 */
"use strict";

import { trackStudioEvent } from "../js/analytics.js";

var STORAGE_PREFIX = "travelogue.snr.narrateDiff.v1.";
var AUTO_HIDE_MS = 10000;

var COPY = {
  title: "文案已更新",
  action: "查看第一处",
  close: "关闭",
};

/**
 * Persist diff before preview reload (called from narrate success).
 * @param {string} tripId
 * @param {{slotsLabel?: string, firstAnchor?: string, slotTypes?: string[], count?: number}} summary
 */
export function stashNarrateDiff(tripId, summary) {
  if (!tripId || !summary || !summary.slotsLabel) return;
  try {
    sessionStorage.setItem(
      STORAGE_PREFIX + String(tripId),
      JSON.stringify({
        slotsLabel: String(summary.slotsLabel || ""),
        firstAnchor: String(summary.firstAnchor || ""),
        slotTypes: summary.slotTypes || [],
        count: summary.count || 0,
        ts: Date.now(),
      })
    );
  } catch (_e) {}
}

function consumeStash(tripId) {
  var key = STORAGE_PREFIX + String(tripId || "");
  try {
    var raw = sessionStorage.getItem(key);
    if (!raw) return null;
    sessionStorage.removeItem(key);
    var data = JSON.parse(raw);
    if (!data || !data.slotsLabel) return null;
    if (data.ts && Date.now() - data.ts > 120000) return null;
    return data;
  } catch (_e) {
    try {
      sessionStorage.removeItem(key);
    } catch (_e2) {}
    return null;
  }
}

/**
 * @param {HTMLElement} root
 * @param {string} tripId
 */
export function mountNarrateDiffBar(root, tripId) {
  if (!root || !tripId) return null;
  var data = consumeStash(tripId);
  if (!data) return null;

  var existing = document.querySelector(".preview-toolbar__narrate-diff");
  if (existing && existing.parentNode) existing.parentNode.removeChild(existing);

  var el = document.createElement("div");
  el.className = "preview-toolbar__narrate-diff";
  el.setAttribute("role", "status");
  el.innerHTML =
    '<div class="preview-toolbar__narrate-diff-copy">' +
    "<strong>" +
    COPY.title +
    "</strong>" +
    "<p>已更新：" +
    escapeText(data.slotsLabel) +
    "</p>" +
    "</div>" +
    '<div class="preview-toolbar__narrate-diff-actions">' +
    '<button type="button" class="preview-toolbar__narrate-diff-jump">' +
    COPY.action +
    "</button>" +
    '<button type="button" class="preview-toolbar__narrate-diff-close">' +
    COPY.close +
    "</button>" +
    "</div>";

  document.body.appendChild(el);
  root._narrateDiffEl = el;

  var hideTimer = setTimeout(function () {
    dismiss("auto");
  }, AUTO_HIDE_MS);

  function dismiss(reason) {
    clearTimeout(hideTimer);
    if (el && el.parentNode) el.parentNode.removeChild(el);
    root._narrateDiffEl = null;
    trackStudioEvent("snr_narrate_diff_dismiss", {
      tripId: tripId || null,
      reason: reason || "unknown",
    });
  }

  var jump = el.querySelector(".preview-toolbar__narrate-diff-jump");
  var closeBtn = el.querySelector(".preview-toolbar__narrate-diff-close");
  if (jump) {
    jump.addEventListener("click", function () {
      var sel = data.firstAnchor || ".chapter-lead, [data-chapter-lead], .cover-hook";
      /** @type {Element | null} */
      var target = null;
      sel.split(",").some(function (s) {
        target = document.querySelector(s.trim());
        return !!target;
      });
      if (target && typeof target.scrollIntoView === "function") {
        target.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      trackStudioEvent("snr_diff_jump", { tripId: tripId || null });
    });
  }
  if (closeBtn) {
    closeBtn.addEventListener("click", function () {
      dismiss("close");
    });
  }

  trackStudioEvent("snr_diff_show", {
    tripId: tripId || null,
    slots_count: data.count || 0,
    slots: data.slotsLabel,
  });
  return el;
}

function escapeText(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
