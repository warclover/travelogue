/**
 * DPI W3 · portfolio dock chrome + export face (FE-DPI-01 / 02).
 */
"use strict";

import {
  formatOverflowLine,
  isPortfolioEdition,
  PORTFOLIO_PAGES_PLATFORM,
  portfolioDockCta,
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
export function portfolioExportPopoverSpec() {
  return {
    title: "导出",
    edition: "portfolio",
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

/**
 * @returns {boolean}
 */
export function shouldSkipRecipeForPortfolioExport() {
  return true;
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
    root._exportPopoverSpec = portfolioExportPopoverSpec;
    root._syncPortfolioCta = syncPortfolioCtaLabel;
    root._resolveExportPlatform = resolvePortfolioExportPlatform;
    root._skipRecipeForExport = shouldSkipRecipeForPortfolioExport;
    root._readPortfolioDraftPrefs = function (prefs) {
      return portfolioExportPopoverSpec().initPlatform(prefs);
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
  el.replaceChildren();
  el.appendChild(document.createTextNode(line + " · "));
  var btn = document.createElement("button");
  btn.type = "button";
  btn.className = "preview-portfolio-overflow__exit";
  btn.textContent =
    (entry && entry.overflowCta) ||
    (root && root._overflowCta) ||
    overflowJournalCta();
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
