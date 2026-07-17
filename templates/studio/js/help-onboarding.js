/**
 * 帮助与情境引导系统 V1 · W0/W1 合同常量与 seen / 门禁（D-HELP-*）。
 * 禁止全站 tour；文案须与精修 V1.1 / 导出门面一致。
 */
"use strict";

import { trackStudioEvent } from "./analytics.js";
import { SS } from "./constants.js";
import {
  DISMISS_KEY as WAIT_TIPS_DISMISS_KEY,
  VERSION_KEY as WAIT_TIPS_VERSION_KEY,
} from "../homepage-v2/wait-tips-copy.js";

/** @deprecated 现网兼容键；门禁以 HELP_LS 为准并双写 */
export var LEGACY_EXPORT_PULSE_SEEN = "travelogue.studio.exportPulseSeen";

export var HELP_LS = {
  previewLongshotSeen: "travelogue.studio.help.previewLongshotSeen",
  exportPulseSeen: "travelogue.studio.help.exportPulseSeen",
  refineSaveSeen: "travelogue.studio.help.refineSaveSeen",
  platformPickSeen: "travelogue.studio.help.platformPickSeen",
  bookendsPickSeen: "travelogue.studio.help.bookendsPickSeen",
  importFolderExpanded: "travelogue.studio.help.importFolderExpanded",
  /** Desktop LLM Setup V1 · 能力卡（全局一次） */
  capabilityCardSeen: "travelogue.desktop.capabilityCard.v1",
  /** L0 Hardening · 首页轻状态 dismiss（可选永久关闭） */
  homeStubBannerDismissed: "travelogue.desktop.homeStubBanner.v1",
  /** L0 Hardening · 首次预览本机文案 tip */
  stubHintSeen: "travelogue.desktop.stubHint.v1",
};

/** session：能力卡本会话压制非关键自动 Help L1（D-DLLM-13） */
var CAPABILITY_SUPPRESS_HELP_SS = "travelogue.desktop.capabilityCard.suppressHelpL1";

