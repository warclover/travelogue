/**
 * 首页 v2 · lightbox-logic 单测（node --test）。
 * 覆盖 PRD §6.4：轻点阈值（mouse 10 / touch 8）、轻点 vs 横拖 vs 内滚。
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  LIGHTBOX_DRAG_THRESHOLD_PX,
  thresholdFor,
  isTap,
  classifyGesture,
} from "../../templates/studio/homepage-v2/lightbox-logic.js";

test("阈值常量 mouse 10 / touch 8", () => {
  assert.equal(LIGHTBOX_DRAG_THRESHOLD_PX.mouse, 10);
  assert.equal(LIGHTBOX_DRAG_THRESHOLD_PX.touch, 8);
  assert.equal(thresholdFor(false), 10);
  assert.equal(thresholdFor(true), 8);
});

test("isTap：位移在阈值内为轻点", () => {
  assert.equal(isTap(5, 5, false), true);
  assert.equal(isTap(10, 0, false), true); // 等于阈值仍算轻点
  assert.equal(isTap(11, 0, false), false);
  assert.equal(isTap(8, 0, true), true);
  assert.equal(isTap(9, 0, true), false); // touch 阈值更小
});

test("classifyGesture：tap / horizontal-drag / vertical-scroll", () => {
  assert.equal(classifyGesture(3, 3, false), "tap");
  assert.equal(classifyGesture(20, 5, false), "horizontal-drag"); // 横拖 → 翻页
  assert.equal(classifyGesture(5, 20, false), "vertical-scroll"); // 纵向 → 内滚
  assert.equal(classifyGesture(20, 5, true), "horizontal-drag");
  // 边界：刚超 touch 阈值的横向移动应判为横拖（不误触 Lightbox）
  assert.equal(classifyGesture(9, 0, true), "horizontal-drag");
});
