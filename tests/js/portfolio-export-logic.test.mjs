/**
 * PFM · 作品集 Dock / 成功面纯函数
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  PORTFOLIO_PAGES_PLATFORM,
  firstSuccessPortfolioCopy,
  formatOverflowLine,
  leftoverIsCapacity,
  isPortfolioEdition,
  portfolioBookUrl,
  portfolioRevealTargets,
  portfolioShareBookUrl,
  EXPORT_OUTPUT_DIRNAME,
  journalDockCta,
  dockCtaFromEntry,
  portfolioDockCta,
  portfolioMainProductsHtml,
  portfolioSuccessCopy,
  portfolioExportHint,
  resolvePortfolioBookPages,
  coverTitleEditLabel,
  readEditionFromDom,
  resolvePortfolioMainPlatform,
  shouldRunSocialBatchExport,
  isPortfolioSocialExportFace,
  isPortfolioPrintOneShot,
  folioMainExportFlags,
  wrapPortfolioSocialGroupHtml,
  wrapJournalPanelAsPortfolioSocialFace,
  portfolioExportDefaultFaceSpec,
  portfolioExportDefaultFaceHtml,
  albumSpreadCardCopy,
  shelfExportMenuCopy,
  shelfExportRequestForTrip,
  coverNameLabel,
  coverNameSegCopy,
  aiGotoCoverNameLabel,
  coverNameTooLongToast,
  coverNameEmptyToast,
  firstSuccessRefineLabel,
  PORTFOLIO_EXPORT_PREFS_KEY,
  PORTFOLIO_SOCIAL_PREFS_KEY,
  readPortfolioExportPrefs,
  writePortfolioExportPrefs,
  readPortfolioSocialPrefs,
  writePortfolioSocialPrefs,
} from "../../templates/studio/js/portfolio-export-logic.js";
import { LONGSHOT_EXPORT_PREFS_KEY } from "../../templates/studio/js/longshot-export-panel.js";

test("isPortfolioEdition", () => {
  assert.equal(isPortfolioEdition("portfolio"), true);
  assert.equal(isPortfolioEdition("folio"), true);
  assert.equal(isPortfolioEdition(""), false);
  assert.equal(isPortfolioEdition("journal"), false);
});

test("readEditionFromDom", () => {
  const html = { getAttribute: (k) => (k === "data-edition" ? "portfolio" : "") };
  assert.equal(readEditionFromDom({ documentElement: html }), "portfolio");
  assert.equal(readEditionFromDom({ documentElement: { getAttribute: () => null } }), "journal");
});

test("resolvePortfolioMainPlatform 恒为页图包，印刷/社交/旧 id 都不抬主钮", () => {
  assert.equal(resolvePortfolioMainPlatform(""), PORTFOLIO_PAGES_PLATFORM);
  assert.equal(resolvePortfolioMainPlatform("wechat_chat"), PORTFOLIO_PAGES_PLATFORM);
  assert.equal(resolvePortfolioMainPlatform("xiaohongshu"), PORTFOLIO_PAGES_PLATFORM);
  assert.equal(resolvePortfolioMainPlatform("album_spread"), PORTFOLIO_PAGES_PLATFORM);
  assert.equal(resolvePortfolioMainPlatform("album_landscape"), PORTFOLIO_PAGES_PLATFORM);
});

test("shouldRunSocialBatchExport 作品集永不批量，游记多选仍批量", () => {
  assert.equal(shouldRunSocialBatchExport("portfolio", ["xiaohongshu", "album_spread"]), false);
  assert.equal(shouldRunSocialBatchExport("folio", ["xiaohongshu", "wechat_moments"]), false);
  assert.equal(
    shouldRunSocialBatchExport("portfolio", ["xiaohongshu", "wechat_chat"]),
    false
  );
  assert.equal(shouldRunSocialBatchExport("journal", ["xiaohongshu", "album_spread"]), true);
  assert.equal(shouldRunSocialBatchExport("journal", ["wechat_chat"]), false);
  assert.equal(
    isPortfolioSocialExportFace({
      getAttribute: (k) => (k === "data-export-face" ? "portfolio:social" : null),
    }),
    true
  );
  assert.equal(
    isPortfolioSocialExportFace({
      getAttribute: () => null,
      querySelector: () => null,
    }),
    false
  );
});

test("isPortfolioPrintOneShot 仅作品集印刷卡", () => {
  assert.equal(isPortfolioPrintOneShot("portfolio", "album_spread"), true);
  assert.equal(isPortfolioPrintOneShot("journal", "album_spread"), false);
  assert.equal(isPortfolioPrintOneShot("portfolio", "xiaohongshu"), false);
});

test("folioMainExportFlags 主路径只要页图，这一本才打 zip", () => {
  assert.deepEqual(folioMainExportFlags(null), { includeZip: false, includePages: true });
  assert.deepEqual(folioMainExportFlags("pages"), { includeZip: false, includePages: true });
  assert.deepEqual(folioMainExportFlags("book"), { includeZip: true, includePages: false });
});

test("portfolioDockCta", () => {
  const cta = portfolioDockCta();
  assert.equal(cta.short, "导出作品集");
  assert.equal(cta.aria, "导出作品集");
  assert.notEqual(cta.aria, "导出长图");
  assert.equal(journalDockCta().aria, "导出长图");
});

test("shelfExportRequestForTrip 作品集带 portfolio_pages", () => {
  const journal = shelfExportMenuCopy("journal");
  assert.equal(journal.exportItem, "保存长图");
  assert.equal(journal.openFolderItem, "打开长图文件夹");
  const folio = shelfExportMenuCopy("portfolio");
  assert.equal(folio.exportItem, "导出作品集");
  assert.equal(folio.openFolderItem, "打开导出文件夹");
  assert.deepEqual(
    shelfExportRequestForTrip({ edition: "portfolio" }, { surface: "grid" }),
    { surface: "grid", platform: PORTFOLIO_PAGES_PLATFORM }
  );
  assert.deepEqual(
    shelfExportRequestForTrip({ edition: "journal" }, { surface: "grid" }),
    { surface: "grid" }
  );
  assert.equal(dockCtaFromEntry({ edition: "journal" }).aria, "导出长图");
  assert.equal(
    dockCtaFromEntry({ dockCta: { short: "导出作品集", aria: "导出作品集" } }).short,
    "导出作品集"
  );
});

test("firstSuccessPortfolioCopy 默认规格句，溢出进 lead", () => {
  const spec = firstSuccessPortfolioCopy({
    title: "林芝",
    portfolio: { folderCount: 129, pageCount: 32, photosPlaced: 81, photosKept: 81 },
  });
  assert.equal(spec.headline, "《林芝》已生成 · 文件夹 129 张，做成大约一本 32 页");
  assert.equal(spec.lead, "作品集已做好。打开看看，满意就能导出。");
  assert.match(spec.detail, /文件夹 129 张/);
  const leftover = firstSuccessPortfolioCopy({
    title: "林芝",
    overflowLine: "有 84 张没放进这本，要的话用游记能全收。",
    overflowDetail: "文件夹 160 张 · 放进这本的有 96 张 · 大约用上 180 张",
    portfolio: { folderCount: 160, pageCount: 32, photosPlaced: 96, photosKept: 180 },
  });
  assert.equal(leftover.headline, "《林芝》已生成 · 文件夹 160 张，做成大约一本 32 页");
  assert.equal(leftover.lead, "有 84 张没放进这本，要的话用游记能全收。");
  assert.match(leftover.detail, /放进这本的有 96 张/);
  assert.equal(leftover.leftover, true);
  assert.equal(firstSuccessPortfolioCopy({ title: "林芝" }).headline, "");
});

test("formatOverflowLine 人话：少收优先，否则文件夹+页数", () => {
  assert.equal(formatOverflowLine(null), "");
  assert.equal(formatOverflowLine({ photosPlaced: 96, photosKept: 96 }), "");
  assert.equal(
    formatOverflowLine({ photosPlaced: 96, photosKept: 180 }),
    "有 84 张没放进这本，要的话用游记能全收。"
  );
  assert.equal(
    formatOverflowLine({ folderCount: 129, pageCount: 32, photosPlaced: 81, photosKept: 81 }),
    "文件夹 129 张，做成大约一本 32 页。"
  );
  assert.equal(
    formatOverflowLine({ photosPlaced: 96, photosKept: 180 }).includes("本册收录"),
    false
  );
  assert.equal(
    formatOverflowLine({
      photosPlaced: 11,
      photosKept: 28,
      overflow: { resolution: "placement_gap", capacity: 29 },
    }),
    "编排没排满，有 17 张没放进这本。"
  );
  assert.equal(
    leftoverIsCapacity({
      photosPlaced: 11,
      photosKept: 28,
      overflow: { resolution: "placement_gap", capacity: 29 },
    }),
    false
  );
  assert.equal(
    leftoverIsCapacity({ photosPlaced: 96, photosKept: 180 }),
    true
  );
});

test("portfolioSuccessCopy 主文案与打开这一本", () => {
  const copy = portfolioSuccessCopy(
    { pageCount: 16, outputs: ["a.png"], userHint: "页图 16 张已保存；这一本已打包，可打开翻阅" },
    { photosPlaced: 96, photosKept: 180 }
  );
  assert.equal(copy.title, "作品集已导出 · 共 16 页");
  assert.equal(copy.primary, "打开这一本");
  assert.equal(copy.overflowLine, "有 84 张没放进这本，要的话用游记能全收。");
  assert.equal(copy.overflowCta, "改用游记（全收）");
  assert.match(copy.hint, /这一本已打包/);
  const blob = [copy.title, copy.hint, copy.primary, copy.secondaryFolder, copy.secondaryZip].join(" ");
  assert.equal(/文案|正在写/.test(blob), false);
});

test("PIS · 导出主句用成册页 X，Y≠X 只进副句", () => {
  assert.equal(resolvePortfolioBookPages({ pageCount: 37 }, { pageCount: 36 }), 36);
  assert.equal(portfolioExportHint(36, 37), "另导出封面 1 张 · 页图按编号使用");
  const copy = portfolioSuccessCopy(
    {
      pageCount: 37,
      outputs: Array.from({ length: 37 }, (_, i) => i + ".png"),
      userHint: "作品集已导出 · 共 37 页",
    },
    { pageCount: 36 }
  );
  assert.equal(copy.title, "作品集已导出 · 共 36 页");
  assert.equal(copy.title.includes("37"), false);
  assert.match(copy.hint, /另导出封面 1 张/);
  assert.equal(copy.hint.includes("共 37 页"), false);
  assert.equal(coverTitleEditLabel("portfolio"), "点击编辑书名");
  assert.equal(coverTitleEditLabel("journal"), "点击编辑杂志名");
});

test("portfolioBookUrl", () => {
  assert.equal(portfolioShareBookUrl("nara"), "/nara/index.html");
  assert.equal(
    portfolioBookUrl({ previewUrl: "/nara/preview" }, "nara"),
    "/nara/index.html"
  );
  assert.equal(portfolioBookUrl(null, "nara"), "/nara/index.html");
  const reveal = portfolioRevealTargets({
    shareZip: "导出文件/奈良-分享.zip",
    outputs: ["导出文件/奈良-portfolio-01.png"],
  });
  assert.equal(reveal.zipRel, "导出文件/奈良-分享.zip");
  assert.equal(reveal.folderRel, EXPORT_OUTPUT_DIRNAME);
  assert.notEqual(reveal.zipRel, reveal.folderRel);
});

test("albumSpreadCardCopy 游记不动，作品集用印刷副文", () => {
  const journal = albumSpreadCardCopy("journal");
  assert.equal(journal.title, "画册印刷");
  assert.equal(journal.subtitle, "跨页");
  const pf = albumSpreadCardCopy("portfolio");
  assert.equal(pf.title, "印刷跨页（现网画册）");
  assert.match(pf.subtitle, /给印刷公司的 3:4 跨页/);
  assert.doesNotMatch(pf.title, /^画册$/);
});

test("wrapPortfolioSocialGroupHtml 默认折叠", () => {
  const html = wrapPortfolioSocialGroupHtml("<button></button>", 6);
  assert.match(html, /data-portfolio-share-fold/);
  assert.doesNotMatch(html, /<details[^>]*\sopen/);
  assert.match(html, /用同一批照片出社交图（6）/);
  assert.match(html, /社交图仍按现网拼贴/);
});

test("portfolioMainProductsHtml 这一本与页图", () => {
  const html = portfolioMainProductsHtml();
  assert.match(html, /data-action="export-portfolio-book"/);
  assert.match(html, /data-action="export-portfolio-pages"/);
  assert.match(html, />页图</);
  assert.match(html, />这一本</);
  assert.doesNotMatch(html, /16:9/);
  assert.doesNotMatch(html, /压缩包/);
});

test("F1 spec 默认面 platforms 为空且无折叠组", () => {
  const spec = portfolioExportDefaultFaceSpec();
  assert.equal(spec.title, "导出作品集");
  assert.deepEqual(spec.platforms, []);
  assert.equal(spec.face, "default");
  assert.equal(spec.crossRiver.label, "想发到微信或小红书？");
  const html = portfolioExportDefaultFaceHtml();
  assert.doesNotMatch(html, /data-portfolio-share-fold/);
  assert.doesNotMatch(html, /data-studio-longshot-platform/);
  assert.match(html, /导出作品集/);
});

test("wrapJournalPanelAsPortfolioSocialFace 套游记面板", () => {
  const journal =
    '<p class="preview-toolbar__export-popover-title">导出设置</p>' +
    '<p class="preview-toolbar__export-popover-note">选好后点「确定」，再点上方灰色按钮开始导出。改「要不要字」会同步预览。</p>' +
    '<button data-action="ok">确定</button>' +
    '<div class="preview-toolbar__export-popover-actions"></div>';
  const html = wrapJournalPanelAsPortfolioSocialFace(journal);
  assert.match(html, /data-fxi-face="social"/);
  assert.match(html, /发到微信、小红书/);
  assert.match(html, /这不是在导出作品集/);
  assert.match(html, /导出长图/);
  assert.match(html, /返回，继续导出作品集/);
  assert.doesNotMatch(html, />确定</);
});

test("FE-FXI-06 封面/Sheet 用词按身份切", () => {
  assert.equal(coverNameLabel("journal"), "杂志名");
  assert.equal(coverNameLabel("portfolio"), "书名");
  assert.equal(coverNameSegCopy("portfolio").label, "书名");
  assert.equal(aiGotoCoverNameLabel("journal"), "去精修 · 杂志名");
  assert.equal(aiGotoCoverNameLabel("portfolio"), "去精修 · 书名");
  assert.equal(coverNameTooLongToast("portfolio"), "书名最多 20 个字");
  assert.equal(coverNameEmptyToast("journal"), "杂志名不能为空");
  assert.equal(firstSuccessRefineLabel("portfolio"), "去精修封面");
  assert.equal(firstSuccessRefineLabel("journal"), "去精修封面和成册类型");
});

function memoryStore(seed) {
  return {
    data: Object.assign({}, seed || {}),
    getItem(key) {
      return Object.prototype.hasOwnProperty.call(this.data, key)
        ? this.data[key]
        : null;
    },
    setItem(key, value) {
      this.data[key] = String(value);
    },
  };
}

test("QA-FXI-04 F2 写社交钥不碰 journal / F1 product", () => {
  const mem = memoryStore({
    [LONGSHOT_EXPORT_PREFS_KEY]: JSON.stringify({
      platform: "wechat_chat",
      platforms: ["wechat_chat"],
    }),
    [PORTFOLIO_EXPORT_PREFS_KEY]: JSON.stringify({ product: "book" }),
  });
  writePortfolioSocialPrefs(
    { platform: "xiaohongshu", platforms: ["xiaohongshu"] },
    mem
  );
  assert.equal(
    JSON.parse(mem.getItem(LONGSHOT_EXPORT_PREFS_KEY)).platform,
    "wechat_chat"
  );
  assert.equal(readPortfolioExportPrefs(mem).product, "book");
  assert.equal(readPortfolioSocialPrefs(mem).platform, "xiaohongshu");
  assert.equal(mem.getItem(PORTFOLIO_SOCIAL_PREFS_KEY) != null, true);
});

test("FE-FXI-07 F1 写 product 不碰 journal 钥", () => {
  const mem = memoryStore({
    [LONGSHOT_EXPORT_PREFS_KEY]: JSON.stringify({
      platform: "wechat_chat",
      platforms: ["wechat_chat"],
    }),
  });
  writePortfolioExportPrefs({ product: "book" }, mem);
  assert.equal(readPortfolioExportPrefs(mem).product, "book");
  assert.equal(
    JSON.parse(mem.getItem(LONGSHOT_EXPORT_PREFS_KEY)).platform,
    "wechat_chat"
  );
  assert.equal(mem.getItem(PORTFOLIO_SOCIAL_PREFS_KEY), null);
});

test("F2 社交钥丢掉 portfolio_pages", () => {
  const mem = memoryStore();
  writePortfolioSocialPrefs(
    { platform: "portfolio_pages", platforms: ["portfolio_pages", "xiaohongshu"] },
    mem
  );
  const social = readPortfolioSocialPrefs(mem);
  assert.equal(social.platform, "xiaohongshu");
  assert.equal(social.platforms.includes("portfolio_pages"), false);
});
