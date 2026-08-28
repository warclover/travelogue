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
  var chips = raw.pageCountChipDetails || raw.page_count_chip_details || [];
  var ratio = Number(
    raw.keptEstimateRatio != null ? raw.keptEstimateRatio : raw.kept_estimate_ratio
  );
  if (!(ratio > 0) || ratio > 1) ratio = 0.67;
  return {
    enabled: raw.enabled === true,
    homepageEntry: raw.homepageEntry === true || raw.homepage_entry === true,
    allowRefineSwitch: raw.allowRefineSwitch !== false && raw.allow_refine_switch !== false,
    maxPages: Number(raw.maxPages || raw.max_pages || 32),
    minKept: minKept > 0 ? minKept : 12,
    keptEstimateRatio: ratio,
    pageCountChipDetails: Array.isArray(chips) ? chips : [],
  };
}

/** 详情「大约」：只说话，不进选档。 */
export function approxKeptSentence(folderCount, ratio) {
  var n = Number(folderCount);
  var r = Number(ratio);
  if (!(n > 0)) return "";
  if (!(r > 0) || r > 1) r = 0.67;
  var approx = Math.max(1, Math.round(n * r));
  return "生成后按实际上版张数定厚度；现在估计大约用上 " + approx + " 张";
}

/** 展示用：C ≥ N 的最薄档；全不够则最厚档。不进选档。 */
export function displayHintPages(folderCount, chips) {
  var n = Number(folderCount);
  var list = (Array.isArray(chips) ? chips : [])
    .map(function (row) {
      return {
        pages: Number(row && (row.pages || row.pageCount)),
        capacity: Number(row && row.capacity),
      };
    })
    .filter(function (row) {
      return row.pages > 0 && row.capacity > 0;
    });
  if (!(n > 0) || !list.length) return 0;
  var under = list.filter(function (row) {
    return row.capacity >= n;
  });
  if (under.length) {
    return under.reduce(function (a, b) {
      return a.capacity <= b.capacity ? a : b;
    }).pages;
  }
  return list.reduce(function (a, b) {
    return a.pages >= b.pages ? a : b;
  }).pages;
}

export function pageSpecSentence(folderCount, chips, selectedId) {
  var n = Number(folderCount);
  var sel = String(selectedId || "auto");
  if (sel !== "auto") {
    var pages = Number(sel);
    if (n > 0 && pages > 0) {
      return "文件夹 " + n + " 张，做成一本 " + pages + " 页。";
    }
    if (pages > 0) return "做成一本 " + pages + " 页。";
  }
  if (n > 0) {
    return "文件夹 " + n + " 张，系统会按能上版的张数自动选厚度。";
  }
  return "系统会按能上版的张数自动选厚度。";
}

function _tripHasIdentity(trip) {
  return !!(trip && (trip.title || trip.tripId || trip.edition));
}

function _tripTitle(trip) {
  return String((trip && trip.title) || "").replace(/\s+/g, " ").trim();
}

function _identityWord(edition) {
  return normalizeEdition(edition) === "portfolio" ? "作品集" : "游记";
}

function _otherEditionOf(edition, existingOther) {
  if (existingOther && existingOther.edition) {
    return normalizeEdition(existingOther.edition);
  }
  return normalizeEdition(edition) === "portfolio" ? "journal" : "portfolio";
}

/**
 * @param {"journal"|"portfolio"} edition
 * @param {{ title?: string, edition?: string, tripId?: string }|null|undefined} existingSelf
 * @param {{ title?: string, edition?: string, tripId?: string }|null|undefined} existingOther
 */
export function folderCollisionCopy(edition, existingSelf, existingOther) {
  var selfWord = _identityWord(edition);
  var otherWord = _identityWord(_otherEditionOf(edition, existingOther));
  var hasSelf = _tripHasIdentity(existingSelf);
  var hasOther = _tripHasIdentity(existingOther);
  var selfTitle = _tripTitle(existingSelf);
  var otherTitle = _tripTitle(existingOther);
  var sameTitle = !!(selfTitle && otherTitle && selfTitle === otherTitle);

  if (hasSelf && !hasOther) {
    if (selfTitle) {
      return (
        "这个文件夹已经做过" + selfWord + "《" + selfTitle +
        "》。继续会覆盖这本" + selfWord + "。"
      );
    }
    return "这个文件夹已经做过" + selfWord + "。继续会覆盖这本" + selfWord + "。";
  }
  if (hasSelf && hasOther) {
    if (sameTitle) {
      return (
        "这个文件夹已经做过" + selfWord +
        "。继续会覆盖这本" + selfWord +
        "，不会动书架上的" + otherWord + "那一本。"
      );
    }
    var selfBit = selfTitle ? selfWord + "《" + selfTitle + "》" : selfWord;
    var otherBit = otherTitle ? otherWord + "《" + otherTitle + "》" : otherWord + "那一本";
    return (
      "这个文件夹已经做过" + selfBit +
      "。继续会覆盖这本" + selfWord +
      "，不会动已有" + otherBit + "。"
    );
  }
  if (!hasSelf && hasOther) {
    var otherNamed = otherTitle ? otherWord + "《" + otherTitle + "》" : otherWord;
    return (
      "将新建一本" + selfWord +
      "，不会覆盖已有" + otherNamed +
      "。两本可以同时留在书架上。"
    );
  }
  return "";
}

