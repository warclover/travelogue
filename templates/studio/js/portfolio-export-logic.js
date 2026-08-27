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
  var store = next.store;
  if (Object.prototype.hasOwnProperty.call(next, "store")) {
    delete next.store;
  }
  if (isPortfolioEdition(trip && trip.edition)) {
    next.platform = PORTFOLIO_PAGES_PLATFORM;
    var product = readPortfolioExportPrefs(store).product;
    var flags = folioMainExportFlags(product);
    next.includeZip = flags.includeZip;
    next.includePages = flags.includePages;
    next.portfolioPiece = product;
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

/** 成册页 X：优先 trip.pageCount，不用 outputs.length。 */
export function resolvePortfolioBookPages(result, portfolio) {
  var x = Number(portfolio && portfolio.pageCount);
  if (x > 0) return x;
  var fromResult = Number(result && result.pageCount);
  if (fromResult > 0) return fromResult;
  return 0;
}

export function portfolioExportHint(bookPages, outputCount) {
  var x = Number(bookPages) || 0;
  var y = Number(outputCount) || 0;
  if (!(y > 0)) return "";
  if (!(x > 0) || y === x) return "这一本可以直接点开翻；页图按编号使用。";
  if (y === x + 1) return "另导出封面 1 张 · 页图按编号使用";
  return "页图 " + y + " 张（含封面/书衣，以文件夹为准）";
}

export function coverTitleEditLabel(edition) {
  return isPortfolioEdition(edition) ? "点击编辑书名" : "点击编辑杂志名";
}

/** 精修封面分区 / 标签：作品集说书名，游记说杂志名。 */
export function coverNameLabel(edition) {
  return isPortfolioEdition(edition) ? "书名" : "杂志名";
}

export function coverNameSegCopy(edition) {
  return {
    label: coverNameLabel(edition),
    hint: "改名·字体",
  };
}

export function aiGotoCoverNameLabel(edition) {
  return isPortfolioEdition(edition) ? "去精修 · 书名" : "去精修 · 杂志名";
}

export function coverNameTooLongToast(edition) {
  return coverNameLabel(edition) + "最多 20 个字";
}

export function coverNameEmptyToast(edition) {
  return coverNameLabel(edition) + "不能为空";
}

export function firstSuccessRefineLabel(edition) {
  return isPortfolioEdition(edition) ? "去精修封面" : "去精修封面和成册类型";
}

export var PORTFOLIO_EXPORT_PREFS_KEY = "travelogue.studio.portfolioExportPrefs.v1";
export var PORTFOLIO_SOCIAL_PREFS_KEY = "travelogue.studio.portfolioSocialPrefs.v1";

function _kvStore(explicit) {
  if (explicit) return explicit;
  try {
    if (typeof localStorage !== "undefined") return localStorage;
  } catch (_e) {}
  return null;
}

function _readJsonStore(store, key) {
  if (!store || typeof store.getItem !== "function") return null;
  try {
    var raw = store.getItem(key);
    if (!raw) return null;
    var parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch (_e) {
    return null;
  }
}

function _writeJsonStore(store, key, value) {
  if (!store || typeof store.setItem !== "function") return;
  try {
    store.setItem(key, JSON.stringify(value));
  } catch (_e) {}
}

/** F1 · 只记页图 / 这一本。禁止写 journal 钥。 */
export function readPortfolioExportPrefs(store) {
  var parsed = _readJsonStore(_kvStore(store), PORTFOLIO_EXPORT_PREFS_KEY);
  var product = parsed && String(parsed.product || "").trim() === "book" ? "book" : "pages";
  return { product: product };
}

export function writePortfolioExportPrefs(prefs, store) {
  var product = prefs && String(prefs.product || "").trim() === "book" ? "book" : "pages";
  _writeJsonStore(_kvStore(store), PORTFOLIO_EXPORT_PREFS_KEY, { product: product });
}

/** F2 · 过河上次平台。禁止写 journal 钥，也不得改 F1 product。 */
export function readPortfolioSocialPrefs(store) {
  var parsed = _readJsonStore(_kvStore(store), PORTFOLIO_SOCIAL_PREFS_KEY) || {};
  var platform = String(parsed.platform || "").trim() || "wechat_chat";
  if (platform === "portfolio_pages") platform = "wechat_chat";
  var platforms = Array.isArray(parsed.platforms)
    ? parsed.platforms
        .map(function (id) {
          return String(id || "").trim();
        })
        .filter(function (id) {
          return id && id !== "portfolio_pages";
        })
    : [];
  if (!platforms.length) platforms = [platform];
  if (platforms.indexOf(platform) < 0) platform = platforms[0];
  return { platform: platform, platforms: platforms };
}

export function writePortfolioSocialPrefs(prefs, store) {
  var next = readPortfolioSocialPrefs({
    getItem: function () {
      return JSON.stringify({
        platform: prefs && prefs.platform,
        platforms: prefs && prefs.platforms,
      });
    },
  });
  _writeJsonStore(_kvStore(store), PORTFOLIO_SOCIAL_PREFS_KEY, next);
}

/**
 * @param {object} result longshot job.result
 * @param {object|null} portfolio entry.portfolio
 */
export function portfolioSuccessCopy(result, portfolio) {
  result = result || {};
  var y = Array.isArray(result.outputs) ? result.outputs.length : 0;
  var n = resolvePortfolioBookPages(result, portfolio);
  var skipped = Array.isArray(result.skippedPages) ? result.skippedPages : [];
  var title =
    n > 0 ? "作品集已导出 · 共 " + n + " 页" : "作品集已导出";
  if (n <= 0 && result.shareZip) title = "这一本已打包";
  var hint = String(result.userHint || "").trim();
  if (!hint || /作品集已导出\s*·\s*共\s*\d+\s*页/.test(hint)) {
    hint = portfolioExportHint(n, y) || (n > 0 || y > 0
      ? "这一本可以直接点开翻；页图按编号使用。"
      : "这一本可以直接点开翻。");
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
  if (isPortfolioEdition(edition)) {
    return {
      title: PORTFOLIO_ALBUM_SPREAD_TITLE,
      subtitle: PORTFOLIO_ALBUM_SPREAD_SUB,
      aria: PORTFOLIO_ALBUM_SPREAD_TITLE + " · " + PORTFOLIO_ALBUM_SPREAD_SUB,
    };
  }
  return { title: "画册印刷", subtitle: "跨页", aria: "画册印刷" };
}

export function portfolioExportDefaultFaceSpec() {
  return {
    title: "导出作品集",
    badge: "作品集",
    lead: "带走你刚做好的这一本。",
    edition: "portfolio",
    face: "default",
    products: ["book", "pages"],
    platforms: [],
    crossRiver: { label: "想发到微信或小红书？", targetFace: "social" },
    confirmLabel: "导出作品集",
    initProduct: "pages",
  };
}

export function portfolioExportSocialFaceSpec() {
  return {
    title: "发到微信、小红书…",
    edition: "portfolio",
    face: "social",
    badge: "按游记来做",
    banner: "这不是在导出作品集。会用同一批照片，按游记的方式做成能发的图。",
    backLabel: "返回，继续导出作品集",
    confirmLabel: "导出长图",
    products: [],
  };
}

export function firstSuccessCrossRiverLabel() {
  return "想发到微信或小红书？";
}

export function portfolioMainProductsHtml(selected) {
  var product = String(selected || "pages").trim() === "book" ? "book" : "pages";
  var pagesOn = product === "pages";
  return (
    '<div class="preview-toolbar__export-popover-field" data-field="portfolio-main">' +
    '<div class="preview-toolbar__export-platform-grid" role="group" aria-label="带走哪一种">' +
    '<button type="button" class="preview-toolbar__export-platform-card' +
    (pagesOn ? " is-on is-selected" : "") +
    '" data-action="export-portfolio-pages" data-fxi-product="pages">' +
    '<span class="preview-toolbar__export-platform-card__title">页图</span>' +
    '<span class="preview-toolbar__export-platform-card__sub">一页一张图，发给别人用</span>' +
    "</button>" +
    '<button type="button" class="preview-toolbar__export-platform-card' +
    (!pagesOn ? " is-on is-selected" : "") +
    '" data-action="export-portfolio-book" data-fxi-product="book">' +
    '<span class="preview-toolbar__export-platform-card__title">这一本</span>' +
    '<span class="preview-toolbar__export-platform-card__sub">一个能点开翻的文件</span>' +
    "</button>" +
    "</div></div>"
  );
}

/** F1 · 作品集导出默认面。禁止六平台 / 折叠组 / 密度。 */
export function portfolioExportDefaultFaceHtml(selected) {
  var spec = portfolioExportDefaultFaceSpec();
  return (
    '<div data-fxi-face="default">' +
    '<div class="preview-toolbar__fxi-head">' +
    '<p class="preview-toolbar__export-popover-title">' +
    spec.title +
    "</p>" +
    '<span class="preview-toolbar__fxi-badge">' +
    spec.badge +
    "</span></div>" +
    '<p class="preview-toolbar__fxi-lead">' +
    spec.lead +
    "</p>" +
    portfolioMainProductsHtml(selected || spec.initProduct) +
    '<p class="preview-toolbar__fxi-cross">' +
    '<button type="button" class="preview-toolbar__fxi-link" data-fxi-cross-river>' +
    spec.crossRiver.label +
    "</button></p>" +
    '<div class="preview-toolbar__export-popover-actions">' +
    '<button type="button" class="preview-toolbar__export-popover-ok" data-action="ok">' +
    spec.confirmLabel +
    "</button>" +
    '<button type="button" class="preview-toolbar__export-popover-cancel" data-action="cancel">取消</button>' +
    "</div></div>"
  );
}

/**
 * F2 · 整面替换：复用游记面板 HTML，只套顶条 / 改标题主钮 / 加返回。
 * 禁止改 buildPanelHtml({edition:"journal"}) 的源。
 */
export function wrapJournalPanelAsPortfolioSocialFace(journalHtml) {
  var spec = portfolioExportSocialFaceSpec();
  var html = String(journalHtml || "");
  html = html.replace(
    '<p class="preview-toolbar__export-popover-title">导出设置</p>',
    '<div class="preview-toolbar__fxi-head">' +
      '<p class="preview-toolbar__export-popover-title">' +
      spec.title +
      "</p>" +
      '<span class="preview-toolbar__fxi-badge">' +
      spec.badge +
      "</span></div>"
  );
  html = html.replace(
    '<p class="preview-toolbar__export-popover-note">选好后点「确定」，再点上方灰色按钮开始导出。改「要不要字」会同步预览。</p>',
    '<p class="preview-toolbar__fxi-banner" data-fxi-banner>' +
      spec.banner +
      "</p>"
  );
  html = html.replace(
    '<span class="preview-toolbar__export-platform-card__title">画册印刷</span>' +
      '<span class="preview-toolbar__export-platform-card__sub">跨页</span>',
    '<span class="preview-toolbar__export-platform-card__title">画册印刷</span>' +
      '<span class="preview-toolbar__export-platform-card__sub">给印刷公司的跨页，不是这本作品集</span>'
  );
  html = html.replace(
    'data-action="ok">确定</button>',
    'data-action="ok">' + spec.confirmLabel + "</button>"
  );
  html = html.replace(
    '<div class="preview-toolbar__export-popover-actions">',
    '<div class="preview-toolbar__export-popover-actions">' +
      '<button type="button" class="preview-toolbar__export-popover-cancel" data-fxi-back>' +
      spec.backLabel +
      "</button>"
  );
  return '<div data-fxi-face="social">' + html + "</div>";
}

/** F2 过河面：复用游记点法，但不走批量。 */
export function isPortfolioSocialExportFace(el) {
  if (!el) return false;
  var key = el.getAttribute && el.getAttribute("data-export-face");
  if (key === "portfolio:social") return true;
  if (el.getAttribute && el.getAttribute("data-fxi-face") === "social") return true;
  return !!(el.querySelector && el.querySelector('[data-fxi-face="social"]'));
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
