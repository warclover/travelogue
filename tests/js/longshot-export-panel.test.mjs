/**
 * Dogfood UX Fixpack M1 · 导出面板平台映射 / CTA（AC-DFX-02）
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  INTENT_TO_PLATFORM,
  PLATFORM_TO_INTENT,
} from "../../templates/studio/js/output-recipe-logic.js";
import {
  confirmedExportSummary,
  ctaLabelForPlatform,
  enabledPlatformsFromConfig,
  shortCtaLabelForPlatform,
} from "../../templates/studio/js/longshot-export-panel.js";

test("poster_bric 在 INTENT/PLATFORM 映射中互逆", () => {
  assert.equal(INTENT_TO_PLATFORM.poster_bric, "poster_bric");
  assert.equal(PLATFORM_TO_INTENT.poster_bric, "poster_bric");
  assert.equal(PLATFORM_TO_INTENT[INTENT_TO_PLATFORM.poster_bric], "poster_bric");
});

test("cta / short / summary 覆盖 poster_bric（禁止回落发微信群）", () => {
  assert.equal(ctaLabelForPlatform("poster_bric"), "导出单屏海报");
  assert.equal(shortCtaLabelForPlatform("poster_bric"), "单屏海报");
  assert.equal(confirmedExportSummary("poster_bric"), "当前将导出：单屏海报");
  assert.notEqual(shortCtaLabelForPlatform("poster_bric"), "发微信群");
});

test("enabledPlatformsFromConfig · gcsPosterBric on/off", () => {
  const off = enabledPlatformsFromConfig({
    longshot2: { enabled: true, platforms: ["wechat_moments", "xiaohongshu"] },
    gcsPosterBric: { enabled: false },
  });
  assert.ok(!off.includes("poster_bric"));

  const on = enabledPlatformsFromConfig({
    longshot2: { enabled: true, platforms: ["wechat_moments", "xiaohongshu"] },
    gcsPosterBric: { enabled: true },
  });
  assert.ok(on.includes("poster_bric"));
  assert.ok(on.includes("wechat_chat"));
});