export var HELP_COPY = {
  firstSuccessNext:
    // FE-FST-06 / USR-03 · 勿承诺杂志级；升级路径改走 Help
    "当前为本机文案。请点击打开卷轴预览查看游记，也可以直接保存长图。",
  longshotTip:
    "验货没问题就点『长图』，生成可发微信的长图",
  longshotAria: "验货没问题就点『长图』，生成可发微信的长图",
  openPreviewCta: "打开卷轴预览 →",
  saveLongshotSecondary: "保存长图",
  importFolderSummary: "不知道选哪个文件夹？",
  importFolderPoints: [
    "同一次旅行放同一文件夹（50–100 张最佳）",
    "Day1/Day2 子夹：合并导入或分两次导入（每次一篇新游记）",
    "支持 JPG / PNG / WebP / HEIC；不移动、不修改原片",
    "手机照片需先传到电脑",
  ],
  importNewTripLine:
    "每个文件夹会生成一篇新的游记，不会覆盖已有游记",
  importNewToast: "将新建一篇游记 · 已选择 N 张",
  publishGuideFallback: [
    "长图已保存到本机",
    "打开微信，按文件名顺序发到群聊",
    "可点『在文件夹中显示』找到文件",
  ],
  demoConvertCta: "试试用自己的照片做一篇 →",
  /** FE-FTUE-08 · FirstSuccess 转化句（PRD §3.2） */
  ftueConvertHint: "下一步可用自己的旅行照片再做一本",
  platformPickTip:
    "会按平台切成多张；页脚有顺序。失败可改回微信群长图",
  bookendsPickTip: "点下方缩略图，即可更换封面或封底",
  bookendsOpeningLabel: "换封面 · 点选一张",
  bookendsClosingLabel: "换封底 · 点选一张",
  bookendsAppliedOpening: "已换封面",
  bookendsAppliedClosing: "已换封底",
  featuredPromotedToast: "已标为精选 · 会优先出现在『放映精选』",
  featuredDemotedToast: "已取消精选",
  featuredMoreLink: "了解更多 →",
  featuredPageHint: "精选 = 记下这张更重要；不会立刻重排整本",
  featuredPresentEmpty: "先在正文点 ★",
  featuredRerankCta: "按精选重排",
  featuredRerankDockTitle: "已记下精选",
  featuredRerankDockSub: "不会立刻重排整本；若要改构图可按精选重排",
  featuredRerankTitle: "按精选重新排版？",
  featuredRerankBody:
    "将按你标过的精选重新选片排版。章序与分章不变；封面、章首或部分屏构图可能变化。",
  featuredRerankLockedNote:
    "当前结构已锁定：不会解锁章序。仅在现有分章内按精选调整封面、章首与部分屏。",
  featuredRerankConfirm: "重新排版",
  featuredRerankBusy: "正在按精选重新排版…",
  featuredRerankDone: "排版已更新",
  featuredRerankDoneCover: "排版已更新 · 封面已更换",
  helpAria: "使用帮助",
  helpTitle: "使用帮助",
  refineSaveLines: [
    "改字马上生效；改拼图请先点下方『更新版面』",
    "『完成』只是退出精修，不是更新版面；精选不会立刻重排整本",
  ],
  refineSaveMore: "了解更多 →",
  replayButton: "重新显示操作提示",
  replayDoneToast:
    "已重置。下次进入预览会再提示如何保存长图与本机文案说明；再次打开精修时会再看到保存说明；切换分享平台、展开首尾装帧时也会再提示；首页能力卡与轻状态也会再出现；下次导入等待时也会再显示小提示。",
  replayWaitTipsButton: "重播等待提示",
  replayWaitTipsDoneToast:
    "已重置等待提示。下次导入生成时会再显示小提示（不是操作引导，也不会挡进度）。",
  stubNarrateTip: "当前为本机文案（可随时在设置中升级）",
  helpDeepLinkPending: "「长图可更新」是什么意思 →",
  helpDeepLinkH3: "了解更多 →",
  /** H1–H7 帮助抽屉条目（H6=封面封底；H7=AI 文案） */
  helpItems: [
    {
      id: "H1",
      title: "怎么选照片文件夹",
      body: [
        "同一次旅行放同一文件夹（50–100 张最佳）",
        "Day1/Day2 子夹：合并导入或分两次导入（每次一篇新游记）",
        "支持 JPG / PNG / WebP / HEIC；不移动、不修改原片",
        "手机照片需先传到电脑",
      ],
    },
    {
      id: "H2",
      title: "「完成」和「更新版面」有什么区别",
      body: [
        "点字改文案：马上在预览看到，导出用当前预览",
        "改拼图 / 版式相关：需点「更新版面」后才进导出",
        "标精选 ★：立刻记下「这张更重要」；点已亮的 ★ 可取消；不会立刻重排整本",
        "若要按精选改构图：用「按精选重排」（会确认；与「更新版面」不同）",
        "点「长图」：导出当前已更新结果",
        "点「精修」：进入精修模式（可收起面板继续改）",
        "Esc / × / 再点「精修」（面板开时）：只关面板，模式可仍为 on",
        "点「完成」：退出精修模式（★ 隐藏）——不是更新版面",
      ],
    },
    {
      id: "H3",
      title: "「长图可更新」是什么意思",
      body: [
        "改了拼图或版式相关设置后，版面还没更新",
        "请先点「更新版面」，再点「长图」导出最新结果",
        "若导出时弹出拦截，选「更新并导出」即可",
        "仅标精选不会触发「长图可更新」；精选是意图，不是立刻重排",
      ],
    },
    {
      id: "H4",
      title: "怎么把长图发到微信群",
      body: [
        "长图已保存到本机",
        "打开微信，按文件名顺序发到群聊",
        "可点「在文件夹中显示」找到文件",
        "分段或多平台时，以成功态发群指引为准",
      ],
    },
    {
      id: "H5",
      title: "出错了怎么办",
      body: [
        "导入失败 → 换文件夹重试 / 新建一篇",
        "导出失败 → 再点「长图」；仍失败见日志或重开 Studio",
        "提示要更新版面 → 先「更新版面」再导出 · 原片不被改",
      ],
    },
    {
      id: "H6",
      title: "怎么换封面封底",
      body: [
        "打开精修 → 点「封面」→ 用分段切换封面或封底",
        "点下方缩略图，即可更换封面或封底",
        "选中的一张会标「当前」；也可点「在画面上看封面 / 封底」滚动画布",
        "封面/封底这页没有 ★ 精选与改拼图",
      ],
    },
    {
      id: "H7",
      title: "要不要配置 AI 文案",
      body: [
        "不配置也可以导入、排版、预览和导出长图（本机文案）",
        "想要杂志感文案：设置 → AI 文案 → 选服务商 → 点官方链接按其指引创建 Key → 粘贴回来 → 点「保存并测试」",
        "通义千问请选对地域：中国站或国际站须与百炼控制台 Key 归属一致；高级可填自定义 https 地址",
        "Key 只存在本机；调用费用由服务商账户结算；默认不上传原片",
        "配好后不会自动重写全文：在预览「更多工具」里点「生成杂志感文案」",
        "连接失败可自助：换 Key、改中国站/国际站、查余额/限流、检查网络后重试「保存并测试」",
      ],
    },
  ],
};

