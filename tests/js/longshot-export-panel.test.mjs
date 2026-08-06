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
  batchChecklistItems,
  batchChecklistItemsFromResult,
  bindPanelDraft,
  buildPanelHtml,
  clampAlbumSlideCount,
  clampSlideCountForPlatform,
  confirmedExportSummary,
  ctaLabelForPlatform,
  ctaLabelForPlatforms,
  detectPlatformFromProgressHint,
  enabledPlatformsFromConfig,
  exportSummaryLine,
  exportSummaryLineForPlatforms,
  formatBatchSuccess,
  isAlbumPresetCount,
  isComposePlatform,
  isXhsPresetCount,
  normalizePlatformList,
  progressSynthesizingTitleForPlatform,
  progressTitleForPlatform,
  resolveAlbumCustomSeed,
  resolveXhsCustomSeed,
  shortCtaLabelForPlatform,
  shortCtaLabelForPlatforms,
  syncPanelUI,
} from "../../templates/studio/js/longshot-export-panel.js";

/** Minimal button stub used by both querySelector and querySelectorAll below. */
function stubBtn(attrName, attrValue) {
  const attrs = { [attrName]: attrValue };
  const classes = new Set();
  return {
    getAttribute(name) {
      return attrs[name] != null ? attrs[name] : null;
    },
    setAttribute(name, value) {
      attrs[name] = value;
    },
    classList: {
      toggle(name, on) {
        if (on) classes.add(name);
        else classes.delete(name);
      },
      contains(name) {
        return classes.has(name);
      },
    },
    // bindPanelDraft wires click handlers unconditionally on every matched
    // button; no-op here since these tests drive state via getDraft/setDraft
    // directly rather than simulating real clicks (no jsdom in this suite).
    addEventListener() {},
    _attrs: attrs,
  };
}

/** Minimal popover stub for syncPanelUI field visibility (no jsdom). */
function stubPopover(platformIds) {
  const copy = { hidden: false };
  const note = { textContent: "" };
  const expectField = { hidden: true };
  const expectBody = { innerHTML: "", textContent: "" };
  const albumCountField = { hidden: true };
  const batchHint = { hidden: true, textContent: "" };
  const platformBtns = (platformIds || []).map((id) =>
    stubBtn("data-studio-longshot-platform", id)
  );
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
      if (sel === "[data-batch-hint]") return batchHint;
      return null;
    },
    querySelectorAll(sel) {
      if (sel === "[data-studio-longshot-platform]") return platformBtns;
      return [];
    },
    _copy: copy,
    _note: note,
    _albumCountField: albumCountField,
    _expectField: expectField,
    _expectBody: expectBody,
    _batchHint: batchHint,
    _platformBtns: platformBtns,
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

test("回归 2026-08-05 · 画册/小红书点击「自定义」必须落在非预设值上（否则自定义框不出现）", () => {
  // 画册：这是用户实测复现的 bug —— 旧代码 fallback 用的 6 本身就是预设值，
  // 导致无论从哪个入口点「自定义」，都会被 isAlbumPresetCount 打回预设态，
  // 自定义输入框永远不出现。
  assert.equal(isAlbumPresetCount(resolveAlbumCustomSeed(null)), false);
  assert.equal(isAlbumPresetCount(resolveAlbumCustomSeed(3)), false);
  assert.equal(isAlbumPresetCount(resolveAlbumCustomSeed(6)), false);
  assert.equal(isAlbumPresetCount(resolveAlbumCustomSeed(9)), false);
  // 已经是自定义值时，保留用户原有输入，不要跳到默认种子值。
  assert.equal(resolveAlbumCustomSeed(7), 7);
  assert.equal(resolveAlbumCustomSeed(20), 20);

  // 小红书：同一套隐患（若用户先点了预设「6/9/12」再点「自定义」）。
  assert.equal(isXhsPresetCount(resolveXhsCustomSeed(null)), false);
  assert.equal(isXhsPresetCount(resolveXhsCustomSeed(6)), false);
  assert.equal(isXhsPresetCount(resolveXhsCustomSeed(9)), false);
  assert.equal(isXhsPresetCount(resolveXhsCustomSeed(12)), false);
  assert.equal(resolveXhsCustomSeed(10), 10);
});

