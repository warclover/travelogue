/**
 * 首页 v2 · carousel-logic 单测（node --test）。
 * 覆盖 DATA-CONTRACT §1.3：clamp 不 wrap、spread 映射、奇数尾页留白、scrollLeft。
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  clampIndex,
  spreadFor,
  scrollLeftFor,
  indexFromScrollLeft,
  canPrev,
  canNext,
  isOddTail,
} from "../../templates/studio/homepage-v2/carousel-logic.js";

const PAGES = [
  { id: "cover", role: "cover" },
  { id: "ch01", role: "chapter" },
  { id: "ch02", role: "chapter" },
  { id: "ch03", role: "chapter" },
  { id: "epilogue", role: "epilogue" },
];

test("clampIndex 不 wrap，clamp 到 [0, pageCount-1]", () => {
  assert.equal(clampIndex(-1, 5), 0);
  assert.equal(clampIndex(0, 5), 0);
  assert.equal(clampIndex(2, 5), 2);
  assert.equal(clampIndex(4, 5), 4);
  assert.equal(clampIndex(5, 5), 4); // 越界不回绕到 0
  assert.equal(clampIndex(99, 5), 4);
  assert.equal(clampIndex(2.4, 5), 2);
  assert.equal(clampIndex(0, 0), 0); // 空集兜底
});

test("spreadFor 左右半页映射（含奇数尾页留白）", () => {
  assert.deepEqual(spreadFor(PAGES, 0), { left: PAGES[0], right: PAGES[1] });
  assert.deepEqual(spreadFor(PAGES, 3), { left: PAGES[3], right: PAGES[4] });
  // 尾页：右半留白
  assert.deepEqual(spreadFor(PAGES, 4), { left: PAGES[4], right: null });
  // 越界请求被 clamp 到尾页
  assert.deepEqual(spreadFor(PAGES, 9), { left: PAGES[4], right: null });
});

test("scrollLeft = i × (viewportWidth/2)", () => {
  assert.equal(scrollLeftFor(0, 1000), 0);
  assert.equal(scrollLeftFor(1, 1000), 500);
  assert.equal(scrollLeftFor(4, 1000), 2000);
});

test("indexFromScrollLeft 反推并 clamp", () => {
  assert.equal(indexFromScrollLeft(0, 1000, 5), 0);
  assert.equal(indexFromScrollLeft(500, 1000, 5), 1);
  assert.equal(indexFromScrollLeft(2500, 1000, 5), 4); // 越界 clamp
  assert.equal(indexFromScrollLeft(-100, 1000, 5), 0);
});

test("canPrev / canNext 边界禁用（首尾箭头）", () => {
  assert.equal(canPrev(0), false);
  assert.equal(canPrev(1), true);
  assert.equal(canNext(3, 5), true);
  assert.equal(canNext(4, 5), false); // 末页禁止下一屏（不拼版回封面）
});

test("isOddTail 仅末页为真", () => {
  assert.equal(isOddTail(PAGES, 4), true);
  assert.equal(isOddTail(PAGES, 3), false);
});
