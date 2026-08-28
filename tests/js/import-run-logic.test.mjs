/**
 * SFH W1 · import-run-logic 单测
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  basenameTitle,
  guessUploadTitle,
  buildImportPayloadFields,
  shouldResumeImport,
  shouldDiscardUploadPendingWithoutJob,
  resolveImportResumeSource,
  isImportPhotoCapExceeded,
  shouldAbortImportPoll,
  shouldClearPendingOnJobTerminal,
  canRetryFailedImport,
  shouldPerformCancelImport,
  normalizeImportProductStage,
  resolveImportStageCopy,
  importPanelCopy,
  isCopyWritingPhrase,
  PORTFOLIO_IMPORT_TITLE,
  PORTFOLIO_IMPORT_ESTIMATE,
  PORTFOLIO_STAGE_CURATE,
  PORTFOLIO_STAGE_RENDER,
  demoExistsOverwriteCopy,
} from "../../templates/studio/homepage-v2/import-run-logic.js";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { waitTipsCardsForEdition } from "../../templates/studio/homepage-v2/wait-tips-copy.js";

test("basenameTitle / guessUploadTitle", () => {
  assert.equal(basenameTitle("C:\\\\trips\\\\京都雨后"), "京都雨后");
  assert.equal(basenameTitle("C:\\\\trips\\\\2025东澳岛9"), "东澳岛 · 旅行");
  assert.equal(guessUploadTitle([]), "我的旅途");
  assert.equal(
    guessUploadTitle([{ webkitRelativePath: "京都雨后/a.jpg" }]),
    "京都雨后"
  );
});

test("buildImportPayloadFields 必填与默认", () => {
  const p = buildImportPayloadFields("/album/foo", null, {}, { template_mode: "smart" });
  assert.equal(p.albumPath, "/album/foo");
  assert.equal(p.title, "foo");
  assert.equal(p.titleUserSet, false);
  assert.equal(p.place, "旅途");
  assert.equal(p.mode, "quick_share");
  assert.equal(p.force, false);
  assert.equal(p.template_mode, "smart");

  const named = buildImportPayloadFields("/a", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", {
    titleUserSet: true,
  }, { template_mode: "manual", template_id: "visual-journal" });
  assert.equal(named.title, "ABCDEFGHIJKLMNOPQRST");
  assert.equal(named.title.length, 20);
  assert.equal(named.titleUserSet, true);
  assert.equal(named.template_id, "visual-journal");
});

test("resume / discard / source 谓词", () => {
  assert.equal(shouldResumeImport("job-1"), true);
  assert.equal(shouldResumeImport(""), false);
  assert.equal(
    shouldDiscardUploadPendingWithoutJob(null, { uploadForm: true }),
    true
  );
  assert.equal(
    shouldDiscardUploadPendingWithoutJob("j1", { uploadForm: true }),
    false
  );
  assert.equal(resolveImportResumeSource({ uploadForm: true }), "浏览器上传");
  assert.equal(resolveImportResumeSource({ albumPath: "/x" }), "本机文件夹");
});

test("cap / poll abort / pending clear / retry", () => {
  assert.equal(isImportPhotoCapExceeded(201, 200), true);
  assert.equal(isImportPhotoCapExceeded(200, 200), false);
  assert.equal(shouldAbortImportPoll(1, 2), true);
  assert.equal(shouldAbortImportPoll(2, 2), false);
  assert.equal(shouldClearPendingOnJobTerminal("succeeded"), true);
  assert.equal(shouldClearPendingOnJobTerminal("cancelled"), true);
  assert.equal(shouldClearPendingOnJobTerminal("failed"), false);
  assert.equal(canRetryFailedImport({ recoverableWithStub: true }), true);
  assert.equal(canRetryFailedImport({ code: "E_IMPORT_PHOTO_CAP" }), false);
});

test("IR-U-03 · cancel API：有 job 才发起；terminal/无 job 为 no-op", () => {
  // 现网无 cancelling 枚举；running 由 activeJobId 表达
  assert.equal(shouldPerformCancelImport("job-running"), true);
  assert.equal(shouldPerformCancelImport(""), false);
  assert.equal(shouldPerformCancelImport(null), false);
  // terminal 后壳层清空 activeJobId → 再次 cancel 不打 API
  assert.equal(shouldPerformCancelImport(undefined), false);
});

test("FE-FST-01 · resolveImportStageCopy：N/N 后切 curate，计数不霸屏", () => {
  assert.equal(normalizeImportProductStage("clustering"), "curate");
  assert.equal(normalizeImportProductStage("lock_structure"), "curate");
  assert.equal(normalizeImportProductStage("narrate"), "narrate");
  assert.equal(normalizeImportProductStage("render"), "render");

  const ingestCount = resolveImportStageCopy({
    stage: "ingest",
    stageHint: "已处理 6/6 张",
  });
  assert.match(ingestCount.main, /整理照片/);
  assert.equal(ingestCount.secondary, "已处理 6/6 张");

  const afterIngest = resolveImportStageCopy({
    stage: "clustering",
    stageHint: "已处理 6/6 张",
  });
  assert.match(afterIngest.main, /分章/);
  assert.equal(afterIngest.secondary, "");

  assert.equal(isCopyWritingPhrase("正在生成画册文案…"), true);
  assert.equal(isCopyWritingPhrase("正在写导语"), true);
  assert.equal(isCopyWritingPhrase("正在按杂志页编排…"), false);
  assert.equal(isCopyWritingPhrase(PORTFOLIO_IMPORT_TITLE), false);

  const narrate = resolveImportStageCopy({ stage: "narrate", stageHint: "" });
  assert.match(narrate.main, /画册文案/);

  const pfNarrate = resolveImportStageCopy({ stage: "narrate" }, "portfolio");
  assert.equal(pfNarrate.main, PORTFOLIO_IMPORT_TITLE);
  assert.equal(isCopyWritingPhrase(pfNarrate.main), false);
  const pfHint = resolveImportStageCopy(
    { stage: "", stageHint: "正在写导语" },
    "portfolio"
  );
  assert.equal(pfHint.main, PORTFOLIO_IMPORT_TITLE);
  const pfCurate = resolveImportStageCopy({ stage: "clustering" }, "portfolio");
  assert.equal(pfCurate.main, PORTFOLIO_STAGE_CURATE);
  const pfRender = resolveImportStageCopy({ stage: "render" }, "portfolio");
  assert.equal(pfRender.main, PORTFOLIO_STAGE_RENDER);
  const panel = importPanelCopy("portfolio");
  assert.equal(panel.title, PORTFOLIO_IMPORT_TITLE);
  assert.equal(panel.estimate, PORTFOLIO_IMPORT_ESTIMATE);
  assert.equal(panel.title.includes("杂志"), false);
  assert.equal(panel.estimate.includes("杂志"), false);
  assert.equal(isCopyWritingPhrase(panel.estimate), false);
  assert.match(importPanelCopy("journal").estimate, /配文/);
  const pfTips = waitTipsCardsForEdition("portfolio");
  assert.ok(pfTips.every((c) => !isCopyWritingPhrase(c.title + c.body)));
  assert.equal(
    pfTips.find((c) => c.id === "WT-03").title,
    "分章排版，交给它"
  );
  assert.equal(
    pfTips.find((c) => c.id === "WT-01").title,
    "可翻的一本，页图也能带走"
  );
  assert.equal(
    pfTips.find((c) => c.id === "WT-04").title,
    "先打开这一本，再导出"
  );
  assert.equal(
    pfTips.find((c) => c.id === "WT-06").title,
    "一本作品集，一个文件夹"
  );
  assert.ok(!pfTips.some((c) => (c.title + c.body).includes("长图")));
});

test("SFC W0 · vision_warmup 主句非空", () => {
  assert.equal(normalizeImportProductStage("vision_warmup"), "vision_warmup");
  assert.equal(normalizeImportProductStage("preparing_vision"), "vision_warmup");
  const warm = resolveImportStageCopy({
    stage: "vision_warmup",
    stageHint: "vision_warmup",
  });
  assert.match(warm.main, /准备识图/);
  const emptyish = resolveImportStageCopy({ stage: "vision_warmup", stageHint: "" });
  assert.match(emptyish.main, /准备识图/);
  assert.ok(emptyish.main.length > 0);
});

test("SFC W0 · stage/hint 双空仍有主句兜底", () => {
  const empty = resolveImportStageCopy({ stage: "", stageHint: "" });
  assert.ok(empty.main.length > 0);
  assert.match(empty.main, /整理照片|正在处理/);
  const bare = resolveImportStageCopy(null);
  assert.ok(bare.main.length > 0);
});

test("PIS · 409 只改作品集正文，游记冻结", () => {
  const journal = demoExistsOverwriteCopy({
    existingIsPf: false,
    existingTitle: "华农油菜花",
  });
  assert.equal(journal.title, "该画册已存在");
  assert.equal(
    journal.body,
    "《华农油菜花》已经用过这个文件夹。覆盖后无法撤销。"
  );
  assert.equal(journal.cancelToast, "未覆盖已有画册");

  const pfSolo = demoExistsOverwriteCopy({
    existingIsPf: true,
    existingTitle: "华农油菜花",
  });
  assert.equal(pfSolo.title, "这本作品集已存在");
  assert.match(pfSolo.body, /做过作品集/);
  assert.equal(pfSolo.body.includes("游记那一本"), false);
  assert.equal(pfSolo.cancelToast, "未覆盖已有作品集");

  const pfBoth = demoExistsOverwriteCopy({
    existingIsPf: true,
    existingTitle: "华农油菜花",
    hasSiblingJournal: true,
  });
  assert.match(pfBoth.body, /不会动书架上的游记那一本/);

  const src = readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), "../../templates/studio/homepage-v2/import-run.js"),
    "utf8"
  );
  assert.match(src, /demoExistsOverwriteCopy/);
});
