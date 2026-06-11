/**
 * trip-stale.js 单测（node --test）。
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  STALE_LABELS,
  tripStaleBits,
  tripStaleSummary,
  primaryStaleLabel,
  tripPreviewHref,
} from "../../templates/studio/js/trip-stale.js";

describe("tripStaleBits", function () {
  it("orders longshot before algorithm before layoutCss", function () {
    assert.deepEqual(
      tripStaleBits({
        layoutCssStale: true,
        algorithmStale: true,
        longshotStale: true,
      }),
      [STALE_LABELS.longshot, STALE_LABELS.algorithm, STALE_LABELS.layoutCss]
    );
  });
});

describe("tripPreviewHref", function () {
  it("focuses longshot when stale", function () {
    assert.equal(
      tripPreviewHref({ tripId: "demo", longshotStale: true }),
      "/demo/index.html?focus=longshot"
    );
  });
});

describe("primaryStaleLabel", function () {
  it("returns first stale bit", function () {
    assert.equal(
      primaryStaleLabel({ layoutCssStale: true, algorithmStale: true }),
      STALE_LABELS.algorithm
    );
  });
});

describe("tripStaleSummary", function () {
  it("joins with separator", function () {
    assert.equal(
      tripStaleSummary({ longshotStale: true, layoutCssStale: true }),
      STALE_LABELS.longshot + " · " + STALE_LABELS.layoutCss
    );
  });
});
