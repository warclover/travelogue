/**
 * PFM · 作品集 Dock / 成功面纯函数
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  PORTFOLIO_PAGES_PLATFORM,
  formatOverflowLine,
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
  wrapPortfolioSocialGroupHtml,
  albumSpreadCardCopy,
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

test("resolvePortfolioMainPlatform 默认页图包，六平台不覆盖", () => {
  assert.equal(resolvePortfolioMainPlatform(""), PORTFOLIO_PAGES_PLATFORM);
  assert.equal(resolvePortfolioMainPlatform("wechat_chat"), PORTFOLIO_PAGES_PLATFORM);
  assert.equal(resolvePortfolioMainPlatform("xiaohongshu"), "xiaohongshu");
});

test("portfolioDockCta", () => {
  const cta = portfolioDockCta();
  assert.equal(cta.short, "导出作品集");
  assert.equal(cta.aria, "导出作品集");
  assert.notEqual(cta.aria, "导出长图");
  assert.equal(journalDockCta().aria, "导出长图");
  assert.equal(dockCtaFromEntry({ edition: "journal" }).aria, "导出长图");
  assert.equal(
    dockCtaFromEntry({ dockCta: { short: "导出作品集", aria: "导出作品集" } }).short,
    "导出作品集"
  );
});

test("formatOverflowLine 仅在实收小于 kept 时出现", () => {
  assert.equal(formatOverflowLine(null), "");
  assert.equal(formatOverflowLine({ photosPlaced: 96, photosKept: 96 }), "");
  assert.equal(
    formatOverflowLine({ photosPlaced: 96, photosKept: 180 }),
    "本册收录 96 / 180 张"
  );
});

test("portfolioSuccessCopy 主文案与打开这一本", () => {
  const copy = portfolioSuccessCopy(
    { pageCount: 16, outputs: ["a.png"], userHint: "页图 16 张已保存；这一本已打包，可打开翻阅" },
    { photosPlaced: 96, photosKept: 180 }
  );
  assert.equal(copy.title, "作品集已导出 · 共 16 页");
  assert.equal(copy.primary, "打开这一本");
  assert.equal(copy.overflowLine, "本册收录 96 / 180 张");
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
