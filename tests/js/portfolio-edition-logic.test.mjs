/**
 * PFM · 成册类型确认 / 书架弱标
 */
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import {
  EDITION_COPY_LOCK,
  editionCardOptions,
  editionCardOptionsForPipeline,
  editionSwitchConfirm,
  overflowJournalCta,
  portfolioRefineIdentitySpec,
  pageCountChipOptions,
  portfolioFlagOffBannerCopy,
  recommendPageCount,
  selectedPageCountChip,
  shouldConfirmThinTier,
  thinTierConfirm,
  shelfEditionLine,
  shelfEditionShort,
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
  assert.match(toPf.body, /改回游记再导出长图/);
  assert.equal(toPf.body.includes("edition"), false);

  const toJ = editionSwitchConfirm("portfolio", "journal");
  assert.equal(toJ.title, "改做成游记？");
  assert.equal(toJ.confirmText, "按游记重排");
  assert.equal(toJ.cancelText, "还是作品集");
  assert.ok(toJ.body.includes(EDITION_COPY_LOCK));
  assert.match(toJ.body, /对不上新的页/);
  assert.equal(toJ.body.includes("换种分享"), false);
});

test("F3 · 作品集精修 spec 无成册类型两卡", () => {
  const spec = portfolioRefineIdentitySpec(36);
  assert.equal(spec.title, "改这本作品集");
  assert.equal(spec.coverLabel, "书名");
  assert.equal(spec.thicknessLead, "现在是 36 页");
  assert.equal(spec.showEditionCards, false);
  assert.equal(spec.showLayoutVibe, false);
  assert.equal(spec.action.label, "想改做成一本游记？");
  assert.equal(spec.action.to, "journal");
});

test("shelfEditionLine 游记与作品集都标身份", () => {
  assert.equal(shelfEditionLine(null), "");
  assert.equal(shelfEditionLine({}), "游记");
  assert.equal(shelfEditionLine({ edition: "journal", pageCount: 12 }), "游记");
  assert.equal(shelfEditionLine({ edition: "portfolio" }), "作品集");
  assert.equal(
    shelfEditionLine({ edition: "portfolio", pageCount: 16 }),
    "作品集 · 16 页"
  );
});

test("华农同名两本封面短标能分开", () => {
  var journal = { title: "华农油菜花", edition: "journal", pageCount: 8 };
  var portfolio = { title: "华农油菜花", edition: "portfolio", pageCount: 13 };
  assert.equal(shelfEditionShort(null), "");
  assert.equal(shelfEditionShort(journal), "游记");
  assert.equal(shelfEditionShort(portfolio), "作品集");
  assert.notEqual(shelfEditionLine(journal), shelfEditionLine(portfolio));
});

test("成册类型两卡不叫成册风格", () => {
  const labels = editionCardOptions().map((o) => o.label).join(" ");
  assert.match(labels, /游记/);
  assert.match(labels, /作品集/);
  assert.equal(labels.includes("成册风格"), false);
  const pf = editionCardOptions().find((o) => o.id === "portfolio");
  assert.equal(pf.consequence, "可翻的一本");
  assert.equal(pf.consequence.includes("杂志页"), false);
});

test("页数芯片只出目录投影的档，缺省仅自动", () => {
  const empty = pageCountChipOptions();
  assert.deepEqual(
    empty.map((o) => o.id),
    ["auto"]
  );
  const opts = pageCountChipOptions([{ pages: 12, capacity: 36 }, { pages: 16, capacity: 53 }]);
  assert.equal(opts[0].id, "auto");
  assert.equal(opts[0].label, "自动");
  assert.deepEqual(
    opts.slice(1).map((o) => o.id),
    ["12", "16"]
  );
  assert.equal(opts[1].hint, "12 页 · 最多约 36 张");
  assert.equal(opts[2].hint, "16 页 · 最多约 53 张");
  assert.equal(shouldConfirmThinTier(27, 180), true);
  assert.equal(shouldConfirmThinTier(81, 80), false);
  assert.equal(
    recommendPageCount(
      [
        { pages: 8, capacity: 27 },
        { pages: 28, capacity: 81 },
      ],
      80
    ),
    28
  );
  const confirm = thinTierConfirm(27, 180, 28, 160);
  assert.match(confirm.body, /大约收得下 27 张/);
  assert.match(confirm.body, /文件夹 160 张/);
  assert.equal(confirm.body.includes("你有"), false);
  assert.equal(confirm.confirmText, "改用 28 页");
  assert.equal(
    recommendPageCount(
      [
        { pages: 8, capacity: 27, demotedPages: 7 },
        { pages: 28, capacity: 81, demotedPages: 0 },
      ],
      80
    ),
    28
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

test("页数 chip 不用 innerHTML 拼 hint", () => {
  const src = readFileSync(
    new URL("../../templates/studio/js/portfolio-edition-logic.js", import.meta.url),
    "utf8"
  );
  assert.equal(src.includes("btn.innerHTML"), false);
  assert.match(src, /chip-label[\s\S]*textContent/);
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
