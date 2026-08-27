/**
 * DPI W3 · portfolio dock chrome + export face (FE-DPI-01 / 02).
 */
"use strict";

import {
  formatOverflowDetail,
  formatOverflowLine,
  isPortfolioEdition,
  PORTFOLIO_PAGES_PLATFORM,
  portfolioDockCta,
  portfolioExportDefaultFaceSpec,
  portfolioExportSocialFaceSpec,
  nextCrossingDefaultPlatform,
  readPortfolioSocialPrefs,
  readToolbarEdition,
} from "./portfolio-export-logic.js";
import {
  overflowJournalCta,
  portfolioFlagOffBannerCopy,
  shouldShowPortfolioFlagOffBanner,
} from "./portfolio-edition-logic.js";

/**
 * @param {object|null|undefined} root
 * @param {object|null|undefined} entry
 * @returns {"journal"|"portfolio"}
 */
export function resolveTripEdition(root, entry) {
  if (entry && Object.prototype.hasOwnProperty.call(entry, "edition")) {
    return isPortfolioEdition(entry.edition) ? "portfolio" : "journal";
  }
  return readToolbarEdition(root);
}

/**
 * @returns {{ short: string, aria: string }}
 */
export function portfolioIdleCta() {
  return portfolioDockCta();
}

/**
 * @returns {{ title: string, edition: string, initPlatform: function(object): {platform: string, platforms: string[]} }}
 */
export function portfolioExportPopoverSpec(opts) {
  opts = opts || {};
  if (opts.face === "social") {
    var social = portfolioExportSocialFaceSpec();
    return {
      title: social.title,
      edition: "portfolio",
      face: "social",
      initPlatform: function () {
        var social = readPortfolioSocialPrefs();
        var platform = nextCrossingDefaultPlatform(social);
        return { platform: platform, platforms: [platform] };
      },
    };
  }
  var face = portfolioExportDefaultFaceSpec();
  return {
    title: face.title,
    edition: "portfolio",
    face: "default",
    initPlatform: function () {
      return { platform: PORTFOLIO_PAGES_PLATFORM, platforms: [PORTFOLIO_PAGES_PLATFORM] };
    },
  };
}

/**
 * @param {string} prefsPlatform
 * @param {{ pending?: string|null, afterLayout?: boolean }} [opts]
 * @returns {string}
 */
export function resolvePortfolioExportPlatform(prefsPlatform, opts) {
  opts = opts || {};
  if (opts.pending) return opts.pending;
  if (opts.afterLayout) return prefsPlatform;
  return PORTFOLIO_PAGES_PLATFORM;
}

var PORTFOLIO_EXPORT_ARMED_KEY = "travelogue.portfolioExportArmed.v1";
var _armedMem = null;

function _sessionStore() {
  try {
    if (typeof sessionStorage !== "undefined") return sessionStorage;
  } catch (_e) {}
  return null;
}

/**
 * 本册点过「确定」后主钮才开导。不写共享 prefs，避免游记 CTA 被页图 id 污染。
 * @param {string} tripId
 */
export function markPortfolioExportArmed(tripId) {
  var id = String(tripId || "").trim();
  if (!id) return;
  var payload = JSON.stringify({ tripId: id, ts: Date.now() });
  var store = _sessionStore();
  if (store) {
    try {
      store.setItem(PORTFOLIO_EXPORT_ARMED_KEY, payload);
      return;
    } catch (_eSet) {}
  }
  _armedMem = payload;
}

/**
 * @param {string} tripId
 * @returns {boolean}
 */
export function isPortfolioExportArmed(tripId) {
  var id = String(tripId || "").trim();
  if (!id) return false;
  var raw = null;
  var store = _sessionStore();
  if (store) {
    try {
      raw = store.getItem(PORTFOLIO_EXPORT_ARMED_KEY);
    } catch (_eGet) {}
  }
  if (!raw) raw = _armedMem;
  if (!raw) return false;
  try {
    var parsed = JSON.parse(raw);
    return !!(parsed && parsed.tripId === id);
  } catch (_eParse) {
    return false;
  }
}

export function clearPortfolioExportArmed() {
  var store = _sessionStore();
  if (store) {
    try {
      store.removeItem(PORTFOLIO_EXPORT_ARMED_KEY);
    } catch (_eDel) {}
  }
  _armedMem = null;
}

/**
 * 未确认先开面板；确认过本册后走页图导出。
 * @param {string} [tripId]
 * @returns {boolean}
 */
export function shouldSkipRecipeForPortfolioExport(tripId) {
  return !isPortfolioExportArmed(tripId);
}

/**
 * @param {object} root
 * @param {HTMLElement} btn
 * @param {{ isV4: boolean, updateDockTip: function(HTMLElement, string): void, emitSnrCtaLabel: function(string, string[]): void }} helpers
 * @returns {boolean} true when this face handled the CTA
 */
