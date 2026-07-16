/**
 * Output Recipe V1 · 客户端 Band / CTA / 意图卡（Phase A）
 * 与 travelogue.export.output_recipe.resolve 对齐；flag 关则不介入。
 */
"use strict";

import { trackStudioEvent } from "./analytics.js";

export var INTENT_TO_PLATFORM = {
  chat_longshot: "wechat_chat",
  moments_scroll: "wechat_moments",
  moments_grid: "moments_grid",
};

export var PLATFORM_TO_INTENT = {
  wechat_chat: "chat_longshot",
  wechat_moments: "moments_scroll",
  moments_grid: "moments_grid",
};

var _cfg = {
  enabled: false,
  sparseMax: 9,
  ambiguousMax: 30,
  narrativeChapterHintAt: 50,
};

var SESSION_INTENT_PREFIX = "travelogue.studio.outputIntent.";

export function applyOutputRecipeConfig(studioCfg) {
  var or = (studioCfg && (studioCfg.outputRecipe || studioCfg.output_recipe)) || {};
  var bands = or.bands || {};
  _cfg.enabled = or.enabled === true;
  _cfg.sparseMax = Number(bands.sparseMax != null ? bands.sparseMax : bands.sparse_max) || 9;
  _cfg.ambiguousMax =
    Number(bands.ambiguousMax != null ? bands.ambiguousMax : bands.ambiguous_max) || 30;
  _cfg.narrativeChapterHintAt =
    Number(
      bands.narrativeChapterHintAt != null
        ? bands.narrativeChapterHintAt
        : bands.narrative_chapter_hint_at
    ) || 50;
}

export function isOutputRecipeEnabled() {
  return !!_cfg.enabled;
}

export function narrativeChapterHintAt() {
  return _cfg.narrativeChapterHintAt;
}

/** D-OR-07 · Narrative≥hint 选整卷时须二次确认 */
export function needsFullExportConfirm(keptN, mode, platform) {
  if (!_cfg.enabled) return false;
  if ((platform || "wechat_chat") !== "wechat_chat") return false;
  if ((mode || "chapter") !== "full") return false;
  var n = Number(keptN) || 0;
  return classifyBand(n) === "narrative" && n >= _cfg.narrativeChapterHintAt;
}

export function classifyBand(keptN) {
  var n = Number(keptN) || 0;
  if (n <= _cfg.sparseMax) return "sparse";
  if (n <= _cfg.ambiguousMax) return "ambiguous";
  return "narrative";
}

export function readSessionIntent(tripId) {
  try {
    var raw = sessionStorage.getItem(SESSION_INTENT_PREFIX + String(tripId || ""));
    if (!raw) return null;
    var parsed = JSON.parse(raw);
    return parsed && parsed.intent ? String(parsed.intent) : null;
  } catch (e) {
    return null;
  }
}

export function writeSessionIntent(tripId, intent) {
  try {
    sessionStorage.setItem(
      SESSION_INTENT_PREFIX + String(tripId || ""),
      JSON.stringify({ intent: intent, ts: Date.now() })
    );
  } catch (e) {}
}

export function clearSessionIntent(tripId) {
  try {
    sessionStorage.removeItem(SESSION_INTENT_PREFIX + String(tripId || ""));
  } catch (e) {}
}

/**
 * @returns {{ band: string, needsIntent: boolean, intent: string|null, platform: string|null, ctaLabel: string, subtitle: string, userHints: string[] }}
 */
export function resolveClientRecipe(keptN, tripId, entrypoint) {
  var band = classifyBand(keptN);
  var ep = entrypoint || "preview";
  if (!_cfg.enabled) {
    return {
      band: band,
      needsIntent: false,
      intent: "chat_longshot",
      platform: "wechat_chat",
      ctaLabel: "导出长图",
      subtitle: "",
      userHints: [],
      source: "flag_disabled",
    };
  }

  var sessionIntent = readSessionIntent(tripId);
  if (sessionIntent && INTENT_TO_PLATFORM[sessionIntent]) {
    return _recipeFromIntent(sessionIntent, band, keptN, "session_override");
  }

  if (band === "ambiguous") {
    if (ep === "preview") {
      return {
        band: band,
        needsIntent: true,
        intent: null,
        platform: null,
        ctaLabel: "选择并导出",
        subtitle: "",
        userHints: ["这趟精选了 " + keptN + " 张，你想怎么发？"],
        source: "band_default",
      };
    }
    // shelf fallback
    return {
      band: band,
      needsIntent: false,
      intent: "chat_longshot",
      platform: "wechat_chat",
      ctaLabel: "导出长图 · 发微信群",
      subtitle: "",
      userHints: ["可到预览选择其他分享方式"],
      source: "band_default",
    };
  }

  if (band === "narrative") {
    var hints = [];
    if (keptN >= _cfg.narrativeChapterHintAt) {
      hints.push("照片较多，已按章节拆成多张，方便发送");
    }
    return {
      band: band,
      needsIntent: false,
      intent: "chat_longshot",
      platform: "wechat_chat",
      ctaLabel: "按章导出长图 · 发微信群",
      subtitle: hints[0] || "",
      userHints: hints,
      source: "band_default",
    };
  }

  // sparse
  return {
    band: band,
    needsIntent: false,
    intent: "chat_longshot",
    platform: "wechat_chat",
    ctaLabel: "导出长图 · 发微信群",
    subtitle: "",
    userHints: [],
    source: "band_default",
  };
}

