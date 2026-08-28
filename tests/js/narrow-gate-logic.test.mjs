/**
 * PFM · 预览窄屏 gate 文案（FE-PFM-12 · AC-PFM-24）
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  JOURNAL_PREVIEW_PHONE_LEAD,
  JOURNAL_PREVIEW_PHONE_TITLE,
  PORTFOLIO_NARROW_REFINE_EXPORT_HINT,
  PORTFOLIO_PREVIEW_PHONE_LEAD,
  resolvePreviewNarrowGateCopy,
} from "../../templates/studio/preview-toolbar/narrow-gate-logic.js";

test("游记手机 gate 字面冻结", () => {
  const copy = resolvePreviewNarrowGateCopy("unsupported_phone", "journal");
  assert.equal(copy.title, JOURNAL_PREVIEW_PHONE_TITLE);
  assert.equal(copy.lead, JOURNAL_PREVIEW_PHONE_LEAD);
  assert.match(copy.lead, /精修与导出/);
  assert.match(copy.lead, /电脑/);
});

test("作品集手机 gate 仍提示电脑精修导出", () => {
  const copy = resolvePreviewNarrowGateCopy("unsupported_phone", "portfolio");
  assert.equal(copy.title, JOURNAL_PREVIEW_PHONE_TITLE);
  assert.equal(copy.lead, PORTFOLIO_PREVIEW_PHONE_LEAD);
  assert.match(copy.lead, /这一本/);
  assert.match(copy.lead, /精修与导出/);
  assert.match(copy.lead, /电脑/);
  assert.equal(/文案|正在写|edition|PFM|page-/.test(copy.title + copy.lead), false);
});

test("作品集窄窗 / 旋转补一句精修导出", () => {
  const rotate = resolvePreviewNarrowGateCopy("unsupported_rotate", "portfolio", {
    title: "请旋转至横屏，或改用电脑",
    lead: "Studio 工作台为横屏双列设计。",
  });
  assert.match(rotate.lead, /精修与导出/);
  assert.equal(rotate.lead.includes(PORTFOLIO_NARROW_REFINE_EXPORT_HINT), true);

  const journalRotate = resolvePreviewNarrowGateCopy("unsupported_rotate", "journal", {
    title: "请旋转至横屏，或改用电脑",
    lead: "Studio 工作台为横屏双列设计。",
  });
  assert.equal(journalRotate.lead.includes(PORTFOLIO_NARROW_REFINE_EXPORT_HINT), false);
});
