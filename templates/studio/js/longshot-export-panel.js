// @ts-nocheck
/**
 * Travelogue Studio · Longshot 2.0 export settings panel (D-LNG2-28).
 * Popover UI lives here — keep preview-toolbar.js thin.
 */
"use strict";

import { HELP_COPY } from "./help-onboarding.js";
import {
  buildIntentPresetHtml,
  defaultPlatformForIntent,
  intentForPlatform,
} from "./export-preset-facade.js";
import {
  albumSpreadCardCopy,
  crossingGateCopy,
  crossingGateSheetModel,
  isCrossingLongshotLocked,
  isPortfolioSocialExportFace,
  nextCrossingDefaultPlatform,
  portfolioExportDefaultFaceHtml,
  wrapJournalPanelAsPortfolioSocialFace,
} from "./portfolio-export-logic.js";

export var LONGSHOT_EXPORT_PREFS_KEY = "travelogue.studio.longshotExportPrefs";
export var MOMENTS_COACH_KEY = "travelogue.studio.longshotMomentsCoachSeen";

export var PLATFORMS = {
  wechat_chat: {
    id: "wechat_chat",
    label: "微信群",
    title: "微信群",
    subtitle: "按序长图",
    cta: "导出长图 · 发微信群",
    showSegmentMode: true,
    copyLabel: "微信群长图 · 要不要字",
    expectHtml:
      "将导出<strong>可按序发群</strong>的长图；可选按章分开或一整张 · 预计视册厚而定",
  },
  wechat_moments: {
    id: "wechat_moments",
    label: "朋友圈 · 长图连读",
    title: "朋友圈",
    subtitle: "长图连读",
    cta: "导出朋友圈 · 长图连读",
    showSegmentMode: false,
    copyLabel: "朋友圈长图 · 要不要字",
    expectHtml:
      "将按完整画册切成 <strong>1–9 段</strong>长图连读（滑动连读）· 预计 30–60 秒",
  },
  poster_bric: {
    id: "poster_bric",
    label: "单张海报 · 3:4",
    title: "单张海报",
    subtitle: "3:4",
    cta: "导出单张海报",
    showSegmentMode: false,
    showCopyControls: false,
    expectHtml:
      "将导出 <strong>1 张 3:4</strong> 竖版拼贴海报（1–6 张代表性精选照片）",
  },
  xiaohongshu: {
    id: "xiaohongshu",
    label: "小红书 · 竖版海报",
    title: "小红书",
    subtitle: "3:4 海报",
    cta: "导出小红书海报",
    showSegmentMode: false,
    showXhsOptions: true,
    // 拼贴出口：用「文案包」，不用长图「要不要字」
    showCopyControls: false,
    expectHtml:
      "将生成 <strong>N 张 3:4 竖版拼贴海报</strong>（非杂志截屏）· auto 约 3–9 张",
  },
  // 导出形式与小红书一致（同一套 3:4 Card 拼贴管线），仅文案/发布场景不同。
  wechat_official: {
    id: "wechat_official",
    label: "公众号 · 图文配图",
    title: "公众号",
    subtitle: "3:4 配图",
    cta: "导出公众号配图",
    showSegmentMode: false,
    showXhsOptions: true,
    showCopyControls: false,
    expectHtml:
      "将生成 <strong>N 张 3:4 竖版拼贴配图</strong>（非杂志截屏）· auto 约 3–9 张 · 可依次插入图文正文",
  },
  album_spread: {
    id: "album_spread",
    label: "画册印刷",
    title: "画册印刷",
    subtitle: "跨页",
    cta: "导出画册跨页",
    showSegmentMode: false,
    showCopyControls: false,
    showAlbumCountOptions: true,
    expectHtml:
      "将导出多张 <strong>两卡跨页</strong>拼贴（3:4+3:4+中缝，约 1.53:1，适合印刷 / 对页预览）。精选照片较多时可能需 <strong>1–2 分钟</strong>，请耐心等待",
  },
  portfolio_pages: {
    id: "portfolio_pages",
    label: "作品集页图",
    title: "作品集",
    subtitle: "这一本 + 页图",
    cta: "导出作品集",
    showSegmentMode: false,
    showCopyControls: false,
    expectHtml: "将导出可翻阅的一本与 16:9 页图序列",
  },
};

/**
 * @param {object} [cfgStudio] studio.longshot2 from GET /config
 */
export function enabledPlatformsFromConfig(cfgStudio) {
  var l2 = (cfgStudio && cfgStudio.longshot2) || {};
  if (l2.enabled === false) return ["wechat_chat"];
  var list = Array.isArray(l2.platforms)
    ? l2.platforms.slice()
    : ["wechat_moments", "xiaohongshu", "wechat_official", "poster_bric", "album_spread"];
  // Compose 出口默认开放；gcs 关闭时可杀停 poster_bric
  var gcs =
    (cfgStudio && (cfgStudio.gcsPosterBric || cfgStudio.gcs_poster_bric)) || {};
  if (gcs.enabled !== false && list.indexOf("poster_bric") < 0) {
    list = list.concat(["poster_bric"]);
  }
  if (list.indexOf("album_spread") < 0) {
    list = list.concat(["album_spread"]);
  }
  var out = ["wechat_chat"];
  list.forEach(function (id) {
    // Studio 下线九宫格；CLI 仍可走 moments_grid
    if (id === "moments_grid") return;
    if (id && id !== "wechat_chat" && out.indexOf(id) < 0) {
      if (
        id === "wechat_moments" ||
        id === "xiaohongshu" ||
        id === "wechat_official" ||
        id === "poster_bric" ||
        id === "album_spread"
      ) {
        out.push(id);
      }
    }
  });
  return out;
}

export function estimateXhsAutoCount(photoCount) {
  var n = Number(photoCount) || 0;
  var n0 = Math.max(1, Math.ceil(n / 4));
  var out;
  if (n < 12) out = Math.max(3, Math.min(n0, 6));
  else {
    out = Math.max(5, Math.min(n0, 9));
    if (n > 48) out = Math.min(out, 10);
  }
  return out;
}

/** FE-LNG2-20 · D-LNG2-04 · clamp user slideCount to profile 1–18. */
export var XHS_SLIDE_COUNT_MIN = 1;
export var XHS_SLIDE_COUNT_MAX = 18;

/** Compose / Slice 清晰度提示（按平台真实画布，而非一律 428×scale） */
export function scaleHintForPlatform(platformId, scale) {
  var s = scale === 3 ? 3 : 2;
  if (platformId === "poster_bric") {
    var aw = s > 2 ? Math.round(1080 * 1.25) : 1080;
    var ah = s > 2 ? Math.round(1440 * 1.25) : 1440;
    return "3:4 画布约 " + aw + "×" + ah + "px";
  }
  if (platformId === "xiaohongshu" || platformId === "wechat_official") {
    var xw = s > 2 ? Math.round(1080 * 1.25) : 1080;
    var xh = s > 2 ? Math.round(1440 * 1.25) : 1440;
    return "竖版海报约 " + xw + "×" + xh + "px（3:4）";
  }
  if (platformId === "album_spread") {
    var sw = s > 2 ? Math.round(2208 * 1.25) : 2208;
    var sh = s > 2 ? Math.round(1440 * 1.25) : 1440;
    return "画册跨页约 " + sw + "×" + sh + "px（1.53:1）";
  }
  if (platformId === "wechat_moments") {
    var mw = s === 3 ? 1284 : 856;
    return "长图切片宽约 " + mw + "px（428×" + s + "）";
  }
  var px = s === 3 ? 1284 : 856;
  return "输出宽约 " + px + "px（逻辑宽 428 × " + s + "）";
}
export var XHS_PRESET_COUNTS = { "6": true, "9": true, "12": true };
//: 2026-08-05 bugfix · must NOT collide with any XHS_PRESET_COUNTS value —
//: it's reused as the "自定义" seed whenever the current slideCount is
//: null/a preset, and the custom row's visibility is inferred purely from
//: "value is not a preset" (see isXhsPresetCount below).
export var XHS_CUSTOM_DEFAULT = 8;

export function clampXhsSlideCount(value) {
  var n = parseInt(value, 10);
  if (!isFinite(n)) return null;
  return Math.max(XHS_SLIDE_COUNT_MIN, Math.min(XHS_SLIDE_COUNT_MAX, n));
}

export function isXhsPresetCount(slideCount) {
  return slideCount != null && !!XHS_PRESET_COUNTS[String(slideCount)];
}

/**
 * 2026-08-05 bugfix · seed value used when the user clicks 张数「自定义」.
 * MUST resolve to a non-preset value, or `isXhsPresetCount()` reclassifies
 * it as a preset on the very next `syncPanelUI` and the custom row/input
 * never appears — clicking "自定义" then looks like a dead button.
 */
