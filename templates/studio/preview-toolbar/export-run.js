/**
 * Preview toolbar · longshot job polling + mount (M-P2b).
 */
"use strict";

import { postJsonBusyRetry, isJobBusyResponse } from "../js/http.js";
import { startJobPollInterval } from "../js/job-poll.js";
import { setToolbarCollapsed } from "./shell.js";
import { setSlowHint } from "./toolbar-ui.js";
import {
  buildLongshotRequestFromPage,
  longshotBtnEl,
  setLongshotExportState,
  hideLongshotDrawer,
  showLongshotDrawer,
  longshotProgressPct,
  openLongshotResultDrawer,
  syncLongshotPreviewChips,
  longshotApi,
  hideStaleHint,
} from "./export-state.js";
import { bindLongshotExportMeta } from "./export-popover.js";

var isJobBusy409 = isJobBusyResponse;
var longshotJobId = null;
var longshotPollCancel = null;
var narratePollCancel = null;
var narrateJobId = null;
var SLOW_JOB_MS = 30000;

export function pollJob(jobId, root, onDone, onSlow, kind) {
  kind = kind || "longshot";
  if (kind === "narrate") {
    if (narratePollCancel) {
      narratePollCancel();
      narratePollCancel = null;
    }
  } else if (longshotPollCancel) {
    longshotPollCancel();
    longshotPollCancel = null;
  }
  var cancelFn = startJobPollInterval(jobId, {
    intervalMs: 800,
    slowMs: SLOW_JOB_MS,
    onSlow: onSlow,
    onTick: function (job) {
      if (
        kind === "longshot" &&
        job.status === "running" &&
        root &&
        jobId === longshotJobId
      ) {
        var pct = longshotProgressPct(job);
        setLongshotExportState(root, "running", {
          hint: job.stageHint ? "正在保存… " + job.stageHint : "正在保存…",
          pct: pct,
        });
      }
    },
    onDone: function (job) {
      if (kind === "narrate") {
        narratePollCancel = null;
      } else {
        longshotPollCancel = null;
        if (jobId === longshotJobId) longshotJobId = null;
      }
      onDone(job);
    },
  });
  if (kind === "narrate") {
    narratePollCancel = cancelFn;
  } else {
    longshotPollCancel = cancelFn;
  }
}
export function startLongshot(root, tripId) {
  var btn = longshotBtnEl(root);
  if (!btn || btn.disabled) return;
  setToolbarCollapsed(root, false, false);
  hideLongshotDrawer(root);
  setLongshotExportState(root, "running", { hint: "正在保存…" });
  setSlowHint(root, "", false);

  postJsonBusyRetry("/__travelogue/longshot", buildLongshotRequestFromPage(tripId), {
    onBusy: function () {
      setLongshotExportState(root, "running", { hint: "排队中，请稍候…" });
    },
  })
    .then(function (res) {
      if (isJobBusy409(res)) {
        setLongshotExportState(root, "running", { hint: "排队中，请稍候…" });
        return;
      }
      if (res.status === 409) {
        setLongshotExportState(root, "error", {
          hint: (res.body && res.body.message) || "请稍候再试",
        });
        return;
      }
      if (res.status !== 202 || !res.body.jobId) {
        setLongshotExportState(root, "error", { hint: "无法开始导出" });
        return;
      }
      longshotJobId = res.body.jobId;
      pollJob(
        res.body.jobId,
        root,
        function (job) {
          setSlowHint(root, "", false);
          if (job.status === "succeeded") {
            setLongshotExportState(root, "done");
            showLongshotDrawer(root, job);
            hideStaleHint(root);
          } else if (job.status === "failed") {
            setLongshotExportState(root, "error");
            showLongshotDrawer(root, job);
          } else {
            setLongshotExportState(root, "idle");
          }
        },
        function () {
          setSlowHint(root, "比预期久一些，请耐心等待…", true);
        }
      );
    })
    .catch(function () {
      setLongshotExportState(root, "error", { hint: "网络错误" });
    });
}

export function mountExportZone(root, tripId) {
  var rightZone = root.querySelector('.preview-toolbar__right') || root.querySelector('.preview-toolbar__bar');
  var exportWrap = document.createElement('div');
  exportWrap.className = 'preview-toolbar__export-zone-wrap';
  var exportZone = document.createElement('div');
  exportZone.className = 'preview-toolbar__export-zone';
  var longshotBtn = document.createElement('button');
  longshotBtn.type = 'button';
  longshotBtn.className =
    'preview-toolbar__longshot preview-toolbar__longshot--main preview-toolbar__longshot--idle preview-toolbar__longshot--primary';
  longshotBtn.textContent = '保存长图';
  var exportSettingsBtn = document.createElement('button');
  exportSettingsBtn.type = 'button';
  exportSettingsBtn.className = 'preview-toolbar__export-settings-trigger preview-toolbar__ctl';
  exportSettingsBtn.setAttribute('aria-label', '导出设置');
  exportSettingsBtn.title = '导出设置';
  exportSettingsBtn.innerHTML =
    '<span class="preview-toolbar__export-meta">导出设置：按章 · 2× · 完整文案</span>' +
    '<span class="preview-toolbar__export-settings-caret" aria-hidden="true">▾</span>';
  var staleBadge = document.createElement('span');
  staleBadge.className = 'preview-toolbar__export-stale';
  staleBadge.hidden = true;
  staleBadge.textContent = '内容已更新';
  exportZone.appendChild(longshotBtn);
  exportZone.appendChild(staleBadge);
  exportZone.appendChild(exportSettingsBtn);
  exportZone.classList.add('preview-toolbar__export-zone--split-idle');
  var progress = document.createElement('div');
  progress.className = 'preview-toolbar__export-progress';
  progress.hidden = true;
  progress.innerHTML = '<div class="preview-toolbar__export-progress-fill"></div>';
  exportWrap.appendChild(exportZone);
  exportWrap.appendChild(progress);
  var exportSlot = root.querySelector('.preview-toolbar__export-slot');
  if (exportSlot) exportSlot.appendChild(exportWrap);
  else if (rightZone) rightZone.insertBefore(exportWrap, rightZone.firstChild);
  setLongshotExportState(root, 'idle');
  bindLongshotExportMeta(root);
  longshotBtn.addEventListener('click', function () {
    if (longshotBtn.classList.contains('preview-toolbar__longshot--done')) {
      openLongshotResultDrawer(root);
      return;
    }
    startLongshot(root, tripId);
  });
  (function waitLongshotApi(attempts) {
    if (longshotApi() || attempts <= 0) {
      syncLongshotPreviewChips(root);
      return;
    }
    window.setTimeout(function () { waitLongshotApi(attempts - 1); }, 150);
  })(24);
  return exportWrap;
}