var LAYOUT_UPDATING_KEY = "travelogue.studio.layoutUpdating";
var LEGACY_PULSE_PREFIX = LEGACY_EXPORT_PULSE_SEEN + ".";

var _longshotHelpActive = false;
var _idleEvalQueued = false;
var _tipEl = null;
var _tipEscHandler = null;

function _lsGet(key) {
  try {
    return localStorage.getItem(key);
  } catch (_e) {
    return null;
  }
}

function _lsSet(key, value) {
  try {
    localStorage.setItem(key, value);
    return true;
  } catch (_e) {
    return false;
  }
}

function _ssGet(key) {
  try {
    return sessionStorage.getItem(key);
  } catch (_e) {
    return null;
  }
}

function _readJsonSs(key) {
  try {
    var raw = sessionStorage.getItem(key);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (_e) {
    return null;
  }
}

export function trackHelpEvent(name, props) {
  try {
    trackStudioEvent(name, props || {});
  } catch (_e) {
    /* ignore */
  }
  try {
    if (typeof console !== "undefined" && console.debug) {
      console.debug("[help]", name, props || {});
    }
  } catch (_e2) {
    /* ignore */
  }
}

/**
 * 迁移：legacy per-trip / 旧全局 exportPulseSeen → 帮助命名空间全局双键。
 * 门禁只读全局；发现 legacy 已学过则双写后视为 seen（AC-HELP-17）。
 */
export function migrateLongshotHelpSeen() {
  var globalHelpPulse = _lsGet(HELP_LS.exportPulseSeen) === "1";
  var globalHelpPreview = _lsGet(HELP_LS.previewLongshotSeen) === "1";
  var legacyGlobal = _lsGet(LEGACY_EXPORT_PULSE_SEEN) === "1";
  var legacyPerTrip = false;
  try {
    for (var i = 0; i < localStorage.length; i++) {
      var k = localStorage.key(i);
      if (k && k.indexOf(LEGACY_PULSE_PREFIX) === 0 && localStorage.getItem(k) === "1") {
        legacyPerTrip = true;
        break;
      }
    }
  } catch (_eScan) {
    /* ignore */
  }

  if (globalHelpPulse || globalHelpPreview) {
    // 与现网旧全局键双写兼容
    if (!_lsGet(LEGACY_EXPORT_PULSE_SEEN)) _lsSet(LEGACY_EXPORT_PULSE_SEEN, "1");
    return true;
  }
  if (legacyGlobal || legacyPerTrip) {
    markLongshotHelpSeen({ silent: true });
    return true;
  }
  return false;
}

/** 门禁：全局 previewLongshotSeen ∨ 全局 exportPulseSeen（含迁移后）。 */
export function hasLongshotHelpSeen() {
  if (migrateLongshotHelpSeen()) return true;
  return (
    _lsGet(HELP_LS.previewLongshotSeen) === "1" ||
    _lsGet(HELP_LS.exportPulseSeen) === "1" ||
    _lsGet(LEGACY_EXPORT_PULSE_SEEN) === "1"
  );
}

/**
 * 双写全局帮助键 + 现网兼容键；不再写 per-trip 门禁键（D-HELP-07′）。
 */
export function markLongshotHelpSeen(meta) {
  meta = meta || {};
  _lsSet(HELP_LS.previewLongshotSeen, "1");
  _lsSet(HELP_LS.exportPulseSeen, "1");
  _lsSet(LEGACY_EXPORT_PULSE_SEEN, "1");
  _longshotHelpActive = false;
  if (!meta.silent && meta.reason) {
    trackHelpEvent("help_coach_dismiss", {
      touchpoint: "T-PREVIEW-LONGSHOT",
      reason: meta.reason,
    });
  }
}

/** 重播用：清全局两键（W2）；顺带清 legacy 全局。 */
export function clearLongshotHelpSeen() {
  try {
    localStorage.removeItem(HELP_LS.previewLongshotSeen);
    localStorage.removeItem(HELP_LS.exportPulseSeen);
    localStorage.removeItem(LEGACY_EXPORT_PULSE_SEEN);
  } catch (_e) {
    /* ignore */
  }
  _longshotHelpActive = false;
}

export function hasRefineSaveSeen() {
  return _lsGet(HELP_LS.refineSaveSeen) === "1";
}

export function markRefineSaveSeen() {
  _lsSet(HELP_LS.refineSaveSeen, "1");
}

export function clearRefineSaveSeen() {
  try {
    localStorage.removeItem(HELP_LS.refineSaveSeen);
  } catch (_e) {
    /* ignore */
  }
}

var LEGACY_MOMENTS_COACH_KEY = "travelogue.studio.longshotMomentsCoachSeen";

export function hasPlatformPickSeen() {
  if (_lsGet(HELP_LS.platformPickSeen) === "1") return true;
  // 兼容 Longshot 2.0 朋友圈 coach 已见
  if (_lsGet(LEGACY_MOMENTS_COACH_KEY) === "1") {
    markPlatformPickSeen({ silent: true });
    return true;
  }
  return false;
}

export function markPlatformPickSeen(meta) {
  meta = meta || {};
  _lsSet(HELP_LS.platformPickSeen, "1");
  _lsSet(LEGACY_MOMENTS_COACH_KEY, "1");
  if (!meta.silent) {
    trackHelpEvent("help_coach_dismiss", {
      touchpoint: "T-PLATFORM-PICK",
      reason: meta.reason || "seen",
    });
  }
}

export function clearPlatformPickSeen() {
  try {
    localStorage.removeItem(HELP_LS.platformPickSeen);
    localStorage.removeItem(LEGACY_MOMENTS_COACH_KEY);
  } catch (_e) {
    /* ignore */
  }
}

export function hasBookendsPickSeen() {
  return _lsGet(HELP_LS.bookendsPickSeen) === "1";
}

export function markBookendsPickSeen(meta) {
  meta = meta || {};
  _lsSet(HELP_LS.bookendsPickSeen, "1");
  if (!meta.silent) {
    trackHelpEvent("help_coach_dismiss", {
      touchpoint: "T-BE-OPEN",
      reason: meta.reason || "shown",
    });
  }
}

export function clearBookendsPickSeen() {
  try {
    localStorage.removeItem(HELP_LS.bookendsPickSeen);
  } catch (_e) {
    /* ignore */
  }
}

/**
 * 首次展开首尾装帧：可见 tip（D-FEED-02 · T-BE-OPEN）。
 * @returns {boolean} 是否本次展示
 */
export function maybeShowBookendsPickTip(showToast) {
  if (hasBookendsPickSeen()) return false;
  if (isHelpL1Blocked()) return false;
  if (isLongshotHelpActive()) return false;

  markBookendsPickSeen({ silent: true });
  trackHelpEvent("help_coach_show", { touchpoint: "T-BE-OPEN" });
  if (typeof showToast === "function") {
    showToast(HELP_COPY.bookendsPickTip, { duration: 4500 });
  }
  return true;
}

/**
 * 首次从默认微信群切到朋友圈/小红书等（AC-HELP-08）。
 * @param {string} fromPlatform
 * @param {string} toPlatform
 * @param {(msg: string, opts?: object) => void} [showToast]
 * @returns {boolean} 是否本次展示
 */
export function maybeShowPlatformPickTip(fromPlatform, toPlatform, showToast) {
  var from = String(fromPlatform || "wechat_chat");
  var to = String(toPlatform || "wechat_chat");
  if (to === "wechat_chat" || to === from) return false;
  if (from !== "wechat_chat") return false;
  if (hasPlatformPickSeen()) return false;
  if (isHelpL1Blocked()) return false;
  // §4.4 · T-PREVIEW-LONGSHOT 优先于 T-PLATFORM-PICK
  if (isLongshotHelpActive()) return false;

  markPlatformPickSeen({ silent: true });
  trackHelpEvent("help_coach_show", {
    touchpoint: "T-PLATFORM-PICK",
    from: from,
    to: to,
  });
  if (typeof showToast === "function") {
    showToast(HELP_COPY.platformPickTip, { duration: 5200 });
  }
  return true;
}

/** 首访长图 L1 是否正在展示（脉冲/tip 周期内）。 */
export function isLongshotHelpActive() {
  return !!_longshotHelpActive || !!_tipEl;
}

/** Wait Tips W2：清 dismiss，不写任何 Help seen（Tips ≠ L1）。 */
export function clearWaitTipsDismissed() {
  try {
    localStorage.removeItem(WAIT_TIPS_DISMISS_KEY);
    localStorage.removeItem(WAIT_TIPS_VERSION_KEY);
  } catch (_e) {
    /* ignore */
  }
}

/**
 * 仅重播等待提示（D-WT-04 W2）；不触发 L1 coach。
 */
export function replayWaitTips() {
  clearWaitTipsDismissed();
  trackHelpEvent("help_drawer_open", { source: "replay_wait_tips" });
  try {
    trackStudioEvent("wait_tips_replay", { source: "help_drawer" });
  } catch (_e) {
    /* ignore */
  }
  return HELP_COPY.replayWaitTipsDoneToast;
}

/**
 * 重播：清长图引导 + 精修保存 hint（及平台选择 seen）+ Wait Tips dismiss。
 * 不自动连环弹出；关闭后展示 replayDoneToast。
 */
export function replayHelpHints() {
  clearLongshotHelpSeen();
  clearRefineSaveSeen();
  clearPlatformPickSeen();
  clearBookendsPickSeen();
  clearCapabilityCardSeen();
  clearHomeStubBannerDismissed();
  clearStubHintSeen();
  clearWaitTipsDismissed();
  // 顺带清部分 legacy per-trip 脉冲键（非必须）
  try {
    var keys = [];
    for (var i = 0; i < localStorage.length; i++) {
      var k = localStorage.key(i);
      if (k && k.indexOf(LEGACY_PULSE_PREFIX) === 0) keys.push(k);
    }
    keys.forEach(function (key) {
      localStorage.removeItem(key);
    });
  } catch (_e2) {
    /* ignore */
  }
  trackHelpEvent("help_drawer_open", { source: "replay" });
  return HELP_COPY.replayDoneToast;
}

export function getHelpItem(itemId) {
  var id = String(itemId || "").toUpperCase();
  var items = HELP_COPY.helpItems || [];
  for (var i = 0; i < items.length; i++) {
    if (items[i].id === id) return items[i];
  }
  return null;
}

/**
 * 忙碌态零 L1（D-HELP-08′）：导入 Job / layoutUpdating / 长图导出中 / 导出拦截 Modal。
 * D-DLLM-13：能力卡**同帧可见**时亦阻塞（仅 DOM 可见态；不含 session suppress，
 * 以免挡预览关键 tip）。首页非关键自动 coach 关闭后压制请用
 * shouldDeferHomeHelpL1ForCapabilityCard。
 */
export function isHelpL1Blocked(root) {
  if (_ssGet(SS.activeJobId)) return true;
  if (_readJsonSs(LAYOUT_UPDATING_KEY)) return true;
  if (typeof document !== "undefined") {
    if (document.body && document.body.classList.contains("studio-modal-open")) {
      return true;
    }
    if (document.querySelector(".studio__modal-backdrop")) return true;
    // D-DLLM-13：能力卡同帧优先
    var cap = document.getElementById("studio-capability-card-root");
    if (cap && !cap.hidden) return true;
  }
  if (root) {
    if (root._exportDockActive) return true;
    var btn =
      root.querySelector(".preview-toolbar__dock-btn--longshot") ||
      root.querySelector("[data-longshot-primary]");
    if (btn && btn.classList.contains("preview-toolbar__longshot--running")) {
      return true;
    }
    var zone = root.querySelector(".preview-toolbar__export-zone--running");
    if (zone) return true;
  }
  return false;
}

export function isCapabilityCardSeen() {
  return _lsGet(HELP_LS.capabilityCardSeen) === "1";
}

export function markCapabilityCardSeen() {
  _lsSet(HELP_LS.capabilityCardSeen, "1");
}

export function clearCapabilityCardSeen() {
  try {
    localStorage.removeItem(HELP_LS.capabilityCardSeen);
  } catch (_e) {
    /* ignore */
  }
  try {
    sessionStorage.removeItem(CAPABILITY_SUPPRESS_HELP_SS);
  } catch (_e2) {
    /* ignore */
  }
}

export function markCapabilityCardSuppressHelpL1() {
  try {
    sessionStorage.setItem(CAPABILITY_SUPPRESS_HELP_SS, "1");
  } catch (_e) {
    /* ignore */
  }
}

export function isCapabilityCardSuppressingHelpL1() {
  return _ssGet(CAPABILITY_SUPPRESS_HELP_SS) === "1";
}

export function isHomeStubBannerDismissed() {
  return _lsGet(HELP_LS.homeStubBannerDismissed) === "1";
}

export function markHomeStubBannerDismissed() {
  _lsSet(HELP_LS.homeStubBannerDismissed, "1");
}

export function clearHomeStubBannerDismissed() {
  try {
    localStorage.removeItem(HELP_LS.homeStubBannerDismissed);
  } catch (_e) {
    /* ignore */
  }
}

export function isStubHintSeen() {
  return _lsGet(HELP_LS.stubHintSeen) === "1";
}

export function markStubHintSeen() {
  _lsSet(HELP_LS.stubHintSeen, "1");
}

export function clearStubHintSeen() {
  try {
    localStorage.removeItem(HELP_LS.stubHintSeen);
  } catch (_e) {
    /* ignore */
  }
}

/**
 * T-CAP-05 · 首次预览本机文案 tip（在长图 tip 之后或已见过后出现）。
 * @param {(msg: string, opts?: object) => void} [showToast]
 * @returns {boolean}
 */
export function maybeShowStubNarrateTip(showToast) {
  if (isStubHintSeen()) return false;
  if (isHelpL1Blocked()) return false;
  if (isLongshotHelpActive()) return false;
  // 长图关键 tip 未出示过：让位，稍后再试由调用方重试
  if (_lsGet(HELP_LS.previewLongshotSeen) !== "1") return false;
  markStubHintSeen();
  trackHelpEvent("help_coach_show", { touchpoint: "T-CAP-05" });
  if (typeof showToast === "function") {
    showToast(HELP_COPY.stubNarrateTip || "当前为本机文案（可随时在设置中升级）", {
      duration: 4200,
    });
  }
  return true;
}

/**
 * 首页非关键自动 Help L1：能力卡优先或本会话已压制（D-DLLM-13）。
 * 预览长图 tip 等关键路径勿调用此门禁（继续只用 isHelpL1Blocked 的忙碌态部分）。
 */
export function shouldDeferHomeHelpL1ForCapabilityCard() {
  if (isCapabilityCardSuppressingHelpL1()) return true;
  try {
    if (typeof document !== "undefined") {
      var cap = document.getElementById("studio-capability-card-root");
      if (cap && !cap.hidden) return true;
    }
  } catch (_e) {
    /* ignore */
  }
  return false;
}

export function prefersReducedMotion() {
  try {
    return (
      typeof window !== "undefined" &&
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  } catch (_e) {
    return false;
  }
}

/**
 * publishGuide 优先；空则三要素兜底（D-HELP-09）。
 * @returns {{ kind: 'publishGuide'|'fallback', text: string, lines: string[] }}
 */
export function resolvePublishGuide(result) {
  result = result || {};
  var guide = String(result.publishGuide || "").trim();
  if (guide) {
    return { kind: "publishGuide", text: guide, lines: [guide] };
  }
  var lines = HELP_COPY.publishGuideFallback.slice();
  return {
    kind: "fallback",
    text: lines.join("\n"),
    lines: lines,
  };
}

function _longshotBtn(root) {
  if (!root) return null;
  return (
    root.querySelector(".preview-toolbar__dock-btn--longshot") ||
    root.querySelector(".preview-toolbar__longshot") ||
    root.querySelector("[data-longshot-primary]")
  );
}

function _removePulse(root) {
  var btn = _longshotBtn(root);
  if (!btn) return;
  btn.classList.remove("preview-toolbar__dock-btn--pulse");
  btn.classList.remove("preview-toolbar__menu-btn--pulse");
  btn.classList.remove("preview-toolbar__dock-btn--pulse-static");
}

function _applyPulse(root) {
  var btn = _longshotBtn(root);
  if (!btn) return;
  if (prefersReducedMotion()) {
    btn.classList.add("preview-toolbar__dock-btn--pulse-static");
  } else {
    btn.classList.add("preview-toolbar__dock-btn--pulse");
  }
  btn.setAttribute("aria-label", HELP_COPY.longshotAria);
}

function _hideLongshotTip() {
  if (_tipEscHandler) {
    document.removeEventListener("keydown", _tipEscHandler, true);
    _tipEscHandler = null;
  }
  if (_tipEl && _tipEl.parentNode) {
    _tipEl.parentNode.removeChild(_tipEl);
  }
  _tipEl = null;
}

function _showLongshotVisibleTip(root, onDismiss) {
  _hideLongshotTip();
  var el = document.createElement("div");
  el.id = "preview-help-longshot-tip";
  el.className = "preview-help-longshot-tip";
  el.setAttribute("role", "status");
  el.setAttribute("aria-live", "polite");

  var text = document.createElement("p");
  text.className = "preview-help-longshot-tip__text";
  text.textContent = HELP_COPY.longshotTip;

  var dismiss = document.createElement("button");
  dismiss.type = "button";
  dismiss.className = "preview-help-longshot-tip__dismiss";
  dismiss.textContent = "知道了";

  el.appendChild(text);
  el.appendChild(dismiss);
  document.body.appendChild(el);
  _tipEl = el;

  function finish(reason) {
    _hideLongshotTip();
    if (typeof onDismiss === "function") onDismiss(reason);
  }

  dismiss.addEventListener("click", function () {
    finish("got_it");
  });
  _tipEscHandler = function (e) {
    if (e.key === "Escape") {
      e.stopPropagation();
      finish("esc");
    }
  };
  document.addEventListener("keydown", _tipEscHandler, true);

  // 脉冲周期结束：可见 tip 自动收起并置 seen（与精修 tip 同类时长略长）
  window.setTimeout(function () {
    if (_tipEl === el) finish("pulse_end");
  }, 8000);

  trackHelpEvent("help_coach_show", {
    touchpoint: "T-PREVIEW-LONGSHOT",
    tripId: null,
  });
}

/**
 * F10 / §3.5 · pending「更新版面」主待办在时，延后长图 tip（不挡主行动）。
 */
export function isHelpLongshotDeferred(root, opts) {
  opts = opts || {};
  if (typeof opts.isLayoutPending === "function" && opts.isLayoutPending()) {
    return true;
  }
  if (root && root._layoutPendingHelpDefer) return true;
  if (typeof document !== "undefined") {
    var warn = document.querySelector(".preview-task-dock--warn");
    if (warn && !warn.hidden) return true;
  }
  return false;
}

/**
 * 评估并展示首访长图 L1：脉冲 + 可见 tip + aria（D-HELP-03′）。
 * 忙碌态跳过；idle 后可再调本函数补评估（AC-HELP-13a）。
 * @returns {boolean} 是否本次展示
 */
export function maybeShowLongshotHelp(root, tripId, opts) {
  opts = opts || {};
  if (hasLongshotHelpSeen()) return false;
  if (isHelpL1Blocked(root) || isHelpLongshotDeferred(root, opts)) {
    if (!opts.skipIdleQueue) queueLongshotHelpIdleEval(root, tripId, opts);
    return false;
  }
  if (_longshotHelpActive) return false;

  var btn = _longshotBtn(root);
  if (!btn) return false;

  _longshotHelpActive = true;
  _applyPulse(root);

  var delay = typeof opts.delayMs === "number" ? opts.delayMs : 400;
  window.setTimeout(function () {
    if (hasLongshotHelpSeen()) return;
    if (isHelpL1Blocked(root) || isHelpLongshotDeferred(root, opts)) {
      _removePulse(root);
      _longshotHelpActive = false;
      queueLongshotHelpIdleEval(root, tripId, opts);
      return;
    }
    _showLongshotVisibleTip(root, function (reason) {
      markLongshotHelpSeen({ reason: reason || "dismiss" });
      _removePulse(root);
    });
  }, delay);

  return true;
}

/**
 * 用户点「长图」：置 seen、清脉冲/tip。
 */
export function onLongshotHelpTargetClick(root) {
  _hideLongshotTip();
  markLongshotHelpSeen({ reason: "target_click" });
  _removePulse(root);
}

export function queueLongshotHelpIdleEval(root, tripId, opts) {
  opts = opts || {};
  if (_idleEvalQueued || hasLongshotHelpSeen()) return;
  _idleEvalQueued = true;
  var tries = 0;
  var timer = window.setInterval(function () {
    tries += 1;
    if (hasLongshotHelpSeen()) {
      window.clearInterval(timer);
      _idleEvalQueued = false;
      return;
    }
    if (!isHelpL1Blocked(root) && !isHelpLongshotDeferred(root, opts)) {
      window.clearInterval(timer);
      _idleEvalQueued = false;
      maybeShowLongshotHelp(root, tripId, {
        skipIdleQueue: true,
        delayMs: 300,
        isLayoutPending: opts.isLayoutPending,
      });
      return;
    }
    if (tries > 120) {
      window.clearInterval(timer);
      _idleEvalQueued = false;
    }
  }, 500);
}

/** @deprecated 兼容旧名：门禁改走 hasLongshotHelpSeen */
export function shouldShowExportPulse(_tripId) {
  return !hasLongshotHelpSeen();
}

/** @deprecated 兼容旧名：双写全局，忽略 tripId 门禁写入 */
export function markExportPulseSeen(_tripId) {
  markLongshotHelpSeen({ reason: "export_success" });
}
