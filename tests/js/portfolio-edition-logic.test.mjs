/**
 * PFM · 成册类型确认 / 书架弱标
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  EDITION_COPY_LOCK,
  editionCardOptions,
  editionCardOptionsForPipeline,
  editionSwitchConfirm,
  overflowJournalCta,
  pageCountChipOptions,
  portfolioFlagOffBannerCopy,
  selectedPageCountChip,
  shelfEditionLine,
  shouldMountEditionType,
  shouldShowPortfolioFlagOffBanner,
  isRadioNavKey,
  nextRadioId,
  radioTabIndex,
} from "../../templates/studio/js/portfolio-edition-logic.js";

test("确认文案必含文字可能无法全部保留", () => {
  const toPf = editionSwitchConfirm("journal", "portfolio");
  assert.equal(toPf.title, "改成「作品集」？");
  assert.equal(toPf.confirmText, "重排页面");
  assert.match(toPf.body, /精选和分组会保留/);
  assert.ok(toPf.body.includes(EDITION_COPY_LOCK));
  assert.match(toPf.body, /换种分享/);
  assert.equal(toPf.body.includes("edition"), false);

  const toJ = editionSwitchConfirm("portfolio", "journal");
  assert.equal(toJ.title, "改回「游记」？");
  assert.ok(toJ.body.includes(EDITION_COPY_LOCK));
  assert.equal(toJ.body.includes("换种分享"), false);
});

test("shelfEditionLine 仅作品集弱标", () => {
  assert.equal(shelfEditionLine({}), "");
  assert.equal(shelfEditionLine({ edition: "journal", pageCount: 12 }), "");
  assert.equal(shelfEditionLine({ edition: "portfolio" }), "作品集");
  assert.equal(
    shelfEditionLine({ edition: "portfolio", pageCount: 16 }),
    "作品集 · 16 页"
  );
});

test("成册类型两卡不叫成册风格", () => {
  const labels = editionCardOptions().map((o) => o.label).join(" ");
  assert.match(labels, /游记/);
  assert.match(labels, /作品集/);
  assert.equal(labels.includes("成册风格"), false);
});

test("页数芯片只出目录投影的档，缺省仅自动", () => {
  const empty = pageCountChipOptions();
  assert.deepEqual(
    empty.map((o) => o.id),
    ["auto"]
  );
  const opts = pageCountChipOptions([16]);
  assert.equal(opts[0].id, "auto");
  assert.equal(opts[0].label, "自动");
  assert.deepEqual(
    opts.slice(1).map((o) => o.id),
    ["16"]
  );
  assert.equal(selectedPageCountChip({ pageCountSource: "auto", pageCount: 16 }), "auto");
  assert.equal(
    selectedPageCountChip({ pageCountSource: "user", pageCount: 16, pageCountRequested: 18 }),
    "18"
  );
});

test("溢出出口是改用游记全收", () => {
  assert.equal(overflowJournalCta(), "改用游记（全收）");
});

test("AC-PFM-07 · 关旗横幅与成册类型显隐", () => {
  assert.equal(shouldShowPortfolioFlagOffBanner("portfolio", false), true);
  assert.equal(shouldShowPortfolioFlagOffBanner("portfolio", true), false);
  assert.equal(shouldShowPortfolioFlagOffBanner("journal", false), false);
  assert.equal(shouldMountEditionType("journal", false), false);
  assert.equal(shouldMountEditionType("journal", true), true);
  assert.equal(shouldMountEditionType("portfolio", false), true);
  const offCards = editionCardOptionsForPipeline(false).map((o) => o.id);
  assert.deepEqual(offCards, ["journal"]);
  const onCards = editionCardOptionsForPipeline(true).map((o) => o.id);
  assert.deepEqual(onCards, ["journal", "portfolio"]);
  const banner = portfolioFlagOffBannerCopy();
  assert.equal(banner.text, "作品集编排暂时关闭 · 这一本仍可翻阅");
  assert.equal(banner.cta, "改为游记重排");
  assert.equal(/文案|正在写|edition|PFM|page-/.test(banner.text + banner.cta), false);
});

test("AC-PFM-13 · 身份 radio 键盘可切到作品集", () => {
  const ids = ["journal", "portfolio"];
  assert.equal(isRadioNavKey("ArrowRight"), true);
  assert.equal(isRadioNavKey("Enter"), false);
  assert.equal(nextRadioId(ids, "journal", "ArrowRight"), "portfolio");
  assert.equal(nextRadioId(ids, "journal", "ArrowDown"), "portfolio");
  assert.equal(nextRadioId(ids, "portfolio", "ArrowLeft"), "journal");
  assert.equal(nextRadioId(ids, "journal", "End"), "portfolio");
  assert.equal(nextRadioId(ids, "portfolio", "Home"), "journal");
  assert.equal(radioTabIndex("journal", "journal"), 0);
  assert.equal(radioTabIndex("journal", "portfolio"), -1);
});
