/**
 * Preview toolbar · layout pending state, sheet dirty, rerender jobs.
 */
"use strict";

import { postJson } from "../js/http.js";
import { isPreviewToolbarV3 } from "./dock.js";
import { syncCoverTitleLayoutClass } from "./inline-edit.js";
import { pollJob, syncLongshotPreviewRowVisibility } from "./longshot.js";
import {
  showToolbarToast,
  toolbarConfirm,
  toolbarAlert,
  setSlowHint,
  setToolbarCollapsed,
  syncToolbarHeight,
  reloadPreviewAfterLayout,
  tripApiBase,
  toolbarBody,
} from "./shell.js";

var _layoutPending = false;
var _pendingDockDismissed = false;
var _layoutPendingMessage = "";
var _g1Pending = false;
var _g1DockDismissed = false;
var _sheetEditDirty = false;
var _sheetEditBaseline = "";
var narrateJobId = null;

export function getLayoutPending() {
  return _layoutPending;
}

export function setLayoutPendingMessage(msg) {
  _layoutPendingMessage = msg;
}

export function getSheetEditDirty() {
  return _sheetEditDirty;
}

export function clearSheetEditDirty(root) {
  _sheetEditDirty = false;
  if (root) root._sheetEditDirty = false;
}

export function dismissPendingDock() {
  _pendingDockDismissed = true;
}

export function dismissG1Dock() {
  _g1DockDismissed = true;
}

export function activateG1Pending() {
  _g1Pending = true;
  _g1DockDismissed = false;
}


export function snapshotEditPanel(el) {
    if (!el) return "";
    var title = el.querySelector(".preview-drawer__title-input");
    var notes = el.querySelector(".preview-drawer__notes");
    var anchors = [];
    el.querySelectorAll(".preview-drawer__anchor").forEach(function (inp) {
      anchors.push((inp.value || "").trim());
    });
    var mood = el.querySelector(".preview-drawer__chip-mood.is-selected");
    var focus = el.querySelector(".preview-drawer__chip-focus.is-selected");
    var note = el.querySelector(".preview-drawer__copy-intent-note");
    var sub = el.querySelector(".preview-drawer__copy-intent-subsequent");
    return JSON.stringify({
      title: title ? title.value : "",
      notes: notes ? notes.value : "",
      anchors: anchors,
      mood: mood ? mood.getAttribute("data-value") : "",
      focus: focus ? focus.getAttribute("data-value") : "",
      intentNote: note ? note.value : "",
      subsequent: sub ? sub.checked : false,
    });
  }


export function markSheetEditBaseline(root, panel) {
    _sheetEditBaseline = snapshotEditPanel(panel);
    _sheetEditDirty = false;
    if (root) root._sheetEditDirty = false;
  }


export function wireSheetEditDirty(root, panel) {
    if (!panel || panel.dataset.sheetDirtyBound === "1") return;
    panel.dataset.sheetDirtyBound = "1";
    function syncDirty() {
      _sheetEditDirty = snapshotEditPanel(panel) !== _sheetEditBaseline;
      if (root) root._sheetEditDirty = _sheetEditDirty;
    }
    panel.addEventListener("input", syncDirty);
    panel.addEventListener("change", syncDirty);
    panel.querySelectorAll(".preview-drawer__chip-mood, .preview-drawer__chip-focus").forEach(
      function (btn) {
        btn.addEventListener("click", function () {
          window.setTimeout(syncDirty, 0);
        });
      }
    );
  }


export function refreshTaskDockState(root) {
    if (!root || !isPreviewToolbarV3(root) || !root._taskDock) return;
    if (root._exportDockActive || root._exportResultShowing) return;
    if (_g1Pending && !_g1DockDismissed) {
      root._taskDock.showG1({});
      return;
    }
    if (_layoutPending && !_pendingDockDismissed) {
      root._taskDock.showPending({
        title: _layoutPendingMessage || "版面有更新",
      });
      return;
    }
    root._taskDock.hide();
  }


export function layoutApplyButtons(root) {
    var scope = root && root.nodeType === 1 ? root : document;
    var toolbar =
      (scope.closest && scope.closest(".preview-toolbar")) ||
      (scope.classList && scope.classList.contains("preview-toolbar") ? scope : null) ||
      document.querySelector(".preview-toolbar");
    var searchRoot = toolbar || scope;
    return searchRoot.querySelectorAll(
      ".preview-toolbar__apply-layout, .preview-sheet__apply-layout, .preview-drawer__apply-layout"
    );
  }


export function syncCoverOpeningStyleInDom(style) {
    var section = document.querySelector('.cover-opening[data-block="cover-opening"]');
    if (!section || !style) return;
    section.setAttribute("data-cover-opening", style);
    var titleEl = section.querySelector(".cover-opening__title");
    if (style === "split-mat") {
      syncCoverTitleLayoutClass(titleEl);
    } else if (titleEl) {
      titleEl.classList.remove(
        "cover-opening__title--vertical",
        "cover-opening__title--vertical-compact",
        "cover-opening__title--horizontal"
      );
    }
  }


