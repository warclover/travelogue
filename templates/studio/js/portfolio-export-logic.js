/**
 * PFM · 作品集 Dock / 成功面文案（FE-PFM-04 / 10 / 16）。
 * 纯函数，供预览工具栏与 Task Dock 共用。
 */
"use strict";

export var PORTFOLIO_PAGES_PLATFORM = "portfolio_pages";

export function isPortfolioEdition(raw) {
  var t = String(raw || "")
    .trim()
    .toLowerCase();
  return t === "portfolio" || t === "folio";
}

export function readEditionFromDom(doc) {
  if (!doc || !doc.documentElement) return "journal";
  return isPortfolioEdition(doc.documentElement.getAttribute("data-edition"))
    ? "portfolio"
    : "journal";
}

export function readToolbarEdition(root, doc) {
  if (root && isPortfolioEdition(root._edition)) return "portfolio";
  return readEditionFromDom(doc || (typeof document !== "undefined" ? document : null));
}

/**
 * 作品集主钮默认 portfolio_pages。
 * 用户已在 ▾ 里确认六平台之一时，视为换种分享，不覆盖。
 */
export function resolvePortfolioMainPlatform(prefsPlatform) {
  var p = String(prefsPlatform || "").trim();
  if (p && p !== "wechat_chat" && p !== PORTFOLIO_PAGES_PLATFORM) return p;
  return PORTFOLIO_PAGES_PLATFORM;
}

export function journalDockCta() {
  return { short: "长图", aria: "导出长图" };
}

export function portfolioDockCta() {
  return { short: "导出作品集", aria: "导出作品集" };
}

export function dockCtaFromEntry(entry) {
  if (entry && entry.dockCta && entry.dockCta.aria) {
    return { short: entry.dockCta.short || entry.dockCta.aria, aria: entry.dockCta.aria };
  }
  return isPortfolioEdition(entry && entry.edition) ? portfolioDockCta() : journalDockCta();
}

export function formatOverflowLine(portfolio) {
  if (!portfolio || typeof portfolio !== "object") return "";
  var placed = Number(portfolio.photosPlaced);
  var kept = Number(portfolio.photosKept);
  if (!(placed >= 0) || !(kept > 0) || placed >= kept) return "";
  return "本册收录 " + placed + " / " + kept + " 张";
}

export function overflowJournalCta() {
  return "改用游记（全收）";
}

export var EXPORT_OUTPUT_DIRNAME = "导出文件";

/** 打开这一本：永远打开可翻阅的 index.html，不用预览工具栏地址。 */
export function portfolioShareBookUrl(tripId) {
  var id = String(tripId || "").trim();
  if (!id) return "";
  return "/" + encodeURIComponent(id) + "/index.html";
}

export function portfolioBookUrl(entry, tripId) {
  var fromId = portfolioShareBookUrl(
    tripId || (entry && (entry.tripId || entry.id))
  );
  if (fromId) return fromId;
  var fromEntry = String(
    (entry && (entry.scrollShareUrl || entry.previewUrl)) || ""
  ).trim();
  if (/\/index\.html$/i.test(fromEntry)) return fromEntry;
  return "";
}

/** 成功面次要动作：压缩包选中文件；文件夹打开导出目录。 */
export function portfolioRevealTargets(result) {
  result = result || {};
  var zipRel = String(result.shareZip || "").trim();
  return {
    zipRel: zipRel,
    folderRel: EXPORT_OUTPUT_DIRNAME,
  };
}

/**
 * @param {object} result longshot job.result
 * @param {object|null} portfolio entry.portfolio
 */
export function portfolioSuccessCopy(result, portfolio) {
  result = result || {};
  var n = Number(result.pageCount);
  if (!(n >= 0)) n = Array.isArray(result.outputs) ? result.outputs.length : 0;
  var skipped = Array.isArray(result.skippedPages) ? result.skippedPages : [];
  var title =
    n > 0 ? "作品集已导出 · 共 " + n + " 页" : "作品集已导出";
  if (n <= 0 && result.shareZip) title = "这一本已打包";
  var hint = String(result.userHint || "").trim();
  if (!hint) {
    hint =
      n > 0
        ? "这一本可以直接点开翻；页图按编号使用。"
        : "这一本可以直接点开翻。";
  }
  if (skipped.length) {
    hint += skipped.length === 1 ? " · 跳过 1 页" : " · 跳过 " + skipped.length + " 页";
  }
  return {
    title: title,
    hint: hint,
    overflowLine: formatOverflowLine(portfolio),
    overflowCta: formatOverflowLine(portfolio) ? overflowJournalCta() : "",
    primary: "打开这一本",
    secondaryFolder: "打开文件夹",
    secondaryZip: "发送压缩包",
    pageCount: n,
  };
}

/** D-PFM-10 / 30 · 作品集导出 ▾ 换种分享（默认折叠）+ 印刷副文 */
export var PORTFOLIO_SOCIAL_GROUP_TITLE = "用同一批照片出社交图";
export var PORTFOLIO_SOCIAL_HINT =
  "社交图仍按现网拼贴，不是这一本作品集的页。";
export var PORTFOLIO_ALBUM_SPREAD_TITLE = "印刷跨页（现网画册）";
export var PORTFOLIO_ALBUM_SPREAD_SUB =
  "给印刷公司的 3:4 跨页，不是这一本";

export function albumSpreadCardCopy(edition) {
  if (edition === "portfolio") {
    return {
      title: PORTFOLIO_ALBUM_SPREAD_TITLE,
      subtitle: PORTFOLIO_ALBUM_SPREAD_SUB,
      aria: PORTFOLIO_ALBUM_SPREAD_TITLE + " · " + PORTFOLIO_ALBUM_SPREAD_SUB,
    };
  }
  return { title: "画册印刷", subtitle: "跨页", aria: "画册印刷" };
}

export function portfolioMainProductsHtml() {
  return (
    '<div class="preview-toolbar__export-popover-field" data-field="portfolio-main">' +
    '<span class="preview-toolbar__export-popover-label">这本作品集</span>' +
    '<div class="preview-toolbar__export-platform-grid" role="group" aria-label="这本作品集">' +
    '<button type="button" class="preview-toolbar__export-platform-card" data-action="export-portfolio-book">' +
    '<span class="preview-toolbar__export-platform-card__title">这一本</span>' +
    '<span class="preview-toolbar__export-platform-card__sub">可点开翻的压缩包</span>' +
    "</button>" +
    '<button type="button" class="preview-toolbar__export-platform-card" data-action="export-portfolio-pages">' +
    '<span class="preview-toolbar__export-platform-card__title">页图序列</span>' +
    '<span class="preview-toolbar__export-platform-card__sub">16:9 页图</span>' +
    "</button>" +
    "</div></div>"
  );
}

export function wrapPortfolioSocialGroupHtml(platformBtnsHtml, count) {
  var n = Number(count) || 0;
  var summary = PORTFOLIO_SOCIAL_GROUP_TITLE + (n > 0 ? "（" + n + "）" : "");
  return (
    '<details class="preview-toolbar__export-share-fold" data-portfolio-share-fold>' +
    "<summary>" +
    summary +
    "</summary>" +
    '<p class="preview-toolbar__export-share-hint">' +
    PORTFOLIO_SOCIAL_HINT +
    "</p>" +
    '<div class="preview-toolbar__export-platform-grid" role="group" aria-label="' +
    PORTFOLIO_SOCIAL_GROUP_TITLE +
    '">' +
    (platformBtnsHtml || "") +
    "</div></details>"
  );
}
