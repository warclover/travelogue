/**
 * 首页 v2 · shelf-actions-logic 单测（node --test）。
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  shelfResumeActions,
  shelfShowCoverLongshotBadge,
  shouldShowBentoStaleBar,
  bentoStaleMessage,
} from "../../templates/studio/homepage-v2/shelf-actions-logic.js";

describe("shelfResumeActions", function () {
  it("fresh trip only opens preview", function () {
    var actions = shelfResumeActions({});
    assert.equal(actions.length, 1);
    assert.equal(actions[0].kind, "open");
    assert.equal(actions[0].primary, true);
  });

  it("longshot stale prioritizes update longshot", function () {
    var actions = shelfResumeActions({ longshotStale: true });
    assert.equal(actions[0].kind, "longshot");
    assert.equal(actions[0].primary, true);
    assert.equal(actions[1].kind, "open");
    assert.equal(actions[1].primary, false);
  });

  it("algorithm stale offers recurate and demotes open", function () {
    var actions = shelfResumeActions({ algorithmStale: true });
    assert.equal(actions.length, 2);
    assert.equal(actions[0].kind, "algorithm");
    assert.equal(actions[0].triggerCurate, true);
    assert.equal(actions[0].primary, true);
    assert.equal(actions[1].kind, "open");
    assert.equal(actions[1].primary, false);
  });

  it("dual stale shows both longshot and algorithm CTAs", function () {
    var actions = shelfResumeActions({ longshotStale: true, algorithmStale: true });
    assert.equal(actions.length, 3);
    assert.equal(actions[0].kind, "longshot");
    assert.equal(actions[0].primary, true);
    assert.equal(actions[1].kind, "algorithm");
    assert.equal(actions[1].primary, false);
    assert.equal(actions[2].kind, "open");
  });
});

describe("shelfShowCoverLongshotBadge", function () {
  it("hides card badge when resume owns the longshot CTA", function () {
    assert.equal(
      shelfShowCoverLongshotBadge(
        { tripId: "a", longshotStale: true },
        { resumeTripId: "a" }
      ),
      false
    );
  });

  it("shows badge for other stale trips", function () {
    assert.equal(
      shelfShowCoverLongshotBadge(
        { tripId: "b", longshotStale: true },
        { resumeTripId: "a" }
      ),
      true
    );
  });

  it("hides when not longshot stale", function () {
    assert.equal(
      shelfShowCoverLongshotBadge({ tripId: "a", longshotStale: false }, { resumeTripId: "a" }),
      false
    );
  });
});

describe("bento stale helpers", function () {
  it("shows bar only for algorithm stale on user tab", function () {
    assert.equal(shouldShowBentoStaleBar({ algorithmStale: true }), true);
    assert.equal(shouldShowBentoStaleBar({ longshotStale: true }), false);
    assert.equal(shouldShowBentoStaleBar(null), false);
  });

  it("picks staleHint then staleHints[0]", function () {
    assert.equal(bentoStaleMessage({ staleHint: "首选" }), "首选");
    assert.equal(bentoStaleMessage({ staleHints: ["第一条", "第二条"] }), "第一条");
    assert.match(bentoStaleMessage({}), /重新排版/);
  });
});
