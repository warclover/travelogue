"""M-C5 · extract preview drawers domain from preview-toolbar.js."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "templates" / "studio" / "preview-toolbar.js"
OUT = ROOT / "templates" / "studio" / "preview-toolbar" / "drawers.js"

DRAWERS_FUNCS = {
    "copyIntentApiUrl",
    "buildCopyIntentChipHtml",
    "trapDrawerFocus",
    "formatAestheticPurposeLine",
    "renderAestheticAlbumProfile",
    "loadAestheticExplain",
    "renderExplainBlock",
    "loadChapterExplain",
    "initPreviewDrawers",
}

DRAWERS_HEADER = '''/**
 * Preview toolbar · overlay drawers (edit / structure / cohort).
 */
"use strict";

import {
  patchJson,
  postJson,
  patchJsonConflictRetry,
  postJsonConflictRetry,
} from "../js/http.js";
import { pollJobUntilDone } from "../js/job-poll.js";
import { STUDIO_USER_NOTES_MAX_LEN } from "../js/constants.js";
import { mountCohortDrawer } from "../cohort-drawer.js";
import {
  showToolbarToast,
  setToolbarCollapsed,
  toolbarConfirm,
  tripApiBase,
} from "./shell.js";

var DRAWER_FOCUSABLE =
  'a[href],button:not([disabled]),input:not([disabled]),textarea:not([disabled]),select:not([disabled]),[tabindex="0"]';
var COPY_INTENT_MOODS = ["松弛", "热闹", "赶路", "意外", "仪式感", "平静"];
var COPY_INTENT_FOCUSES = ["人", "地方", "食物", "关系", "自我感受"];
var AESTHETIC_STRATUM_LABELS = {
  person: "人像",
  landscape: "风景",
  food: "美食",
  group: "合影",
  general: "通用",
};
var AESTHETIC_PURPOSE_LABELS = {
  cover: "封面",
  hero: "主图",
  moment: "瞬间",
};

var _fetchEntry = function (_tripId) {
  return Promise.resolve({});
};
var _currentChapterId = function () {
  return "";
};
var _markSheetEditBaseline = function (_root, _panel) {};
var _wireSheetEditDirty = function (_root, _panel) {};
var _startLlmNarrate = function (_root, _tripId, _btn) {};
var _applyLayoutRerender = function (_tripId, _root) {};
var _getLayoutPending = function () {
  return false;
};

export function registerDrawersBridge(api) {
  if (typeof api.fetchEntry === "function") _fetchEntry = api.fetchEntry;
  if (typeof api.currentChapterId === "function") _currentChapterId = api.currentChapterId;
  if (typeof api.markSheetEditBaseline === "function") {
    _markSheetEditBaseline = api.markSheetEditBaseline;
  }
  if (typeof api.wireSheetEditDirty === "function") _wireSheetEditDirty = api.wireSheetEditDirty;
  if (typeof api.startLlmNarrate === "function") _startLlmNarrate = api.startLlmNarrate;
  if (typeof api.applyLayoutRerender === "function") {
    _applyLayoutRerender = api.applyLayoutRerender;
  }
  if (typeof api.getLayoutPending === "function") _getLayoutPending = api.getLayoutPending;
}

'''

IMPORT_BLOCK = '''import {
  registerDrawersBridge,
  initPreviewDrawers,
  trapDrawerFocus,
  formatAestheticPurposeLine,
} from "./preview-toolbar/drawers.js";
'''

BRIDGE_SNIPPET = '''
    registerDrawersBridge({
      fetchEntry: fetchEntry,
      currentChapterId: currentChapterId,
      markSheetEditBaseline: markSheetEditBaseline,
      wireSheetEditDirty: wireSheetEditDirty,
      startLlmNarrate: startLlmNarrate,
      applyLayoutRerender: applyLayoutRerender,
      getLayoutPending: function () { return _layoutPending; },
    });
'''


def parse_functions(lines: list[str]) -> tuple[dict[str, list[str]], list[str]]:
    funcs: dict[str, list[str]] = {}
    order: list[str] = []
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)function (\w+)", lines[i])
        if not m:
            i += 1
            continue
        name = m.group(2)
        indent = len(m.group(1))
        start = i
        i += 1
        while i < len(lines):
            m2 = re.match(r"^(\s*)function ", lines[i])
            if m2 and len(m2.group(1)) == indent:
                break
            i += 1
        funcs[name] = lines[start:i]
        order.append(name)
    return funcs, order


def patch_drawers_body(body: list[str]) -> list[str]:
    text = "\n".join(body)
    repl = [
        ("fetchEntry(", "_fetchEntry("),
        ("currentChapterId(", "_currentChapterId("),
        ("markSheetEditBaseline(", "_markSheetEditBaseline("),
        ("wireSheetEditDirty(", "_wireSheetEditDirty("),
        ("startLlmNarrate(", "_startLlmNarrate("),
        ("applyLayoutRerender(", "_applyLayoutRerender("),
    ]
    for old, new in repl:
        text = text.replace(old, new)
    text = re.sub(r"(?<![.\w])_layoutPending\b", "_getLayoutPending()", text)
    cleaned: list[str] = []
    skipping = False
    for line in text.splitlines():
        if re.match(r"^\s*var _layoutPending = false", line) or "_getLayoutPending() = false" in line:
            skipping = True
            continue
        if skipping:
            if re.match(r"^\s*var _sheetEditBaseline", line):
                skipping = False
            continue
        cleaned.append(line)
    out: list[str] = []
    for line in cleaned:
        if re.match(r"^  function \w+", line):
            line = re.sub(r"^  function ", "export function ", line, count=1)
        out.append(line)
    return out


def strip_drawers_constants(lines: list[str]) -> list[str]:
    out: list[str] = []
    skip_next_string = False
    for line in lines:
        if re.match(r"^\s*var DRAWER_FOCUSABLE", line):
            skip_next_string = True
            continue
        if skip_next_string and line.strip().startswith("'"):
            skip_next_string = False
            continue
        if re.match(r"^\s*var COPY_INTENT_MOODS", line):
            continue
        if re.match(r"^\s*var COPY_INTENT_FOCUSES", line):
            continue
        out.append(line)
    return out


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    if "./preview-toolbar/drawers.js" in text:
        print("drawers import already present")
        return

    lines = text.splitlines()
    funcs, order = parse_functions(lines)
    missing = DRAWERS_FUNCS - set(funcs)
    if missing:
        raise SystemExit(f"missing drawers functions: {sorted(missing)}")

    drawer_parts = [DRAWERS_HEADER]
    for name in order:
        if name in DRAWERS_FUNCS:
            drawer_parts.extend(patch_drawers_body(funcs[name]))
            drawer_parts.append("")
    OUT.write_text("\n".join(drawer_parts).rstrip() + "\n", encoding="utf-8")

    rebuilt: list[str] = []
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)function (\w+)", lines[i])
        if m and m.group(2) in DRAWERS_FUNCS:
            indent = len(m.group(1))
            i += 1
            while i < len(lines):
                m2 = re.match(r"^(\s*)function ", lines[i])
                if m2 and len(m2.group(1)) == indent:
                    break
                i += 1
            continue
        rebuilt.append(lines[i])
        i += 1

    rebuilt = strip_drawers_constants(rebuilt)
    insert_idx = None
    for idx, line in enumerate(rebuilt):
        if line.strip() == '} from "./preview-toolbar/shell.js";':
            insert_idx = idx + 1
            break
    if insert_idx is None:
        raise SystemExit("shell import anchor not found")
    rebuilt[insert_idx:insert_idx] = IMPORT_BLOCK.splitlines()

    patched = "\n".join(rebuilt)
    marker = "    registerInlineEditBridge({"
    if marker not in patched:
        raise SystemExit("inline edit bridge not found")
    patched = patched.replace(marker, BRIDGE_SNIPPET.strip() + "\n" + marker, 1)

    state_marker = "  function snapshotEditPanel(el) {"
    if state_marker in patched and "_layoutPending = false" not in patched:
        state_vars = """
  var _layoutPending = false;
  var _pendingDockDismissed = false;
  var _layoutPendingMessage = "";
  var _g1Pending = false;
  var _g1DockDismissed = false;
  var _sheetEditDirty = false;
  var _sheetEditBaseline = "";
"""
        patched = patched.replace(state_marker, state_vars.strip() + "\n\n" + state_marker, 1)

    SRC.write_text(patched + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}; patched entry")


if __name__ == "__main__":
    main()