export function syncPortfolioCtaLabel(root, btn, helpers) {
  var packCta = portfolioDockCta();
  btn.removeAttribute("data-recipe-subtitle");
  if (helpers.isV4) {
    var packLabelEl = btn.querySelector(".preview-toolbar__dock-export-label");
    if (packLabelEl && !btn.classList.contains("preview-toolbar__longshot--running")) {
      packLabelEl.textContent = packCta.short;
    }
    btn.setAttribute("aria-label", packCta.aria);
    helpers.updateDockTip(btn, packCta.aria);
  } else if (!btn.classList.contains("preview-toolbar__longshot--running")) {
    btn.textContent = packCta.short;
    btn.setAttribute("aria-label", packCta.aria);
  } else {
    btn.setAttribute("aria-label", packCta.aria);
  }
  helpers.emitSnrCtaLabel(packCta.aria, [PORTFOLIO_PAGES_PLATFORM]);
  return true;
}

/**
 * @param {object|null|undefined} root
 * @param {object|null|undefined} entry
 */
export function applyPortfolioDockLogic(root, entry) {
  if (root) {
    root._dockCta =
      entry && entry.dockCta && entry.dockCta.aria
        ? { short: entry.dockCta.short || entry.dockCta.aria, aria: entry.dockCta.aria }
        : portfolioIdleCta();
    root._exportPopoverSpec = function () {
      return portfolioExportPopoverSpec({ face: root._fxiExportFace });
    };
    root._syncPortfolioCta = syncPortfolioCtaLabel;
    root._resolveExportPlatform = resolvePortfolioExportPlatform;
    root._skipRecipeForExport = shouldSkipRecipeForPortfolioExport;
    root._readPortfolioDraftPrefs = function (prefs) {
      return portfolioExportPopoverSpec({ face: root._fxiExportFace }).initPlatform(
        prefs
      );
    };
  }
  if (entry) {
    syncPortfolioOverflowBadge(root, entry.portfolio, entry);
    syncPortfolioFlagOffBanner(root, entry);
  }
}

/**
 * @param {object|null|undefined} root
 * @param {object|null|undefined} portfolio
 * @param {object|null|undefined} entry
 */
export function syncPortfolioOverflowBadge(root, portfolio, entry) {
  var host = root || (typeof document !== "undefined" ? document.body : null);
  if (!host || !host.querySelector) return;
  var line =
    (entry && entry.overflowLine) ||
    (root && root._overflowLine) ||
    formatOverflowLine(portfolio);
  var detail =
    (entry && entry.overflowDetail) ||
    (root && root._overflowDetail) ||
    formatOverflowDetail(portfolio);
  var cta =
    (entry && entry.overflowCta) ||
    (root && root._overflowCta) ||
    "";
  var el = (typeof document !== "undefined" ? document : host).querySelector(
    ".preview-portfolio-overflow"
  );
  if (!line) {
    if (el) el.hidden = true;
    return;
  }
  if (!el && typeof document !== "undefined") {
    el = document.createElement("div");
    el.className = "preview-portfolio-overflow";
    el.setAttribute("role", "status");
    document.body.appendChild(el);
  }
  if (!el) return;
  el.hidden = false;
  if (detail) el.setAttribute("title", detail);
  else el.removeAttribute("title");
  el.replaceChildren();
  el.appendChild(document.createTextNode(cta ? line + " · " : line));
  if (!cta) return;
  var btn = document.createElement("button");
  btn.type = "button";
  btn.className = "preview-portfolio-overflow__exit";
  btn.textContent = cta || overflowJournalCta();
  btn.addEventListener("click", function (ev) {
    ev.preventDefault();
    if (host && typeof host._onPortfolioToJournal === "function") {
      host._onPortfolioToJournal();
      return;
    }
    if (root && typeof root._onPortfolioToJournal === "function") {
      root._onPortfolioToJournal();
    }
  });
  el.appendChild(btn);
}

/**
 * @param {object|null|undefined} root
 * @param {object|null|undefined} entry
 */
export function syncPortfolioFlagOffBanner(root, entry) {
  var host = root || (typeof document !== "undefined" ? document.body : null);
  if (!host || !host.querySelector) return;
  var enabled = entry && entry.portfolioPipelineEnabled === true;
  var edition =
    entry && Object.prototype.hasOwnProperty.call(entry, "edition")
      ? entry.edition
      : root && root._edition;
  var show = shouldShowPortfolioFlagOffBanner(edition, enabled);
  var el = (typeof document !== "undefined" ? document : host).querySelector(
    ".preview-portfolio-flag-off"
  );
  if (!show) {
    if (el) el.hidden = true;
    return;
  }
  if (!el && typeof document !== "undefined") {
    el = document.createElement("div");
    el.className = "preview-portfolio-flag-off";
    el.setAttribute("role", "status");
    document.body.appendChild(el);
  }
  if (!el) return;
  var copy = portfolioFlagOffBannerCopy();
  el.hidden = false;
  el.replaceChildren();
  el.appendChild(document.createTextNode(copy.text + " · "));
  var btn = document.createElement("button");
  btn.type = "button";
  btn.className = "preview-portfolio-flag-off__exit";
  btn.textContent = copy.cta;
  btn.addEventListener("click", function (ev) {
    ev.preventDefault();
    if (host && typeof host._onPortfolioToJournal === "function") {
      host._onPortfolioToJournal();
      return;
    }
    if (root && typeof root._onPortfolioToJournal === "function") {
      root._onPortfolioToJournal();
    }
  });
  el.appendChild(btn);
}
