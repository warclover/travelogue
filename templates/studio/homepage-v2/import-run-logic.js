/**
 * 首页 v2 · 导入编排纯逻辑（无 DOM / 无 fetch · node --test）
 * SFH W1 · 壳层见 import-run.js。
 */
"use strict";

import { resolveDisplayTitle } from "../js/title-humanize.js";
import { STAGE_LABELS, STAGE_HINT_LABELS } from "../js/constants.js";

/** Orchestrator 阶段名 → 产品阶段（FE-FST-01 · SFC vision_warmup） */
export function normalizeImportProductStage(stage) {
  var s = String(stage || "");
  if (s === "vision_warmup" || s === "preparing_vision") return "vision_warmup";
  if (s === "ingest") return "ingest";
  if (
    s === "clustering" ||
    s === "curate" ||
    s === "layout" ||
    s === "lock_structure"
  ) {
    return "curate";
  }
  if (s === "narrate" || s === "lock_copy") return "narrate";
  if (s === "render" || s === "export") return "render";
  return s;
}

/**
 * FE-FST-01 · 导入进度主句/次行。
 * SFC W0 · D-SFC-04 · running 主句永不为空；vision_warmup 优先。
 * @param {{ stage?: string, stageHint?: string }|null} job
 * @returns {{ main: string, secondary: string }}
 */
export function resolveImportStageCopy(job) {
  var stage = normalizeImportProductStage(job && job.stage);
  var rawHint = String((job && job.stageHint) || "").trim();
  var mappedHint = STAGE_HINT_LABELS[rawHint] || STAGE_HINT_LABELS[stage] || "";
  var stageMain = STAGE_LABELS[stage] || "";
  var isPhotoCount =
    /^已处理\s*\d+\s*\/\s*\d+/.test(rawHint) ||
    /正在导入并挑选照片/.test(rawHint);
  var fallback = "正在处理…";

  if (stage === "vision_warmup") {
    return {
      main: stageMain || mappedHint || "正在准备识图（首次可能较慢）",
      secondary: "",
    };
  }

  if (stage && stage !== "ingest" && stageMain) {
    return { main: stageMain, secondary: "" };
  }

  if (mappedHint) {
    return { main: mappedHint, secondary: isPhotoCount ? rawHint : "" };
  }

  if (stage === "ingest" || !stage) {
    if (isPhotoCount) {
      return {
        main: STAGE_LABELS.ingest || "正在整理照片…",
        secondary: rawHint,
      };
    }
    if (rawHint) return { main: rawHint, secondary: "" };
    return { main: STAGE_LABELS.ingest || "正在整理照片…", secondary: "" };
  }

  return { main: stageMain || rawHint || fallback, secondary: "" };
}

export function basenameTitle(path) {
  if (!path) return "我的旅途";
  var parts = String(path).replace(/[\\/]+$/, "").split(/[\\/]/);
  var folder = parts[parts.length - 1] || "";
  return resolveDisplayTitle({ title: folder }, { rawTitle: folder });
}

export function basenameFromRelativePath(rel) {
  if (!rel) return "";
  var parts = String(rel).split(/[\\/]/);
  return (parts[0] || "").trim();
}

/** @param {{ webkitRelativePath?: string, name?: string }[]} files */
export function guessUploadTitle(files) {
  if (!files || !files.length) return "我的旅途";
  var title = basenameFromRelativePath(files[0].webkitRelativePath);
  return resolveDisplayTitle({ title: title }, { rawTitle: title });
}

/**
 * @param {object} opts
 * @param {{ template_mode?: string, template_id?: string }} templateParams
 */
export function buildImportPayloadFields(albumPath, title, opts, templateParams) {
  opts = opts || {};
  var tpl = templateParams || { template_mode: "smart" };
  return Object.assign(
    {
      albumPath: albumPath,
      title: (title || basenameTitle(albumPath)).slice(0, 20) || "我的旅途",
      titleUserSet: opts.titleUserSet === true,
      place: "旅途",
      placeUserSet: false,
      mode: "quick_share",
      force: false,
    },
    tpl
  );
}

/** 有 activeJobId 才可续跑 poll */
export function shouldResumeImport(jobId) {
  return !!jobId;
}

/** 仅有 uploadForm pending、无 jobId → 丢弃不可恢复的上传草稿 */
export function shouldDiscardUploadPendingWithoutJob(jobId, pending) {
  return !jobId && !!(pending && pending.uploadForm);
}

export function resolveImportResumeSource(pending) {
  if (pending && pending.uploadForm) return "浏览器上传";
  if (pending && pending.albumPath) return "本机文件夹";
  return "本机文件夹";
}

export function isImportPhotoCapExceeded(count, cap) {
  return Number(count) > Number(cap);
}

/** poll 代际作废 */
export function shouldAbortImportPoll(gen, activeGen) {
  return gen !== activeGen;
}

/**
 * L0：成功/取消清 pending；失败保留以便重试。
 * @param {"succeeded"|"cancelled"|"failed"|string} status
 */
export function shouldClearPendingOnJobTerminal(status) {
  return status === "succeeded" || status === "cancelled";
}

/** 失败态允许重试（含 recoverableWithStub） */
export function canRetryFailedImport(err) {
  if (!err) return false;
  if (err.recoverableWithStub === true) return true;
  var code = err.code || "";
  return code !== "E_IMPORT_PHOTO_CAP";
}

/**
 * IR-U-03 · 是否应对服务端发起 cancel。
 * 现网无独立 cancelling 枚举：有 activeJobId 才 POST /cancel；无 job 时仅本地清态（API no-op）。
 * terminal 态下壳层通常已清空 _activeJobId，故再次 cancel → false。
 */
export function shouldPerformCancelImport(activeJobId) {
  return !!activeJobId;
}