export function resolveXhsCustomSeed(currentSlideCount) {
  var prev = clampXhsSlideCount(currentSlideCount);
  return prev != null && !isXhsPresetCount(prev) ? prev : XHS_CUSTOM_DEFAULT;
}

/**
 * P2 · 画册跨页数（mirrors 小红书张数控件；单位是「跨页」而非「张」— 一跨页
 * ≈两张 3:4 卡，见 collage_pack.py `_album_target_per_card`）。
 * 上限对齐 `config/platform_profiles.yaml` album_spread.output.max_pages。
 * 印刷友好：快捷预设为 4 的倍数；自动模式见 ``estimateAlbumAutoCount`` /
 * 后端 ``resolve_album_slide_count``。
 */
export var ALBUM_SLIDE_COUNT_MIN = 1;
export var ALBUM_SLIDE_COUNT_MAX = 30;
export var ALBUM_PRESET_COUNTS = { "4": true, "8": true, "12": true, "16": true };
/** 旧版 3/6/9 预设 → 最近印刷档，打开画册面板时迁移。 */
export var ALBUM_LEGACY_PRESET_MIGRATE = { "3": 4, "6": 8, "9": 12 };
//: 2026-08-05 bugfix (user report: 画册「自定义」点击无反应) · must NOT
//: collide with any ALBUM_PRESET_COUNTS value — see XHS_CUSTOM_DEFAULT above
//: for why. The old code reused `6` here, which *is* an album preset, so
//: clicking "自定义" always re-resolved back to the "6" preset button and
//: the custom input never appeared. 5 仍不在 4/8/12/16 内，可继续当种子。
export var ALBUM_CUSTOM_DEFAULT = 5;

/**
 * 画册自动跨页数 · 与后端 ``resolve_album_slide_count`` 对齐：
 * ~8 张/跨页估算，原始估算 ≥3 时向上取整到 4 的倍数；小本保持 1–2。
 */
export function estimateAlbumAutoCount(photoCount) {
  var n = Number(photoCount) || 0;
  var n0 = n > 0 ? Math.max(1, Math.ceil(n / 8)) : 1;
  if (n0 < 3) return n0;
  var maxQuantum = Math.max(4, Math.floor(ALBUM_SLIDE_COUNT_MAX / 4) * 4);
  var out = Math.ceil(n0 / 4) * 4;
  return Math.max(4, Math.min(out, maxQuantum, ALBUM_SLIDE_COUNT_MAX));
}

export function clampAlbumSlideCount(value) {
  var n = parseInt(value, 10);
  if (!isFinite(n)) return null;
  return Math.max(ALBUM_SLIDE_COUNT_MIN, Math.min(ALBUM_SLIDE_COUNT_MAX, n));
}

export function isAlbumPresetCount(slideCount) {
  return slideCount != null && !!ALBUM_PRESET_COUNTS[String(slideCount)];
}

/** 旧快捷档 3/6/9 → 4/8/12；其它值原样夹取。 */
export function migrateAlbumLegacyPreset(slideCount) {
  if (slideCount == null) return null;
  var mapped = ALBUM_LEGACY_PRESET_MIGRATE[String(slideCount)];
  if (mapped != null) return mapped;
  return clampAlbumSlideCount(slideCount);
}

/**
 * 2026-08-05 bugfix (user report: 画册模式导出，无法选择自定义张数) · seed
 * value used when the user clicks 跨页数「自定义」. Same contract as
 * resolveXhsCustomSeed above: MUST resolve to a non-preset value. The old
 * inline fallback (`6`) was itself an ALBUM_PRESET_COUNTS member, so this
 * previously failed unconditionally — every click on "自定义" re-resolved
 * back to the "6" preset and the custom input never appeared.
 */
export function resolveAlbumCustomSeed(currentSlideCount) {
  var prev = clampAlbumSlideCount(currentSlideCount);
  return prev != null && !isAlbumPresetCount(prev) ? prev : ALBUM_CUSTOM_DEFAULT;
}

/** 与 confirmed/draft platform 联动的通用 slideCount 夹取（张数 vs 跨页数）。 */
export function clampSlideCountForPlatform(platformId, value) {
  return platformId === "album_spread"
    ? clampAlbumSlideCount(value)
    : clampXhsSlideCount(value);
}

export function isSmartCropUiEnabled(cfgStudio) {
  var l2 = (cfgStudio && cfgStudio.longshot2) || {};
  var sc = l2.smartCrop || l2.smart_crop || {};
  return sc.enabled === true;
}

/**
 * PRD-BATCH-EXPORT-MULTISELECT-V1 · 多选批量导出（Stage 2 MVP，D-BEX-01）。
 *
 * `platforms` 是勾选态的真实来源（可 1..N 个）；`platform`（单值）作为向后
 * 兼容字段继续保留 = `platforms[0]`，供仍按单平台假设写的旧调用点使用
 * （output-recipe intent 映射、标题风险门禁、sparse-moments 提示等——这些
 * 只对"主平台"生效，是 v1 的有意简化，未纳入 PRD 正式验收范围）。
 *
 * MVP 范围收窄（用户 2026-08-06 确认）：勾选 2 个及以上平台时，**不**提供
 * 手风琴式逐平台设置（张数/跨页数/分段模式）——批量场景下所有平台统一走
 * 自动/默认设置；需要自定义张数请单选该平台单独导出。真正的"每平台独立
 * 设置"留作后续迭代（对应 PRD D-BEX-01 的完整版）。
 */
/**
 * Retired Studio ids still seen in localStorage. Do not map them to
 * album_spread — that hijacked the folio main button onto 3:4 print.
 * Journal unknown/retired ids fall back to wechat_chat (长图).
 */
export var RETIRED_ALBUM_PLATFORM_IDS = {
  album_landscape: true,
  album: true,
  album_print: true,
};

export function canonicalizePlatformId(id) {
  var s = String(id || "").trim();
  if (!s) return "";
  if (RETIRED_ALBUM_PLATFORM_IDS[s]) return "wechat_chat";
  return s;
}

export function normalizePlatformList(list, fallback) {
  var out = [];
  (Array.isArray(list) ? list : []).forEach(function (id) {
    var s = canonicalizePlatformId(id);
    if (s && out.indexOf(s) < 0) out.push(s);
  });
  if (!out.length) out.push(canonicalizePlatformId(fallback) || "wechat_chat");
  return out;
}

export function readExportPrefs() {
  var defaults = {
    platform: "wechat_chat",
    platforms: ["wechat_chat"],
    mode: "chapter",
    scale: 2,
    slideCount: null,
    padMode: "letterbox",
    includeAppendix: false,
    density: "default",
    userConfirmed: false,
  };
  try {
    var raw = localStorage.getItem(LONGSHOT_EXPORT_PREFS_KEY);
    if (!raw) return defaults;
    var parsed = JSON.parse(raw);
    var platform = canonicalizePlatformId(parsed.platform || defaults.platform);
    var platforms = normalizePlatformList(parsed.platforms, platform);
    if (platforms.indexOf(platform) < 0) platform = platforms[0];
    return {
      platform: platform,
      platforms: platforms,
      mode: parsed.mode === "full" || parsed.mode === "chapter" ? parsed.mode : "chapter",
      scale: parsed.scale === 3 ? 3 : 2,
      slideCount:
        parsed.slideCount == null
          ? null
          : clampSlideCountForPlatform(platform, parsed.slideCount),
      padMode: parsed.padMode || "letterbox",
      includeAppendix: parsed.includeAppendix === true,
      density: parsed.density === "compact" ? "compact" : "default",
      userConfirmed: parsed.userConfirmed === true,
    };
  } catch (e) {
    return defaults;
  }
}

/**
 * AC-DFX-01/02 · 用户已确认过导出目标（含重启后 localStorage 残留）。
 * 未确认时才允许 Output Recipe 按册厚猜微信长图。
 *
 * 存量 prefs 没有 userConfirmed：非默认微信群、或多选，视为已确认。
 */
export function isConfirmedExportTarget(prefs) {
  if (!prefs || typeof prefs !== "object") return false;
  if (prefs.userConfirmed === true) return true;
  if (Array.isArray(prefs.platforms) && prefs.platforms.length > 1) return true;
  var platform = String(prefs.platform || "");
  return !!(platform && platform !== "wechat_chat");
}

export function writeExportPrefs(prefs) {
  try {
    localStorage.setItem(LONGSHOT_EXPORT_PREFS_KEY, JSON.stringify(prefs));
  } catch (e) {}
}

