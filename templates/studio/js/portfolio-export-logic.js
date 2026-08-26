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
 * 作品集主钮永远是页图包。共享 prefs 里的社交/印刷 id（含旧 album_*）
 * 不得抬成主平台——那些只走 ▾ 一次性导出。
 */
export function resolvePortfolioMainPlatform(_prefsPlatform) {
  return PORTFOLIO_PAGES_PLATFORM;
}

/** 作品集主路径永不走社交批量；游记仍按多选走 batch。 */
export function shouldRunSocialBatchExport(edition, platforms) {
  if (isPortfolioEdition(edition)) return false;
  return Array.isArray(platforms) && platforms.length > 1;
}

/** ▾ 印刷跨页：一次性，不写回主偏好。 */
export function isPortfolioPrintOneShot(edition, platform) {
  return isPortfolioEdition(edition) && String(platform || "").trim() === "album_spread";
}

/**
 * 作品集主路径只要 16:9 页图。zip「这一本」只走 ▾ 卡片。
 * @param {"pages"|"book"|string|null|undefined} piece
 */
export function folioMainExportFlags(piece) {
  if (String(piece || "").trim().toLowerCase() === "book") {
    return { includeZip: true, includePages: false };
  }
  return { includeZip: false, includePages: true };
}

export function journalDockCta() {
  return { short: "长图", aria: "导出长图" };
}

export function portfolioDockCta() {
  return { short: "导出作品集", aria: "导出作品集" };
}

/** 书架菜单：作品集走页图包，不走缺省群长图。 */
export function shelfExportMenuCopy(edition) {
  if (isPortfolioEdition(edition)) {
    return { exportItem: "导出作品集", openFolderItem: "打开导出文件夹" };
  }
  return { exportItem: "保存长图", openFolderItem: "打开长图文件夹" };
}

export function shelfExportRequestForTrip(trip, opts) {
  var next = Object.assign({}, opts || {});
  if (isPortfolioEdition(trip && trip.edition)) {
    next.platform = PORTFOLIO_PAGES_PLATFORM;
  }
  return next;
}

export function dockCtaFromEntry(entry) {
  if (entry && entry.dockCta && entry.dockCta.aria) {
    return { short: entry.dockCta.short || entry.dockCta.aria, aria: entry.dockCta.aria };
  }
  return isPortfolioEdition(entry && entry.edition) ? portfolioDockCta() : journalDockCta();
}

export function formatOverflowDetail(portfolio) {
  if (!portfolio || typeof portfolio !== "object") return "";
  var parts = [];
  var folder = Number(portfolio.folderCount);
  var placed = Number(portfolio.photosPlaced);
  var kept = Number(portfolio.photosKept);
  if (folder > 0) parts.push("文件夹 " + folder + " 张");
  if (placed >= 0) parts.push("放进这本的有 " + placed + " 张");
  if (kept > 0) parts.push("大约用上 " + kept + " 张");
  return parts.join(" · ");
}

export function portfolioHasLeftover(portfolio) {
  if (!portfolio || typeof portfolio !== "object") return false;
  var placed = Number(portfolio.photosPlaced);
  var kept = Number(portfolio.photosKept);
  return placed >= 0 && kept > 0 && placed < kept;
}

function leftoverCapacity(portfolio) {
  var ov = (portfolio && portfolio.overflow) || {};
  var res = String(ov.resolution || portfolio.overflowResolution || "");
  var placed = Number(portfolio.photosPlaced);
  var kept = Number(portfolio.photosKept);
  var leftover = placed >= 0 && kept > 0 && placed < kept ? kept - placed : 0;
  if (leftover <= 0) return false;
  var cap = Number(ov.capacity != null ? ov.capacity : portfolio.capacity);
  if (res === "placement_gap") return false;
  if (cap > 0 && placed < cap) return false;
  if (
    res === "capped" ||
    res === "tier_upgraded_then_capped" ||
    res === "tier_upgraded"
  ) {
    return true;
  }
  return cap > 0 ? kept > cap : true;
}

export function leftoverIsCapacity(portfolio) {
  if (!portfolioHasLeftover(portfolio)) return false;
  return leftoverCapacity(portfolio);
}

export function formatOverflowLine(portfolio) {
  if (!portfolio || typeof portfolio !== "object") return "";
  var placed = Number(portfolio.photosPlaced);
  var kept = Number(portfolio.photosKept);
  var leftover = placed >= 0 && kept > 0 && placed < kept ? kept - placed : 0;
  if (leftover > 0) {
    if (leftoverCapacity(portfolio)) {
      return "有 " + leftover + " 张没放进这本，要的话用游记能全收。";
    }
    return "编排没排满，有 " + leftover + " 张没放进这本。";
  }
  var folder = Number(portfolio.folderCount);
  var pages = Number(portfolio.pageCount);
  if (folder > 0 && pages > 0) {
    return "文件夹 " + folder + " 张，做成大约一本 " + pages + " 页。";
  }
  return "";
}

export function overflowJournalCta() {
  return "改用游记（全收）";
}

/** FirstSuccess · 作品集默认人话规格；溢出另起 lead，N/M/P 进详情。 */
export function firstSuccessPortfolioCopy(result) {
  var title = String((result && result.title) || "我的旅途");
  var portfolio = (result && result.portfolio) || {};
  var leftover = portfolioHasLeftover(portfolio);
  var folder = Number(portfolio.folderCount);
  var pages = Number(portfolio.pageCount);
  var spec = folder > 0 && pages > 0
    ? "文件夹 " + folder + " 张，做成大约一本 " + pages + " 页"
    : "";
  var overflow = leftover
    ? String((result && result.overflowLine) || formatOverflowLine(portfolio) || "").trim()
    : "";
  var headline = "";
  if (spec || overflow) {
    headline = "《" + title + "》已生成";
    if (spec) headline += " · " + spec;
    else headline += " · " + overflow.replace(/。$/, "");
  }
  var lead = leftover && overflow
    ? overflow
    : "作品集已做好。打开看看，满意就能导出。";
  var detail = String(
    (result && result.overflowDetail) || formatOverflowDetail(portfolio) || ""
  ).trim();
  return { headline: headline, lead: lead, detail: detail, leftover: leftover };
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
    overflowCta: leftoverIsCapacity(portfolio) ? overflowJournalCta() : "",
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