export function refreshPreviewAfterCopySave(res, tripId, root) {
    var rendered = res.body && res.body.rendered;
    if (rendered && rendered.length) {
      return Promise.resolve(true);
    }
    return applyLayoutRerender(tripId, root);
  }


export function setLayoutPending(on) {
    _layoutPending = !!on;
    if (on) _pendingDockDismissed = false;
    document
      .querySelectorAll(
        ".preview-toolbar__apply-layout, .preview-sheet__apply-layout, .preview-drawer__apply-layout"
      )
      .forEach(function (btn) {
        btn.hidden = !_layoutPending;
      });
    document.querySelectorAll(".preview-toolbar__pending-row").forEach(function (row) {
      row.hidden = !_layoutPending;
    });
    var toolbar = document.querySelector(".preview-toolbar");
    if (toolbar && isPreviewToolbarV3(toolbar)) {
      if (toolbar._sheet) toolbar._sheet.setPendingDot(_layoutPending);
      refreshTaskDockState(toolbar);
      if (toolbar._sheet && typeof toolbar._sheet.refreshLayoutTab === "function") {
        toolbar._sheet.refreshLayoutTab();
      }
      return;
    }
    if (toolbar) {
      syncLongshotPreviewRowVisibility(toolbar);
      requestAnimationFrame(function () {
        syncToolbarHeight(toolbar);
      });
    }
  }


export function startLlmNarrate(root, tripId, btn) {
    if (!btn || btn.disabled) return;
    toolbarConfirm({
      title: "生成杂志感文案",
      body: "将调用 LLM 重写 hook、导语与图注，可能覆盖未锁定的文案。继续？",
      confirmText: "继续",
    }).then(function (ok) {
      if (!ok) return;
      setToolbarCollapsed(root, false, false);
      btn.disabled = true;
      setSlowHint(root, "", false);
      setSlowHint(root, "正在生成杂志感文案…", true);
      return postJson("/__travelogue/narrate", { tripId: tripId });
    }).then(function (res) {
      if (!res) return;
      if (res.status === 409 || res.status === 400) {
        setSlowHint(root, (res.body && res.body.message) || "无法开始", true);
        btn.disabled = false;
        return;
      }
      if (res.status !== 202 || !res.body.jobId) {
        setSlowHint(root, "无法开始文案生成", true);
        btn.disabled = false;
        return;
      }
      narrateJobId = res.body.jobId;
      pollJob(
        res.body.jobId,
        root,
        function (job) {
          btn.disabled = false;
          narrateJobId = null;
          setSlowHint(root, "", false);
          if (job.status === "succeeded") {
            window.location.reload();
            return;
          }
          var err = (job.error && (job.error.message || job.error.code)) || "文案生成失败";
          toolbarAlert(err, { error: true });
        },
        function () {
          setSlowHint(root, "比预期久一些，请耐心等待…", true);
        },
        "narrate"
      );
    }).catch(function () {
      btn.disabled = false;
      setSlowHint(root, "网络错误", true);
    });
  }


export function refreshPreviewCover(root) {
    var body = toolbarBody(root);
    var card = body.querySelector(".preview-toolbar__preview-card");
    if (card) card.remove();
  }


export function applyLayoutRerender(tripId, root) {
    var applyBtns = layoutApplyButtons(
      root || document.querySelector(".preview-toolbar") || document.body
    );
    var pendingBtn =
      (root && root.querySelector && root.querySelector(".preview-toolbar__pending-apply")) ||
      document.querySelector(".preview-toolbar__pending-apply");
    applyBtns.forEach(function (btn) {
      btn.disabled = true;
    });
    if (pendingBtn) pendingBtn.disabled = true;
    showToolbarToast("正在更新版面…", { duration: 3000 });
    return postJson(tripApiBase(tripId) + "/rerender", {})
      .then(function (res) {
        applyBtns.forEach(function (btn) {
          btn.disabled = false;
        });
        if (pendingBtn) pendingBtn.disabled = false;
        if (res.status !== 200 || !res.body.ok) {
          showToolbarToast((res.body && res.body.error) || "更新版面失败", { error: true });
          setLayoutPending(true);
          return false;
        }
        setLayoutPending(false);
        reloadPreviewAfterLayout();
        return true;
      })
      .catch(function () {
        applyBtns.forEach(function (btn) {
          btn.disabled = false;
        });
        if (pendingBtn) pendingBtn.disabled = false;
        showToolbarToast("更新版面失败", { error: true });
        setLayoutPending(true);
        return false;
      });
  }



export function fetchEntry(tripId) {
    return fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry")
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; });
  }


export function currentChapterId() {
    var sections = document.querySelectorAll("section.chapter[data-chapter-id]");
    var best = null;
    var bestVis = 0;
    sections.forEach(function (sec) {
      var rect = sec.getBoundingClientRect();
      var vis = Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0);
      if (vis > bestVis) {
        bestVis = vis;
        best = sec.getAttribute("data-chapter-id");
      }
    });
    return best;
  }