export function ctaLabelForPlatform(platformId) {
  var p = PLATFORMS[platformId] || PLATFORMS.wechat_chat;
  return p.cta;
}

function _platformTitle(platformId) {
  var p = PLATFORMS[platformId];
  return (p && (p.title || p.label)) || platformId || "导出";
}

/**
 * 批量态 CTA 文案（G-BEX-01 + SNR D-SNR-11）· 单选与单平台文案一致；
 * 多选用人话「导出 · {主平台}等 N 项」，禁止孤立「N 个模式」作主文案。
 */
export function ctaLabelForPlatforms(platformIds) {
  var ids = normalizePlatformList(platformIds);
  if (ids.length <= 1) return ctaLabelForPlatform(ids[0]);
  return "导出 · " + _platformTitle(ids[0]) + "等 " + ids.length + " 项";
}

/** Dock / 窄栏短标签（AC-DFX-02 · 含 compose 出口，禁止回落到「发微信群」） */
export function shortCtaLabelForPlatform(platformId) {
  // SNR COPY-SNR-C* · 短标签带平台名（对齐「导出小红书」）；禁裸「连读/按章」
  if (platformId === "wechat_moments") return "导出朋友圈";
  if (platformId === "xiaohongshu") return "导出小红书";
  if (platformId === "wechat_official") return "导出公众号";
  if (platformId === "poster_bric") return "导出海报";
  if (platformId === "album_spread") return "导出画册";
  if (platformId === "portfolio_pages") return "导出作品集";
  return "长图";
}

/** 批量态窄栏短标签 · 单选时与单平台文案完全一致（零回归）。 */
export function shortCtaLabelForPlatforms(platformIds) {
  var ids = normalizePlatformList(platformIds);
  if (ids.length <= 1) return shortCtaLabelForPlatform(ids[0]);
  return _platformTitle(ids[0]) + "等" + ids.length + "项";
}

/**
 * 导出进度 · Task Dock 第一行标题（P0 · 禁止对 Compose 平台回落到「微信」文案）
 * 与 `shortCtaLabelForPlatform` 同源分流，但用于进行中态而非按钮标签。
 */
export var PROGRESS_TITLES = {
  wechat_chat: "正在生成可发微信的长图…",
  wechat_moments: "正在生成朋友圈长图…",
  moments_grid: "正在生成拼贴导出…",
  xiaohongshu: "正在生成小红书竖版拼贴…",
  wechat_official: "正在生成公众号竖版拼贴…",
  poster_bric: "正在生成 3:4 单张海报…",
  album_spread: "正在生成画册跨页，照片较多时请耐心等待…",
  portfolio_pages: "正在导出作品集…",
};

/** Compose 引擎出口（3:4 卡片管线）· 与 Slice/长图区分文案与副标题语义 */
export var COMPOSE_PLATFORMS = {
  xiaohongshu: true,
  wechat_official: true,
  poster_bric: true,
  album_spread: true,
};

export function isComposePlatform(platformId) {
  return COMPOSE_PLATFORMS[platformId] === true;
}

export function progressTitleForPlatform(platformId) {
  return PROGRESS_TITLES[platformId] || PROGRESS_TITLES.wechat_chat;
}

export function progressSynthesizingTitleForPlatform(platformId) {
  if (platformId === "portfolio_pages") return "正在保存这一本与页图…";
  return isComposePlatform(platformId) ? "正在合成拼贴…" : "正在合成长图…";
}

/**
 * 进度第二行。作品集只走页图语义；游记微信群 / 拼贴文案保持原样。
 * @param {string} platformId
 * @param {{ quality?: string, mode?: string }} [opts]
 */
export function progressSubtitleForPlatform(platformId, opts) {
  opts = opts || {};
  var quality = opts.quality || "高清";
  var mode = opts.mode || "chapter";
  if (platformId === "portfolio_pages") return "16:9 页图 · " + quality;
  if (isComposePlatform(platformId)) return "3:4 拼贴 · " + quality;
  if (platformId === "wechat_moments") return "长图连读 · " + quality;
  if (platformId === "wechat_chat") {
    return (mode === "full" ? "一整张发群" : "按章发群") + " · " + quality;
  }
  return quality;
}

/**
 * 从后端/排队阶段的自由文本 hint 里识别平台（比 localStorage prefs 更即时，
 * 用于 resume / stageHint 场景下 prefs 可能滞后的兜底），识别不到返回 null。
 */
export function detectPlatformFromProgressHint(hint) {
  var text = String(hint || "");
  if (/作品集|页图|这一本/.test(text)) return "portfolio_pages";
  if (/小红书/.test(text)) return "xiaohongshu";
  if (/公众号/.test(text)) return "wechat_official";
  if (/画册|跨页/.test(text)) return "album_spread";
  if (/单(张|屏)海报/.test(text)) return "poster_bric";
  if (/朋友圈|连读/.test(text)) return "wechat_moments";
  if (/九宫格/.test(text)) return "moments_grid";
  return null;
}

/** 摘要尾句 · 各模式共用（按钮文案随模式变，指引固定指右上角 CTA） */
var EXPORT_SUMMARY_CTA_HINT = "点「长图」开始导出";

function _withExportCtaHint(line) {
  return String(line || "") + " · " + EXPORT_SUMMARY_CTA_HINT;
}

/** 设置入口摘要 · 「当前将导出：…」 */
export function confirmedExportSummary(platformId) {
  var p = PLATFORMS[platformId] || PLATFORMS.wechat_chat;
  return _withExportCtaHint("当前将导出：" + (p.label || p.title || platformId));
}

/**
 * 摘要行：draft 与 confirmed 不一致时提示「未确定」，避免误以为已切换平台。
 * @param {string} confirmedPlatform
 * @param {string} [draftPlatform]
 */
export function exportSummaryLine(confirmedPlatform, draftPlatform) {
  var confirmed = confirmedPlatform || "wechat_chat";
  var draft = draftPlatform || confirmed;
  var confirmedLabel =
    (PLATFORMS[confirmed] && (PLATFORMS[confirmed].label || PLATFORMS[confirmed].title)) ||
    confirmed;
  if (draft === confirmed) {
    return _withExportCtaHint("当前将导出：" + confirmedLabel);
  }
  var draftLabel =
    (PLATFORMS[draft] && (PLATFORMS[draft].label || PLATFORMS[draft].title)) || draft;
  return _withExportCtaHint("已改选：" + draftLabel + "（点「确定」后生效）");
}

function _platformLabel(id) {
  return (PLATFORMS[id] && (PLATFORMS[id].label || PLATFORMS[id].title)) || id;
}

/** 摘要行的多选变体（confirmed/draft 均为 platforms 数组）。 */
export function exportSummaryLineForPlatforms(confirmedPlatforms, draftPlatforms) {
  var confirmed = normalizePlatformList(confirmedPlatforms);
  var draft = draftPlatforms && draftPlatforms.length ? normalizePlatformList(draftPlatforms) : confirmed;
  if (confirmed.length <= 1 && draft.length <= 1) {
    return exportSummaryLine(confirmed[0], draft[0]);
  }
  var same =
    confirmed.length === draft.length &&
    confirmed.every(function (id) {
      return draft.indexOf(id) >= 0;
    });
  var draftLabel =
    draft.length <= 1 ? _platformLabel(draft[0]) : draft.length + " 个模式（" + draft.map(_platformLabel).join("、") + "）";
  if (same) {
    return _withExportCtaHint("当前将导出：" + draftLabel);
  }
  return _withExportCtaHint("已改选：" + draftLabel + "（点「确定」后生效）");
}

export function shouldShowMomentsCoach() {
  try {
    // 与帮助系统 T-PLATFORM-PICK 同周期（D-HELP / AC-HELP-08）
    if (localStorage.getItem("travelogue.studio.help.platformPickSeen") === "1") {
      return false;
    }
    return localStorage.getItem(MOMENTS_COACH_KEY) !== "1";
  } catch (e) {
    return true;
  }
}

export function markMomentsCoachSeen() {
  try {
    localStorage.setItem(MOMENTS_COACH_KEY, "1");
    localStorage.setItem("travelogue.studio.help.platformPickSeen", "1");
  } catch (e) {}
}

/** D-LNG2-17 · photos < 15 → suggest wechat_chat (non-blocking). */
export var SPARSE_MOMENTS_PHOTO_THRESHOLD = 15;

export function shouldHintSparseMoments(photoCount) {
  var n = Number(photoCount);
  return isFinite(n) && n > 0 && n < SPARSE_MOMENTS_PHOTO_THRESHOLD;
}

