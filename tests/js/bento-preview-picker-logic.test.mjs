/**
 * 首页 v2 · bento-preview-picker-logic 单测（node --test）。
 */
import test from "node:test";
import assert from "node:assert/strict";
import {
  tripLabel,
  matchesPreviewSearch,
  stalePreviewLabel,
  filterUserTrips,
  shouldDisablePreviewPicker,
} from "../../templates/studio/homepage-v2/bento-preview-picker-logic.js";

test("tripLabel prefers title then tripId", () => {
  assert.equal(tripLabel({ title: "林芝", tripId: "linzhi" }), "林芝");
  assert.equal(tripLabel({ tripId: "kyoto-rain" }), "kyoto-rain");
  assert.equal(tripLabel(null), "");
});

test("matchesPreviewSearch filters title and tripId", () => {
  var trip = { title: "凯哥拍摄精选3", tripId: "demo-2025-3" };
  assert.equal(matchesPreviewSearch(trip, ""), true);
  assert.equal(matchesPreviewSearch(trip, "凯哥"), true);
  assert.equal(matchesPreviewSearch(trip, "2025-3"), true);
  assert.equal(matchesPreviewSearch(trip, "missing"), false);
});

test("stalePreviewLabel prioritizes longshot", () => {
  assert.equal(stalePreviewLabel({ longshotStale: true, algorithmStale: true }), "长图待更新");
  assert.equal(stalePreviewLabel({ algorithmStale: true }), "算法待更新");
  assert.equal(stalePreviewLabel({}), "");
});

test("shouldDisablePreviewPicker when only demo trips", () => {
  assert.equal(
    shouldDisablePreviewPicker([{ tripId: "demo-album", title: "示例" }]),
    true
  );
  assert.equal(
    shouldDisablePreviewPicker([
      { tripId: "demo-album" },
      { tripId: "kyoto-rain", title: "京都" },
    ]),
    false
  );
  assert.equal(filterUserTrips([{ tripId: "demo-album" }, { tripId: "a" }]).length, 1);
});