/** 向导可见字（游记=HTML 默认冻结值；作品集=本波）。 */
export function wizardCopy(edition) {
  var pf = normalizeEdition(edition) === "portfolio";
  return {
    pickTitle: pf ? "制作一本作品集" : "制作我的影像画册",
    pickButton: pf ? "选择本次作品集的照片文件夹" : "选择照片文件夹",
    pickHint: pf
      ? "一本作品集一个文件夹，无需上传照片，隐私无忧"
      : "一本画册一个文件夹，无需上传照片，隐私无忧",
    firstTip: pf
      ? "选一次作品集的文件夹即可。不用先整理，也不用上传。"
      : "选一次旅行的照片文件夹即可。不用先整理，也不用上传。",
    folderHelpHtml: pf
      ? [
          "同一次作品集放同一文件夹（50–100 张最佳）",
          "Day1/Day2 子夹：合并导入或分两次导入（每次一本<strong>新</strong>作品集）",
          "支持 JPG / PNG / WebP / HEIC；不移动、不修改原片",
          "手机照片需先传到电脑",
        ]
      : [
          "同一次画册放同一文件夹（50–100 张最佳）",
          "Day1/Day2 子夹：合并导入或分两次导入（每次一本<strong>新</strong>画册）",
          "支持 JPG / PNG / WebP / HEIC；不移动、不修改原片",
          "手机照片需先传到电脑",
        ],
    confirmTitle: pf ? "确认作品集规格" : "确认并开始",
    verifyFoot: pf
      ? "制作时将自动去重与挑选 · 换文件夹可再做一本"
      : "制作时将自动去重与挑选 · 换文件夹可再做一篇",
    journalCardSubline: "推荐 · 发群",
    quickDesc: pf
      ? "按页编排，做完能点开翻。要发群请改选游记。"
      : "优先出微信长图，适合马上分享",
    fineTitle: pf ? "个性化定制" : "个性化定制画册",
    fineDesc: pf
      ? "输入书名等信息，定制更多细节"
      : "输入画册相关信息，定制更多细节",
    trust: pf
      ? "照片多时可能超过 10 分钟；可离开，做好了再回来。"
      : "根据不同照片数量（上限250张），生成画册耗时不同，通常需要1-8分钟",
    hideDemo: pf,
  };
}

/**
 * @param {{
 *   edition?: string,
 *   mode?: string,
 *   fineVisited?: boolean,
 *   uploading?: boolean,
 *   covering?: boolean
 * }} opts
 */
export function wizardStartLabel(opts) {
  var o = opts || {};
  if (o.uploading) return "开始上传";
  var pf = normalizeEdition(o.edition) === "portfolio";
  if (String(o.mode || "") === "fine_craft") {
    if (o.fineVisited) return pf ? "定制作品集细节 →" : "定制画册细节 →";
    return "填写细节 →";
  }
  if (pf && o.covering) return "覆盖并开始制作作品集";
  if (pf) return "开始制作作品集 →";
  return "开始制作 →";
}

/** WIZ-01 · 游记只说文件夹张数，不猜造 M/P/C。 */
export function wizardPhotoSummaryLine(n, opts) {
  opts = opts || {};
  var count = Number(n);
  if (!Number.isFinite(count) || count < 0) return "";
  var keepAll = String(opts.keepMode || "").toLowerCase() === "keep_all";
  if (keepAll) return "文件夹有 " + count + " 张，将全部保留进入制作。";
  if (normalizeEdition(opts.edition) === "portfolio") {
    return "文件夹有 " + count + " 张，系统会按能上版的张数自动选厚度。";
  }
  return "文件夹有 " + count + " 张。制作时会自动去重与挑选，成册张数以完成后为准。";
}

/** WIZ-01 · 张数弱建议，不阻断开始。 */
export function wizardCountHint(n) {
  var count = Number(n);
  if (!Number.isFinite(count)) return { bucket: "", text: "" };
  if (count < 4) return { bucket: "few", text: "照片偏少，成册可能较短" };
  if (count >= 50 && count <= 100) {
    return { bucket: "sweet", text: "50–100 张最合适，也可以继续" };
  }
  if (count > 300) return { bucket: "many", text: "照片较多，预计需要多几分钟" };
  return { bucket: "", text: "" };
}

export function shouldShowPageSpec(edition, pipe) {
  return normalizeEdition(edition) === "portfolio" && shouldShowEditionSegment(pipe);
}

export function buildPageCountFields(edition, selectedId) {
  if (normalizeEdition(edition) !== "portfolio") return {};
  var id = String(selectedId || "auto");
  if (id === "auto") return { pageCountSource: "auto" };
  var n = Number(id);
  if (!(n > 0)) return { pageCountSource: "auto" };
  return { pageCount: n, pageCountSource: "user" };
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
export var PORTFOLIO_EDITION_SUBLINE = "可翻的一本";
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
