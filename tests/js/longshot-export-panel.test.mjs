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
  PLATFORMS,
  confirmedExportSummary,
  ctaLabelForPlatform,
  enabledPlatformsFromConfig,
  exportSummaryLine,
  shortCtaLabelForPlatform,
  syncPanelUI,
} from "../../templates/studio/js/longshot-export-panel.js";

/** Minimal popover stub for syncPanelUI field visibility (no jsdom). */
function stubPopover() {
  const copy = { hidden: false };
  const note = { textContent: "" };
  const expectField = { hidden: true };
  const expectBody = { innerHTML: "", textContent: "" };
  return {
    querySelector(sel) {
      if (sel === '[data-field="copy"]') return copy;
      if (sel === ".preview-toolbar__export-popover-note") return note;
      if (sel === '[data-field="mode"]') return { hidden: false };
      if (sel === '[data-field="xhs-count"]') return { hidden: true };
      if (sel === '[data-field="xhs-pad"]') return { hidden: true };
      if (sel === '[data-field="expect"]') return expectField;
      if (sel === "[data-expect-body]") return expectBody;
      if (sel === '[data-field="coach"]') return { hidden: true, textContent: "" };
      if (sel === "[data-xhs-custom-row]") return { hidden: true };
      if (sel === "[data-studio-xhs-custom-input]") return null;
      if (sel === "[data-smart-crop-btn]") return null;
      if (sel === "[data-xhs-estimate]") return null;
      return null;
    },
    querySelectorAll() {
      return [];
    },
    _copy: copy,
    _note: note,
  };
}

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

test("exportSummaryLine · draft 未确认时提示待生效", () => {
  assert.equal(
    exportSummaryLine("wechat_chat", "wechat_chat"),
    "当前将导出：微信群"
  );
  assert.match(
    exportSummaryLine("wechat_chat", "wechat_moments"),
    /已改选：.*点「确定」后生效/
  );
  assert.match(
    exportSummaryLine("wechat_chat", "wechat_moments"),
    /金色按钮仍按：微信群/
  );
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

test("poster_bric / moments_grid 隐藏「长图要不要字」", () => {
  assert.equal(PLATFORMS.poster_bric.showCopyControls, false);
  assert.equal(PLATFORMS.moments_grid.showCopyControls, false);
  assert.notEqual(PLATFORMS.wechat_chat.showCopyControls, false);

  const popPoster = stubPopover();
  syncPanelUI(popPoster, { platform: "poster_bric", mode: "full", scale: 2 });
  assert.equal(popPoster._copy.hidden, true);
  assert.match(popPoster._note.textContent, /金色按钮/);
  assert.doesNotMatch(popPoster._note.textContent, /要不要字/);

  const popChat = stubPopover();
  syncPanelUI(popChat, { platform: "wechat_chat", mode: "chapter", scale: 2 });
  assert.equal(popChat._copy.hidden, false);
  assert.match(popChat._note.textContent, /要不要字/);
});