export function sparseMomentsHintMessage() {
  return "照片较少，朋友圈配图可能偏短；建议改用微信群长图。";
}

/** Best-effort photo count from preview / longshot DOM. */
export function estimatePhotoCountFromDom(doc) {
  doc = doc || (typeof document !== "undefined" ? document : null);
  if (!doc) return 0;
  var slots = doc.querySelectorAll(
    ".layout-slot__img, .media-card img, .media-card__visual, [data-block='media-card']"
  );
  if (slots.length) return slots.length;
  var imgs = doc.querySelectorAll("main img");
  return imgs.length;
}

/**
 * Build popover inner HTML for enabled platforms.
 * @param {string[]} platformIds
 * @param {{edition?: string}} [opts] 作品集 edition=portfolio 时换种分享默认折叠
 */
/** FE-PFM-06 · 游记 Dock / ▾ 快照。开旗与否不改变游记字面。 */
export function journalDockChrome() {
  return { short: "长图", aria: "导出长图" };
}

export function journalExportPanelSnapshot(platformIds) {
  return {
    dock: journalDockChrome(),
    title: "导出设置",
    html: buildPanelHtml(platformIds, { edition: "journal" }),
  };
}

export function buildPanelHtml(platformIds, opts) {
  opts = opts || {};
  var edition = opts.edition === "portfolio" ? "portfolio" : "journal";
  var face = opts.face === "social" ? "social" : "default";
  if (edition === "portfolio" && face === "social") {
    return wrapJournalPanelAsPortfolioSocialFace(
      buildPanelHtml(platformIds, { edition: "journal", intentFacade: false })
    );
  }
  if (edition === "portfolio") {
    return portfolioExportDefaultFaceHtml(opts.product);
  }
  var ids = platformIds && platformIds.length ? platformIds : ["wechat_chat", "wechat_moments"];
  var socialIds = ids.filter(function (id) {
    return id && id !== "portfolio_pages";
  });
  var platformBtns = socialIds
    .map(function (id) {
      var p = PLATFORMS[id] || { id: id, label: id };
      var title = p.title || p.label || id;
      var sub = p.subtitle || "";
      var aria = p.label || title;
      var extraClass = "";
      if (id === "album_spread") {
        var albumCopy = albumSpreadCardCopy(edition);
        title = albumCopy.title;
        sub = albumCopy.subtitle;
        aria = albumCopy.aria;
        if (edition === "portfolio") extraClass = " preview-toolbar__export-platform-card--stack";
      }
      return (
        '<button type="button" class="preview-toolbar__export-platform-card' +
        extraClass +
        '" ' +
        'data-studio-longshot-platform="' +
        p.id +
        '" aria-label="' +
        aria +
        '">' +
        '<span class="preview-toolbar__export-platform-card__title">' +
        title +
        "</span>" +
        (sub
          ? '<span class="preview-toolbar__export-platform-card__sub">' +
            sub +
            "</span>"
          : "") +
        "</button>"
      );
    })
    .join("");

  var platformGrid =
    '<div class="preview-toolbar__export-platform-grid" role="group" aria-label="按渠道导出（点击可多选）">' +
    platformBtns +
    "</div>" +
    '<p class="preview-toolbar__export-batch-hint" data-batch-hint hidden></p>';
  var platformField =
    opts.intentFacade === false
      ? '<div class="preview-toolbar__export-popover-field" data-field="platform">' +
        '<span class="preview-toolbar__export-popover-label">导出模式（用途） · 点击可多选</span>' +
        platformGrid +
        "</div>"
      : '<div class="preview-toolbar__export-popover-field" data-field="intent">' +
        '<span class="preview-toolbar__export-popover-label">这次要做什么</span>' +
        buildIntentPresetHtml() +
        "</div>" +
        '<details class="preview-toolbar__export-advanced" data-field="platform">' +
        "<summary>高级 · 按渠道导出</summary>" +
        platformGrid +
        "</details>";

  return (
    '<p class="preview-toolbar__export-popover-title">' +
    "导出设置" +
    "</p>" +
    '<p class="preview-toolbar__export-popover-note">选好用途后点「确定」，再点「长图」开始导出。</p>' +
    '<p class="preview-toolbar__export-confirmed-summary" data-export-confirmed-summary aria-live="polite"></p>' +
    '<div class="preview-toolbar__export-popover-body">' +
    platformField +
    '<div class="preview-toolbar__export-popover-field preview-toolbar__export-copy-field" data-field="copy">' +
    '<span class="preview-toolbar__export-popover-label" data-copy-label>长图要不要字</span>' +
    '<div class="preview-toolbar__export-popover-seg" role="group" data-copy-preset-seg>' +
    '<button type="button" data-copy-preset="photos">纯照片</button>' +
    '<button type="button" data-copy-preset="full">带文字</button>' +
    "</div>" +
    '<div class="preview-toolbar__export-copy-chips">' +
    '<button type="button" class="preview-toolbar__export-copy-chip" data-preview-chip="caption">图注</button>' +
    '<button type="button" class="preview-toolbar__export-copy-chip" data-preview-chip="narrative">导语</button>' +
    "</div>" +
    '<p class="preview-toolbar__export-copy-hint">改动会同步预览；导出长图按此出图。</p>' +
    "</div>" +
    '<div class="preview-toolbar__export-popover-field" data-field="mode">' +
    '<span class="preview-toolbar__export-popover-label">导出范围</span>' +
    '<div class="preview-toolbar__export-popover-seg" role="group">' +
    '<button type="button" data-studio-longshot-mode="chapter">按章分开</button>' +
    '<button type="button" data-studio-longshot-mode="full">一整张</button>' +
    "</div></div>" +
    '<div class="preview-toolbar__export-popover-field" data-field="xhs-count" hidden>' +
    '<span class="preview-toolbar__export-popover-label">张数</span>' +
    '<div class="preview-toolbar__export-popover-seg" role="group" data-xhs-count-seg>' +
    '<button type="button" data-studio-xhs-count="auto">自动</button>' +
    '<button type="button" data-studio-xhs-count="6">6</button>' +
    '<button type="button" data-studio-xhs-count="9">9</button>' +
    '<button type="button" data-studio-xhs-count="12">12</button>' +
    '<button type="button" data-studio-xhs-count="custom">自定义</button>' +
    "</div>" +
    '<div class="preview-toolbar__export-xhs-custom" data-xhs-custom-row hidden>' +
    '<label class="preview-toolbar__export-xhs-custom-label">' +
    '<span>张数（1–18）</span>' +
    '<input type="number" min="1" max="18" step="1" inputmode="numeric" ' +
    'data-studio-xhs-custom-input class="preview-toolbar__export-xhs-custom-input" />' +
    "</label></div>" +
    '<p class="preview-toolbar__export-xhs-estimate" data-xhs-estimate hidden></p>' +
    "</div>" +
    '<div class="preview-toolbar__export-popover-field" data-field="album-count" hidden>' +
    '<span class="preview-toolbar__export-popover-label">跨页数</span>' +
    '<div class="preview-toolbar__export-popover-seg" role="group" data-album-count-seg>' +
    '<button type="button" data-studio-album-count="auto">自动</button>' +
    '<button type="button" data-studio-album-count="4">4</button>' +
    '<button type="button" data-studio-album-count="8">8</button>' +
    '<button type="button" data-studio-album-count="12">12</button>' +
    '<button type="button" data-studio-album-count="16">16</button>' +
    '<button type="button" data-studio-album-count="custom">自定义</button>' +
    "</div>" +
    '<div class="preview-toolbar__export-xhs-custom" data-album-custom-row hidden>' +
    '<label class="preview-toolbar__export-xhs-custom-label">' +
    '<span>跨页数（1–30）</span>' +
    '<input type="number" min="1" max="30" step="1" inputmode="numeric" ' +
    'data-studio-album-custom-input class="preview-toolbar__export-xhs-custom-input" />' +
    "</label></div>" +
    '<p class="preview-toolbar__export-xhs-estimate" data-album-estimate hidden></p>' +
    "</div>" +
    '<div class="preview-toolbar__export-popover-field" data-field="xhs-pad" hidden>' +
    '<span class="preview-toolbar__export-popover-label">填充</span>' +
    '<div class="preview-toolbar__export-popover-seg" role="group">' +
    '<button type="button" data-studio-xhs-pad="letterbox">留白边</button>' +
    '<button type="button" data-studio-xhs-pad="smart_crop" data-smart-crop-btn>智能裁切</button>' +
    "</div></div>" +
    '<div class="preview-toolbar__export-popover-field" data-field="xhs-copy-pack" hidden>' +
    '<span class="preview-toolbar__export-popover-label">文案包</span>' +
    '<div class="preview-toolbar__export-copy-pack-row">' +
    '<button type="button" class="preview-toolbar__export-copy-pack-btn" data-action="copy-xhs-pack">复制文案包</button>' +
    '<button type="button" class="preview-toolbar__export-copy-pack-btn preview-toolbar__export-copy-pack-btn--ghost" data-action="copy-xhs-pack-titles" hidden>仅标题和话题</button>' +
    "</div>" +
    '<p class="preview-toolbar__export-xhs-copy-hint" data-xhs-copy-hint>' +
    "标题和话题已备好 · 正文可粘贴后自填" +
    "</p>" +
    '<p class="preview-toolbar__export-xhs-copy-upgrade" data-xhs-copy-upgrade hidden>' +
    '<button type="button" class="preview-toolbar__export-xhs-upgrade-link" data-action="snr-upgrade-copy">生成杂志感后可带正文</button>' +
    "</p></div>" +
    '<div class="preview-toolbar__export-popover-field" data-field="scale">' +
    '<span class="preview-toolbar__export-popover-label">清晰度</span>' +
    '<div class="preview-toolbar__export-popover-seg" role="group">' +
    '<button type="button" data-studio-longshot-scale="2" title="标准清晰度">标准</button>' +
    '<button type="button" data-studio-longshot-scale="3" title="更高清晰度">更清晰</button>' +
    "</div>" +
    '<p class="preview-toolbar__export-scale-hint" data-scale-hint>输出尺寸随导出目标变化</p>' +
    "</div>" +
    '<div class="preview-toolbar__export-popover-field" data-field="density"' +
    (edition === "portfolio" ? " hidden" : "") +
    ">" +
    '<span class="preview-toolbar__export-popover-label">长图密度</span>' +
    '<div class="preview-toolbar__export-popover-seg" role="group">' +
    '<button type="button" data-studio-longshot-density="default">默认</button>' +
    '<button type="button" data-studio-longshot-density="compact">紧凑</button>' +
    "</div>" +
    '<p class="preview-toolbar__export-density-hint">切换后点确定将更新版面。</p>' +
    "</div>" +
    '<div class="preview-toolbar__export-popover-field" data-field="appendix" hidden>' +
    '<label class="preview-toolbar__export-appendix">' +
    '<input type="checkbox" data-studio-include-appendix />' +
    '<span data-appendix-label>未含 · 往年旧照</span>' +
    "</label>" +
    '<p class="preview-toolbar__export-appendix-hint">默认不含附录旧照；勾选后一并导出。</p>' +
    "</div>" +
    '<div class="preview-toolbar__export-popover-field" data-field="expect" hidden>' +
    '<span class="preview-toolbar__export-popover-label">预期</span>' +
    '<div class="preview-toolbar__export-expect" data-expect-body></div></div>' +
    '<p class="preview-toolbar__export-coach" data-field="coach" hidden></p>' +
    '<details class="preview-toolbar__export-more" data-field="more">' +
    "<summary>更多输出</summary>" +
    '<div class="preview-toolbar__export-more-links">' +
    '<button type="button" class="preview-toolbar__export-more-link" data-action="export-zip">导出 zip（自行托管）</button>' +
    '<button type="button" class="preview-toolbar__export-more-link" data-action="reveal-folder">在文件夹中显示</button>' +
    (edition === "portfolio"
      ? '<button type="button" class="preview-toolbar__export-more-link" data-ltn-dual-preview hidden>对比网页版与导出长图</button>'
      : '<button type="button" class="preview-toolbar__export-more-link" data-ltn-dual-preview>对比网页版与导出长图</button>') +
    "</div></details>" +
    "</div>" +
    '<div class="preview-toolbar__export-popover-actions">' +
    '<button type="button" class="preview-toolbar__export-popover-ok" data-action="ok">确定</button>' +
    '<button type="button" class="preview-toolbar__export-popover-cancel" data-action="cancel">取消</button>' +
    "</div>"
  );
}

