/**

 * Output Recipe V1 · 客户端 Band / CTA / 意图卡（Phase A）

 * 与 travelogue.export.output_recipe.resolve 对齐；flag 关则不介入。

 * D-OR-27 / Share-Ready：Band / needs_intent 以服务端 kept_n 为准。

 * 纯逻辑见 output-recipe-logic.js（SFH W0b）。

 */

"use strict";



import { trackStudioEvent } from "./analytics.js";

import { getJson } from "./http.js";

import {

  INTENT_TO_PLATFORM,

  PLATFORM_TO_INTENT,

  DEFAULT_BANDS,

  parseStudioOutputRecipeConfig,

  classifyBand as classifyBandWithCfg,

  needsFullExportConfirm as needsFullExportConfirmWithCfg,

  resolveClientRecipe as resolveClientRecipeWithCfg,

  mapServerRecipePayload,

  readSessionIntentFromStorage,

  writeSessionIntentToStorage,

  clearSessionIntentFromStorage,

} from "./output-recipe-logic.js";



export { INTENT_TO_PLATFORM, PLATFORM_TO_INTENT };



/** PRD-SHARE-READY §4.5 · recipe API 失败冻结 toast */

export var RECIPE_API_FAIL_TOAST =

  "暂时按微信群长图导出，可稍后重试选分享方式。";



var _cfg = {

  enabled: false,

  sparseMax: DEFAULT_BANDS.sparseMax,

  ambiguousMax: DEFAULT_BANDS.ambiguousMax,

  narrativeChapterHintAt: DEFAULT_BANDS.narrativeChapterHintAt,

};



/** @type {Record<string, { keptN: number, ts: number }>} */

var _keptNCache = {};



export function applyOutputRecipeConfig(studioCfg) {

  _cfg = parseStudioOutputRecipeConfig(studioCfg);

}



export function isOutputRecipeEnabled() {

  return !!_cfg.enabled;

}



export function narrativeChapterHintAt() {

  return _cfg.narrativeChapterHintAt;

}



/** D-OR-07 · Narrative≥hint 选整卷时须二次确认 */

export function needsFullExportConfirm(keptN, mode, platform) {

  return needsFullExportConfirmWithCfg(keptN, mode, platform, _cfg);

}



export function classifyBand(keptN) {

  return classifyBandWithCfg(keptN, _cfg);

}



export function readSessionIntent(tripId) {

  try {

    return readSessionIntentFromStorage(sessionStorage, tripId);

  } catch (e) {

    return null;

  }

}



export function writeSessionIntent(tripId, intent) {

  try {

    writeSessionIntentToStorage(sessionStorage, tripId, intent);

  } catch (e) {}

}



export function clearSessionIntent(tripId) {

  try {

    clearSessionIntentFromStorage(sessionStorage, tripId);

  } catch (e) {}

}



export function getCachedKeptN(tripId) {

  var c = _keptNCache[String(tripId || "")];

  return c && c.keptN != null ? Number(c.keptN) : null;

}



export function setCachedKeptN(tripId, keptN) {

  var n = Number(keptN);

  if (!tripId || !isFinite(n) || n < 0) return;

  _keptNCache[String(tripId)] = { keptN: n, ts: Date.now() };

}



/**

 * 将服务端 GET /output-recipe 载荷映射为客户端 tipRecipe。

 * session intent 仍优先（与 resolveClientRecipe 一致）。

 */

export function tipRecipeFromServerPayload(body, tripId, entrypoint) {

  var tip = mapServerRecipePayload(body, entrypoint, _cfg, readSessionIntent(tripId));

  if (tip && tip.keptN != null) setCachedKeptN(tripId, tip.keptN);

  return tip;

}



/**

 * D-OR-27 · 拉取服务端 recipe（权威 kept_n）。

 * @returns {Promise<{ ok: boolean, tipRecipe?: object, keptN?: number, failed?: boolean }>}

 */

