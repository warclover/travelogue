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
} from "../../templates/studio/homepage-v2/import-run-logic.js";

test("basenameTitle / guessUploadTitle", () => {
  assert.equal(basenameTitle("C:\\\\trips\\\\京都雨后"), "京都雨后");
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
