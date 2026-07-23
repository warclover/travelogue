/**
 * QFX D-QFX-03 / AC-QFX-04 · ai-surface 只读导出；动态 import 无法翻转默认面。
 */
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import * as aiSurface from "../../templates/studio/js/ai-surface.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");

test("ai-surface 仅导出只读 API", () => {
  assert.equal(typeof aiSurface.isAiSurfaceEnabled, "function");
  assert.equal(typeof aiSurface.ensureAiSurfaceHydrated, "function");
  assert.equal(typeof aiSurface.getAiSurfaceState, "function");
  assert.equal(typeof aiSurface.whenAiSurface, "function");
  assert.equal(aiSurface.setAiSurfaceEnabled, undefined);
  assert.equal(aiSurface.hydrateAiSurfaceFromConfig, undefined);
  assert.equal(aiSurface.getAiSurfaceState(), "unknown");
  assert.equal(aiSurface.isAiSurfaceEnabled(), false);
});

test("动态 import 后无法挂写 setter，默认面保持关闭", () => {
  // ESM namespace 不可扩展：调用方无法注入 setAiSurfaceEnabled
  assert.throws(() => {
    aiSurface.setAiSurfaceEnabled = () => {};
  }, TypeError);
  assert.equal(aiSurface.isAiSurfaceEnabled(), false);
  aiSurface.whenAiSurface(() => {
    assert.fail("whenAiSurface must not run while disabled");
  });
});

test("设置 AI 区 / LLM Modal 入口源码只读门控", () => {
  const settings = readFileSync(
    join(root, "templates/studio/homepage-v2/settings-panel.js"),
    "utf8"
  );
  const llm = readFileSync(
    join(root, "templates/studio/js/llm-settings.js"),
    "utf8"
  );
  assert.match(settings, /isAiSurfaceEnabled/);
  assert.doesNotMatch(settings, /setAiSurfaceEnabled/);
  assert.match(settings, /zone\.hidden\s*=\s*!on/);
  assert.match(llm, /if\s*\(\s*!isAiSurfaceEnabled\(\)\s*\)\s*return/);
});
