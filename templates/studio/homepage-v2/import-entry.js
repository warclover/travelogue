/**
 * 首页 v2 · 导入入口薄编排（RET-3）。
 *
 * CTA / shelf / failed / harness 只依赖本模块；一律打开 Wizard。
 * `openImportSheet` / `closeImportSheet` / `initImportSheet` 保留为兼容别名。
 */
import { V2, $ } from "./store.js";
import { trackStudioEvent } from "../js/analytics.js";

let _ctaWired = false;
let _uiReady = null;

function ensureUiReady() {
  if (_uiReady) return _uiReady;
  _uiReady = import("./import-wizard.js").then(function (m) {
    m.initImportWizard();
    return m;
  });
  return _uiReady;
}

export function openImportSheet(opts) {
  opts = opts || {};
  if (V2.state === "Importing") {
    if (typeof studioToast === "function") studioToast("正在制作中", { duration: 2200 });
    return;
  }
  ensureUiReady().then(function (m) {
    m.openImportWizard(opts);
  });
}

export function closeImportSheet(reason) {
  ensureUiReady().then(function (m) {
    if (typeof m.isImportWizardOpen === "function" && m.isImportWizardOpen()) {
      m.closeImportWizard(reason);
    }
  });
}

export function initImportSheet() {
  ensureUiReady();
  if (_ctaWired) return;
  _ctaWired = true;
  var cta = $("v2-cta");
  if (cta) {
    cta.addEventListener("click", function () {
      var surface = cta.classList.contains("is-headline") ? "headline" : "bench";
      trackStudioEvent("cta_click", { surface: surface });
      openImportSheet();
    });
  }
}
