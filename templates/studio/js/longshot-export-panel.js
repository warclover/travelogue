// @ts-nocheck
/**
 * Travelogue Studio · Longshot 2.0 export settings panel (D-LNG2-28).
 * Popover UI lives here — keep preview-toolbar.js thin.
 */
"use strict";

import { HELP_COPY } from "./help-onboarding.js";

export var LONGSHOT_EXPORT_PREFS_KEY = "travelogue.studio.longshotExportPrefs";
export var MOMENTS_COACH_KEY = "travelogue.studio.longshotMomentsCoachSeen";

export var PLATFORMS = {
  wechat_chat: {
    id: "wechat_chat",
    label: "微信群",
    title: "微信群",
    subtitle: "长图 · 按序发群",
    cta: "导出长图",
    showSegmentMode: true,
  },
  wechat_moments: {
    id: "wechat_moments",
    label: "朋友圈 · 长图连读",
    title: "朋友圈",
    subtitle: "长图连读",
    cta: "导出朋友圈 · 长图连读",
    showSegmentMode: false,
    expectHtml:
      "将按完整画册切成 <strong>1–9 段</strong>长图连读（滑动连读）· 预计 30–60 秒",
  },
  poster_bric: {
    id: "poster_bric",
    label: "单张海报 · A4",
    title: "单张海报",
    subtitle: "A4 拼贴",
    cta: "导出 A4 海报",
    showSegmentMode: false,
    showCopyControls: false,
    expectHtml:
      "将导出 <strong>1 张 A4</strong> 竖版拼贴海报（3–9 张精选）",
  },
  xiaohongshu: {
    id: "xiaohongshu",
    label: "小红书 · 竖版海报",
    title: "小红书",
    subtitle: "3:4 拼贴海报",
    cta: "导出小红书海报",
    showSegmentMode: false,
    showXhsOptions: true,
    expectHtml:
      "将生成 <strong>N 张 3:4 竖版拼贴海报</strong>（非杂志截屏）· auto 约 3–9 张",
  },
  album_spread: {
    id: "album_spread",
    label: "画册印刷",
    title: "画册印刷",
    subtitle: "2.8:1 跨页",
    cta: "导出画册跨页",
    showSegmentMode: false,
    showCopyControls: false,
    expectHtml:
      "将导出多张 <strong>约 2.8:1</strong> 横版跨页拼贴（适合印刷 / 对页预览）",
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
    : ["wechat_moments", "xiaohongshu", "poster_bric", "album_spread"];
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
    var aw = s > 2 ? Math.round(1748 * 1.25) : 1748;
    var ah = s > 2 ? Math.round(2480 * 1.25) : 2480;
    return "A4 画布约 " + aw + "×" + ah + "px";
  }
  if (platformId === "xiaohongshu") {
    var xw = s > 2 ? Math.round(1080 * 1.25) : 1080;
    var xh = s > 2 ? Math.round(1440 * 1.25) : 1440;
    return "竖版海报约 " + xw + "×" + xh + "px（3:4）";
  }
  if (platformId === "album_spread") {
    return "画册跨页约 2800×1000px（2.8:1）";
  }
  if (platformId === "wechat_moments") {
    var mw = s === 3 ? 1284 : 856;
    return "长图切片宽约 " + mw + "px（428×" + s + "）";
  }
  var px = s === 3 ? 1284 : 856;
  return "输出宽约 " + px + "px（逻辑宽 428 × " + s + "）";
}
export var XHS_PRESET_COUNTS = { "6": true, "9": true, "12": true };

export function clampXhsSlideCount(value) {
  var n = parseInt(value, 10);
  if (!isFinite(n)) return null;
  return Math.max(XHS_SLIDE_COUNT_MIN, Math.min(XHS_SLIDE_COUNT_MAX, n));
}

export function isXhsPresetCount(slideCount) {
  return slideCount != null && !!XHS_PRESET_COUNTS[String(slideCount)];
}

export function isSmartCropUiEnabled(cfgStudio) {
  var l2 = (cfgStudio && cfgStudio.longshot2) || {};
  var sc = l2.smartCrop || l2.smart_crop || {};
  return sc.enabled === true;
}

