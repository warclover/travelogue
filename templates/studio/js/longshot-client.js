/**
 * Travelogue Studio · shared longshot export client (M14 · preview + shelf).
 */
import { postJson, postJsonBusyRetry, isJobBusyResponse } from "./http.js";
import { pollJobUntilDone } from "./job-poll.js";

export const LONGSHOT_SLOW_MS = 45000;
export const LONGSHOT_POLL_MS = 800;

/** @type {Record<string, { scale: number, copyDisplay: string, format: string, label: string }>} */
export const LONGSHOT_PRESETS = {
  shelf: {
    scale: 3,
    copyDisplay: "photos",
    format: "png",
    label: "纯照片 · 3×",
  },
  preview: {
    scale: 2,
    copyDisplay: "full",
    format: "png",
    label: "完整文案 · 2×",
  },
};

/**
 * @param {string} tripId
 * @param {keyof typeof LONGSHOT_PRESETS | object} preset
 */
export function buildLongshotRequest(tripId, preset) {
  var p = typeof preset === "string" ? LONGSHOT_PRESETS[preset] : preset;
  if (!p) p = LONGSHOT_PRESETS.preview;
  return {
    tripId: tripId,
    scale: p.scale,
    format: p.format || "png",
    copyDisplay: p.copyDisplay || "full",
  };
}

export function revealLongshotOutput(tripId, relPath) {
  return postJson("/__travelogue/reveal", { tripId: tripId, relPath: relPath });
}

/**
 * @param {string} tripId
 * @param {keyof typeof LONGSHOT_PRESETS | object} preset
 * @param {{ onBusy?: function(): void }} [options]
 */
export function startLongshotJob(tripId, preset, options) {
  options = options || {};
  return postJsonBusyRetry(
    "/__travelogue/longshot",
    buildLongshotRequest(tripId, preset),
    { onBusy: options.onBusy }
  );
}

/**
 * @param {string} jobId
 * @param {object} [options]
 * @param {function(object): void} [options.onProgress]
 * @param {function(): void} [options.onSlow]
 * @param {number} [options.slowMs]
 */
export function waitForLongshotJob(jobId, options) {
  options = options || {};
  return pollJobUntilDone(jobId, {
    intervalMs: LONGSHOT_POLL_MS,
    slowMs: options.slowMs || LONGSHOT_SLOW_MS,
    onSlow: options.onSlow,
    onTick: function (job) {
      if (typeof options.onProgress === "function") options.onProgress(job);
    },
  });
}

/**
 * @param {object} job
 * @returns {{ ok: boolean, title: string, lines: string[], outputs: string[], revealPath: string|null, captureMethod: string, segmented: boolean }}
 */
export function formatLongshotResult(job) {
  if (!job || job.status === "failed") {
    var err = job && job.error;
    return {
      ok: false,
      title: "无法保存长图",
      lines: [(err && (err.message || err.code)) || "导出失败，请重试"],
      outputs: [],
      revealPath: null,
      captureMethod: "",
      segmented: false,
    };
  }

  var result = job.result || {};
  var outputs = result.outputs || [];
  var method = result.captureMethod || "p0";
  var segmented = result.segmented || outputs.length > 1;
  var lines = [];

  if (segmented && outputs.length > 1) {
    lines.push(
      result.userHint ||
        "已按章导出 " + outputs.length + " 张，底部含页码（如 2/5）便于微信按序发送。"
    );
  }
  if (method === "p1") {
    lines.push("已使用兼容模式导出，与预览可能有细微差异。");
  }
  outputs.forEach(function (rel) {
    lines.push("· " + rel);
  });

  return {
    ok: true,
    title: "长图已保存",
    lines: lines,
    outputs: outputs,
    revealPath: outputs.length ? outputs[0] : null,
    captureMethod: method,
    segmented: segmented,
  };
}

export { isJobBusyResponse };
