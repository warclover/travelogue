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
} from "../../templates/studio/homepage-v2/import-run-logic.js";

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

  const narrate = resolveImportStageCopy({ stage: "narrate", stageHint: "" });
  assert.match(narrate.main, /画册文案/);
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
