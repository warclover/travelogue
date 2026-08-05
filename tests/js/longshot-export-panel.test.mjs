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
  buildPanelHtml,
  clampAlbumSlideCount,
  clampSlideCountForPlatform,
  confirmedExportSummary,
  ctaLabelForPlatform,
  detectPlatformFromProgressHint,
  enabledPlatformsFromConfig,
  exportSummaryLine,
  isAlbumPresetCount,
  isComposePlatform,
  progressSynthesizingTitleForPlatform,
  progressTitleForPlatform,
  shortCtaLabelForPlatform,
  syncPanelUI,
} from "../../templates/studio/js/longshot-export-panel.js";

/** Minimal popover stub for syncPanelUI field visibility (no jsdom). */
function stubPopover() {
  const copy = { hidden: false };
  const note = { textContent: "" };
  const expectField = { hidden: true };
  const expectBody = { innerHTML: "", textContent: "" };
  const albumCountField = { hidden: true };
  return {
    querySelector(sel) {
      if (sel === '[data-field="copy"]') return copy;
      if (sel === ".preview-toolbar__export-popover-note") return note;
      if (sel === '[data-field="mode"]') return { hidden: false };
      if (sel === '[data-field="xhs-count"]') return { hidden: true };
      if (sel === '[data-field="xhs-pad"]') return { hidden: true };
      if (sel === '[data-field="album-count"]') return albumCountField;
      if (sel === '[data-field="expect"]') return expectField;
      if (sel === "[data-expect-body]") return expectBody;
      if (sel === '[data-field="coach"]') return { hidden: true, textContent: "" };
      if (sel === "[data-xhs-custom-row]") return { hidden: true };
      if (sel === "[data-studio-xhs-custom-input]") return null;
      if (sel === "[data-album-custom-row]") return { hidden: true };
      if (sel === "[data-studio-album-custom-input]") return null;
      if (sel === "[data-smart-crop-btn]") return null;
      if (sel === "[data-scale-hint]") return { textContent: "" };
      if (sel === "[data-xhs-estimate]") return null;
      return null;
    },
    querySelectorAll() {
      return [];
    },
    _copy: copy,
    _note: note,
    _albumCountField: albumCountField,
    _expectBody: expectBody,
  };
}

test("CQA · needsFullExportConfirm 认 mode=full 而非 segmentMode", async () => {
  const { needsFullExportConfirm } = await import(
    "../../templates/studio/js/output-recipe-logic.js"
  );
  const cfg = {
    enabled: true,
    sparseMax: 12,
    ambiguousMax: 40,
    narrativeChapterHintAt: 41,
  };
  assert.equal(needsFullExportConfirm(50, "full", "wechat_chat", cfg), true);
  assert.equal(needsFullExportConfirm(50, "chapter", "wechat_chat", cfg), false);
  // stale segmentMode-style "auto" must not be treated as full
  assert.equal(needsFullExportConfirm(50, "auto", "wechat_chat", cfg), false);
});

test("poster_bric 在 INTENT/PLATFORM 映射中互逆", () => {
  assert.equal(INTENT_TO_PLATFORM.poster_bric, "poster_bric");
  assert.equal(PLATFORM_TO_INTENT.poster_bric, "poster_bric");
  assert.equal(PLATFORM_TO_INTENT[INTENT_TO_PLATFORM.poster_bric], "poster_bric");
});

test("cta / short / summary 覆盖 poster_bric（禁止回落发微信群）", () => {
  assert.equal(ctaLabelForPlatform("poster_bric"), "导出单张海报");
  assert.equal(shortCtaLabelForPlatform("poster_bric"), "单张海报");
  assert.equal(confirmedExportSummary("poster_bric"), "当前将导出：单张海报 · 3:4");
  assert.notEqual(shortCtaLabelForPlatform("poster_bric"), "发微信群");
});

