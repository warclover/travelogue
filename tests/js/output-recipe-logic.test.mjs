/**
 * SFH W0b · output-recipe-logic 单测 + 共享 Band 向量。
 */
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  INTENT_TO_PLATFORM,
  PLATFORM_TO_INTENT,
  DEFAULT_BANDS,
  parseStudioOutputRecipeConfig,
  normalizeBands,
  isBandThresholdOrderValid,
  classifyBand,
  needsFullExportConfirm,
  resolveClientRecipe,
  mapServerRecipePayload,
  readSessionIntentFromStorage,
  writeSessionIntentToStorage,
  clearSessionIntentFromStorage,
} from "../../templates/studio/js/output-recipe-logic.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
const vectors = JSON.parse(
  readFileSync(join(root, "tests/fixtures/output_recipe_band_vectors.json"), "utf8")
);

function cfgFromSet(setId, enabled) {
  const t = vectors.thresholdSets[setId];
  return {
    enabled: enabled !== false,
    sparseMax: t.sparseMax,
    ambiguousMax: t.ambiguousMax,
    narrativeChapterHintAt: t.narrativeChapterHintAt,
  };
}

test("INTENT_TO_PLATFORM / PLATFORM_TO_INTENT 关键键互逆", () => {
  for (const [intent, platform] of Object.entries(INTENT_TO_PLATFORM)) {
    assert.equal(PLATFORM_TO_INTENT[platform], intent);
  }
  for (const [platform, intent] of Object.entries(PLATFORM_TO_INTENT)) {
    assert.equal(INTENT_TO_PLATFORM[intent], platform);
  }
});

test("parseStudioOutputRecipeConfig 默认与 camel/snake", () => {
  assert.deepEqual(parseStudioOutputRecipeConfig({}), {
    enabled: false,
    ...DEFAULT_BANDS,
  });
  const parsed = parseStudioOutputRecipeConfig({
    outputRecipe: {
      enabled: true,
      bands: { sparse_max: 5, ambiguousMax: 20, narrative_chapter_hint_at: 35 },
    },
  });
  assert.equal(parsed.enabled, true);
  assert.equal(parsed.sparseMax, 5);
  assert.equal(parsed.ambiguousMax, 20);
  assert.equal(parsed.narrativeChapterHintAt, 35);
});

test("共享向量 · classifyBand 与夹具一致", () => {
  for (const c of vectors.bandCases) {
    const band = classifyBand(c.keptN, vectors.thresholdSets[c.thresholds]);
    assert.equal(band, c.band, `${c.thresholds} keptN=${c.keptN}`);
  }
});

test("共享向量 · needsFullExportConfirm", () => {
  for (const c of vectors.confirmCases) {
    const cfg = cfgFromSet(c.thresholds, c.enabled);
    const got = needsFullExportConfirm(c.keptN, c.mode, c.platform, cfg);
    assert.equal(got, c.expect, JSON.stringify(c));
  }
});

test("共享向量 · resolveClientRecipe（降级/本地路径）", () => {
  for (const c of vectors.clientResolveCases) {
    const cfg = cfgFromSet(c.thresholds, c.enabled);
    const tip = resolveClientRecipe(c.keptN, c.entrypoint, cfg, c.sessionIntent);
    assert.equal(tip.band, c.band, c.id);
    assert.equal(tip.needsIntent, c.needsIntent, c.id);
    assert.equal(tip.intent, c.intent, c.id);
  }
});

test("共享向量 · mapServerRecipePayload 采信服务端", () => {
  for (const c of vectors.serverMapCases) {
    const cfg = cfgFromSet(c.thresholds, c.enabled);
    const tip = mapServerRecipePayload(c.body, c.entrypoint, cfg, c.sessionIntent);
    assert.equal(tip.band, c.expect.band, c.id);
    assert.equal(tip.needsIntent, c.expect.needsIntent, c.id);
    assert.equal(tip.intent, c.expect.intent, c.id);
    assert.equal(tip.source, c.expect.source, c.id);
    assert.equal(tip.keptN, c.expect.keptN, c.id);
  }
});

test("session storage helpers round-trip", () => {
  const store = new Map();
  const storage = {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
  };
  assert.equal(readSessionIntentFromStorage(storage, "t1"), null);
  writeSessionIntentToStorage(storage, "t1", "moments_grid");
  assert.equal(readSessionIntentFromStorage(storage, "t1"), "moments_grid");
  clearSessionIntentFromStorage(storage, "t1");
  assert.equal(readSessionIntentFromStorage(storage, "t1"), null);
});

test("OR-X-05 · 非法/NaN/空阈值 fail-open 回退默认（不抛错）", () => {
  assert.deepEqual(
    normalizeBands({ sparseMax: NaN, ambiguousMax: "x", narrativeChapterHintAt: null }),
    DEFAULT_BANDS
  );
  assert.deepEqual(normalizeBands({ sparseMax: 0, ambiguousMax: 0 }), {
    ...DEFAULT_BANDS,
    // Number(0)||default → 默认（历史 FE 行为；合法 0 不保留）
  });
  assert.equal(classifyBand(10, { sparseMax: "bad", ambiguousMax: "worse" }), "ambiguous");
});

test("OR-X-06 · 阈值顺序护栏布尔；乱序不自动改写", () => {
  assert.equal(isBandThresholdOrderValid(DEFAULT_BANDS), true);
  assert.equal(isBandThresholdOrderValid({ sparseMax: 30, ambiguousMax: 9 }), false);
  const inverted = normalizeBands({ sparseMax: 30, ambiguousMax: 9 });
  assert.equal(inverted.sparseMax, 30);
  assert.equal(inverted.ambiguousMax, 9);
  // 乱序下 classify 仍按数值比较（不拒绝）
  assert.equal(classifyBand(10, inverted), "sparse"); // 10 <= 30
});
