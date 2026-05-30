/**
 * Travelogue Studio · shared job status polling (homepage, success page, preview toolbar).
 */

export function fetchJobStatus(jobId) {
  return fetch("/__travelogue/status?jobId=" + encodeURIComponent(jobId))
    .then(function (resp) {
      if (!resp.ok) throw new Error("status unavailable");
      return resp.json();
    });
}

/**
 * Poll until job reaches a terminal state.
 * @param {string} jobId
 * @param {object} [options]
 * @param {number} [options.intervalMs=500]
 * @param {number} [options.slowMs=30000]
 * @param {number} [options.maxErrors=5]
 * @param {function(): boolean} [options.shouldAbort]
 * @param {function(object, number)} [options.onTick] - (job, startedAt)
 * @param {function()} [options.onSlow]
 * @returns {Promise<object>}
 */
export function pollJobUntilDone(jobId, options) {
  options = options || {};
  var intervalMs = options.intervalMs || 500;
  var maxErrors = options.maxErrors || 5;
  var startedAt = options.startedAt || Date.now();
  var slowShown = false;
  var errorCount = 0;
  var timer = null;

  return new Promise(function (resolve, reject) {
    function clearTimer() {
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
    }
    function schedule() {
      timer = setTimeout(tick, intervalMs);
    }
    function tick() {
      if (options.shouldAbort && options.shouldAbort()) {
        clearTimer();
        reject(new Error("已取消"));
        return;
      }
      fetchJobStatus(jobId).then(function (job) {
        errorCount = 0;
        if (options.onSlow && !slowShown && Date.now() - startedAt > (options.slowMs || 30000)) {
          slowShown = true;
          options.onSlow();
        }
        if (typeof options.onTick === "function") options.onTick(job, startedAt);
        if (job.status === "succeeded" || job.status === "failed" || job.status === "cancelled") {
          clearTimer();
          resolve(job);
          return;
        }
        schedule();
      }).catch(function () {
        errorCount += 1;
        if (errorCount >= maxErrors) {
          clearTimer();
          reject(new Error("网络错误，请重试"));
          return;
        }
        schedule();
      });
    }
    tick();
  });
}

/** Interval-based poll with explicit cancel (preview toolbar longshot). */
export function startJobPollInterval(jobId, options) {
  options = options || {};
  var intervalMs = options.intervalMs || 800;
  var startedAt = Date.now();
  var slowShown = false;
  var errorCount = 0;
  var timer = setInterval(function () {
    if (options.onSlow && !slowShown && Date.now() - startedAt > (options.slowMs || 30000)) {
      slowShown = true;
      options.onSlow();
    }
    fetchJobStatus(jobId).then(function (job) {
      errorCount = 0;
      if (typeof options.onTick === "function") options.onTick(job, startedAt);
      if (job.status === "succeeded" || job.status === "failed" || job.status === "cancelled") {
        clearInterval(timer);
        if (typeof options.onDone === "function") options.onDone(job);
      }
    }).catch(function () {
      errorCount += 1;
      if (errorCount >= (options.maxErrors || 5)) {
        clearInterval(timer);
        if (typeof options.onError === "function") options.onError(new Error("网络错误"));
      }
    });
  }, intervalMs);
  return function cancel() {
    clearInterval(timer);
  };
}
