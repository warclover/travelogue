/**
 * SFH W2 · import-wizard-logic 单测（关闭确认 / dirty / 步骤矩阵）
 */
import test from "node:test";
import assert from "node:assert/strict";

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import {
  normalizeWizardStep,
  isFineSnapshotDirty,
  isPhotoPrefsNonDefault,
  shouldConfirmCloseWizard,
  canLeavePickStep,
  canNavigateWizardStep,
  wizardHitsToStart,
  resolvePhotoKeepModeFromDraft,
  normalizeEdition,
  parsePortfolioPipelineConfig,
  shouldShowEditionSegment,
  shouldResetEditionToJournal,
  shouldShowHomepagePortfolioEntry,
  isPortfolioLowPhoto,
  portfolioEditionSubline,
  shouldConfirmLowPhoto,
  lowPhotoContinueConfirm,
  lowPhotoHint,
} from "../../templates/studio/homepage-v2/import-wizard-logic.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const QFX_VECTORS = JSON.parse(
  readFileSync(
    join(__dirname, "../fixtures/qfx/photo_keep_mode_vectors.json"),
    "utf8"
  )
);

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
  assert.equal(isPhotoPrefsNonDefault({ photoKeepMode: "recommended" }), false);
  assert.equal(isPhotoPrefsNonDefault({ photoKeepMode: "keep_all" }), true);
  assert.equal(isPhotoPrefsNonDefault({ photoKeepMode: "keep_bursts" }), true);
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
  assert.equal(wizardHitsToStart("quick_share", "journal"), 2);
  assert.equal(wizardHitsToStart("quick_share", "portfolio"), 2);
  assert.equal(wizardHitsToStart("fine_craft", "portfolio"), 3);
  assert.equal(canNavigateWizardStep("pick", "confirm", "quick_share"), true);
  assert.equal(canNavigateWizardStep("confirm", "fine", "quick_share"), false);
});

test("PFM edition helpers default hidden", () => {
  assert.equal(normalizeEdition(""), "journal");
  assert.equal(normalizeEdition("folio"), "portfolio");
  const off = parsePortfolioPipelineConfig({});
  assert.equal(off.enabled, false);
  assert.equal(off.homepageEntry, false);
  assert.equal(shouldShowEditionSegment(off), false);
  assert.equal(shouldResetEditionToJournal(off, false), false);
  assert.equal(shouldResetEditionToJournal(off, true), true);
  assert.equal(shouldShowHomepagePortfolioEntry(off), false);
  const on = parsePortfolioPipelineConfig({
    portfolioPipeline: { enabled: true, homepageEntry: false },
  });
  assert.equal(shouldResetEditionToJournal(on, true), false);
  assert.equal(shouldShowEditionSegment(on), true);
  assert.equal(shouldShowHomepagePortfolioEntry(on), false);
  assert.equal(
    shouldShowHomepagePortfolioEntry({ enabled: false, homepageEntry: true }),
    false
  );
  assert.equal(isPortfolioLowPhoto(8, 12), true);
  assert.equal(isPortfolioLowPhoto(30, 12), false);
  assert.equal(
    parsePortfolioPipelineConfig({ portfolioPipeline: { minKept: 48 } }).minKept,
    48
  );
});

test("PFM FE-PFM-02 low photo grey-out + informed continue", () => {
  assert.equal(isPortfolioLowPhoto(14, 48), true);
  assert.equal(isPortfolioLowPhoto(48, 48), false);
  assert.equal(isPortfolioLowPhoto(null, 48), false);
  assert.equal(portfolioEditionSubline(true), "照片较少");
  assert.equal(portfolioEditionSubline(false), "杂志页");
  assert.equal(shouldConfirmLowPhoto(14, 48, "user", "journal"), true);
  assert.equal(shouldConfirmLowPhoto(14, 48, "homepage", "journal"), false);
  assert.equal(shouldConfirmLowPhoto(14, 48, "user", "portfolio"), false);
  assert.equal(shouldConfirmLowPhoto(60, 48, "user", "journal"), false);
  assert.equal(lowPhotoHint(48), "照片较少，作品集更适合 48 张以上");
  assert.equal(lowPhotoHint(30), "照片较少，作品集更适合 30 张以上");
  const copy = lowPhotoContinueConfirm(48);
  assert.match(copy.body, /48 张以上/);
  assert.doesNotMatch(copy.body, /30 张以上/);
  assert.equal(copy.confirmText, "仍做作品集");
  assert.match(
    readFileSync(
      join(__dirname, "../../templates/studio/homepage-v2/import-wizard.js"),
      "utf8"
    ),
    /studioModal/
  );
});

test("resolvePhotoKeepModeFromDraft 对齐 QFX 合同向量", () => {
  for (const row of QFX_VECTORS.vectors) {
    const draft = {
      photoKeepMode: row.photoKeepMode || undefined,
      photoCullEnabled: row.photoCullEnabled,
      keepNearDuplicates: row.keepNearDuplicates,
    };
    assert.equal(
      resolvePhotoKeepModeFromDraft(draft),
      row.expectMode,
      row.id
    );
  }
});
