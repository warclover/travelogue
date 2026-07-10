/**
 * layout-tier 单测（node --test）。
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  resolveLayoutTier,
  shouldEagerCarouselPage,
} from "../../templates/studio/homepage-v2/layout-tier.js";

test("resolveLayoutTier L3 when manifestError", () => {
  assert.equal(resolveLayoutTier({ manifestError: true }), "L3");
});

test("resolveLayoutTier L2 when harnessSlowNet opt", () => {
  assert.equal(resolveLayoutTier({ harnessSlowNet: true }), "L2");
});

test("shouldEagerCarouselPage only first two slides on all tiers", () => {
  assert.equal(shouldEagerCarouselPage(0, "L0"), true);
  assert.equal(shouldEagerCarouselPage(1, "L0"), true);
  assert.equal(shouldEagerCarouselPage(2, "L0"), false);
  assert.equal(shouldEagerCarouselPage(0, "L2"), true);
  assert.equal(shouldEagerCarouselPage(1, "L2"), true);
  assert.equal(shouldEagerCarouselPage(2, "L2"), false);
  assert.equal(shouldEagerCarouselPage(4, "L0"), false);
});
