/**
 * SFH W1 · longshot-logic 单测
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  assessMagazineTitleRisk,
  disconnectExportFeedback,
  isFlagExpired,
  isExportSideEffectActiveFor,
  shouldShowLongshotStale,
  isLongshotContentStale,
  shouldReleaseLayoutUpdatingUi,
} from "../../templates/studio/preview-toolbar/longshot-logic.js";

test("assessMagazineTitleRisk 边界", () => {
  assert.deepEqual(assessMagazineTitleRisk(""), { level: "severe", reason: "empty" });
  assert.deepEqual(assessMagazineTitleRisk("a"), { level: "severe", reason: "too_short" });
  assert.equal(assessMagazineTitleRisk("京都雨后"), null);
  assert.equal(assessMagazineTitleRisk("京都+雨后").reason, "plus_join");
  assert.equal(assessMagazineTitleRisk("foo+bar"), null); // 艺术书名 bypass
});

test("disconnectExportFeedback", () => {
  const fb = disconnectExportFeedback("trip-1", "/other/");
  assert.equal(fb.linkHref, "/trip-1/");
  assert.match(fb.title, /服务已停止/);
  const noId = disconnectExportFeedback("", "/preview/");
  assert.equal(noId.linkHref, "/preview/");
});

test("isFlagExpired / sideEffect", () => {
  const now = 1_000_000;
  assert.equal(isFlagExpired(null, now, 1000), true);
  assert.equal(isFlagExpired({ ts: now - 500 }, now, 1000), false);
  assert.equal(isFlagExpired({ ts: now - 1500 }, now, 1000), true);

  assert.equal(
    isExportSideEffectActiveFor({ tripId: "t1", until: now + 10 }, "t1", now),
    true
  );
  assert.equal(
    isExportSideEffectActiveFor({ tripId: "t1", until: now - 1 }, "t1", now),
    false
  );
  assert.equal(
    isExportSideEffectActiveFor({ tripId: "t2", until: now + 10 }, "t1", now),
    false
  );
});

test("shouldShowLongshotStale 优先级", () => {
  assert.equal(
    shouldShowLongshotStale({ longshotStale: true, layoutPending: true }),
    false
  );
  assert.equal(
    shouldShowLongshotStale({ longshotStale: true, sideEffectActive: true }),
    false
  );
  assert.equal(
    shouldShowLongshotStale({ longshotStale: true }),
    true
  );
  assert.equal(shouldShowLongshotStale({ longshotStale: false }), false);
});

test("isLongshotContentStale · 缺字段 fail-open", () => {
  assert.equal(isLongshotContentStale(null, {}), false);
  assert.equal(
    isLongshotContentStale({ contentRevision: "1" }, { contentRevision: "2" }),
    true
  );
  assert.equal(
    isLongshotContentStale({ contentRevision: "1" }, { contentRevision: "1" }),
    false
  );
  assert.equal(
    isLongshotContentStale(
      { contentRevision: "1", exportToken: "a" },
      { contentRevision: "1", exportToken: "b" }
    ),
    true
  );
  assert.equal(
    isLongshotContentStale({ contentRevision: "1" }, { exportToken: "a" }),
    false
  );
});

test("shouldReleaseLayoutUpdatingUi · 不续跑则释放 busy", () => {
  assert.equal(shouldReleaseLayoutUpdatingUi({}), false);
  assert.equal(
    shouldReleaseLayoutUpdatingUi({
      showedUpdating: true,
      hasExportAfterFlag: true,
      layoutPending: false,
    }),
    false
  );
  assert.equal(
    shouldReleaseLayoutUpdatingUi({
      showedUpdating: true,
      hasExportAfterFlag: true,
      layoutPending: true,
    }),
    true
  );
  assert.equal(
    shouldReleaseLayoutUpdatingUi({
      showedUpdating: true,
      hasExportAfterFlag: false,
      hasUpdateOnlyHint: true,
    }),
    false
  );
  assert.equal(
    shouldReleaseLayoutUpdatingUi({
      showedUpdating: true,
      hasExportAfterFlag: false,
      hasUpdateOnlyHint: false,
    }),
    true
  );
});