test("wechat_official（公众号）导出形式与 xiaohongshu 一致，仅文案/标识不同", () => {
  // INTENT/PLATFORM 映射互逆，同 poster_bric 的校验方式。
  assert.equal(INTENT_TO_PLATFORM.wechat_official, "wechat_official");
  assert.equal(PLATFORM_TO_INTENT.wechat_official, "wechat_official");
  assert.equal(
    PLATFORM_TO_INTENT[INTENT_TO_PLATFORM.wechat_official],
    "wechat_official"
  );

  // Compose 路径归属与 xiaohongshu 相同（3:4 Card 管线，非 Playwright 长图）。
  assert.equal(isComposePlatform("wechat_official"), true);

  assert.equal(shortCtaLabelForPlatform("wechat_official"), "公众号");
  assert.notEqual(shortCtaLabelForPlatform("wechat_official"), "发微信群");
  assert.match(ctaLabelForPlatform("wechat_official"), /公众号/);

  assert.match(progressTitleForPlatform("wechat_official"), /公众号/);
  assert.doesNotMatch(progressTitleForPlatform("wechat_official"), /微信群|小红书/);
  assert.equal(
    progressSynthesizingTitleForPlatform("wechat_official"),
    "正在合成拼贴…"
  );

  assert.equal(
    detectPlatformFromProgressHint("公众号配图排队中，请稍候…"),
    "wechat_official"
  );

  // 默认灰度名单默认展示公众号（与小红书同级，方案见 OQ 决策 2026-08-05）。
  const enabled = enabledPlatformsFromConfig({
    longshot2: { enabled: true },
  });
  assert.ok(enabled.includes("wechat_official"));

  // 弹层内复用小红书那套「张数」控件（showXhsOptions），非小红书专属文案。
  assert.equal(PLATFORMS.wechat_official.showXhsOptions, true);
  assert.notEqual(PLATFORMS.wechat_official.label, PLATFORMS.xiaohongshu.label);
});

// PRD-BATCH-EXPORT-MULTISELECT-V1 · Stage 2 MVP（导出面板多选，D-BEX-01 简化版）

test("normalizePlatformList · 去重/去空，兜底 wechat_chat", () => {
  assert.deepEqual(normalizePlatformList(["xiaohongshu", "xiaohongshu", "album_spread"]), [
    "xiaohongshu",
    "album_spread",
  ]);
  assert.deepEqual(normalizePlatformList([]), ["wechat_chat"]);
  assert.deepEqual(normalizePlatformList(null), ["wechat_chat"]);
  assert.deepEqual(normalizePlatformList(["", null, "xiaohongshu"]), ["xiaohongshu"]);
  assert.deepEqual(normalizePlatformList([], "poster_bric"), ["poster_bric"]);
});

test("ctaLabelForPlatforms / shortCtaLabelForPlatforms · 单选=单平台文案零回归，多选='N 个模式'", () => {
  assert.equal(ctaLabelForPlatforms(["xiaohongshu"]), ctaLabelForPlatform("xiaohongshu"));
  assert.equal(
    shortCtaLabelForPlatforms(["xiaohongshu"]),
    shortCtaLabelForPlatform("xiaohongshu")
  );
  assert.equal(ctaLabelForPlatforms(["xiaohongshu", "wechat_moments"]), "导出 2 个模式");
  assert.equal(shortCtaLabelForPlatforms(["xiaohongshu", "wechat_moments", "album_spread"]), "3 个模式");
});

test("exportSummaryLineForPlatforms · 单选零回归；多选展示平台清单与待确认态", () => {
  assert.equal(
    exportSummaryLineForPlatforms(["wechat_chat"], ["wechat_chat"]),
    exportSummaryLine("wechat_chat", "wechat_chat")
  );
  const same = exportSummaryLineForPlatforms(
    ["xiaohongshu", "wechat_moments"],
    ["xiaohongshu", "wechat_moments"]
  );
  assert.match(same, /当前将导出：2 个模式/);
  assert.match(same, /小红书/);
  assert.match(same, /朋友圈/);

  const pending = exportSummaryLineForPlatforms(["wechat_chat"], ["xiaohongshu", "wechat_moments"]);
  assert.match(pending, /已改选：2 个模式/);
  assert.match(pending, /点「确定」后生效/);
  assert.match(pending, /金色按钮仍按：微信群/);
});

test("formatBatchSuccess · 全部成功 / 部分失败文案（D-BEX-05 不整体判失败)", () => {
  const allOk = formatBatchSuccess({
    batch: true,
    succeededCount: 2,
    failedCount: 0,
    items: [
      { platform: "xiaohongshu", ok: true, pageCount: 8 },
      { platform: "wechat_moments", ok: true, outputs: ["a.png", "b.png", "c.png"] },
    ],
  });
  assert.equal(allOk.title, "✓ 2 个模式已全部导出");
  assert.match(allOk.lines[0], /小红书.*8 张/);
  assert.match(allOk.lines[1], /连读.*3 张/);

  const partial = formatBatchSuccess({
    batch: true,
    succeededCount: 1,
    failedCount: 1,
    items: [
      { platform: "xiaohongshu", ok: true, pageCount: 8 },
      { platform: "wechat_moments", ok: false, error: "E_LNG_CAPTURE_TOO_LARGE", message: "画布太大" },
    ],
  });
  assert.equal(partial.title, "已完成 1/2 个模式（1 个失败）");
  assert.match(partial.lines[1], /✗.*画布太大/);
});

