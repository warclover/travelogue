/**
 * SFH W2 · import-wizard-logic 单测（关闭确认 / dirty / 步骤矩阵）
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  normalizeWizardStep,
  isFineSnapshotDirty,
  isPhotoPrefsNonDefault,
  shouldConfirmCloseWizard,
  canLeavePickStep,
  canNavigateWizardStep,
} from "../../templates/studio/homepage-v2/import-wizard-logic.js";

test("normalizeWizardStep", () => {
  assert.equal(normalizeWizardStep("fine"), "fine");
  assert.equal(normalizeWizardStep("confirm"), "confirm");
  assert.equal(normalizeWizardStep("pick"), "pick");
  assert.equal(normalizeWizardStep("other"), "pick");
});

test("isFineSnapshotDirty", () => {
  assert.equal(isFineSnapshotDirty(null, { title: "a" }), false);
  assert.equal(
    isFineSnapshotDirty({ title: "a", place: "" }, { title: "a", place: "" }),
    false
  );
  assert.equal(
    isFineSnapshotDirty({ title: "a" }, { title: "b" }),
    true
  );
});

test("isPhotoPrefsNonDefault", () => {
  assert.equal(isPhotoPrefsNonDefault({}), false);
  assert.equal(isPhotoPrefsNonDefault({ photoCullEnabled: true }), false);
  assert.equal(isPhotoPrefsNonDefault({ photoCullEnabled: false }), true);
  assert.equal(
    isPhotoPrefsNonDefault({ photoCullEnabled: true, keepNearDuplicates: true }),
    true
  );
});

test("shouldConfirmCloseWizard 风险矩阵", () => {
  assert.equal(shouldConfirmCloseWizard({ step: "pick" }), false);
  assert.equal(
    shouldConfirmCloseWizard({ step: "fine", fineDirty: true }),
    true
  );
  assert.equal(
    shouldConfirmCloseWizard({ step: "fine", fineDirty: false, photoPrefsNonDefault: true }),
    true
  );
  assert.equal(
    shouldConfirmCloseWizard({ step: "confirm", photoPrefsNonDefault: true }),
    true
  );
  assert.equal(
    shouldConfirmCloseWizard({ step: "confirm", photoPrefsNonDefault: false }),
    false
  );
});

test("canLeavePickStep / canNavigateWizardStep", () => {
  assert.equal(canLeavePickStep(""), false);
  assert.equal(canLeavePickStep("  /album  "), true);
  assert.equal(canNavigateWizardStep("pick", "confirm", "quick_share"), true);
  assert.equal(canNavigateWizardStep("confirm", "fine", "quick_share"), false);
  assert.equal(canNavigateWizardStep("confirm", "fine", "fine_craft"), true);
  assert.equal(canNavigateWizardStep("fine", "pick", "fine_craft"), true);
});
