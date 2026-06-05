/**
 * 首页 v2 · Studio 重新排版（POST /trips/{id}/curate + job poll）。
 */
import { postJson, withJobBusyRetry } from "../js/http.js";
import { pollJobUntilDone } from "../js/job-poll.js";

function toast(msg, opts) {
  if (typeof studioToast === "function") studioToast(msg, opts);
}

/**
 * @param {string} tripId
 * @returns {Promise<string>} jobId
 */
export function startTripCurateJob(tripId) {
  var url = "/__travelogue/trips/" + encodeURIComponent(tripId) + "/curate";
  return withJobBusyRetry(function () {
    return postJson(url, { force: true });
  }, {
    onBusy: function () {
      toast("已有任务进行中，稍后自动重试…", { duration: 2800 });
    },
  }).then(function (res) {
    if (res && res.status === 202 && res.body && res.body.jobId) {
      return res.body.jobId;
    }
    var code = res && res.body && res.body.error;
    var err = new Error((res && res.body && res.body.message) || "无法开始重新排版");
    err.code = code;
    err.status = res && res.status;
    throw err;
  });
}

/**
 * @param {string} tripId
 * @param {{ onProgress?: function(string): void }} [opts]
 * @returns {Promise<object>} terminal job
 */
export function runTripCurateJob(tripId, opts) {
  opts = opts || {};
  return startTripCurateJob(tripId).then(function (jobId) {
    if (typeof opts.onProgress === "function") opts.onProgress("正在重新排版…");
    return pollJobUntilDone(jobId, {
      intervalMs: 800,
      onTick: function (job) {
        if (typeof opts.onProgress === "function" && job && job.stageHint) {
          opts.onProgress(job.stageHint);
        }
      },
    });
  });
}