test("batchChecklistItems · 进行中清单：早于当前=done，当前=running，其余=queued", () => {
  const items = batchChecklistItems(["xiaohongshu", "wechat_moments", "album_spread"], 2);
  assert.deepEqual(
    items.map((it) => [it.platform, it.status]),
    [
      ["xiaohongshu", "done"],
      ["wechat_moments", "running"],
      ["album_spread", "queued"],
    ]
  );
  assert.equal(items[1].label, shortCtaLabelForPlatform("wechat_moments"));

  // cur < 1 / 非数字兜底为 1（第一项 running，其余 queued）
  const first = batchChecklistItems(["xiaohongshu", "wechat_moments"], 0);
  assert.deepEqual(first.map((it) => it.status), ["running", "queued"]);

  // cur 超过清单长度：全部视为 done（已跑完轮到下一批，仅用于展示）
  const allDone = batchChecklistItems(["xiaohongshu", "wechat_moments"], 5);
  assert.deepEqual(allDone.map((it) => it.status), ["done", "done"]);
});

test("batchChecklistItemsFromResult · 完成态：ok→done+张数，失败→failed+原因（D-BEX-05）", () => {
  const items = batchChecklistItemsFromResult({
    items: [
      { platform: "xiaohongshu", ok: true, pageCount: 8 },
      { platform: "wechat_moments", ok: false, error: "E_LNG_CAPTURE_TOO_LARGE", message: "画布太大" },
      { platform: "album_spread", ok: true, outputs: ["a.png", "b.png"] },
    ],
  });
  assert.deepEqual(items[0], {
    platform: "xiaohongshu",
    label: shortCtaLabelForPlatform("xiaohongshu"),
    status: "done",
    detail: "8 张",
  });
  assert.equal(items[1].status, "failed");
  assert.equal(items[1].detail, "画布太大");
  assert.equal(items[2].detail, "2 张"); // 无 pageCount 时兜底用 outputs.length
  assert.deepEqual(batchChecklistItemsFromResult({}), []);
});

test("syncPanelUI · 多选态隐藏张数/跨页数控件，展示批量提示", () => {
  const popSingle = stubPopover(["xiaohongshu", "album_spread"]);
  syncPanelUI(popSingle, { platforms: ["xiaohongshu"], mode: "chapter", scale: 2 });
  assert.equal(popSingle._batchHint.hidden, true);
  assert.equal(popSingle._platformBtns[0].getAttribute("aria-checked"), "true");
  assert.equal(popSingle._platformBtns[1].getAttribute("aria-checked"), "false");

  const popBatch = stubPopover(["xiaohongshu", "album_spread"]);
  syncPanelUI(popBatch, {
    platforms: ["xiaohongshu", "album_spread"],
    mode: "chapter",
    scale: 2,
  });
  assert.equal(popBatch._batchHint.hidden, false);
  assert.match(popBatch._batchHint.textContent, /批量导出.*2 个模式/);
  assert.equal(popBatch._albumCountField.hidden, true); // 批量态强制隐藏（MVP 简化）
  assert.equal(popBatch._expectField.hidden, true);
  assert.equal(popBatch._expectBody.textContent, "");
  assert.equal(popBatch._platformBtns[0].getAttribute("aria-checked"), "true");
  assert.equal(popBatch._platformBtns[1].getAttribute("aria-checked"), "true");
});

test("bindPanelDraft · getDraft/setDraft 单选零回归 + platforms 数组往返", () => {
  const pop = stubPopover(["xiaohongshu", "album_spread"]);
  const panel = bindPanelDraft(pop, { platform: "xiaohongshu" }, {});
  const draft1 = panel.getDraft();
  assert.equal(draft1.platform, "xiaohongshu");
  assert.deepEqual(draft1.platforms, ["xiaohongshu"]);

  panel.setDraft({ platforms: ["xiaohongshu", "wechat_moments"] });
  const draft2 = panel.getDraft();
  assert.equal(draft2.platform, "xiaohongshu");
  assert.deepEqual(draft2.platforms, ["xiaohongshu", "wechat_moments"]);

  // 向后兼容：仅传 platform（旧调用点）仍可用，等价单元素数组。
  panel.setDraft({ platform: "poster_bric" });
  assert.deepEqual(panel.getDraft().platforms, ["poster_bric"]);
});
