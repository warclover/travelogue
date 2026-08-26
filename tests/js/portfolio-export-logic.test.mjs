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
  readEditionFromDom,
  resolvePortfolioMainPlatform,
  shouldRunSocialBatchExport,
  isPortfolioPrintOneShot,
  folioMainExportFlags,
  wrapPortfolioSocialGroupHtml,
  albumSpreadCardCopy,
  shelfExportMenuCopy,
  shelfExportRequestForTrip,
} from "../../templates/studio/js/portfolio-export-logic.js";

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
  assert.equal(shouldRunSocialBatchExport("journal", ["xiaohongshu", "album_spread"]), true);
  assert.equal(shouldRunSocialBatchExport("journal", ["wechat_chat"]), false);
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
  assert.match(html, /这本作品集/);
  assert.match(html, /data-action="export-portfolio-book"/);
  assert.match(html, /data-action="export-portfolio-pages"/);
});
