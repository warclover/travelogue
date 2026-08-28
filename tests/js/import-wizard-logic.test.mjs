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
  displayHintPages,
  pageSpecSentence,
  folderCollisionCopy,
  wizardCopy,
  wizardStartLabel,
  wizardPhotoSummaryLine,
  wizardCountHint,
  approxKeptSentence,
  shouldShowPageSpec,
  buildPageCountFields,
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
  assert.equal(portfolioEditionSubline(false), "可翻的一本");
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

const PFO_CHIPS = [
  { pages: 8, capacity: 19 },
  { pages: 12, capacity: 29 },
  { pages: 16, capacity: 43 },
  { pages: 20, capacity: 65 },
  { pages: 24, capacity: 67 },
  { pages: 28, capacity: 76 },
  { pages: 32, capacity: 88 },
  { pages: 36, capacity: 96 },
];

test("PFO 向导规格句默认自动、游记不带页数", () => {
  assert.equal(displayHintPages(19, PFO_CHIPS), 8);
  assert.equal(displayHintPages(20, PFO_CHIPS), 12);
  assert.equal(displayHintPages(100, PFO_CHIPS), 36);
  assert.equal(displayHintPages(0, PFO_CHIPS), 0);
  assert.equal(
    pageSpecSentence(48, PFO_CHIPS),
    "文件夹 48 张，系统会按能上版的张数自动选厚度。"
  );
  assert.equal(
    pageSpecSentence(31, PFO_CHIPS, "16"),
    "文件夹 31 张，做成一本 16 页。"
  );
  assert.equal(
    folderCollisionCopy("portfolio", { title: "华农油菜花" }, { title: "华农油菜花" }),
    "这个文件夹已经做过作品集。继续会覆盖这本作品集，不会动书架上的游记那一本。"
  );
  assert.equal(
    folderCollisionCopy("portfolio", { title: "华农油菜花" }, null),
    "这个文件夹已经做过作品集《华农油菜花》。继续会覆盖这本作品集。"
  );
  assert.equal(
    folderCollisionCopy(
      "portfolio",
      { title: "东澳作品集" },
      { title: "珠海东澳岛一日游" }
    ),
    "这个文件夹已经做过作品集《东澳作品集》。继续会覆盖这本作品集，不会动已有游记《珠海东澳岛一日游》。"
  );
  assert.equal(
    folderCollisionCopy("portfolio", null, { title: "华农油菜花" }),
    "将新建一本作品集，不会覆盖已有游记《华农油菜花》。两本可以同时留在书架上。"
  );
  assert.equal(
    folderCollisionCopy("portfolio", null, {
      title: "珠海东澳岛一日游",
      edition: "portfolio",
    }),
    "将新建一本作品集，不会覆盖已有作品集《珠海东澳岛一日游》。两本可以同时留在书架上。"
  );
  assert.equal(
    folderCollisionCopy("journal", { title: "华农油菜花" }, { title: "华农油菜花" }),
    "这个文件夹已经做过游记。继续会覆盖这本游记，不会动书架上的作品集那一本。"
  );
  const huang = folderCollisionCopy(
    "portfolio",
    { title: "华农油菜花" },
    { title: "华农油菜花" }
  );
  assert.equal(huang.includes("《华农油菜花》"), false);
  const pfCopy = wizardCopy("portfolio");
  assert.equal(pfCopy.pickButton, "选择本次作品集的照片文件夹");
  assert.equal(pfCopy.quickDesc.includes("请改选游记"), true);
  assert.equal(pfCopy.quickDesc.includes("杂志"), false);
  assert.equal(pfCopy.hideDemo, true);
  assert.equal(wizardCopy("journal").pickButton, "选择照片文件夹");
  assert.equal(wizardCopy("journal").hideDemo, false);
  assert.equal(
    wizardPhotoSummaryLine(48),
    "文件夹有 48 张。制作时会自动去重与挑选，成册张数以完成后为准。"
  );
  assert.equal(
    wizardPhotoSummaryLine(12, { keepMode: "keep_all" }),
    "文件夹有 12 张，将全部保留进入制作。"
  );
  assert.equal(wizardCountHint(72).bucket, "sweet");
  assert.equal(wizardCountHint(2).bucket, "few");
  assert.equal(
    wizardStartLabel({ edition: "portfolio", covering: true }),
    "覆盖并开始制作作品集"
  );
  assert.equal(
    wizardStartLabel({ edition: "portfolio" }),
    "开始制作作品集 →"
  );
  assert.equal(wizardStartLabel({ edition: "journal" }), "开始制作 →");
  const on = parsePortfolioPipelineConfig({
    portfolioPipeline: { enabled: true },
  });
  assert.equal(shouldShowPageSpec("portfolio", on), true);
  assert.equal(shouldShowPageSpec("journal", on), false);
  assert.deepEqual(buildPageCountFields("journal", "32"), {});
  assert.deepEqual(buildPageCountFields("portfolio", "auto"), {
    pageCountSource: "auto",
  });
  assert.deepEqual(buildPageCountFields("portfolio", "32"), {
    pageCount: 32,
    pageCountSource: "user",
  });
  assert.equal(parsePortfolioPipelineConfig({}).keptEstimateRatio, 0.67);
  assert.equal(
    parsePortfolioPipelineConfig({
      portfolioPipeline: { keptEstimateRatio: 0.5 },
    }).keptEstimateRatio,
    0.5
  );
  assert.equal(
    approxKeptSentence(160, 0.67),
    "生成后按实际上版张数定厚度；现在估计大约用上 107 张"
  );
  assert.equal(approxKeptSentence(0, 0.67), "");
  const wizard = readFileSync(
    join(__dirname, "../../templates/studio/homepage-v2/import-wizard.js"),
    "utf8"
  );
  assert.match(wizard, /buildPageCountFields\(_activeEdition/);
  assert.match(wizard, /换一本更厚 \/ 更薄/);
  assert.match(wizard, /wizardCopy\(_activeEdition\)/);
  assert.match(wizard, /wizardStartLabel/);
  assert.match(wizard, /hasSiblingJournal/);
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
