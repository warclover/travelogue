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
    // D-REF-18 · G1 > layoutPending > longshotStale；同时最多一层主待办
    if (_g1Pending) {
      // 横幅在视口内时由横幅承担；滚出且未「稍后」时由 Task Dock 镜像
      if (!root._g1BannerVisible && !_g1DockDismissed) {
        root._taskDock.showG1({});
      } else {
        root._taskDock.hide();
      }
      return;
    }
    if (_layoutPending && !_pendingDockDismissed) {
      root._taskDock.showPending({
        title: _layoutPendingMessage || "版面有更新",
      });
      return;
    }
    var longshotStale =
      !!root._longshotStale ||
      !!(root.querySelector && root.querySelector(".preview-toolbar__longshot--stale"));
    if (longshotStale && !root._staleDockDismissed) {
      root._taskDock.showStale({});
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


export function startLlmNarrate(root, tripId, btn, opts) {
    opts = opts || {};
    if (!btn || btn.disabled) return Promise.resolve();

    function run() {
      btn.disabled = true;
      if (btn.dataset && !btn.dataset.labelBusy) {
        btn.dataset.labelIdle = btn.textContent || "";
        btn.dataset.labelBusy = "1";
        btn.textContent = "正在重写…";
      }
      setToolbarCollapsed(root, false, false);
      setSlowHint(root, "", false);
      setSlowHint(root, opts.busyHint || "正在生成杂志感文案…", true);
      return postJson("/__travelogue/narrate", { tripId: tripId })
        .then(function (res) {
          if (!res) return;
          if (res.status === 409 || res.status === 400) {
            setSlowHint(root, (res.body && res.body.message) || "无法开始", true);
            btn.disabled = false;
            if (btn.dataset.labelIdle) btn.textContent = btn.dataset.labelIdle;
            return;
          }
          if (res.status !== 202 || !res.body.jobId) {
            setSlowHint(root, "无法开始文案生成", true);
            btn.disabled = false;
            if (btn.dataset.labelIdle) btn.textContent = btn.dataset.labelIdle;
            return;
          }
          narrateJobId = res.body.jobId;
          pollJob(
            res.body.jobId,
            root,
            function (job) {
              btn.disabled = false;
              if (btn.dataset.labelIdle) btn.textContent = btn.dataset.labelIdle;
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
        })
        .catch(function () {
          btn.disabled = false;
          if (btn.dataset.labelIdle) btn.textContent = btn.dataset.labelIdle;
          setSlowHint(root, "网络错误", true);
        });
    }

    if (opts.skipConfirm) {
      return run();
    }
    return toolbarConfirm({
      title: opts.confirmTitle || "生成杂志感文案",
      body:
        opts.confirmBody ||
        "将调用 LLM 重写 hook、导语与图注，可能覆盖未锁定的文案。继续？",
      confirmText: opts.confirmText || "继续",
    }).then(function (ok) {
      if (!ok) return;
      return run();
    });
  }


export function refreshPreviewCover(root) {
    var body = toolbarBody(root);
    var card = body.querySelector(".preview-toolbar__preview-card");
    if (card) card.remove();
  }


export function applyLayoutRerender(tripId, root, opts) {
    opts = opts || {};
    var LAYOUT_RERENDER_TIMEOUT_MS = opts.timeoutMs || 90000;
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
    showToolbarToast(opts.busyMessage || "正在更新版面…", { duration: 3000 });

    var timedOut = false;
    var timeoutId = null;
    var timeoutPromise = new Promise(function (_resolve, reject) {
      timeoutId = setTimeout(function () {
        timedOut = true;
        reject(new Error("layout_rerender_timeout"));
      }, LAYOUT_RERENDER_TIMEOUT_MS);
    });

    function finishButtons() {
      applyBtns.forEach(function (btn) {
        btn.disabled = false;
      });
      if (pendingBtn) pendingBtn.disabled = false;
    }

    return Promise.race([
      postJson(tripApiBase(tripId) + "/rerender", {}),
      timeoutPromise,
    ])
      .then(function (res) {
        if (timeoutId) clearTimeout(timeoutId);
        finishButtons();
        if (res.status !== 200 || !res.body.ok) {
          var errCode =
            (res.body && (res.body.error || res.body.code)) ||
            "E_LAYOUT_RERENDER";
          showToolbarToast(
            opts.failMessage || (res.body && res.body.error) || "更新版面失败",
            { error: true }
          );
          setLayoutPending(true);
          if (typeof opts.onFail === "function") {
            try {
              opts.onFail(errCode, res);
            } catch (eFail) {}
          }
          return false;
        }
        setLayoutPending(false);
        if (typeof opts.beforeReload === "function") {
          try {
            opts.beforeReload();
          } catch (eBefore) {}
        }
        reloadPreviewAfterLayout();
        return true;
      })
      .catch(function (err) {
        if (timeoutId) clearTimeout(timeoutId);
        finishButtons();
        var isTimeout =
          timedOut ||
          (err && String(err.message || "") === "layout_rerender_timeout");
        var failMsg = isTimeout
          ? opts.failMessage || "版面没有更新成功，长图尚未开始"
          : opts.failMessage || "更新版面失败";
        showToolbarToast(failMsg, { error: true });
        setLayoutPending(true);
        if (typeof opts.onFail === "function") {
          try {
            opts.onFail(isTimeout ? "E_LAYOUT_TIMEOUT" : "E_NETWORK");
          } catch (eFailNet) {}
        }
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