/**
 * Sync selected states + secondary fields visibility.
 * @param {HTMLElement} pop
 * @param {{platform:string, mode:string, scale:number, slideCount?:number|null, padMode?:string}} draft
 * @param {{smartCropEnabled?: boolean, photoCount?: number}} [opts]
 */
function _clgEsc(s) {
  return String(s || "").replace(/[&<>"]/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
  });
}

export function crossingGateSheetHtml(model) {
  model = model || crossingGateSheetModel({ loading: true });
  var copy = crossingGateCopy();
  return (
    '<div class="preview-toolbar__clg-veil" data-clg-veil></div>' +
    '<div class="preview-toolbar__clg-sheet" role="dialog" aria-modal="true" aria-labelledby="clg-sheet-title">' +
    '<button type="button" class="preview-toolbar__clg-dismiss" data-clg-dismiss aria-label="' +
    _clgEsc(copy.sheetStay) +
    '">×</button>' +
    '<h3 id="clg-sheet-title" class="preview-toolbar__clg-sheet-title">' +
    _clgEsc(model.title) +
    "</h3>" +
    '<p class="preview-toolbar__clg-sheet-body">' +
    _clgEsc(model.body) +
    "</p>" +
    '<div class="preview-toolbar__clg-sheet-actions">' +
    (model.primary
      ? '<button type="button" class="preview-toolbar__export-popover-ok" data-clg-primary' +
        (model.primaryDisabled ? " disabled" : "") +
        ">" +
        _clgEsc(model.primary) +
        "</button>"
      : "") +
    (model.secondary
      ? '<button type="button" class="preview-toolbar__export-popover-cancel" data-clg-secondary>' +
        _clgEsc(model.secondary) +
        "</button>"
      : "") +
    "</div></div>"
  );
}

export function renderCrossingGateSheet(pop, sibling, currentTitle) {
  if (!pop || typeof pop.querySelector !== "function") return;
  var model = crossingGateSheetModel(sibling, currentTitle);
  var host = pop.querySelector("[data-clg-sheet]");
  if (!host && typeof document !== "undefined" && document.createElement) {
    host = document.createElement("div");
    host.setAttribute("data-clg-sheet", "1");
    host.className = "preview-toolbar__clg-sheet-host";
    pop.appendChild(host);
  }
  if (!host) return;
  host.hidden = false;
  host.innerHTML = crossingGateSheetHtml(model);
  pop.classList.add("is-clg-open");
  host._clgVariant = model.variant;
}

export function closeCrossingGateSheet(pop) {
  if (!pop || typeof pop.querySelector !== "function") return;
  var pid = pop._clgGatePid;
  pop._clgSheetOpen = false;
  var host = pop.querySelector("[data-clg-sheet]");
  if (host) {
    host.hidden = true;
    host.innerHTML = "";
  }
  pop.classList.remove("is-clg-open");
  var gate =
    pid &&
    pop.querySelector &&
    pop.querySelector('[data-studio-longshot-platform="' + pid + '"]');
  if (gate && typeof gate.focus === "function") {
    try {
      gate.focus();
    } catch (_eFocus) {}
  }
}

