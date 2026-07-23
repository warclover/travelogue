/**
 * CQA AC-06/07/08/09 · export prefs + panel settle + job terminal (source contracts).
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");

test("CQA · 改用按章 writes prefs.mode=chapter (AC-06)", () => {
  const src = readFileSync(
    join(root, "templates/studio/preview-toolbar/longshot.js"),
    "utf8"
  );
  assert.match(src, /secondaryText:\s*"改用按章导出"/);
  assert.match(src, /nextPrefs\.mode\s*=\s*"chapter"/);
  assert.match(src, /prefs\.mode\s*===\s*"full"/);
  // Prefs storage path must not write segmentMode
  assert.doesNotMatch(src, /nextPrefs\.segmentMode\s*=/);
  assert.doesNotMatch(src, /prefs\.segmentMode\s*===\s*"full"/);
});

test("CQA · export panel Escape settles once (AC-07)", () => {
  const src = readFileSync(
    join(root, "templates/studio/preview-toolbar/longshot.js"),
    "utf8"
  );
  assert.match(src, /_activeExportPanelFinish/);
  assert.match(src, /if \(e\.key === "Escape"\)[\s\S]*_activeExportPanelFinish\(false\)/);
  assert.match(src, /function finish\(ok\) \{\s*if \(settled\) return;/);
});

test("CQA · drawers confirm/regen use pollJobUntilDone (AC-08/09)", () => {
  const drawers = readFileSync(
    join(root, "templates/studio/preview-toolbar/drawers.js"),
    "utf8"
  );
  const chapter = readFileSync(
    join(root, "templates/studio/preview-toolbar/chapter-panel.js"),
    "utf8"
  );
  assert.match(drawers, /return pollJobUntilDone\(/);
  assert.match(drawers, /正在调整结构…/);
  // chapter-panel awaits drawers confirm/regen Promise (terminal from pollJobUntilDone)
  assert.match(chapter, /drawers\.confirmStructure\(\)/);
  assert.match(chapter, /\.then\(function \(job\)|\.catch\(/);
  assert.match(chapter, /no false "已保存"|Keep panel open; no false/);
  // No premature success toast on 202 alone
  assert.doesNotMatch(
    drawers,
    /status === 202[\s\S]{0,120}已保存/
  );
});
