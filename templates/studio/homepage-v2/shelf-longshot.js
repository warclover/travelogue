/**
 * 首页 v2 · 书架「保存长图」Modal 流程（M14）。
 */
import { trackStudioEvent } from "../js/analytics.js";
import {
  LONGSHOT_PRESETS,
  startLongshotJob,
  waitForLongshotJob,
  revealLongshotOutput,
  formatLongshotResult,
  isJobBusyResponse,
} from "../js/longshot-client.js";
import { V2 } from "./store.js";

var _activeModal = null;
var _backgroundJob = null;

function toast(msg, opts) {
  if (typeof studioToast === "function") studioToast(msg, opts);
}

function focusNoScroll(el) {
  if (!el || !el.focus) return;
  try {
    el.focus({ preventScroll: true });
  } catch (_e) {
    el.focus();
  }
}

function closeActiveModal() {
  if (!_activeModal) return;
  _activeModal.close(false);
  _activeModal = null;
}

function openShelfLongshotModal(opts) {
  closeActiveModal();
  opts = opts || {};

  var backdrop = document.createElement("div");
  backdrop.className = "studio__modal-backdrop";

  var modal = document.createElement("div");
  modal.className = "studio__modal";
  modal.setAttribute("role", "dialog");
  modal.setAttribute("aria-modal", "true");

  var titleEl = document.createElement("h3");
  titleEl.textContent = opts.title || "";

  var bodyEl = document.createElement("div");
  bodyEl.className = "studio__modal-body v2-shelf-longshot__body";

  var actions = document.createElement("div");
  actions.className = "studio__modal-actions";

  var primaryBtn = document.createElement("button");
  primaryBtn.type = "button";
  primaryBtn.className = "studio__btn studio__btn--sm studio__btn--primary";
  primaryBtn.textContent = opts.primaryText || "关闭";
  primaryBtn.hidden = opts.primaryHidden !== false;

  var secondaryBtn = document.createElement("button");
  secondaryBtn.type = "button";
  secondaryBtn.className = "studio__btn studio__btn--ghost studio__btn--sm";
  secondaryBtn.textContent = opts.secondaryText || "关闭";
  secondaryBtn.hidden = !!opts.secondaryHidden;

  if (!secondaryBtn.hidden) actions.appendChild(secondaryBtn);
  if (!primaryBtn.hidden) actions.appendChild(primaryBtn);
  modal.appendChild(titleEl);
  modal.appendChild(bodyEl);
  modal.appendChild(actions);
  backdrop.appendChild(modal);
  document.body.appendChild(backdrop);
  document.body.classList.add("studio-modal-open");

  var previousFocus = document.activeElement;
  var closed = false;

  function setBodyLines(lines) {
    bodyEl.textContent = "";
    (lines || []).forEach(function (line) {
      var p = document.createElement("p");
      p.textContent = line;
      bodyEl.appendChild(p);
    });
  }

  function cleanup() {
    if (closed) return;
    closed = true;
    backdrop.remove();
    if (!document.querySelector(".studio__modal-backdrop")) {
      document.body.classList.remove("studio-modal-open");
    }
    if (previousFocus && previousFocus.focus) focusNoScroll(previousFocus);
  }

  secondaryBtn.addEventListener("click", function () { controller.close(false); });
  primaryBtn.addEventListener("click", function () {
    if (typeof controller._onPrimary === "function") controller._onPrimary();
    else controller.close(true);
  });
  backdrop.addEventListener("click", function (e) {
    if (e.target === backdrop) controller.close(false);
  });

  var controller = {
    el: modal,
    setTitle: function (text) { titleEl.textContent = text; },
    setBodyLines: setBodyLines,
    setProgress: function (hint) {
      setBodyLines([
        "「" + (opts.tripTitle || "") + "」",
        LONGSHOT_PRESETS.shelf.label,
        hint || "正在合成长图…",
      ]);
    },
    showResult: function (formatted, tripId) {
      controller.setTitle(formatted.ok ? formatted.title : formatted.title);
      var lines = [LONGSHOT_PRESETS.shelf.label].concat(formatted.lines);
      if (formatted.ok) lines.unshift("「" + (opts.tripTitle || "") + "」");
      setBodyLines(lines);
      primaryBtn.hidden = false;
      primaryBtn.textContent = formatted.ok ? "在文件夹中显示" : "关闭";
      secondaryBtn.hidden = !formatted.ok;
      secondaryBtn.textContent = "关闭";
      controller._onPrimary = formatted.ok
        ? function () {
            trackStudioEvent("shelf_longshot_reveal", { trip_id: tripId });
            revealLongshotOutput(tripId, formatted.revealPath).catch(function () {
              toast("无法打开文件夹", { duration: 3200 });
            });
            controller.close(true);
          }
        : function () { controller.close(false); };
      focusNoScroll(primaryBtn);
    },
    close: function () {
      cleanup();
      if (_activeModal === controller) _activeModal = null;
    },
  };

  if (opts.initialLines) setBodyLines(opts.initialLines);
  _activeModal = controller;
  focusNoScroll(secondaryBtn.hidden ? primaryBtn : secondaryBtn);
  return controller;
}

