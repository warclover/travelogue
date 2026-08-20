/**
 * PFM · 预览窄屏 gate 文案（FE-PFM-12 · AC-PFM-24）。
 * 游记字面冻结；作品集仍提示电脑精修 / 导出。
 */
"use strict";

import { isPortfolioEdition } from "../js/portfolio-export-logic.js";

export var JOURNAL_PREVIEW_PHONE_TITLE = "请在电脑浏览器打开预览工作台";
export var JOURNAL_PREVIEW_PHONE_LEAD =
  "手机可阅读分享页；精修与导出请在电脑浏览器打开本地址。";
export var PORTFOLIO_PREVIEW_PHONE_TITLE = "请在电脑浏览器打开预览工作台";
export var PORTFOLIO_PREVIEW_PHONE_LEAD =
  "手机可翻阅这一本；精修与导出请在电脑浏览器打开本地址。";
export var PORTFOLIO_NARROW_REFINE_EXPORT_HINT = "精修与导出请在电脑完成。";

export function resolvePreviewNarrowGateCopy(layout, edition, base) {
  base = base || {};
  var portfolio = isPortfolioEdition(edition);
  if (layout === "unsupported_phone") {
    return {
      title: portfolio ? PORTFOLIO_PREVIEW_PHONE_TITLE : JOURNAL_PREVIEW_PHONE_TITLE,
      lead: portfolio ? PORTFOLIO_PREVIEW_PHONE_LEAD : JOURNAL_PREVIEW_PHONE_LEAD,
    };
  }
  var title = String(base.title || "");
  var lead = String(base.lead || "");
  if (portfolio && !/精修|导出/.test(title + lead)) {
    lead = (lead ? lead.replace(/。?$/, "。") : "") + PORTFOLIO_NARROW_REFINE_EXPORT_HINT;
  }
  return { title: title, lead: lead };
}
