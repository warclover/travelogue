/**
 * CQA AC-18 · sheet/settings llm-status listeners must be removable (singular bind).
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");

test("CQA · init-v3 unbinds travelogue:llm-status on sheet close/tab", () => {
  const src = readFileSync(
    join(root, "templates/studio/preview-toolbar/init-v3.js"),
    "utf8"
  );
  assert.match(src, /unbindSheetLlmStatus/);
  assert.match(src, /removeEventListener\("travelogue:llm-status"/);
  assert.match(src, /onSheetClosed:[\s\S]*unbindSheetLlmStatus/);
  assert.match(src, /onSheetTabShown:[\s\S]*unbindSheetLlmStatus/);
});

test("CQA · settings-panel binds llm-status once", () => {
  const src = readFileSync(
    join(root, "templates/studio/homepage-v2/settings-panel.js"),
    "utf8"
  );
  assert.match(src, /_llmStatusHandler/);
  assert.match(src, /if \(!_llmStatusHandler\)/);
});