/**
 * @param {object} trip
 * @param {{ surface: string }} opts
 */
export function runShelfLongshot(trip, opts) {
  opts = opts || {};
  var surface = opts.surface || "grid";
  var tripId = trip.tripId;
  var title = trip.title || tripId;

  trackStudioEvent("shelf_longshot_start", {
    trip_id: tripId,
    surface: surface,
    scale: LONGSHOT_PRESETS.shelf.scale,
    copy_display: LONGSHOT_PRESETS.shelf.copyDisplay,
  });

  var modal = openShelfLongshotModal({
    title: "正在保存长图",
    tripTitle: title,
    initialLines: [
      "「" + title + "」",
      LONGSHOT_PRESETS.shelf.label,
      "正在提交任务…",
    ],
    primaryHidden: true,
    secondaryHidden: false,
    secondaryText: "关闭",
  });

  var dismissed = false;
  var originalClose = modal.close.bind(modal);
  modal.close = function () {
    dismissed = true;
    originalClose();
  };

  return startLongshotJob(tripId, "shelf", {
    onBusy: function () {
      modal.setProgress("排队中，请稍候…");
    },
  }).then(function (res) {
    if (dismissed) return null;
    if (isJobBusyResponse(res)) {
      trackStudioEvent("shelf_longshot_busy", { trip_id: tripId, surface: surface });
      modal.close();
      toast("已有长图任务进行中，请稍候", { duration: 3200 });
      return null;
    }
    if (res.status === 409) {
      modal.close();
      toast((res.body && res.body.message) || "请稍候再试", { duration: 3200 });
      return null;
    }
    if (res.status !== 202 || !res.body.jobId) {
      modal.close();
      toast("无法开始导出", { duration: 3200 });
      return null;
    }

    modal.setProgress("正在合成长图…");
    var jobId = res.body.jobId;
    _backgroundJob = waitForLongshotJob(jobId, {
      onProgress: function (job) {
        if (dismissed) return;
        if (job.status === "running" && job.stageHint) {
          modal.setProgress(job.stageHint);
        }
      },
      onSlow: function () {
        if (dismissed) {
          toast("比预期久一些，请耐心等待…", { duration: 4000 });
          return;
        }
        modal.setProgress("比预期久一些，请耐心等待…");
      },
    }).then(function (job) {
      _backgroundJob = null;
      if (dismissed) {
        if (job.status === "succeeded") {
          toast("长图已保存", { duration: 3000 });
          if (typeof V2.reroute === "function") V2.reroute();
        }
        return job;
      }

      var formatted = formatLongshotResult(job);
      if (job.status === "succeeded") {
        trackStudioEvent("shelf_longshot_success", {
          trip_id: tripId,
          surface: surface,
          segmented: !!formatted.segmented,
          capture_method: formatted.captureMethod,
          output_count: formatted.outputs.length,
        });
        if (typeof V2.reroute === "function") V2.reroute();
      } else {
        trackStudioEvent("shelf_longshot_fail", {
          trip_id: tripId,
          surface: surface,
          error_code: job.error && job.error.code,
        });
      }
      modal.showResult(formatted, tripId);
      return job;
    }).catch(function () {
      _backgroundJob = null;
      if (dismissed) return null;
      modal.close();
      toast("网络错误，请重试", { duration: 3200 });
      trackStudioEvent("shelf_longshot_fail", { trip_id: tripId, surface: surface, error_code: "network" });
      return null;
    });

    return _backgroundJob;
  }).catch(function () {
    if (!dismissed) {
      modal.close();
      toast("网络错误，请重试", { duration: 3200 });
    }
    return null;
  });
}