export function syncPanelUI(pop, draft, opts) {
  if (!pop || !draft) return;
  opts = opts || {};
  var socialFace = isPortfolioSocialExportFace(pop);
  var platforms = normalizePlatformList(draft.platforms || [draft.platform]);
  if (socialFace) {
    var usable = platforms.filter(function (id) {
      return !isCrossingLongshotLocked(id);
    });
    if (!usable.length) {
      usable = [nextCrossingDefaultPlatform({ platform: draft.platform, platforms: platforms })];
    }
    draft.platforms = usable.slice(0, 1);
    draft.platform = draft.platforms[0];
    platforms = draft.platforms.slice();
  }
  var isBatch = platforms.length > 1 && !socialFace;
  var platform = platforms[0];
  var meta = PLATFORMS[platform] || PLATFORMS.wechat_chat;
  // MVP · 批量态（≥2 平台）不做手风琴逐平台设置，统一隐藏张数/跨页数控件。
  var showXhs = !isBatch && !!meta.showXhsOptions;
  var showAlbumCount = !isBatch && !!meta.showAlbumCountOptions;
  var smartOn = opts.smartCropEnabled === true;

  // 旧快捷档 3/6/9 → 4/8/12（仅画册单选态；自定义其它值不动）
  if (showAlbumCount && draft.slideCount != null) {
    var migratedAlbum = migrateAlbumLegacyPreset(draft.slideCount);
    if (migratedAlbum != null && migratedAlbum !== draft.slideCount) {
      draft.slideCount = migratedAlbum;
    }
  }

  var gateCopy = socialFace ? crossingGateCopy() : null;
  var currentIntent = intentForPlatform(platform);
  pop.querySelectorAll("[data-export-intent]").forEach(function (btn) {
    var on = btn.getAttribute("data-export-intent") === currentIntent.id;
    btn.classList.toggle("is-selected", on);
    btn.setAttribute("aria-checked", on ? "true" : "false");
  });
  pop.querySelectorAll("[data-studio-longshot-platform]").forEach(function (btn) {
    var pid = btn.getAttribute("data-studio-longshot-platform");
    var on = platforms.indexOf(pid) >= 0;
    btn.classList.toggle("is-selected", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
    btn.setAttribute("aria-checked", on ? "true" : "false");
    btn.setAttribute("role", socialFace ? "radio" : "checkbox");
    if (socialFace && isCrossingLongshotLocked(pid)) {
      btn.setAttribute("data-clg-locked", "1");
      var sub =
        btn.querySelector &&
        btn.querySelector(".preview-toolbar__export-platform-card__sub");
      if (sub) {
        sub.textContent = gateCopy.gateSub;
        if (!sub.id) sub.id = "clg-gate-sub-" + pid;
        btn.setAttribute("aria-describedby", sub.id);
      }
    } else {
      btn.removeAttribute("data-clg-locked");
      btn.removeAttribute("aria-describedby");
    }
  });
  var batchHint = pop.querySelector("[data-batch-hint]");
  if (batchHint) {
    batchHint.hidden = !isBatch;
    if (isBatch) {
      var hasAlbum = platforms.indexOf("album_spread") >= 0;
      batchHint.textContent =
        "批量导出：将按顺序导出 " +
        platforms.length +
        " 个模式，均使用各平台默认设置（自动张数）。需要自定义张数请单选该平台单独导出。" +
        (hasAlbum
          ? " 含画册时精选照片较多可能需 1–2 分钟，请耐心等待。"
          : "");
    } else {
      batchHint.textContent = "";
    }
  }
  pop.querySelectorAll("[data-studio-longshot-mode]").forEach(function (btn) {
    var on = btn.getAttribute("data-studio-longshot-mode") === draft.mode;
    btn.classList.toggle("is-selected", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  });
  pop.querySelectorAll("[data-studio-longshot-scale]").forEach(function (btn) {
    var on = String(btn.getAttribute("data-studio-longshot-scale")) === String(draft.scale);
    btn.classList.toggle("is-selected", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  });
  var scaleHint = pop.querySelector("[data-scale-hint]");
  if (scaleHint) {
    scaleHint.textContent = scaleHintForPlatform(platform, draft.scale);
  }
  pop.querySelectorAll("[data-studio-longshot-density]").forEach(function (btn) {
    var on =
      (btn.getAttribute("data-studio-longshot-density") || "default") ===
      (draft.density || "default");
    btn.classList.toggle("is-selected", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  });

  var countKey = draft.slideCount == null ? "auto" : String(draft.slideCount);
  var useCustom = draft.slideCount != null && !isXhsPresetCount(draft.slideCount);
  pop.querySelectorAll("[data-studio-xhs-count]").forEach(function (btn) {
    var key = btn.getAttribute("data-studio-xhs-count");
    var on = useCustom ? key === "custom" : key === countKey;
    btn.classList.toggle("is-selected", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  });
  var customRow = pop.querySelector("[data-xhs-custom-row]");
  var customInput = pop.querySelector("[data-studio-xhs-custom-input]");
  if (customRow) customRow.hidden = !(showXhs && useCustom);
  if (customInput && showXhs && useCustom) {
    if (document.activeElement !== customInput) {
      customInput.value = String(draft.slideCount);
    }
  }

  // P2 · 画册跨页数（同一套 draft.slideCount，语义按 platform 区分）
  var albumCountKey = draft.slideCount == null ? "auto" : String(draft.slideCount);
  var albumUseCustom = draft.slideCount != null && !isAlbumPresetCount(draft.slideCount);
  pop.querySelectorAll("[data-studio-album-count]").forEach(function (btn) {
    var key = btn.getAttribute("data-studio-album-count");
    var on = albumUseCustom ? key === "custom" : key === albumCountKey;
    btn.classList.toggle("is-selected", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  });
  var albumCustomRow = pop.querySelector("[data-album-custom-row]");
  var albumCustomInput = pop.querySelector("[data-studio-album-custom-input]");
  if (albumCustomRow) albumCustomRow.hidden = !(showAlbumCount && albumUseCustom);
  if (albumCustomInput && showAlbumCount && albumUseCustom) {
    if (document.activeElement !== albumCustomInput) {
      albumCustomInput.value = String(draft.slideCount);
    }
  }
  var pad = draft.padMode || "letterbox";
  if (pad === "smart_crop" && !smartOn) pad = "letterbox";
  pop.querySelectorAll("[data-studio-xhs-pad]").forEach(function (btn) {
    var on = btn.getAttribute("data-studio-xhs-pad") === pad;
    btn.classList.toggle("is-selected", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  });
  var smartBtn = pop.querySelector("[data-smart-crop-btn]");
  if (smartBtn) {
    smartBtn.disabled = !smartOn;
    smartBtn.title = smartOn ? "" : "智能裁切为实验功能，需开启配置开关";
  }

  var modeField = pop.querySelector('[data-field="mode"]');
  // 仅微信群单选显「按章/一整张」；批量或其它平台隐藏（D-LNG2-15 / D-BEX-01）
  // F2 过河面永远藏按章：闸卡不可用，可用卡也不吃卷轴。
  if (modeField) modeField.hidden = socialFace || isBatch || !meta.showSegmentMode;

  var copyField = pop.querySelector('[data-field="copy"]');
  if (copyField) {
    // 海报 / 拼贴文案包平台：不走长图「要不要字」
    copyField.hidden = isBatch || meta.showCopyControls === false;
  }
  var copyLabelEl = pop.querySelector("[data-copy-label]");
  if (copyLabelEl) {
    copyLabelEl.textContent = meta.copyLabel || "长图要不要字";
  }
  var densityField = pop.querySelector('[data-field="density"]');
  if (densityField) {
    // 长图密度仅微信群/朋友圈；拼贴出口隐藏。作品集主路径（页图）也隐藏。
    var folioMain =
      opts.edition === "portfolio" &&
      platform !== "wechat_chat" &&
      platform !== "wechat_moments";
    densityField.hidden = isBatch || isComposePlatform(platform) || folioMain;
  }
  var dualBtn = pop.querySelector("[data-ltn-dual-preview]");
  if (dualBtn) {
    dualBtn.hidden =
      opts.edition === "portfolio" &&
      platform !== "wechat_chat" &&
      platform !== "wechat_moments";
  }
  var noteEl = pop.querySelector(".preview-toolbar__export-popover-note");
  if (noteEl) {
    noteEl.textContent =
      isBatch || meta.showCopyControls === false
        ? "选好后点「确定」，再点「长图」开始导出。"
        : "选好后点「确定」，再点「长图」开始导出。改「要不要字」会同步预览。";
  }

  var xhsCount = pop.querySelector('[data-field="xhs-count"]');
  var xhsPad = pop.querySelector('[data-field="xhs-pad"]');
  var xhsPack = pop.querySelector('[data-field="xhs-copy-pack"]');
  var albumCountField = pop.querySelector('[data-field="album-count"]');
  if (albumCountField) albumCountField.hidden = !showAlbumCount;
  if (xhsCount) xhsCount.hidden = !showXhs;
  // Compose 路径不再做 letterbox/smart_crop；隐藏以免误导
  if (xhsPad) xhsPad.hidden = true;
  if (xhsPack) xhsPack.hidden = !showXhs;

  var est = pop.querySelector("[data-xhs-estimate]");
  if (est) {
    if (showXhs && draft.slideCount == null) {
      var n = estimateXhsAutoCount(opts.photoCount || estimatePhotoCountFromDom());
      est.hidden = false;
      est.textContent = "预计约 " + n + " 张（按照片数自动）";
    } else {
      est.hidden = true;
      est.textContent = "";
    }
  }
  var albumEst = pop.querySelector("[data-album-estimate]");
  if (albumEst) {
    if (showAlbumCount && draft.slideCount == null) {
      var albumN = estimateAlbumAutoCount(
        opts.photoCount || estimatePhotoCountFromDom()
      );
      albumEst.hidden = false;
      albumEst.textContent =
        albumN < 4
          ? "预计约 " + albumN + " 跨页（小本自动）"
          : "预计约 " + albumN + " 跨页（自动 · 印刷 4 的倍数）";
    } else {
      albumEst.hidden = true;
      albumEst.textContent = "";
    }
  }

  var appendixField = pop.querySelector('[data-field="appendix"]');
  var appendixInput = pop.querySelector("[data-studio-include-appendix]");
  var appendixLabel = pop.querySelector("[data-appendix-label]");
  var appendixN = opts.appendixCount || 0;
  if (appendixField) {
    appendixField.hidden = !(appendixN >= 2);
    if (appendixLabel && appendixN >= 2) {
      appendixLabel.textContent = "未含 · 往年旧照（" + appendixN + " 张）";
    }
    if (appendixInput) {
      appendixInput.checked = draft.includeAppendix === true;
    }
  }

  var expectField = pop.querySelector('[data-field="expect"]');
  var expectBody = pop.querySelector("[data-expect-body]");
  if (expectField && expectBody) {
    if (isBatch) {
      // 批量态下预期文案由上方 batch-hint 承担，避免误导为"仅第一个平台的预期"。
      expectField.hidden = true;
      expectBody.textContent = "";
    } else if (meta.expectHtml) {
      expectField.hidden = false;
      if (showXhs && draft.slideCount == null) {
        var autoN = estimateXhsAutoCount(opts.photoCount || estimatePhotoCountFromDom());
        expectBody.innerHTML =
          "将生成约 <strong>" +
          autoN +
          " 张</strong> 3:4 竖版拼贴海报（auto）· 预计较快完成";
      } else if (showXhs && draft.slideCount != null) {
        expectBody.innerHTML =
          "将生成 <strong>" +
          draft.slideCount +
          " 张</strong> 3:4 竖版拼贴海报 · 预计较快完成";
      } else if (showAlbumCount && draft.slideCount == null) {
        var albumAutoN = estimateAlbumAutoCount(
          opts.photoCount || estimatePhotoCountFromDom()
        );
        expectBody.innerHTML =
          "将导出约 <strong>" +
          albumAutoN +
          " 张两卡跨页</strong>拼贴（自动" +
          (albumAutoN >= 4 ? " · 印刷 4 的倍数" : " · 小本") +
          "，约 1.53:1）";
      } else if (showAlbumCount && draft.slideCount != null) {
        expectBody.innerHTML =
          "将导出 <strong>" +
          draft.slideCount +
          " 张两卡跨页</strong>拼贴（3:4+3:4+中缝，约 1.53:1）";
      } else {
        expectBody.innerHTML = meta.expectHtml;
      }
    } else {
      expectField.hidden = true;
      expectBody.textContent = "";
    }
  }

  var coach = pop.querySelector('[data-field="coach"]');
  if (coach) {
    var showPlatformCoach =
      platform !== "wechat_chat" && shouldShowMomentsCoach();
    if (showPlatformCoach) {
      coach.hidden = false;
      coach.textContent = HELP_COPY.platformPickTip;
    } else {
      coach.hidden = true;
      coach.textContent = "";
    }
  }

  if (socialFace) {
    var okBtn = pop.querySelector('[data-action="ok"]');
    if (okBtn) {
      var lockedMain = isCrossingLongshotLocked(platform);
      okBtn.textContent = lockedMain
        ? crossingGateCopy().sheetTitle
        : shortCtaLabelForPlatform(platform);
      okBtn.disabled = lockedMain;
    }
  }
}

/**
 * Wire draft mutation handlers on a freshly built popover.
 * @returns {{ getDraft: function(): object, setDraft: function(object): void, setUiOpts: function(object): void }}
 */
export function bindPanelDraft(pop, initialDraft, opts) {
  opts = opts || {};
  var uiOpts = {
    smartCropEnabled: opts.smartCropEnabled === true,
    photoCount: opts.photoCount || 0,
    appendixCount: opts.appendixCount || 0,
    edition: opts.edition === "portfolio" ? "portfolio" : "journal",
  };
  var draft = {
    platform: (initialDraft && initialDraft.platform) || "wechat_chat",
    platforms: normalizePlatformList(
      initialDraft && initialDraft.platforms,
      (initialDraft && initialDraft.platform) || "wechat_chat"
    ),
    mode: (initialDraft && initialDraft.mode) || "chapter",
    scale: (initialDraft && initialDraft.scale) || 2,
    slideCount: initialDraft ? initialDraft.slideCount : null,
    padMode: (initialDraft && initialDraft.padMode) || "letterbox",
    includeAppendix: !!(initialDraft && initialDraft.includeAppendix),
    density:
      (initialDraft && initialDraft.density) === "compact" ? "compact" : "default",
  };
  var onDraftChange = typeof opts.onDraftChange === "function" ? opts.onDraftChange : null;

  function refresh() {
    syncPanelUI(pop, draft, uiOpts);
    if (onDraftChange) {
      try {
        onDraftChange({
          platform: draft.platforms[0],
          platforms: draft.platforms.slice(),
          mode: draft.mode,
          scale: draft.scale,
          slideCount: draft.slideCount,
          padMode: draft.padMode,
          includeAppendix: !!draft.includeAppendix,
          density: draft.density || "default",
        });
      } catch (_e) {}
    }
  }

  pop.querySelectorAll("[data-studio-longshot-density]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      draft.density =
        btn.getAttribute("data-studio-longshot-density") === "compact"
          ? "compact"
          : "default";
      refresh();
    });
  });

  pop.querySelectorAll("[data-export-intent]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var intentId = btn.getAttribute("data-export-intent") || "daily_share";
      draft.platforms = [defaultPlatformForIntent(intentId)];
      draft.platform = draft.platforms[0];
      refresh();
    });
  });
  pop.querySelectorAll("[data-studio-longshot-platform]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var pid = btn.getAttribute("data-studio-longshot-platform") || "wechat_chat";
      if (isPortfolioSocialExportFace(pop) && isCrossingLongshotLocked(pid)) {
        if (typeof pop._onCrossingGate === "function") pop._onCrossingGate(pid);
        return;
      }
      if (isPortfolioSocialExportFace(pop)) {
        draft.platforms = [pid];
        draft.platform = pid;
        refresh();
        return;
      }
      var idx = draft.platforms.indexOf(pid);
      if (idx >= 0) {
        // 再点同一项：取消勾选（至少保留 1 个）
        if (draft.platforms.length > 1) draft.platforms.splice(idx, 1);
      } else {
        // 点新平台：加入多选，并提到首位 → 二级区跟刚点的平台
        draft.platforms = [pid].concat(draft.platforms);
      }
      draft.platform = draft.platforms[0];
      refresh();
    });
  });
  pop.querySelectorAll("[data-studio-longshot-mode]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      draft.mode = btn.getAttribute("data-studio-longshot-mode") || "chapter";
      refresh();
    });
  });
  pop.querySelectorAll("[data-studio-longshot-scale]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      draft.scale = parseInt(btn.getAttribute("data-studio-longshot-scale"), 10) || 2;
      refresh();
    });
  });
  pop.querySelectorAll("[data-studio-xhs-count]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var v = btn.getAttribute("data-studio-xhs-count") || "auto";
      if (v === "auto") {
        draft.slideCount = null;
      } else if (v === "custom") {
        draft.slideCount = resolveXhsCustomSeed(draft.slideCount);
        refresh();
        var inp = pop.querySelector("[data-studio-xhs-custom-input]");
        if (inp) {
          try {
            inp.focus();
            inp.select();
          } catch (e) {}
        }
        return;
      } else {
        draft.slideCount = clampXhsSlideCount(v);
      }
      refresh();
    });
  });
  var customInput = pop.querySelector("[data-studio-xhs-custom-input]");
  if (customInput) {
    function applyCustomInput() {
      var n = clampXhsSlideCount(customInput.value);
      if (n == null) return;
      draft.slideCount = n;
      customInput.value = String(n);
      refresh();
    }
    customInput.addEventListener("change", applyCustomInput);
    customInput.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter") {
        ev.preventDefault();
        applyCustomInput();
      }
    });
  }
  // P2 · 画册「跨页数」— 与小红书「张数」同一 draft.slideCount 字段，按
  // album_spread 自身的 1–30 范围夹取。
  pop.querySelectorAll("[data-studio-album-count]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var v = btn.getAttribute("data-studio-album-count") || "auto";
      if (v === "auto") {
        draft.slideCount = null;
      } else if (v === "custom") {
        draft.slideCount = resolveAlbumCustomSeed(draft.slideCount);
        refresh();
        var inp = pop.querySelector("[data-studio-album-custom-input]");
        if (inp) {
          try {
            inp.focus();
            inp.select();
          } catch (e) {}
        }
        return;
      } else {
        draft.slideCount = clampAlbumSlideCount(v);
      }
      refresh();
    });
  });
  var albumCustomInput = pop.querySelector("[data-studio-album-custom-input]");
  if (albumCustomInput) {
    function applyAlbumCustomInput() {
      var n = clampAlbumSlideCount(albumCustomInput.value);
      if (n == null) return;
      draft.slideCount = n;
      albumCustomInput.value = String(n);
      refresh();
    }
    albumCustomInput.addEventListener("change", applyAlbumCustomInput);
    albumCustomInput.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter") {
        ev.preventDefault();
        applyAlbumCustomInput();
      }
    });
  }
  pop.querySelectorAll("[data-studio-xhs-pad]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      if (btn.disabled) return;
      draft.padMode = btn.getAttribute("data-studio-xhs-pad") || "letterbox";
      refresh();
    });
  });
  var appendixCb = pop.querySelector("[data-studio-include-appendix]");
  if (appendixCb) {
    appendixCb.addEventListener("change", function () {
      draft.includeAppendix = !!appendixCb.checked;
      // Label flips meaning when checked: 「含 · 往年旧照」
      var label = pop.querySelector("[data-appendix-label]");
      if (label && uiOpts.appendixCount >= 2) {
        label.textContent = draft.includeAppendix
          ? "含 · 往年旧照（" + uiOpts.appendixCount + " 张）"
          : "未含 · 往年旧照（" + uiOpts.appendixCount + " 张）";
      }
      refresh();
    });
  }

  refresh();

  return {
    getDraft: function () {
      return {
        platform: draft.platforms[0],
        platforms: draft.platforms.slice(),
        mode: draft.mode,
        scale: draft.scale,
        slideCount:
          draft.slideCount == null
            ? null
            : clampSlideCountForPlatform(draft.platform, draft.slideCount),
        padMode: draft.padMode,
        includeAppendix: !!draft.includeAppendix,
        density: draft.density === "compact" ? "compact" : "default",
      };
    },
    setDraft: function (next) {
      draft.platforms = normalizePlatformList(
        next && next.platforms,
        (next && next.platform) || draft.platform
      );
      draft.platform = draft.platforms[0];
      draft.mode = next.mode || draft.mode;
      draft.scale = next.scale || draft.scale;
      draft.slideCount =
        next.slideCount == null
          ? null
          : clampSlideCountForPlatform(draft.platform, next.slideCount);
      draft.padMode = next.padMode || draft.padMode;
      if (next && typeof next.includeAppendix === "boolean") {
        draft.includeAppendix = next.includeAppendix;
      }
      if (next && next.density) {
        draft.density = next.density === "compact" ? "compact" : "default";
      }
      refresh();
    },
    setUiOpts: function (nextOpts) {
      if (nextOpts && typeof nextOpts.smartCropEnabled === "boolean") {
        uiOpts.smartCropEnabled = nextOpts.smartCropEnabled;
      }
      if (nextOpts && nextOpts.photoCount != null) {
        uiOpts.photoCount = nextOpts.photoCount;
      }
      if (nextOpts && nextOpts.appendixCount != null) {
        uiOpts.appendixCount = nextOpts.appendixCount;
      }
      refresh();
    },
  };
}

