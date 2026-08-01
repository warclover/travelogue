// @ts-nocheck
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
    entrypoint: "shelf",
  },
  preview: {
    scale: 2,
    copyDisplay: "full",
    format: "png",
    label: "带文字 · 2×",
    entrypoint: "preview",
  },
};

/**
 * @param {string} tripId
 * @param {keyof typeof LONGSHOT_PRESETS | object} preset
 */
export function buildLongshotRequest(tripId, preset) {
  var p = typeof preset === "string" ? LONGSHOT_PRESETS[preset] : preset;
  if (!p) p = LONGSHOT_PRESETS.preview;
  var segmentMode = p.segmentMode || "auto";
  if (segmentMode !== "full" && segmentMode !== "chapter" && segmentMode !== "auto") {
    segmentMode = "auto";
  }
  var body = {
    tripId: tripId,
    scale: p.scale,
    format: p.format || "png",
    copyDisplay: p.copyDisplay || "full",
    segmentMode: segmentMode,
  };
  // Only attach platform when caller opts in (shelf / 1.x omit → branch A)
  if (p.platform) {
    body.platform = p.platform;
    if (p.platform !== "wechat_chat") {
      body.segmentMode = "auto";
    }
  }
  if (p.intent) {
    body.intent = p.intent;
  }
  if (p.entrypoint) {
    body.entrypoint = p.entrypoint;
  }
  if (p.slideCount != null && p.slideCount !== "") {
    body.slideCount = p.slideCount;
  }
  if (p.padMode) {
    body.padMode = p.padMode;
  }
  if (p.includeAppendix === true) {
    body.includeAppendix = true;
  }
  return body;
}

/** Resolve copyDisplay from live preview DOM (Studio toolbar chips). */
export function resolveCopyDisplayFromDom(doc) {
  doc = doc || (typeof document !== "undefined" ? document : null);
  if (!doc || !doc.documentElement) return "full";
  var html = doc.documentElement;
  if (html.getAttribute("data-photos-only") === "on") return "photos";
  if (html.getAttribute("data-copy-display") === "photos") return "photos";
  return "full";
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
 * @returns {{ ok: boolean, title: string, lines: string[], outputs: string[], revealPath: string|null, captureMethod: string, segmented: boolean, platform?: string, publishGuide?: string }}
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
      platform: "",
      publishGuide: "",
    };
  }

  var result = job.result || {};
  var outputs = result.outputs || [];
  var method = result.captureMethod || "p0";
  var segmented = result.segmented || outputs.length > 1;
  var platform = result.platform || "wechat_chat";
  var lines = [];
  var title = "长图已保存";

  if (platform === "moments_grid") {
    var nGrid = result.pageCount || outputs.length;
    title = "✓ " + nGrid + " 张九宫格已就绪";
    if (result.userHint) lines.push(result.userHint);
    if (result.publishGuide) lines.push(result.publishGuide);
  } else if (platform === "poster_bric") {
    title = "✓ 单屏海报已就绪";
    if (result.userHint) lines.push(result.userHint);
    if (result.publishGuide) lines.push(result.publishGuide);
  } else if (platform === "wechat_moments") {
    var n = result.pageCount || outputs.length;
    title = "✓ " + n + " 张长图连读已就绪";
    lines.push("这不是九宫格 · 滑动连读的长图切片");
    if (result.userHint) lines.push(result.userHint);
    if (result.publishGuide) lines.push(result.publishGuide);
  } else if (platform === "xiaohongshu") {
    title = "✓ " + (result.pageCount || outputs.length) + " 张 3:4 配图已就绪";
    if (result.userHint) lines.push(result.userHint);
    if (result.publishGuide) lines.push(result.publishGuide);
  } else {
    // FE-FST-04 · 默认微信群：已保存确认（发群教学改走 Help H4）
    var displayTitle = String(result.displayTitle || result.title || "").trim();
    if (segmented && outputs.length > 1) {
      title = "长图已保存（共 " + outputs.length + " 段）";
      lines.push(
        result.userHint ||
          "已按章导出 " + outputs.length + " 张，底部含页码便于按序发送。"
      );
    } else if (displayTitle) {
      title = "《" + displayTitle + "》长图已保存";
    } else {
      title = "长图已保存";
    }
  }
  if (method === "p1") {
    lines.push("已使用兼容模式导出，与预览可能有细微差异。");
  }
  outputs.forEach(function (rel) {
    lines.push("· " + rel);
  });

  return {
    ok: true,
    title: title,
    lines: lines,
    outputs: outputs,
    revealPath: outputs.length ? outputs[0] : null,
    captureMethod: method,
    segmented: segmented,
    platform: platform,
    publishGuide: result.publishGuide || "",
  };
}

export { isJobBusyResponse };