export function readExportPrefs() {
  var defaults = {
    platform: "wechat_chat",
    mode: "chapter",
    scale: 2,
    slideCount: null,
    padMode: "letterbox",
    includeAppendix: false,
    density: "default",
  };
  try {
    var raw = localStorage.getItem(LONGSHOT_EXPORT_PREFS_KEY);
    if (!raw) return defaults;
    var parsed = JSON.parse(raw);
    return {
      platform: parsed.platform || defaults.platform,
      mode: parsed.mode === "full" || parsed.mode === "chapter" ? parsed.mode : "chapter",
      scale: parsed.scale === 3 ? 3 : 2,
      slideCount:
        parsed.slideCount == null ? null : clampXhsSlideCount(parsed.slideCount),
      padMode: parsed.padMode || "letterbox",
      includeAppendix: parsed.includeAppendix === true,
      density: parsed.density === "compact" ? "compact" : "default",
    };
  } catch (e) {
    return defaults;
  }
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

/** Dock / 窄栏短标签（AC-DFX-02 · 含 compose 出口，禁止回落到「发微信群」） */
export function shortCtaLabelForPlatform(platformId) {
  // PMX · 短标签须带导出动作；「连读」 alone 易被当成模式名而非主 CTA
  if (platformId === "wechat_moments") return "导出连读";
  if (platformId === "xiaohongshu") return "小红书";
  if (platformId === "poster_bric") return "A4海报";
  if (platformId === "album_spread") return "画册";
  return "发微信群";
}

/** 设置入口摘要 · 「当前将导出：…」 */
export function confirmedExportSummary(platformId) {
  var p = PLATFORMS[platformId] || PLATFORMS.wechat_chat;
  return "当前将导出：" + (p.label || p.title || platformId);
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
    return "当前将导出：" + confirmedLabel;
  }
  var draftLabel =
    (PLATFORMS[draft] && (PLATFORMS[draft].label || PLATFORMS[draft].title)) || draft;
  return "已改选：" + draftLabel + "（点「确定」后生效）· 金色按钮仍按：" + confirmedLabel;
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
 */
export function buildPanelHtml(platformIds) {
  var ids = platformIds && platformIds.length ? platformIds : ["wechat_chat", "wechat_moments"];
  var platformBtns = ids
    .map(function (id) {
      var p = PLATFORMS[id] || { id: id, label: id };
      var title = p.title || p.label || id;
      var sub = p.subtitle || "";
      var aria = p.label || title;
      return (
        '<button type="button" class="preview-toolbar__export-platform-card" ' +
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

  return (
    '<p class="preview-toolbar__export-popover-title">导出设置</p>' +
    '<p class="preview-toolbar__export-popover-note">选好后点「确定」，再点上方金色按钮开始导出。改「要不要字」会同步预览。</p>' +
    '<p class="preview-toolbar__export-confirmed-summary" data-export-confirmed-summary aria-live="polite"></p>' +
    '<p class="preview-toolbar__export-dual"><button type="button" class="preview-toolbar__export-dual-btn" data-ltn-dual-preview>对比网页与长图</button></p>' +
    '<div class="preview-toolbar__export-popover-body">' +
    '<div class="preview-toolbar__export-popover-field" data-field="platform">' +
    '<span class="preview-toolbar__export-popover-label">发到哪里</span>' +
    '<div class="preview-toolbar__export-platform-grid" role="radiogroup" aria-label="发到哪里">' +
    platformBtns +
    "</div></div>" +
    '<div class="preview-toolbar__export-popover-field preview-toolbar__export-copy-field" data-field="copy">' +
    '<span class="preview-toolbar__export-popover-label">长图要不要字</span>' +
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
    '<div class="preview-toolbar__export-popover-field" data-field="xhs-pad" hidden>' +
    '<span class="preview-toolbar__export-popover-label">填充</span>' +
    '<div class="preview-toolbar__export-popover-seg" role="group">' +
    '<button type="button" data-studio-xhs-pad="letterbox">留白边</button>' +
    '<button type="button" data-studio-xhs-pad="smart_crop" data-smart-crop-btn>智能裁切</button>' +
    "</div></div>" +
    '<div class="preview-toolbar__export-popover-field" data-field="xhs-copy-pack" hidden>' +
    '<span class="preview-toolbar__export-popover-label">文案包</span>' +
    '<button type="button" class="preview-toolbar__export-copy-pack-btn" data-action="copy-xhs-pack">复制文案包</button>' +
    '<p class="preview-toolbar__export-xhs-copy-hint" data-xhs-copy-hint>' +
    "标题和话题已备好 · 正文可粘贴后自填" +
    "</p></div>" +
    '<div class="preview-toolbar__export-popover-field" data-field="scale">' +
    '<span class="preview-toolbar__export-popover-label">清晰度</span>' +
    '<div class="preview-toolbar__export-popover-seg" role="group">' +
    '<button type="button" data-studio-longshot-scale="2" title="标准清晰度">标准</button>' +
    '<button type="button" data-studio-longshot-scale="3" title="更高清晰度">更清晰</button>' +
    "</div>" +
    '<p class="preview-toolbar__export-scale-hint" data-scale-hint>输出尺寸随导出目标变化</p>' +
    "</div>" +
    '<div class="preview-toolbar__export-popover-field" data-field="density">' +
    '<span class="preview-toolbar__export-popover-label">长图密度</span>' +
    '<div class="preview-toolbar__export-popover-seg" role="group">' +
    '<button type="button" data-studio-longshot-density="default">默认</button>' +
    '<button type="button" data-studio-longshot-density="compact">紧凑</button>' +
    "</div>" +
    '<p class="preview-toolbar__export-density-hint">切换后点确定将更新版面；导出前可「对比网页与长图」。</p>' +
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
export function syncPanelUI(pop, draft, opts) {
  if (!pop || !draft) return;
  opts = opts || {};
  var platform = draft.platform || "wechat_chat";
  var meta = PLATFORMS[platform] || PLATFORMS.wechat_chat;
  var showXhs = !!meta.showXhsOptions;
  var smartOn = opts.smartCropEnabled === true;

  pop.querySelectorAll("[data-studio-longshot-platform]").forEach(function (btn) {
    var on = btn.getAttribute("data-studio-longshot-platform") === platform;
    btn.classList.toggle("is-selected", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
    btn.setAttribute("aria-checked", on ? "true" : "false");
    if (!btn.getAttribute("role")) btn.setAttribute("role", "radio");
  });
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
  if (customInput && useCustom) {
    if (document.activeElement !== customInput) {
      customInput.value = String(draft.slideCount);
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
  if (modeField) modeField.hidden = !meta.showSegmentMode;

  var copyField = pop.querySelector('[data-field="copy"]');
  if (copyField) {
    // 海报 / 九宫格非长图文案语义，避免「长图要不要字」误导
    copyField.hidden = meta.showCopyControls === false;
  }
  var noteEl = pop.querySelector(".preview-toolbar__export-popover-note");
  if (noteEl) {
    noteEl.textContent =
      meta.showCopyControls === false
        ? "选好后点「确定」，再点上方金色按钮开始导出。"
        : "选好后点「确定」，再点上方金色按钮开始导出。改「要不要字」会同步预览。";
  }

  var xhsCount = pop.querySelector('[data-field="xhs-count"]');
  var xhsPad = pop.querySelector('[data-field="xhs-pad"]');
  var xhsPack = pop.querySelector('[data-field="xhs-copy-pack"]');
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
    if (meta.expectHtml) {
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
  };
  var draft = {
    platform: (initialDraft && initialDraft.platform) || "wechat_chat",
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
          platform: draft.platform,
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

  pop.querySelectorAll("[data-studio-longshot-platform]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      draft.platform = btn.getAttribute("data-studio-longshot-platform") || "wechat_chat";
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
        var prev = clampXhsSlideCount(draft.slideCount);
        draft.slideCount = prev != null ? prev : 8;
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
        platform: draft.platform,
        mode: draft.mode,
        scale: draft.scale,
        slideCount:
          draft.slideCount == null ? null : clampXhsSlideCount(draft.slideCount),
        padMode: draft.padMode,
        includeAppendix: !!draft.includeAppendix,
        density: draft.density === "compact" ? "compact" : "default",
      };
    },
    setDraft: function (next) {
      draft.platform = next.platform || draft.platform;
      draft.mode = next.mode || draft.mode;
      draft.scale = next.scale || draft.scale;
      draft.slideCount =
        next.slideCount == null ? null : clampXhsSlideCount(next.slideCount);
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
    title = "✓ A4 海报已就绪";
  } else if (platform === "wechat_moments") {
    title = "✓ " + n + " 张长图连读已就绪";
  } else if (platform === "xiaohongshu") {
    title = "✓ " + n + " 张竖版拼贴海报已就绪";
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
