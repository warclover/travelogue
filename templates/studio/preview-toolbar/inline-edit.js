/**
 * Preview toolbar · cover title inline edit (AC-ARC-14b).
 */
"use strict";

import { postJsonConflictRetry } from "../js/http.js";

var _tripApiBase = function (_tripId) {
  return "";
};
var _reloadPreviewAfterLayout = function () {};
var _showToolbarToast = function (_message, _opts) {};
var _isSharePreview = function () {
  return false;
};

export function registerInlineEditBridge(api) {
  if (typeof api.tripApiBase === "function") _tripApiBase = api.tripApiBase;
  if (typeof api.reloadPreviewAfterLayout === "function") {
    _reloadPreviewAfterLayout = api.reloadPreviewAfterLayout;
  }
  if (typeof api.showToolbarToast === "function") _showToolbarToast = api.showToolbarToast;
  if (typeof api.isSharePreview === "function") _isSharePreview = api.isSharePreview;
}

export function resolveSplitMatTitleLayoutClass(title) {
    var t = String(title || "").trim();
    var n = t.length;
    if (n <= 8) return "cover-opening__title--vertical";
    if (n <= 14) return "cover-opening__title--vertical-compact";
    return "cover-opening__title--horizontal";
  }

export function syncCoverTitleLayoutClass(el) {
    if (!el) return;
    var section = document.querySelector('.cover-opening[data-cover-opening="split-mat"]');
    if (!section) return;
    el.classList.remove(
      "cover-opening__title--vertical",
      "cover-opening__title--vertical-compact",
      "cover-opening__title--horizontal"
    );
    el.classList.add(resolveSplitMatTitleLayoutClass(el.dataset.title || el.textContent || ""));
  }

function _friendlyApiError(body, fallback) {
  var msg = body && body.message;
  if (typeof msg === "string" && msg.trim()) return msg.trim();
  var code = body && body.error;
  // 禁止把 E_SERVER 等工程码直接抛给用户
  if (typeof code === "string" && code && code.indexOf("E_") !== 0) return code;
  return fallback || "操作失败，请稍后重试";
}

export function saveMagazineTitle(tripId, next, el, onDone, opts) {
    opts = opts || {};
    var prev = (el.dataset.title || el.textContent || "").trim();
    if (next === prev) {
      if (onDone) onDone(false);
      return;
    }
    el.classList.add("preview-toolbar__title--saving");
    if (el.classList.contains("cover-opening__title")) {
      el.classList.add("cover-opening__title--saving");
    }
    postJsonConflictRetry(_tripApiBase(tripId) + "/save-copy", {
      patches: [{ path: "meta.title", value: next }],
    })
      .then(function (res) {
        el.classList.remove("preview-toolbar__title--saving");
        el.classList.remove("cover-opening__title--saving");
        if (res.status !== 200 || !res.body.ok) {
          _showToolbarToast(_friendlyApiError(res.body, "保存失败"), { error: true });
          if (onDone) onDone(false);
          return;
        }
        el.textContent = next;
        el.dataset.title = next;
        syncCoverTitleLayoutClass(el);
        // PRD §4.4 · 轻 ✓，不刷「已保存」toast
        el.classList.add("cover-opening__title--saved");
        window.clearTimeout(el._savedMarkTimer);
        el._savedMarkTimer = window.setTimeout(function () {
          el.classList.remove("cover-opening__title--saved");
        }, 1500);
        try {
          document.title = next;
        } catch (eTitle) {}
        try {
          window.dispatchEvent(new CustomEvent("travelogue:copy-saved"));
        } catch (e0) {}
        // 生成字体前先改名：跳过整页刷新，避免打断后续 resolve
        if (res.body.rendered && res.body.rendered.length && !opts.skipReload) {
          if (onDone) onDone(true);
          _reloadPreviewAfterLayout();
          return;
        }
        if (onDone) onDone(true);
      })
      .catch(function () {
        el.classList.remove("preview-toolbar__title--saving");
        el.classList.remove("cover-opening__title--saving");
        _showToolbarToast("保存失败", { error: true });
        if (onDone) onDone(false);
      });
  }

