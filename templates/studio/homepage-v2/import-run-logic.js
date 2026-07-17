/**
 * 首页 v2 · 导入编排纯逻辑（无 DOM / 无 fetch · node --test）
 * SFH W1 · 壳层见 import-run.js。
 */
"use strict";

import { humanizeFolderTitle } from "../js/title-humanize.js";

export function basenameTitle(path) {
  if (!path) return "我的旅途";
  var parts = String(path).replace(/[\\/]+$/, "").split(/[\\/]/);
  return humanizeFolderTitle(parts[parts.length - 1] || "");
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
  return humanizeFolderTitle(title);
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
