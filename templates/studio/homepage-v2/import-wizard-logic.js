/**
 * 首页 v2 · 导入向导纯逻辑（无 DOM · node --test）
 * SFH W2 · 关闭确认 / 步骤合法性 / dirty 快照。
 */
"use strict";

export var WIZARD_STEPS = ["pick", "confirm", "fine"];

/** @param {string} step */
export function normalizeWizardStep(step) {
  if (step === "fine") return "fine";
  if (step === "confirm") return "confirm";
  return "pick";
}

/**
 * fine 步字段快照是否相对入口快照变脏。
 * @param {Record<string, unknown>|null|undefined} entrySnapshot
 * @param {Record<string, unknown>|null|undefined} current
 */
export function isFineSnapshotDirty(entrySnapshot, current) {
  if (!entrySnapshot || !current) return false;
  var keys = Object.keys(entrySnapshot);
  for (var i = 0; i < keys.length; i++) {
    var k = keys[i];
    if (String(current[k] || "") !== String(entrySnapshot[k] || "")) return true;
  }
  return false;
}

/**
 * 照片偏好是否非默认：推荐精简为默认（P9-F3 三选一）。
 * @param {{
 *   photoKeepMode?: string,
 *   photoCullEnabled?: boolean,
 *   keepNearDuplicates?: boolean
 * }} prefs
 */
export function isPhotoPrefsNonDefault(prefs) {
  var p = prefs || {};
  var mode = String(p.photoKeepMode || "").trim().toLowerCase();
  if (mode === "recommended" || mode === "keep_bursts" || mode === "keep_all") {
    return mode !== "recommended";
  }
  var cullOn = p.photoCullEnabled !== false;
  var keepDupes = p.keepNearDuplicates === true;
  return !cullOn || keepDupes;
}

/** @param {string|null|undefined} mode */
export function derivePhotoPrefsFromMode(mode) {
  var m = String(mode || "recommended").trim().toLowerCase();
  if (m === "keep_all") {
    return { photoKeepMode: "keep_all", photoCullEnabled: false, keepNearDuplicates: true };
  }
  if (m === "keep_bursts") {
    return { photoKeepMode: "keep_bursts", photoCullEnabled: true, keepNearDuplicates: true };
  }
  return { photoKeepMode: "recommended", photoCullEnabled: true, keepNearDuplicates: false };
}

/**
 * 旧草稿两布尔 → 三档（session 内 cull 关映射 keep_all，与读盘推断不同）。
 * @param {{ photoKeepMode?: string, photoCullEnabled?: boolean, keepNearDuplicates?: boolean }} draft
 */
export function resolvePhotoKeepModeFromDraft(draft) {
  var d = draft || {};
  var mode = String(d.photoKeepMode || "").trim().toLowerCase();
  if (mode === "recommended" || mode === "keep_bursts" || mode === "keep_all") {
    return mode;
  }
  if (d.photoCullEnabled === false) return "keep_all";
  if (d.keepNearDuplicates === true) return "keep_bursts";
  return "recommended";
}

/**
 * 关闭向导是否需要确认（与 shouldConfirmClose 行为等价）。
 * @param {{
 *   step?: string,
 *   fineDirty?: boolean,
 *   photoPrefsNonDefault?: boolean
 * }} ctx
 */
export function shouldConfirmCloseWizard(ctx) {
  var c = ctx || {};
  var step = normalizeWizardStep(c.step);
  if (step === "pick") return false;
  if (step === "fine" && c.fineDirty) return true;
  if ((step === "confirm" || step === "fine") && c.photoPrefsNonDefault) return true;
  return false;
}

/** pick → confirm/fine 前须有文件夹路径 */
export function canLeavePickStep(albumPath) {
  return !!(albumPath && String(albumPath).trim());
}

/**
 * 模式与步骤前进合法性（粗矩阵）。
 * @param {"pick"|"confirm"|"fine"} from
 * @param {"pick"|"confirm"|"fine"} to
 * @param {"quick_share"|"fine_craft"|string} mode
 */
export function canNavigateWizardStep(from, to, mode) {
  var a = normalizeWizardStep(from);
  var b = normalizeWizardStep(to);
  if (a === b) return true;
  if (b === "pick") return true; // 允许回 Step1
  if (a === "pick" && (b === "confirm" || b === "fine")) return true;
  if (a === "confirm" && b === "fine") return mode === "fine_craft";
  if (a === "fine" && b === "confirm") return true;
  return false;
}