export function fetchServerRecipe(tripId, entrypoint) {

  var tid = String(tripId || "");

  var ep = entrypoint || "preview";

  if (!tid) {

    return Promise.resolve({ ok: false, failed: true });

  }

  var url =

    "/__travelogue/output-recipe?tripId=" +

    encodeURIComponent(tid) +

    "&entrypoint=" +

    encodeURIComponent(ep);

  return getJson(url)

    .then(function (result) {

      if (result.status !== 200 || !result.body || !result.body.ok) {

        return { ok: false, failed: true };

      }

      var tipRecipe = tipRecipeFromServerPayload(result.body, tid, ep);

      return {

        ok: true,

        tipRecipe: tipRecipe,

        keptN: tipRecipe.keptN,

        failed: false,

      };

    })

    .catch(function () {

      return { ok: false, failed: true };

    });

}



/**

 * @returns {{ band: string, needsIntent: boolean, intent: string|null, platform: string|null, ctaLabel: string, subtitle: string, userHints: string[] }}

 */

export function resolveClientRecipe(keptN, tripId, entrypoint) {

  return resolveClientRecipeWithCfg(keptN, entrypoint, _cfg, readSessionIntent(tripId));

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

export function showAmbiguousIntentCard(keptN, userHints) {

  return new Promise(function (resolve) {

    var n = Number(keptN) || 0;

    var nGrid = Math.min(9, Math.max(0, n));

    trackIntentShown({

      band: "ambiguous",

      options: ["chat_longshot", "moments_grid", "moments_scroll"],

      phase: "B",

      kept_n: n,

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

    var hint0 =

      Array.isArray(userHints) && userHints.length ? String(userHints[0] || "").trim() : "";

    title.textContent = hint0 || ("这趟精选了 " + n + " 张，你想怎么发？");



    var body = document.createElement("div");

    body.className = "studio__modal-body";



    var selected = "chat_longshot";

    var options = [

      {

        intent: "chat_longshot",

        label: "微信群 · 长图",

        desc: "整篇游记发到群里 · 推荐",

        primary: true,

      },

      {

        intent: "moments_grid",

        label: "朋友圈 · 九宫格",

        desc: "约 " + nGrid + " 张 1:1 · 有几张发几张",

        primary: false,

      },

      {

        intent: "moments_scroll",

        label: "朋友圈 · 长图连读",

        desc: "最多 9 段，滑动连读",

        primary: false,

      },

    ];



    options.forEach(function (opt, idx) {

      var btn = document.createElement("button");

      btn.type = "button";

      // USR-02 · 唯一 primary；其余 secondary 描边

      btn.className = opt.primary

        ? "studio__btn studio__btn--primary studio__btn--block output-recipe-intent--primary"

        : "studio__btn studio__btn--ghost studio__btn--block";

      btn.style.display = "block";

      btn.style.width = "100%";

      btn.style.textAlign = "left";

      btn.style.marginBottom = "8px";

      btn.setAttribute("data-output-intent", opt.intent);

      btn.setAttribute("data-intent-weight", opt.primary ? "primary" : "secondary");

      btn.setAttribute("aria-pressed", idx === 0 ? "true" : "false");

      btn.innerHTML =

        "<strong>" +

        opt.label +

        "</strong><br><span style='opacity:.85;font-size:12px'>" +

        opt.desc +

        "</span>";

      btn.addEventListener("click", function () {

        selected = opt.intent;

        body.querySelectorAll("[data-output-intent]").forEach(function (el) {

          var on = el === btn;

          el.setAttribute("aria-pressed", on ? "true" : "false");

          var isPrimaryOpt = el.getAttribute("data-intent-weight") === "primary";

          // 选中态：主选项保持 primary 样式；次选项选中时加 outline

          if (isPrimaryOpt) {

            el.className = on

              ? "studio__btn studio__btn--primary studio__btn--block output-recipe-intent--primary"

              : "studio__btn studio__btn--ghost studio__btn--block";

            el.style.outline = "";

          } else {

            el.className = "studio__btn studio__btn--ghost studio__btn--block";

            el.style.outline = on ? "2px solid currentColor" : "";

          }

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

    primary.setAttribute("data-output-recipe-confirm", "export");

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


