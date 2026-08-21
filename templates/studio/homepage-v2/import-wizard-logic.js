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
 * 旧草稿两布尔 → 三档（对齐 Python infer_mode_from_bools；永不升 keep_all）。
 * @param {{ photoKeepMode?: string, photoCullEnabled?: boolean, keepNearDuplicates?: boolean }} draft
 */
export function resolvePhotoKeepModeFromDraft(draft) {
  var d = draft || {};
  var mode = String(d.photoKeepMode || "").trim().toLowerCase();
  if (mode === "recommended" || mode === "keep_bursts" || mode === "keep_all") {
    return mode;
  }
  // QFX D-QFX-05 / AC-12：cull=false 单独不足以上 keep_all
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
/** AC-PFM-14 · 作品集 + 快速仍两击（选夹 + 开始）；身份不加第三击。 */
export function wizardHitsToStart(mode, edition) {
  void normalizeEdition(edition);
  return String(mode || "quick_share") === "fine_craft" ? 3 : 2;
}

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

export function normalizeEdition(raw) {
  var t = String(raw || "").trim().toLowerCase();
  if (t === "portfolio" || t === "folio") return "portfolio";
  return "journal";
}

export function parsePortfolioPipelineConfig(studioCfg) {
  var raw = (studioCfg && (studioCfg.portfolioPipeline || studioCfg.portfolio_pipeline)) || {};
  var minKept = Number(raw.minKept != null ? raw.minKept : raw.min_kept);
  if (!(minKept > 0)) {
    minKept = raw.minKeptOverride != null ? Number(raw.minKeptOverride) : Number(raw.min_kept_override);
  }
  return {
    enabled: raw.enabled === true,
    homepageEntry: raw.homepageEntry === true || raw.homepage_entry === true,
    allowRefineSwitch: raw.allowRefineSwitch !== false && raw.allow_refine_switch !== false,
    maxPages: Number(raw.maxPages || raw.max_pages || 32),
    minKept: minKept > 0 ? minKept : 12,
  };
}

export function shouldShowEditionSegment(pipe) {
  return !!(pipe && pipe.enabled);
}

/** hydrate 完成前不要把作品集选择静默改回游记。 */
export function shouldResetEditionToJournal(pipe, hydrated) {
  return hydrated === true && !shouldShowEditionSegment(pipe);
}

export function shouldShowHomepagePortfolioEntry(pipe) {
  return !!(pipe && pipe.enabled && pipe.homepageEntry);
}

export function isPortfolioLowPhoto(count, minKept) {
  if (count == null || count === "") return false;
  var n = Number(count);
  if (!Number.isFinite(n)) return false;
  return n < Number(minKept || 12);
}

/** 线框 F1c · 作品集卡副文。低照片用短句，完整提示走确认模态。 */
export var PORTFOLIO_EDITION_SUBLINE = "杂志页";
export var PORTFOLIO_LOW_PHOTO_SUBLINE = "照片较少";

export function lowPhotoHint(minKept) {
  var n = Number(minKept);
  if (!(n > 0)) n = 12;
  return "照片较少，作品集更适合 " + n + " 张以上";
}

export function portfolioEditionSubline(low) {
  return low ? PORTFOLIO_LOW_PHOTO_SUBLINE : PORTFOLIO_EDITION_SUBLINE;
}

/**
 * 用户点作品集且张数低于派生阈值时，先确认再选中（不硬拒）。
 * 首页次链预选 / 恢复草稿不弹。
 */
export function shouldConfirmLowPhoto(count, minKept, source, currentEdition) {
  if (source !== "user") return false;
  if (normalizeEdition(currentEdition) === "portfolio") return false;
  return isPortfolioLowPhoto(count, minKept);
}

export function lowPhotoContinueConfirm(minKept) {
  return {
    title: "仍做作品集？",
    body: lowPhotoHint(minKept) + "。确认后仍可继续。",
    confirmText: "仍做作品集",
    cancelText: "取消",
  };
}