/**
 * Format success copy for platform jobs (no thumbnail strip · D-LNG2-24).
 */
export function formatPlatformSuccess(result) {
  result = result || {};
  var platform = result.platform || "wechat_chat";
  var n = result.pageCount || (result.outputs && result.outputs.length) || 0;
  var title = "✓ 长图已保存";
  if (platform === "poster_bric") {
    title = "✓ 单张海报已就绪";
  } else if (platform === "wechat_moments") {
    title = "✓ " + n + " 张长图连读已就绪";
  } else if (platform === "xiaohongshu") {
    title = "✓ " + n + " 张竖版拼贴海报已就绪";
  } else if (platform === "wechat_official") {
    title = "✓ " + n + " 张公众号配图已就绪";
  } else if (platform === "album_spread") {
    title = "✓ " + n + " 张画册跨页已就绪";
  }
  return {
    title: title,
    publishGuide: result.publishGuide || "",
    userHint: result.userHint || "",
    outputs: result.outputs || [],
  };
}

/**
 * Stage 3 · 批量导出「进行中」清单的逐项状态（纯函数，供 Task Dock 清单化
 * 渲染调用）。`cur1Based` 是后端 `job.stageIndex`（当前第几个平台在跑，
 * 1-based）；早于它的记为 done、等于它的记为 running、其余 queued——这是
 * 展示态的最佳猜测，真实逐项成败要等 job 完成才知道（`result.items`，见
 * `formatBatchSuccess`），不代表已完成的项一定成功。
 *
 * 细粒度页进度不进清单项（2026-08-06 用户实测：单项进度条忽有忽无、显得乱），
 * 只留给 `batchOverallProgressRatio` 驱动顶部总进度条。
 */
