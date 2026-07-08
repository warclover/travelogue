"""M-C5 · extract layout/core state from preview-toolbar.js."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "templates" / "studio" / "preview-toolbar.js"
OUT = ROOT / "templates" / "studio" / "preview-toolbar" / "core.js"

CORE_FUNCS = {
    "snapshotEditPanel",
    "markSheetEditBaseline",
    "wireSheetEditDirty",
    "refreshTaskDockState",
    "layoutApplyButtons",
    "syncCoverOpeningStyleInDom",
    "refreshPreviewAfterCopySave",
    "setLayoutPending",
    "startLlmNarrate",
    "refreshPreviewCover",
    "applyLayoutRerender",
    "fetchEntry",
    "currentChapterId",
}

CORE_HEADER = '''/**
 * Preview toolbar · layout pending state, sheet dirty, rerender jobs.
 */
"use strict";

import { postJson } from "../js/http.js";
import { isPreviewToolbarV3 } from "./dock.js";
import { syncCoverTitleLayoutClass } from "./inline-edit.js";
import { pollJob, syncLongshotPreviewRowVisibility } from "./longshot.js";
import {
  showToolbarToast,
  toolbarConfirm,
  toolbarAlert,
  setSlowHint,
  setToolbarCollapsed,
  syncToolbarHeight,
  reloadPreviewAfterLayout,
  tripApiBase,
  toolbarBody,
} from "./shell.js";

var _layoutPending = false;
var _pendingDockDismissed = false;
var _layoutPendingMessage = "";
var _g1Pending = false;
var _g1DockDismissed = false;
var _sheetEditDirty = false;
var _sheetEditBaseline = "";

export function getLayoutPending() {
  return _layoutPending;
}

export function setLayoutPendingMessage(msg) {
  _layoutPendingMessage = msg;
}

export function getSheetEditDirty() {
  return _sheetEditDirty;
}

export function clearSheetEditDirty(root) {
  _sheetEditDirty = false;
  if (root) root._sheetEditDirty = false;
}

export function dismissPendingDock() {
  _pendingDockDismissed = true;
}

export function dismissG1Dock() {
  _g1DockDismissed = true;
}

export function activateG1Pending() {
  _g1Pending = true;
  _g1DockDismissed = false;
}

'''

IMPORT_BLOCK = '''import {
  getLayoutPending,
  setLayoutPendingMessage,
  getSheetEditDirty,
  clearSheetEditDirty,
  dismissPendingDock,
  dismissG1Dock,
  activateG1Pending,
  snapshotEditPanel,
  markSheetEditBaseline,
  wireSheetEditDirty,
  refreshTaskDockState,
  setLayoutPending,
  startLlmNarrate,
  applyLayoutRerender,
  fetchEntry,
  currentChapterId,
  refreshPreviewCover,
  syncCoverOpeningStyleInDom,
  refreshPreviewAfterCopySave,
} from "./preview-toolbar/core.js";
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


def patch_core_body(body: list[str]) -> list[str]:
    out: list[str] = []
    for line in body:
        if re.match(r"^  function \w+", line):
            line = re.sub(r"^  function ", "export function ", line, count=1)
        out.append(line)
    return out


def strip_core_state(lines: list[str]) -> list[str]:
    drop = (
        r"^\s*var _layoutPending",
        r"^\s*var _pendingDockDismissed",
        r"^\s*var _layoutPendingMessage",
        r"^\s*var _g1Pending",
        r"^\s*var _g1DockDismissed",
        r"^\s*var _sheetEditDirty",
        r"^\s*var _sheetEditBaseline",
    )
    return [line for line in lines if not any(re.match(p, line) for p in drop)]


def patch_entry(text: str) -> str:
    repl = [
        (
            "      getLayoutPending: function () { return _layoutPending; },",
            "      getLayoutPending: getLayoutPending,",
        ),
        (
            "      setLayoutPendingMessage: function (msg) { _layoutPendingMessage = msg; },",
            "      setLayoutPendingMessage: setLayoutPendingMessage,",
        ),
        (
            "      getLayoutPending: function () { return _layoutPending; },",
            "      getLayoutPending: getLayoutPending,",
        ),
        ("      isLayoutPending: function () { return _layoutPending; },", "      isLayoutPending: getLayoutPending,"),
        ("        if (tabId !== \"edit\" || !_sheetEditDirty) {", "        if (tabId !== \"edit\" || !getSheetEditDirty()) {"),
        (
            "          _sheetEditDirty = false;\n          root._sheetEditDirty = false;",
            "          clearSheetEditDirty(root);",
        ),
        ("        _pendingDockDismissed = true;", "        dismissPendingDock();"),
        ("        _g1DockDismissed = true;", "        dismissG1Dock();"),
        (
            "        _g1Pending = true;\n        _g1DockDismissed = false;",
            "        activateG1Pending();",
        ),
    ]
    for old, new in repl:
        text = text.replace(old, new)
    return text


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    if "./preview-toolbar/core.js" in text:
        print("core import already present")
        return

    lines = text.splitlines()
    funcs, order = parse_functions(lines)
    missing = CORE_FUNCS - set(funcs)
    if missing:
        raise SystemExit(f"missing core functions: {sorted(missing)}")

    core_parts = [CORE_HEADER]
    for name in order:
        if name in CORE_FUNCS:
            core_parts.extend(patch_core_body(funcs[name]))
            core_parts.append("")
    OUT.write_text("\n".join(core_parts).rstrip() + "\n", encoding="utf-8")

    rebuilt: list[str] = []
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)function (\w+)", lines[i])
        if m and m.group(2) in CORE_FUNCS:
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

    rebuilt = strip_core_state(rebuilt)
    insert_idx = None
    for idx, line in enumerate(rebuilt):
        if line.strip() == '} from "./preview-toolbar/drawers.js";':
            insert_idx = idx + 1
            break
    if insert_idx is None:
        raise SystemExit("drawers import anchor not found")
    rebuilt[insert_idx:insert_idx] = IMPORT_BLOCK.splitlines()

    patched = patch_entry("\n".join(rebuilt))
    SRC.write_text(patched + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}; patched entry")


if __name__ == "__main__":
    main()
