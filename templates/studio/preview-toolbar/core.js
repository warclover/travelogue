/**
 * Preview toolbar · layout pending state, sheet dirty, rerender jobs.
 */
"use strict";

import { postJson } from "../js/http.js";
import { trackStudioEvent } from "../js/analytics.js";
import { isAiSurfaceEnabled } from "../js/ai-surface.js";
import { DARK_COPY } from "../js/ai-surface-dark-copy.js";
import { isPreviewToolbarV3 } from "./dock.js";
import { syncCoverTitleLayoutClass } from "./inline-edit.js";
import { pollJob, syncLongshotPreviewRowVisibility } from "./longshot.js";
import {
  showToolbarToast,
  toolbarConfirm,
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
var _sourceMissing = false;
var _sourceMissingDockDismissed = false;
var _sheetEditDirty = false;
var _sheetEditBaseline = "";
var narrateJobId = null;

export function getLayoutPending() {
  return _layoutPending;
}

export function getSourceMissing() {
  return _sourceMissing;
}

export function setSourceMissing(on) {
  _sourceMissing = !!on;
  if (on) _sourceMissingDockDismissed = false;
  var toolbar = document.querySelector(".preview-toolbar");
  if (toolbar && isPreviewToolbarV3(toolbar)) {
    refreshTaskDockState(toolbar);
  }
}

export function dismissSourceMissingDock() {
  _sourceMissingDockDismissed = true;
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
    // D-PCU · 默认/实验均不走黄底 G1 Strip；分章走 Dock 面板
    // 栈：export(外层) > layoutPending > sourceMissing > copyRefresh > longshotStale
    if (_layoutPending && !_pendingDockDismissed) {
      var pendingTitle = _layoutPendingMessage || "版面有改动";
      root._taskDock.showPending({
        title: pendingTitle,
        compact:
          typeof pendingTitle === "string" &&
          pendingTitle.indexOf("预览需更新") !== -1,
      });
      return;
    }
    if (_sourceMissing && !_sourceMissingDockDismissed) {
      root._taskDock.showPending({
        title: "原相册无法访问",
      });
      return;
    }
    // FE-SFI-05 · copyRefresh 高于 longshotStale（先刷新再导出）
    var copyRefresh =
      !!root._copyRefreshHint &&
      !root._copyRefreshDismissed &&
      typeof root._taskDock.showCopyRefresh === "function";
    if (copyRefresh) {
      root._taskDock.showCopyRefresh({});
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


var COPY_REFRESH_FAIL_TOAST =
  "这次没写完，稍后再试 · 原文案保持不变";

export function startLlmNarrate(root, tripId, btn, opts) {
    opts = opts || {};
    // NAS · D-NAS-19 / FE-NAS-09：函数级门闩（藏 UI 不够）
    if (!isAiSurfaceEnabled()) return Promise.resolve();
    if (!btn || btn.disabled) return Promise.resolve();
    var narrateStartedAt = 0;

    function setNarrateSheetStatus(label) {
      // SNR COPY-SNR-S01 · 同步 AI Sheet 状态条
      try {
        var el =
          (root &&
            root.querySelector &&
            root.querySelector("[data-ai-narrate-status]")) ||
          document.querySelector("[data-ai-narrate-status]");
        if (el && label) el.textContent = label;
        if (typeof opts.onStatus === "function") opts.onStatus(label);
      } catch (_e) {}
    }

    function failRefresh(meta) {
      trackStudioEvent("copy_refresh_failed", meta || {});
      setNarrateSheetStatus("失败可重试");
      showToolbarToast(COPY_REFRESH_FAIL_TOAST, { error: true, duration: 5200 });
      setSlowHint(root, "", false);
    }

    function run() {
      trackStudioEvent("llm_narrate_click", {
        available: true,
        source: opts.source || "preview",
      });
      narrateStartedAt = Date.now();
      btn.disabled = true;
      if (btn.dataset && !btn.dataset.labelBusy) {
        btn.dataset.labelIdle = btn.textContent || "";
        btn.dataset.labelBusy = "1";
        btn.textContent = "正在生成…";
      }
      setNarrateSheetStatus("生成中");
      setToolbarCollapsed(root, false, false);
      setSlowHint(root, "", false);
      setSlowHint(root, opts.busyHint || DARK_COPY.narrateBusy, true);
      return postJson("/__travelogue/narrate", { tripId: tripId })
        .then(function (res) {
          if (!res) return;
          if (res.status === 409 || res.status === 400) {
            var failCode = res.body && res.body.error;
            btn.disabled = false;
            if (btn.dataset.labelIdle) btn.textContent = btn.dataset.labelIdle;
            setSlowHint(root, "", false);
            setNarrateSheetStatus("失败可重试");
            if (
              failCode === "E_LLM_AUTH" ||
              failCode === "E_LLM_NETWORK" ||
              failCode === "E_LLM_PING"
            ) {
              trackStudioEvent("copy_refresh_failed", {
                code: failCode,
                trip_id: tripId,
              });
              toolbarConfirm({
                title: DARK_COPY.narrateFailTitle,
                body: DARK_COPY.narrateFailBody,
                confirmText: "去检查配置",
                cancelText: "知道了",
              }).then(function (ok) {
                if (!ok) return;
                // @ts-expect-error runtime Studio absolute URL (not a TS-resolvable module path)
                import("/__studio/js/llm-settings.js")
                  .then(function (mod) {
                    if (mod && typeof mod.openLlmSettings === "function") {
                      mod.openLlmSettings({ source: "preview_narrate_fail" });
                    }
                  })
                  .catch(function () {});
              });
              return;
            }
            failRefresh({ code: failCode || "start_fail", trip_id: tripId });
            return;
          }
          if (res.status !== 202 || !res.body.jobId) {
            btn.disabled = false;
            if (btn.dataset.labelIdle) btn.textContent = btn.dataset.labelIdle;
            failRefresh({ code: "no_job", trip_id: tripId });
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
                var durationMs = narrateStartedAt ? Date.now() - narrateStartedAt : 0;
                var originSkip =
                  (job.result && job.result.origin_skip_count) ||
                  (job.result && job.result.originSkipCount) ||
                  0;
                trackStudioEvent("copy_refresh_done", {
                  trip_id: tripId,
                  duration: durationMs,
                  origin_skip_count: originSkip,
                });
                // SNR D-SNR-06 · 刷新前同步暂存 diff，reload 后挂条
                try {
                  var diff =
                    (job.result && job.result.diffSummary) ||
                    (job.result && job.result.diff_summary) ||
                    null;
                  if (diff && diff.slotsLabel) {
                    sessionStorage.setItem(
                      "travelogue.snr.narrateDiff.v1." + String(tripId),
                      JSON.stringify({
                        slotsLabel: String(diff.slotsLabel || ""),
                        firstAnchor: String(diff.firstAnchor || ""),
                        slotTypes: diff.slotTypes || [],
                        count: diff.count || 0,
                        ts: Date.now(),
                      })
                    );
                    trackStudioEvent("snr_diff_show", {
                      trip_id: tripId,
                      slots_count: diff.count || 0,
                      slots: String(diff.slotsLabel || ""),
                    });
                  }
                } catch (_diffErr) {}
                setNarrateSheetStatus("已是杂志文案");
                window.location.reload();
                return;
              }
              var errCode = job.error && job.error.code;
              setNarrateSheetStatus("失败可重试");
              if (
                errCode === "E_LLM_AUTH" ||
                errCode === "E_LLM_NETWORK" ||
                errCode === "E_LLM_PING"
              ) {
                trackStudioEvent("copy_refresh_failed", {
                  code: errCode,
                  trip_id: tripId,
                });
                toolbarConfirm({
                  title: DARK_COPY.narrateFailTitle,
                  body: DARK_COPY.narrateFailBody,
                  confirmText: "去检查配置",
                  cancelText: "知道了",
                }).then(function (ok) {
                  if (!ok) return;
                  // @ts-expect-error runtime Studio absolute URL (not a TS-resolvable module path)
                  import("/__studio/js/llm-settings.js")
                    .then(function (mod) {
                      if (mod && typeof mod.openLlmSettings === "function") {
                        mod.openLlmSettings({ source: "preview_narrate_fail" });
                      }
                    })
                    .catch(function () {});
                });
                return;
              }
              failRefresh({
                code: errCode || "job_fail",
                trip_id: tripId,
                duration: narrateStartedAt ? Date.now() - narrateStartedAt : 0,
              });
            },
            function () {
              setNarrateSheetStatus("生成中");
              setSlowHint(root, "比预期久一些，请耐心等待…", true);
            },
            "narrate"
          );
        })
        .catch(function () {
          btn.disabled = false;
          if (btn.dataset.labelIdle) btn.textContent = btn.dataset.labelIdle;
          failRefresh({ code: "network", trip_id: tripId });
        });
    }

    if (opts.skipConfirm) {
      return run();
    }
    return toolbarConfirm({
      title: opts.confirmTitle || DARK_COPY.narrateConfirmTitle,
      body:
        opts.confirmBody ||
        "将为这本重新写开头一句和图说；你自己改过的内容不会动。通常不到一分钟。",
      confirmText: opts.confirmText || DARK_COPY.narrateConfirmText,
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
          var bodyMsg =
            (res.body && (res.body.message || res.body.error)) || "更新版面失败";
          var busy = errCode === "E_STUDIO_JOB_BUSY";
          showToolbarToast(
            (busy && bodyMsg) || opts.failMessage || bodyMsg,
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
