/**
 * 首页 v2 · viewport-logic 单测（node --test）。
 * 覆盖 PRD §10.1 支持矩阵：wide / iPad 横屏 / 竖屏旋转 / 手机 / 窄窗。
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  classifyViewport,
  isSupported,
  unsupportedCopy,
} from "../../templates/studio/homepage-v2/viewport-logic.js";

test("classifyViewport 支持矩阵", () => {
  assert.equal(classifyViewport(1440, 900, false), "wide");
  assert.equal(classifyViewport(1024, 1366, false), "wide"); // ≥1024 即 Bento
  assert.equal(classifyViewport(900, 700, false), "tablet_landscape"); // iPad 横屏
  assert.equal(classifyViewport(800, 1100, false), "unsupported_rotate"); // 平板竖屏
  assert.equal(classifyViewport(500, 900, true), "unsupported_phone"); // 手机触屏
  assert.equal(classifyViewport(700, 500, false), "unsupported_narrow"); // 桌面窄窗
});

test("isSupported 仅 wide / tablet_landscape", () => {
  assert.equal(isSupported("wide"), true);
  assert.equal(isSupported("tablet_landscape"), true);
  assert.equal(isSupported("unsupported_rotate"), false);
  assert.equal(isSupported("unsupported_phone"), false);
  assert.equal(isSupported("unsupported_narrow"), false);
});

test("unsupportedCopy 文案分支", () => {
  assert.match(unsupportedCopy("unsupported_rotate").title, /横屏/);
  assert.match(unsupportedCopy("unsupported_phone").title, /电脑浏览器/);
  assert.match(unsupportedCopy("unsupported_narrow").title, /拉宽/);
});

test("unsupportedCopy narrow 含当前宽度", () => {
  var copy = unsupportedCopy("unsupported_narrow", { width: 390 });
  assert.match(copy.lead, /当前 390px/);
  assert.equal(copy.actions.length, 0);
});

test("unsupportedCopy phone 含动作区", () => {
  var copy = unsupportedCopy("unsupported_phone");
  assert.equal(copy.actions.length, 2);
  assert.equal(copy.actions[0].type, "miniapp_qr");
  assert.equal(copy.actions[1].type, "copy_link");
  assert.match(copy.actions[1].label, /复制/);
});