function _recipeFromIntent(intent, band, keptN, source) {
  var platform = INTENT_TO_PLATFORM[intent] || "wechat_chat";
  var nGrid = Math.min(9, Math.max(0, Number(keptN) || 0));
  var cta =
    intent === "moments_grid"
      ? "导出朋友圈 · 九宫格"
      : intent === "moments_scroll"
        ? "导出朋友圈 · 长图连读"
        : band === "narrative"
          ? "按章导出长图 · 发微信群"
          : "导出长图 · 发微信群";
  var hints = [];
  if (intent === "moments_grid") {
    hints.push("约 " + nGrid + " 张 1:1 · 有几张发几张");
  }
  return {
    band: band,
    needsIntent: false,
    intent: intent,
    platform: platform,
    ctaLabel: cta,
    subtitle: hints[0] || "",
    userHints: hints,
    source: source || "intent_choice",
  };
}

export function trackRecipeResolve(meta) {
  trackStudioEvent("output_recipe_resolve", meta || {});
}

export function trackIntentShown(meta) {
  trackStudioEvent("output_intent_shown", meta || {});
}

export function trackIntentSelected(meta) {
  trackStudioEvent("output_intent_selected", meta || {});
}

/**
 * Ambiguous 意图卡（Phase B0：发群 / 九宫格 / 长图连读）
 * @returns {Promise<{intent: string, exportNow: boolean}|null>}
 */
export function showAmbiguousIntentCard(keptN) {
  return new Promise(function (resolve) {
    var n = Number(keptN) || 0;
    var nGrid = Math.min(9, Math.max(0, n));
    trackIntentShown({
      band: "ambiguous",
      options: ["chat_longshot", "moments_grid", "moments_scroll"],
      phase: "B",
      kept_n: keptN,
    });

    var backdrop = document.createElement("div");
    backdrop.className = "studio__modal-backdrop";
    backdrop.setAttribute("data-output-recipe-intent", "1");

    var modal = document.createElement("div");
    modal.className = "studio__modal";
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.setAttribute("aria-label", "选择分享方式");

    var title = document.createElement("h3");
    title.textContent = "这趟精选了 " + keptN + " 张，你想怎么发？";

    var body = document.createElement("div");
    body.className = "studio__modal-body";

    var selected = "chat_longshot";
    var options = [
      {
        intent: "chat_longshot",
        label: "微信群 · 长图",
        desc: "整篇游记发到群里",
      },
      {
        intent: "moments_grid",
        label: "朋友圈 · 九宫格",
        desc: "约 " + nGrid + " 张 1:1 · 有几张发几张",
      },
      {
        intent: "moments_scroll",
        label: "朋友圈 · 长图连读",
        desc: "最多 9 段，滑动连读",
      },
    ];

    options.forEach(function (opt, idx) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "studio__btn studio__btn--ghost";
      btn.style.display = "block";
      btn.style.width = "100%";
      btn.style.textAlign = "left";
      btn.style.marginBottom = "8px";
      btn.setAttribute("data-output-intent", opt.intent);
      btn.setAttribute("aria-pressed", idx === 0 ? "true" : "false");
      if (idx === 0) btn.style.outline = "2px solid currentColor";
      btn.innerHTML =
        "<strong>" +
        opt.label +
        "</strong><br><span style='opacity:.75;font-size:12px'>" +
        opt.desc +
        "</span>";
      btn.addEventListener("click", function () {
        selected = opt.intent;
        body.querySelectorAll("[data-output-intent]").forEach(function (el) {
          el.setAttribute("aria-pressed", el === btn ? "true" : "false");
          el.style.outline = el === btn ? "2px solid currentColor" : "";
        });
      });
      body.appendChild(btn);
    });

    var actions = document.createElement("div");
    actions.className = "studio__modal-actions";

    var saveOnly = document.createElement("button");
    saveOnly.type = "button";
    saveOnly.className = "studio__btn studio__btn--ghost studio__btn--sm";
    saveOnly.textContent = "先选不导出";

    var primary = document.createElement("button");
    primary.type = "button";
    primary.className = "studio__btn studio__btn--sm studio__btn--primary";
    primary.textContent = "选择并导出";

    actions.appendChild(saveOnly);
    actions.appendChild(primary);
    modal.appendChild(title);
    modal.appendChild(body);
    modal.appendChild(actions);
    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);
    document.body.classList.add("studio-modal-open");

    function cleanup(result) {
      backdrop.remove();
      if (!document.querySelector(".studio__modal-backdrop")) {
        document.body.classList.remove("studio-modal-open");
      }
      resolve(result);
    }

    saveOnly.addEventListener("click", function () {
      trackIntentSelected({ intent: selected, remember_pref: false, export_now: false });
      cleanup({ intent: selected, exportNow: false });
    });
    primary.addEventListener("click", function () {
      trackIntentSelected({ intent: selected, remember_pref: false, export_now: true });
      cleanup({ intent: selected, exportNow: true });
    });
    backdrop.addEventListener("click", function (e) {
      if (e.target === backdrop) cleanup(null);
    });

    primary.focus();
  });
}
