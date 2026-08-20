/**
 * PFM · 精修成册类型 / 书架弱标纯函数（FE-PFM-07 / 08 / 11）。
 * 用户可见文案不得出现 edition / PFM / page-*（AC-PFM-23）。
 */
"use strict";

import { isPortfolioEdition, overflowJournalCta } from "./portfolio-export-logic.js";

export { overflowJournalCta };

export var EDITION_COPY_LOCK = "你手动改过的文字可能无法全部保留。";
export var PORTFOLIO_FLAG_OFF_TEXT = "作品集编排暂时关闭 · 这一本仍可翻阅";
export var PORTFOLIO_FLAG_OFF_CTA = "改为游记重排";

/** 关旗后打开存量作品集：横幅 + 可改回游记（AC-PFM-07 后半）。 */
export function shouldShowPortfolioFlagOffBanner(edition, pipelineEnabled) {
  return isPortfolioEdition(edition) && pipelineEnabled === false;
}

/** 关旗时游记不露成册类型；存量作品集仍露，以便改回。 */
export function shouldMountEditionType(edition, pipelineEnabled) {
  if (pipelineEnabled === true) return true;
  return isPortfolioEdition(edition);
}

export function editionCardOptionsForPipeline(pipelineEnabled) {
  var all = editionCardOptions();
  if (pipelineEnabled === true) return all;
  return all.filter(function (opt) {
    return opt.id === "journal";
  });
}

export function portfolioFlagOffBannerCopy() {
  return { text: PORTFOLIO_FLAG_OFF_TEXT, cta: PORTFOLIO_FLAG_OFF_CTA };
}

/** FE-PFM-15 · WAI-ARIA radio 方向键（水平/垂直同一套）。 */
export function isRadioNavKey(key) {
  return (
    key === "ArrowLeft" ||
    key === "ArrowRight" ||
    key === "ArrowUp" ||
    key === "ArrowDown" ||
    key === "Home" ||
    key === "End"
  );
}

export function nextRadioId(ids, current, key) {
  var list = Array.isArray(ids) ? ids.filter(Boolean) : [];
  if (!list.length) return current || "";
  if (key === "Home") return list[0];
  if (key === "End") return list[list.length - 1];
  var i = list.indexOf(current);
  if (i < 0) i = 0;
  if (key === "ArrowLeft" || key === "ArrowUp") {
    return list[i <= 0 ? list.length - 1 : i - 1];
  }
  if (key === "ArrowRight" || key === "ArrowDown") {
    return list[i >= list.length - 1 ? 0 : i + 1];
  }
  return current || list[0];
}

export function radioTabIndex(selectedId, optionId) {
  return selectedId === optionId ? 0 : -1;
}

export function normalizeEdition(raw) {
  return isPortfolioEdition(raw) ? "portfolio" : "journal";
}

/**
 * @param {string} from
 * @param {string} to
 */
export function editionSwitchConfirm(from, to) {
  var next = normalizeEdition(to);
  var toPortfolio = next === "portfolio";
  var body =
    "精选和分组会保留，页面将按另一套版式重排。" + EDITION_COPY_LOCK;
  if (toPortfolio) {
    body += "页数可能变少，照片可能收录不全；发群请改用「换种分享」。";
  }
  return {
    title: toPortfolio ? "改成「作品集」？" : "改回「游记」？",
    body: body,
    confirmText: "重排页面",
    cancelText: "取消",
  };
}

/**
 * 作品集票面弱标。游记返回空串，避免每张都写「游记」。
 * @param {{ edition?: string, pageCount?: number }|null} trip
 */
export function shelfEditionLine(trip) {
  if (!trip || !isPortfolioEdition(trip.edition)) return "";
  var n = Number(trip.pageCount);
  if (n > 0) return "作品集 · " + n + " 页";
  return "作品集";
}

export function editionCardOptions() {
  return [
    {
      id: "journal",
      label: "游记",
      consequence: "卷轴 + 长图，适合发群",
    },
    {
      id: "portfolio",
      label: "作品集",
      consequence: "杂志页 + 可翻阅的一本",
    },
  ];
}

export var PAGE_COUNT_CHIPS = [8, 12, 16, 20, 24, 28, 32];

export function pageCountChipOptions(chips) {
  var list = Array.isArray(chips) && chips.length ? chips : PAGE_COUNT_CHIPS;
  return [{ id: "auto", label: "自动" }].concat(
    list.map(function (n) {
      return { id: String(n), label: String(n) };
    })
  );
}

/** @param {{ pageCountSource?: string, pageCount?: number, pageCountRequested?: number }} portfolio */
export function selectedPageCountChip(portfolio) {
  if (!portfolio || String(portfolio.pageCountSource || "auto") !== "user") {
    return "auto";
  }
  var requested = Number(portfolio.pageCountRequested);
  if (requested > 0) return String(requested);
  var used = Number(portfolio.pageCount);
  if (used > 0) return String(used);
  return "auto";
}

