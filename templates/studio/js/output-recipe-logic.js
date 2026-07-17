/**
 * Output Recipe · 纯逻辑（无 DOM / 无 fetch · node --test）
 * SFH W0b · 壳层见 output-recipe.js；成功服务端载荷映射优先采信服务端字段（R-SFH-04）。
 */
"use strict";

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

export var SESSION_INTENT_PREFIX = "travelogue.studio.outputIntent.";

/** 与 config/output_recipe_bands.yaml 默认及 FE Number(x)||default 行为对齐 */
export var DEFAULT_BANDS = {
  sparseMax: 9,
  ambiguousMax: 30,
  narrativeChapterHintAt: 50,
};

/**
 * 解析 studio.outputRecipe 配置（保留历史 Number(x)||default：合法 0 会回退默认）。
 * @returns {{ enabled: boolean, sparseMax: number, ambiguousMax: number, narrativeChapterHintAt: number }}
 */
export function parseStudioOutputRecipeConfig(studioCfg) {
  var or = (studioCfg && (studioCfg.outputRecipe || studioCfg.output_recipe)) || {};
  var bands = or.bands || {};
  return {
    enabled: or.enabled === true,
    sparseMax: Number(bands.sparseMax != null ? bands.sparseMax : bands.sparse_max) || 9,
    ambiguousMax:
      Number(bands.ambiguousMax != null ? bands.ambiguousMax : bands.ambiguous_max) || 30,
    narrativeChapterHintAt:
      Number(
        bands.narrativeChapterHintAt != null
          ? bands.narrativeChapterHintAt
          : bands.narrative_chapter_hint_at
      ) || 50,
  };
}

/**
 * 规范化阈值。
 * OR-X-05 冻结：非法 / NaN / 空 → Number(x)||default（与历史 FE 一致，不抛错）。
 * OR-X-06：关系合法性见 isBandThresholdOrderValid；normalize **不**自动改写乱序阈值。
 * @param {Partial<typeof DEFAULT_BANDS>|null|undefined} bands
 */
export function normalizeBands(bands) {
  var b = bands || {};
  return {
    sparseMax: Number(b.sparseMax) || DEFAULT_BANDS.sparseMax,
    ambiguousMax: Number(b.ambiguousMax) || DEFAULT_BANDS.ambiguousMax,
    narrativeChapterHintAt:
      Number(b.narrativeChapterHintAt) || DEFAULT_BANDS.narrativeChapterHintAt,
  };
}

/** OR-X-06 · sparseMax < ambiguousMax（规范化后）；乱序时仍可 classify，仅作护栏布尔 */
export function isBandThresholdOrderValid(bands) {
  var t = normalizeBands(bands);
  return t.sparseMax < t.ambiguousMax;
}

/**
 * @param {number|string|null|undefined} keptN
 * @param {Partial<typeof DEFAULT_BANDS>|null|undefined} bands
 * @returns {"sparse"|"ambiguous"|"narrative"}
 */
export function classifyBand(keptN, bands) {
  var t = normalizeBands(bands);
  var n = Number(keptN) || 0;
  if (n <= t.sparseMax) return "sparse";
  if (n <= t.ambiguousMax) return "ambiguous";
  return "narrative";
}

/**
 * @param {object} cfg { enabled, sparseMax, ambiguousMax, narrativeChapterHintAt }
 */
export function needsFullExportConfirm(keptN, mode, platform, cfg) {
  var c = cfg || {};
  if (!c.enabled) return false;
  if ((platform || "wechat_chat") !== "wechat_chat") return false;
  if ((mode || "chapter") !== "full") return false;
  var n = Number(keptN) || 0;
  var hint = Number(c.narrativeChapterHintAt) || DEFAULT_BANDS.narrativeChapterHintAt;
  return classifyBand(n, c) === "narrative" && n >= hint;
}

/**
 * @param {string|null|undefined} sessionIntent
 * @param {object} cfg
 * @returns {object} tipRecipe
 */
export function resolveClientRecipe(keptN, entrypoint, cfg, sessionIntent) {
  var c = cfg || { enabled: false };
  var band = classifyBand(keptN, c);
  var ep = entrypoint || "preview";
  if (!c.enabled) {
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

  if (sessionIntent && INTENT_TO_PLATFORM[sessionIntent]) {
    return recipeFromIntent(sessionIntent, band, keptN, "session_override");
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
    var hintAt = Number(c.narrativeChapterHintAt) || DEFAULT_BANDS.narrativeChapterHintAt;
    if (keptN >= hintAt) {
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

export function recipeFromIntent(intent, band, keptN, source) {
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

/**
 * 将服务端 GET /output-recipe 载荷映射为 tipRecipe。
 * 有 needs_intent / 合法 intent 时采信服务端 band；session intent 仍优先。
 * @param {object} cfg
 * @param {string|null|undefined} sessionIntent
 */
export function mapServerRecipePayload(body, entrypoint, cfg, sessionIntent) {
  var keptN = Number(
    body && body.keptN != null
      ? body.keptN
      : body && body.recipe && body.recipe.kept_n
  );
  if (!isFinite(keptN) || keptN < 0) keptN = 0;
  var ep = entrypoint || "preview";
  if (sessionIntent && INTENT_TO_PLATFORM[sessionIntent]) {
    var fromSession = recipeFromIntent(
      sessionIntent,
      classifyBand(keptN, cfg),
      keptN,
      "session_override"
    );
    fromSession.keptN = keptN;
    return fromSession;
  }
  var r = (body && body.recipe) || {};
  if (r.needs_intent) {
    return {
      band: r.band || classifyBand(keptN, cfg),
      needsIntent: true,
      intent: null,
      platform: null,
      ctaLabel: r.cta_label || "选择并导出",
      subtitle: "",
      userHints:
        r.user_hints && r.user_hints.length
          ? r.user_hints
          : ["这趟精选了 " + keptN + " 张，你想怎么发？"],
      source: "server",
      keptN: keptN,
    };
  }
  if (r.intent && INTENT_TO_PLATFORM[r.intent]) {
    var fromIntent = recipeFromIntent(
      r.intent,
      r.band || classifyBand(keptN, cfg),
      keptN,
      "server"
    );
    if (r.cta_label) fromIntent.ctaLabel = r.cta_label;
    if (r.user_hints && r.user_hints.length) fromIntent.userHints = r.user_hints;
    fromIntent.keptN = keptN;
    return fromIntent;
  }
  var local = resolveClientRecipe(keptN, ep, cfg, null);
  local.source = "server_kept_n";
  local.keptN = keptN;
  return local;
}

/** @param {{ getItem: Function }} storage */
export function readSessionIntentFromStorage(storage, tripId) {
  try {
    var raw = storage.getItem(SESSION_INTENT_PREFIX + String(tripId || ""));
    if (!raw) return null;
    var parsed = JSON.parse(raw);
    return parsed && parsed.intent ? String(parsed.intent) : null;
  } catch (e) {
    return null;
  }
}

/** @param {{ setItem: Function }} storage */
export function writeSessionIntentToStorage(storage, tripId, intent) {
  try {
    storage.setItem(
      SESSION_INTENT_PREFIX + String(tripId || ""),
      JSON.stringify({ intent: intent, ts: Date.now() })
    );
  } catch (e) {}
}

/** @param {{ removeItem: Function }} storage */
export function clearSessionIntentFromStorage(storage, tripId) {
  try {
    storage.removeItem(SESSION_INTENT_PREFIX + String(tripId || ""));
  } catch (e) {}
}
