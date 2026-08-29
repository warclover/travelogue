/**
 * QFX D-QFX-12 · 复制三态合同。
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  COPY_DONE,
  COPY_FAIL,
  COPY_OK,
  COPY_PENDING,
  COPY_RETRY,
  bindCopyPageUrlControl,
  copyTextThreeState,
} from "../../templates/studio/js/copy-page-url.js";

function stubClipboard(writeText) {
  Object.defineProperty(globalThis, "navigator", {
    configurable: true,
    value: {
      clipboard: { writeText },
    },
  });
}

function stubDocument(execCommand = () => false) {
  globalThis.document = {
    createElement: () => ({
      style: {},
      setAttribute() {},
      select() {},
    }),
    body: { appendChild() {}, removeChild() {} },
    execCommand,
  };
}

test("copy 文案常量对齐 COPY-QFX", () => {
  assert.equal(COPY_PENDING, "正在复制…");
  assert.equal(COPY_OK, "地址已复制，请在电脑浏览器打开");
  assert.equal(COPY_DONE, "已复制");
  assert.equal(COPY_FAIL, "无法自动复制。请长按选择下方地址并复制。");
  assert.equal(COPY_RETRY, "重新复制");
});

test("clipboard 成功 → ok", async () => {
  stubClipboard(async () => {});
  stubDocument();
  globalThis.studioToast = () => {};
  assert.equal(await copyTextThreeState("https://example.test"), "ok");
});

test("成功后按钮先显示已复制，不立刻回到默认文案", async () => {
  stubClipboard(async () => {});
  stubDocument();
  globalThis.studioToast = () => {};
  let handler = null;
  const button = {
    textContent: "复制电脑打开地址",
    dataset: {},
    addEventListener(_type, fn) {
      handler = fn;
    },
  };
  const pending = [];
  globalThis.setTimeout = (fn) => {
    pending.push(fn);
    return 1;
  };
  globalThis.clearTimeout = () => {};
  bindCopyPageUrlControl({
    button,
    getUrl: () => "https://example.test",
    defaultLabel: "复制电脑打开地址",
  });
  handler();
  assert.equal(button.textContent, COPY_PENDING);
  await Promise.resolve();
  await Promise.resolve();
  assert.equal(button.textContent, COPY_DONE);
  assert.equal(pending.length, 1);
  pending[0]();
  assert.equal(button.textContent, "复制电脑打开地址");
});

test("clipboard 失败且 fallback 失败 → fail（无成功态）", async () => {
  stubClipboard(async () => {
    throw new Error("denied");
  });
  stubDocument(() => false);
  globalThis.studioToast = () => {};
  assert.equal(await copyTextThreeState("https://example.test"), "fail");
});