export function batchChecklistItems(platformIds, cur1Based) {
  var ids = normalizePlatformList(platformIds);
  var cur = Math.max(1, Number(cur1Based) || 1);
  return ids.map(function (id, idx) {
    var status = idx + 1 < cur ? "done" : idx + 1 === cur ? "running" : "queued";
    return { platform: id, label: shortCtaLabelForPlatform(id), status: status };
  });
}

/**
 * Stage 3 · 批量导出「进行中」总进度比例（0–1，纯函数），供 Task Dock 顶部
 * 总进度条使用。折算方式：已完成的平台各记 1 份，当前运行中的平台按其
 * 内部真实进度（`itemProgress.cur/total`）记部分份；没有细进度数据时给
 * 一个保守的基线份额（0.15），让条至少可见地"往前挪一点"，不是卡死在
 * 整数格点上——比单纯的 (cur-1)/total 更"生动"，也不会在没数据时撒谎到
 * 接近 100%。
 */
export function batchOverallProgressRatio(platformIds, cur1Based, itemProgress) {
  var ids = normalizePlatformList(platformIds);
  var total = ids.length;
  if (!total) return 0;
  var cur = Math.max(1, Math.min(total, Number(cur1Based) || 1));
  var doneCount = cur - 1;
  var currentFrac = 0.15;
  if (itemProgress && Number(itemProgress.total) > 0 && Number(itemProgress.cur) >= 0) {
    currentFrac = Math.max(0, Math.min(1, Number(itemProgress.cur) / Number(itemProgress.total)));
  }
  return Math.max(0, Math.min(1, (doneCount + currentFrac) / total));
}

/**
 * 批量导出结果的文案（result.batch === true 的形状，见
 * PRD-BATCH-EXPORT-MULTISELECT-V1 §4.3）· 部分失败不整体判失败（D-BEX-05）。
 */
export function formatBatchSuccess(result) {
  result = result || {};
  var items = result.items || [];
  var total = items.length;
  var succeeded =
    result.succeededCount != null
      ? result.succeededCount
      : items.filter(function (i) {
          return i.ok;
        }).length;
  var failed = result.failedCount != null ? result.failedCount : total - succeeded;
  var title;
  if (total > 0 && succeeded === 0) {
    // 全失败仍可能以 job.status=succeeded 收尾（D-BEX-05 容器语义），
    // 文案必须与「部分成功」区分开，避免「已完成 0/N」误导。
    title = total + " 个模式全部失败";
  } else if (failed > 0) {
    title = "已完成 " + succeeded + "/" + total + " 个模式（" + failed + " 个失败）";
  } else {
    title = "✓ " + total + " 个模式已全部导出";
  }
  var lines = items.map(function (item) {
    var label = shortCtaLabelForPlatform(item.platform);
    if (item.ok) {
      var n = item.pageCount || (item.outputs && item.outputs.length) || 0;
      return "✓ " + label + " · " + n + " 张";
    }
    return "✗ " + label + " · " + (item.message || item.error || "失败");
  });
  return {
    title: title,
    lines: lines,
    items: items,
    succeededCount: succeeded,
    failedCount: failed,
  };
}

/**
 * Stage 3 · 完成态清单的逐项状态（结构化 status/detail，供 Task Dock 逐项
 * 渲染图标+文案）。与 `formatBatchSuccess` 的 `lines`（拼好的整行字符串）
 * 是同一份 `result.items` 的两种呈现，服务不同 UI 形态。
 */
export function batchChecklistItemsFromResult(result) {
  result = result || {};
  var items = result.items || [];
  return items.map(function (item) {
    var label = shortCtaLabelForPlatform(item.platform);
    if (item.ok) {
      var n = item.pageCount || (item.outputs && item.outputs.length) || 0;
      return { platform: item.platform, label: label, status: "done", detail: n + " 张" };
    }
    return {
      platform: item.platform,
      label: label,
      status: "failed",
      detail: item.message || item.error || "失败",
    };
  });
}