test("wechat_moments 短标签带导出动作（禁止裸「连读」）", () => {
  assert.equal(shortCtaLabelForPlatform("wechat_moments"), "导出连读");
  assert.match(ctaLabelForPlatform("wechat_moments"), /导出.*连读|长图连读/);
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

test("poster_bric / album_spread 隐藏「长图要不要字」；Studio 无九宫格入口", () => {
  assert.equal(PLATFORMS.poster_bric.showCopyControls, false);
  assert.equal(PLATFORMS.album_spread.showCopyControls, false);
  assert.equal(PLATFORMS.moments_grid, undefined);
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

test("P0 · humanExportProgress 平台文案（禁止回落到「微信」）", () => {
  assert.equal(isComposePlatform("xiaohongshu"), true);
  assert.equal(isComposePlatform("poster_bric"), true);
  assert.equal(isComposePlatform("album_spread"), true);
  assert.equal(isComposePlatform("wechat_chat"), false);

  assert.match(progressTitleForPlatform("xiaohongshu"), /小红书/);
  assert.match(progressTitleForPlatform("poster_bric"), /单张海报/);
  assert.match(progressTitleForPlatform("album_spread"), /画册/);
  assert.doesNotMatch(progressTitleForPlatform("poster_bric"), /微信/);
  assert.doesNotMatch(progressTitleForPlatform("album_spread"), /微信/);

  assert.equal(progressSynthesizingTitleForPlatform("xiaohongshu"), "正在合成拼贴…");
  assert.equal(progressSynthesizingTitleForPlatform("wechat_chat"), "正在合成长图…");

  assert.equal(detectPlatformFromProgressHint("小红书海报排队中，请稍候…"), "xiaohongshu");
  assert.equal(detectPlatformFromProgressHint("画册跨页排队中，请稍候…"), "album_spread");
  assert.equal(detectPlatformFromProgressHint("单张海报排队中，请稍候…"), "poster_bric");
  assert.equal(detectPlatformFromProgressHint("朋友圈连读排队中，请稍候…"), "wechat_moments");
  assert.equal(detectPlatformFromProgressHint("拼贴页 1/3"), null);
});

test("P2 · 画册跨页数：夹取范围与小红书区分（1–30 vs 1–18）", () => {
  assert.equal(clampAlbumSlideCount(0), 1);
  assert.equal(clampAlbumSlideCount(30), 30);
  assert.equal(clampAlbumSlideCount(99), 30);
  assert.equal(isAlbumPresetCount(3), true);
  assert.equal(isAlbumPresetCount(18), false);

  // 同一个数字，两个平台的夹取上限不同（18 vs 30）。
  assert.equal(clampSlideCountForPlatform("xiaohongshu", 25), 18);
  assert.equal(clampSlideCountForPlatform("album_spread", 25), 25);
});

test("P2 · buildPanelHtml 含跨页数字段；syncPanelUI 按 platform 显隐", () => {
  const html = buildPanelHtml(["wechat_chat", "xiaohongshu", "album_spread"]);
  assert.match(html, /data-field="album-count"/);
  assert.match(html, /data-studio-album-count="auto"/);
  assert.match(html, /跨页数/);

  const popAlbum = stubPopover();
  syncPanelUI(popAlbum, { platform: "album_spread", mode: "chapter", scale: 2, slideCount: null });
  assert.equal(popAlbum._albumCountField.hidden, false);

  const popChat = stubPopover();
  syncPanelUI(popChat, { platform: "wechat_chat", mode: "chapter", scale: 2 });
  assert.equal(popChat._albumCountField.hidden, true);

  const popManual = stubPopover();
  syncPanelUI(popManual, {
    platform: "album_spread",
    mode: "chapter",
    scale: 2,
    slideCount: 6,
  });
  assert.match(popManual._expectBody.innerHTML, /6/);
  assert.match(popManual._expectBody.innerHTML, /跨页/);
});
