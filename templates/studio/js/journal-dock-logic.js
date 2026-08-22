/**
 * DPI W3 · journal dock chrome (FE-DPI-01).
 */
"use strict";

import { journalDockCta } from "./portfolio-export-logic.js";

export { journalDockCta };

/**
 * @param {object|null|undefined} root
 * @returns {{ short: string, aria: string }}
 */
export function journalIdleCta(root) {
  void root;
  return journalDockCta();
}

/**
 * Clear portfolio chrome hooks and restore journal dock defaults.
 * @param {object|null|undefined} root
 * @param {object|null|undefined} [entry]
 */
export function applyJournalDockLogic(root, entry) {
  void entry;
  if (root) {
    root._dockCta = journalDockCta();
    root._exportPopoverSpec = null;
    root._syncPortfolioCta = null;
    root._resolveExportPlatform = null;
    root._skipRecipeForExport = null;
    root._readPortfolioDraftPrefs = null;
  }
  hidePortfolioDockBanners();
}

function hidePortfolioDockBanners() {
  if (typeof document === "undefined") return;
  ["preview-portfolio-overflow", "preview-portfolio-flag-off"].forEach(function (cls) {
    var el = document.querySelector("." + cls);
    if (el) el.hidden = true;
  });
}
