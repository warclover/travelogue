/**
 * Travelogue Studio · Longshot 2.0 export settings panel (D-LNG2-28).
 * Popover UI lives here — keep preview-toolbar.js thin.
 */
"use strict";

export var LONGSHOT_EXPORT_PREFS_KEY = "travelogue.studio.longshotExportPrefs";
export var MOMENTS_COACH_KEY = "travelogue.studio.longshotMomentsCoachSeen";

export var PLATFORMS = {
  wechat_chat: {
    id: "wechat_chat",
    label: "微信群",
    cta: "导出长图",
    showSegmentMode: true,
  },
  wechat_moments: {
    id: "wechat_moments",
    label: "朋友圈",
    cta: "导出朋友圈配图",
    showSegmentMode: false,
    expectHtml:
      "将按完整照片生成 <strong>1–9 张</strong>配图（默认纯图、高度随图）· 预计 30–60 秒",
  },
  xiaohongshu: {
    id: "xiaohongshu",
    label: "小红书",
    cta: "导出小红书配图",
    showSegmentMode: false,
    showXhsOptions: true,
    expectHtml:
      "将生成 <strong>3:4</strong> 配图（auto 约 5–9 张）· 默认留白边填充",
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
    : ["wechat_moments", "xiaohongshu"];
  var out = ["wechat_chat"];
  list.forEach(function (id) {
    if (id && id !== "wechat_chat" && out.indexOf(id) < 0) {
      if (id === "wechat_moments" || id === "xiaohongshu") out.push(id);
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

export function shouldShowMomentsCoach() {
  try {
    return localStorage.getItem(MOMENTS_COACH_KEY) !== "1";
  } catch (e) {
    return true;
  }
}

export function markMomentsCoachSeen() {
  try {
    localStorage.setItem(MOMENTS_COACH_KEY, "1");
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
      return (
        '<button type="button" data-studio-longshot-platform="' +
        p.id +
        '">' +
        (p.label || id) +
        "</button>"
      );
    })
    .join("");

  return (
    '<p class="preview-toolbar__export-popover-title">导出设置</p>' +
    '<p class="preview-toolbar__export-popover-note">调整平台与清晰度；点左侧按钮开始导出。</p>' +
    '<div class="preview-toolbar__export-popover-field" data-field="platform">' +
    '<span class="preview-toolbar__export-popover-label">分享平台</span>' +
    '<div class="preview-toolbar__export-popover-seg" role="group">' +
    platformBtns +
    "</div></div>" +
    '<div class="preview-toolbar__export-popover-field" data-field="expect" hidden>' +
    '<span class="preview-toolbar__export-popover-label">预期</span>' +
    '<div class="preview-toolbar__export-expect" data-expect-body></div></div>' +
    '<div class="preview-toolbar__export-popover-field" data-field="mode">' +
    '<span class="preview-toolbar__export-popover-label">导出范围</span>' +
    '<div class="preview-toolbar__export-popover-seg" role="group">' +
    '<button type="button" data-studio-longshot-mode="chapter">按章导出</button>' +
    '<button type="button" data-studio-longshot-mode="full">完整长图</button>' +
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
    '<div class="preview-toolbar__export-popover-field" data-field="scale">' +
    '<span class="preview-toolbar__export-popover-label">清晰度</span>' +
    '<div class="preview-toolbar__export-popover-seg" role="group">' +
    '<button type="button" data-studio-longshot-scale="2">标准 2×</button>' +
    '<button type="button" data-studio-longshot-scale="3">高清 3×</button>' +
    "</div></div>" +
    '<p class="preview-toolbar__export-coach" data-field="coach" hidden></p>' +
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

  var xhsCount = pop.querySelector('[data-field="xhs-count"]');
  var xhsPad = pop.querySelector('[data-field="xhs-pad"]');
  if (xhsCount) xhsCount.hidden = !showXhs;
  if (xhsPad) xhsPad.hidden = !showXhs;

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
          " 张</strong> 3:4 配图（auto）· 默认留白边 · 预计 30–60 秒";
      } else if (showXhs && draft.slideCount != null) {
        expectBody.innerHTML =
          "将生成 <strong>" +
          draft.slideCount +
          " 张</strong> 3:4 配图 · 预计 30–60 秒";
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
    if (platform === "wechat_moments" && shouldShowMomentsCoach()) {
      coach.hidden = false;
      coach.textContent = "将按编号 01→09 选图发布到朋友圈。";
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
  };
  var draft = {
    platform: (initialDraft && initialDraft.platform) || "wechat_chat",
    mode: (initialDraft && initialDraft.mode) || "chapter",
    scale: (initialDraft && initialDraft.scale) || 2,
    slideCount: initialDraft ? initialDraft.slideCount : null,
    padMode: (initialDraft && initialDraft.padMode) || "letterbox",
  };

  function refresh() {
    syncPanelUI(pop, draft, uiOpts);
  }

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
      };
    },
    setDraft: function (next) {
      draft.platform = next.platform || draft.platform;
      draft.mode = next.mode || draft.mode;
      draft.scale = next.scale || draft.scale;
      draft.slideCount =
        next.slideCount == null ? null : clampXhsSlideCount(next.slideCount);
      draft.padMode = next.padMode || draft.padMode;
      refresh();
    },
    setUiOpts: function (nextOpts) {
      if (nextOpts && typeof nextOpts.smartCropEnabled === "boolean") {
        uiOpts.smartCropEnabled = nextOpts.smartCropEnabled;
      }
      if (nextOpts && nextOpts.photoCount != null) {
        uiOpts.photoCount = nextOpts.photoCount;
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
  if (platform === "wechat_moments") {
    title = "✓ " + n + " 张朋友圈配图已就绪";
  } else if (platform === "xiaohongshu") {
    title = "✓ " + n + " 张 3:4 配图已就绪";
  }
  return {
    title: title,
    publishGuide: result.publishGuide || "",
    userHint: result.userHint || "",
    outputs: result.outputs || [],
  };
}
