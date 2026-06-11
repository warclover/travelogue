/**
 * Preview toolbar · layout pending / 暂存修改状态（M-P2b · §6.3）。
 */
"use strict";
import { getPreviewStore, setPreviewStore, syncPendingStore } from "./store.js";
var _layoutStale = false;
var _pendingItems = [];
var _pendingFeatured = 0;
var _pendingMedia = 0;
var _detailOpen = false;
var _undoHandler = null;
var _flashTimer = null;
function syncLongshotPreviewRowVisibility(root) {
  if (!root) return;
  var row = root.querySelector(".preview-toolbar__longshot-preview-row");
  if (row) row.hidden = true;
}
function recalcCounts() {
  _pendingFeatured = 0;
  _pendingMedia = 0;
  _pendingItems.forEach(function (item) {
    if (item.kind === "featured") _pendingFeatured += 1;
    if (item.kind === "media") _pendingMedia += 1;
  });
}
function pendingSummaryText() {
  var count = _pendingFeatured + _pendingMedia;
  var parts = [];
  if (_pendingFeatured > 0) parts.push("精选 ×" + _pendingFeatured);
  if (_pendingMedia > 0) parts.push("媒资 ×" + _pendingMedia);
  var detail = parts.length ? "（" + parts.join(" · ") + "）" : "";
  return "已暂存 " + count + " 处修改" + detail + " · 应用排版后生效";
}
function itemLabel(item) {
  if (item.label) return item.label;
  if (item.kind === "featured") return "标为精选 · " + (item.assetId || "");
  if (item.kind === "media") {
    var to = item.mediaClass === "collage" ? "拼图" : "普通照片";
    return "媒资改判 · " + (item.assetId || "") + " → " + to;
  }
  return "暂存修改";
}
function flashPendingHighlight(root) {
  if (!root) root = document.querySelector(".preview-toolbar");
  if (!root) return;
  var banner = root.querySelector(".preview-toolbar__pending-banner");
  if (!banner) return;
  banner.classList.remove("preview-toolbar__pending-banner--flash");
  void banner.offsetWidth;
  banner.classList.add("preview-toolbar__pending-banner--flash");
  if (_flashTimer) clearTimeout(_flashTimer);
  _flashTimer = setTimeout(function () {
    _flashTimer = null;
    if (banner) banner.classList.remove("preview-toolbar__pending-banner--flash");
  }, 900);
}
function renderPendingDetail(root) {
  var panel = root.querySelector(".preview-toolbar__pending-detail");
  if (!panel) return;
  panel.innerHTML = "";
  if (!_detailOpen || !_pendingItems.length) {
    panel.hidden = true;
    return;
  }
  panel.hidden = false;
  var list = document.createElement("ul");
  list.className = "preview-toolbar__pending-detail-list";
  _pendingItems.forEach(function (item) {
    var li = document.createElement("li");
    li.className = "preview-toolbar__pending-detail-item";
    var label = document.createElement("span");
    label.className = "preview-toolbar__pending-detail-label";
    label.textContent = itemLabel(item);
    var undoBtn = document.createElement("button");
    undoBtn.type = "button";
    undoBtn.className = "preview-toolbar__pending-undo";
    undoBtn.textContent = "撤销";
    undoBtn.addEventListener("click", function () {
      if (!_undoHandler) return;
      undoBtn.disabled = true;
      Promise.resolve(_undoHandler(item))
        .then(function (ok) {
          if (ok !== false) removePendingItem(item.id);
        })
        .finally(function () {
          undoBtn.disabled = false;
        });
    });
    li.appendChild(label);
    li.appendChild(undoBtn);
    list.appendChild(li);
  });
  panel.appendChild(list);
}
export function getPendingCount() {
  return _pendingFeatured + _pendingMedia;
}
export function hasLayoutPending() {
  return _layoutStale || _pendingItems.length > 0;
}
export function getPendingItems() {
  return _pendingItems.slice();
}
export function setPendingUndoHandler(fn) {
  _undoHandler = fn;
}
export function registerPendingChange(change) {
  if (!change || !change.kind) return null;
  var id =
    "p" +
    Date.now().toString(36) +
    Math.random().toString(36).slice(2, 6);
  _pendingItems.push(
    Object.assign({ id: id }, change)
  );
  recalcCounts();
  refreshPendingUi();
  return id;
}
export function removePendingItem(id) {
  _pendingItems = _pendingItems.filter(function (item) {
    return item.id !== id;
  });
  recalcCounts();
  if (!_pendingItems.length) _layoutStale = false;
  refreshPendingUi();
}
export function refreshPendingUi(root) {
  if (!root) root = document.querySelector(".preview-toolbar");
  if (!root) return;
  var count = _pendingFeatured + _pendingMedia;
  var on = _layoutStale || count > 0;
  syncPendingStore(_pendingItems, count);
  root.querySelectorAll(".preview-toolbar__apply-layout").forEach(function (btn) {
    btn.hidden = !on;
  });
  root.querySelectorAll(".preview-toolbar__apply-layout-main").forEach(function (btn) {
    btn.hidden = false;
    btn.classList.toggle("preview-toolbar__ctl--primary", on);
    btn.classList.toggle("preview-toolbar__apply-layout-main--idle", !on);
    btn.disabled = !on;
  });
  root.querySelectorAll(".preview-toolbar__pending-row").forEach(function (row) {
    row.hidden = !on || getPreviewStore().mode !== "edit";
  });
  var pendingText = root.querySelector(".preview-toolbar__pending-text");
  if (pendingText && on && count > 0) {
    pendingText.textContent = pendingSummaryText();
  } else if (pendingText && on && _layoutStale) {
    pendingText.textContent = "已暂存修改 · 应用排版后生效";
  }
  var detailBtn = root.querySelector(".preview-toolbar__pending-detail-toggle");
  if (detailBtn) {
    detailBtn.hidden = count === 0;
    detailBtn.setAttribute("aria-expanded", _detailOpen && count > 0 ? "true" : "false");
    detailBtn.textContent = _detailOpen ? "收起明细" : "查看明细";
  }
  renderPendingDetail(root);
  syncLongshotPreviewRowVisibility(root);
}
export function setLayoutPending(on, opts) {
  opts = opts || {};
  if (opts.reset) {
    _layoutStale = false;
    _pendingItems = [];
    _pendingFeatured = 0;
    _pendingMedia = 0;
    _detailOpen = false;
    refreshPendingUi();
    return;
  }
  if (opts.kind && opts.item) {
    registerPendingChange(opts.item);
    flashPendingHighlight();
    return;
  }
  if (opts.kind === "featured") {
    registerPendingChange({
      kind: "featured",
      assetId: opts.assetId || "",
      label: opts.label,
      wasFeatured: !!opts.wasFeatured,
    });
    flashPendingHighlight();
    return;
  }
  if (opts.kind === "media") {
    registerPendingChange({
      kind: "media",
      assetId: opts.assetId || "",
      mediaClass: opts.mediaClass,
      prevMediaClass: opts.prevMediaClass,
      label: opts.label,
    });
    flashPendingHighlight();
    return;
  }
  _layoutStale = !!on;
  refreshPendingUi();
}
export function initPendingBar(root) {
  if (!root) return;
  var detailBtn = root.querySelector(".preview-toolbar__pending-detail-toggle");
  if (detailBtn && detailBtn.dataset.bound !== "1") {
    detailBtn.dataset.bound = "1";
    detailBtn.addEventListener("click", function () {
      if (!getPendingCount()) return;
      _detailOpen = !_detailOpen;
      refreshPendingUi(root);
    });
  }
}
