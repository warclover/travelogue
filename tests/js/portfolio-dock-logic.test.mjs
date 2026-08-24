/**
 * 作品集 Dock 导出平台：pending 须保留，游记路径不走此函数。
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  PORTFOLIO_PAGES_PLATFORM,
  resolvePortfolioMainPlatform,
} from "../../templates/studio/js/portfolio-export-logic.js";
import {
  portfolioExportPopoverSpec,
  portfolioIdleCta,
  resolvePortfolioExportPlatform,
  shouldSkipRecipeForPortfolioExport,
} from "../../templates/studio/js/portfolio-dock-logic.js";

test("resolvePortfolioExportPlatform · pending 作品集不被 prefs 盖掉", () => {
  assert.equal(
    resolvePortfolioExportPlatform("wechat_chat", {
      pending: PORTFOLIO_PAGES_PLATFORM,
    }),
    PORTFOLIO_PAGES_PLATFORM
  );
  assert.equal(
    resolvePortfolioExportPlatform("xiaohongshu", { afterLayout: true }),
    "xiaohongshu"
  );
  assert.equal(
    resolvePortfolioExportPlatform("wechat_chat"),
    resolvePortfolioMainPlatform("wechat_chat")
  );
});

test("resolvePortfolioExportPlatform · 无 pending 恒 portfolio_pages", () => {
  assert.equal(resolvePortfolioExportPlatform("album_spread"), PORTFOLIO_PAGES_PLATFORM);
  assert.equal(resolvePortfolioExportPlatform("xiaohongshu"), PORTFOLIO_PAGES_PLATFORM);
  assert.equal(resolvePortfolioExportPlatform("album_landscape"), PORTFOLIO_PAGES_PLATFORM);
  assert.equal(
    resolvePortfolioExportPlatform("album_spread", { pending: "album_spread" }),
    "album_spread"
  );
});

test("作品集主钮与主区 seed 恒为导出作品集 / 页图包", () => {
  assert.equal(portfolioIdleCta().short, "导出作品集");
  assert.equal(shouldSkipRecipeForPortfolioExport(), true);
  assert.deepEqual(portfolioExportPopoverSpec().initPlatform({
    platform: "album_spread",
    platforms: ["xiaohongshu", "album_spread"],
  }), {
    platform: PORTFOLIO_PAGES_PLATFORM,
    platforms: [PORTFOLIO_PAGES_PLATFORM],
  });
});