/** Trust V1 · 门禁/无 DOM 节点时共用写路径 */
export function saveMagazineTitleValue(tripId, nextTitle, opts) {
  opts = opts || {};
  var next = String(nextTitle || "").trim();
  if (!next) {
    return Promise.resolve(false);
  }
  var el = document.querySelector(".cover-opening__title");
  if (el) {
    return new Promise(function (resolve) {
      saveMagazineTitle(tripId, next, el, function (ok) {
        resolve(!!ok);
      }, opts);
    });
  }
  return postJsonConflictRetry(_tripApiBase(tripId) + "/save-copy", {
    patches: [{ path: "meta.title", value: next }],
  }).then(function (res) {
    if (res.status !== 200 || !res.body.ok) {
      _showToolbarToast(_friendlyApiError(res.body, "保存失败"), { error: true });
      return false;
    }
    try {
      document.title = next;
    } catch (e1) {}
    try {
      window.dispatchEvent(new CustomEvent("travelogue:copy-saved"));
    } catch (e2) {}
    return true;
  }).catch(function () {
    _showToolbarToast("保存失败", { error: true });
    return false;
  });
}

export function initCoverTitleEdit(tripId, opts) {
    opts = opts || {};
    if (_isSharePreview()) return;
    var titleEl = document.querySelector(".cover-opening__title");
    if (!titleEl || titleEl.dataset.coverTitleEdit === "on") return;
    titleEl.dataset.coverTitleEdit = "on";
    titleEl.classList.add("cover-opening__title--editable");
    titleEl.setAttribute("role", "button");
    titleEl.setAttribute("tabindex", "0");
    titleEl.setAttribute("aria-label", "点击编辑杂志名");
    titleEl.title = "点击编辑杂志名";
    titleEl.dataset.title = (titleEl.textContent || "").trim();
    syncCoverTitleLayoutClass(titleEl);

    fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        // PMX D3 · 封面只绑展示名；禁止用裸 meta.title 覆盖已渲染人话名
        var summary = data && data.intentSummary;
        var t = summary
          ? String(summary.displayTitle || "").trim()
          : "";
        if (!t) return;
        titleEl.textContent = t;
        titleEl.dataset.title = t;
        syncCoverTitleLayoutClass(titleEl);
      })
      .catch(function () {});

    function openEditor() {
      // RCI · 点书名优先打开精修「封面 · 杂志名」
      if (typeof opts.onOpenNameSeg === "function") {
        opts.onOpenNameSeg();
        return;
      }
      if (titleEl.classList.contains("cover-opening__title--saving")) return;
      if (titleEl.parentElement.querySelector(".cover-opening__title-input")) return;
      var input = document.createElement("input");
      input.type = "text";
      input.className = "cover-opening__title-input";
      input.maxLength = 20;
      input.value = titleEl.dataset.title || titleEl.textContent || "";
      titleEl.hidden = true;
      titleEl.parentElement.insertBefore(input, titleEl.nextSibling);
      input.focus();
      input.select();

      var imeComposing = false;
      var finished = false;
      function finish(save) {
        if (finished) return;
        if (save && (imeComposing || input.isComposing)) return;
        finished = true;
        var next = (input.value || "").trim();
        input.remove();
        titleEl.hidden = false;
        if (!save) {
          titleEl.textContent = titleEl.dataset.title || titleEl.textContent;
          return;
        }
        if (next.length > 20) {
          _showToolbarToast("杂志名最多 20 个字", { error: true });
          return;
        }
        if (!next) {
          _showToolbarToast("杂志名不能为空", { error: true });
          return;
        }
        saveMagazineTitle(tripId, next, titleEl);
      }

      input.addEventListener("compositionstart", function () {
        imeComposing = true;
      });
      input.addEventListener("compositionend", function () {
        imeComposing = false;
      });
      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          if (e.isComposing || imeComposing) {
            e.preventDefault();
            return;
          }
          e.preventDefault();
          finish(true);
        }
        if (e.key === "Escape") {
          e.preventDefault();
          finish(false);
        }
      });
      input.addEventListener("blur", function () {
        if (imeComposing || input.isComposing) return;
        finish(true);
      });
    }

    titleEl.addEventListener("click", openEditor);
    titleEl.addEventListener("keydown", function (/** @type {KeyboardEvent} */ e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openEditor();
      }
    });
  }
