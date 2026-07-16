"""M-C5 · extract toolbar shell/chrome utilities from preview-toolbar.js."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "templates" / "studio" / "preview-toolbar.js"
OUT = ROOT / "templates" / "studio" / "preview-toolbar" / "shell.js"

SHELL_FUNCS = {
    "tripIdFromPath",
    "tripApiBase",
    "toolbarConfirm",
    "toolbarAlert",
    "showToolbarToast",
    "maybeShowCoverOpeningStyleToast",
    "reloadPreviewAfterLayout",
    "setSlowHint",
    "toolbarBody",
    "syncToolbarHeight",
    "setToolbarCollapsed",
    "toggleToolbarCollapsed",
    "bindToolbarCollapse",
}

SHELL_HEADER = '''/**
 * Preview toolbar · shared chrome (toast, collapse, layout height).
 */
"use strict";

import { trackStudioEvent } from "../js/analytics.js";
import { isPreviewToolbarV3, isPreviewToolbarV4 } from "./dock.js";

var COLLAPSE_KEY = "travelogue.studio.previewToolbar.collapsed";
var COVER_STYLE_TOAST_KEY = "travelogue.coverStyleToast.";
var _toastTimer = null;

'''

STATE_VARS = '''
  var _layoutPending = false;
  var _pendingDockDismissed = false;
  var _layoutPendingMessage = "";
  var _g1Pending = false;
  var _g1DockDismissed = false;
  var _sheetEditDirty = false;
  var _sheetEditBaseline = "";
'''

IMPORT_BLOCK = '''import {
  tripIdFromPath,
  tripApiBase,
  toolbarConfirm,
  toolbarAlert,
  showToolbarToast,
  maybeShowCoverOpeningStyleToast,
  reloadPreviewAfterLayout,
  setSlowHint,
  toolbarBody,
  syncToolbarHeight,
  setToolbarCollapsed,
  toggleToolbarCollapsed,
  bindToolbarCollapse,
} from "./preview-toolbar/shell.js";
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


def patch_shell_body(body: list[str]) -> list[str]:
    out: list[str] = []
    for line in body:
        if re.match(r"^\s*var _toastTimer", line):
            continue
        if re.match(r"^  function \w+", line):
            line = re.sub(r"^  function ", "export function ", line, count=1)
        out.append(line)
    return out


def strip_shell_state(lines: list[str]) -> list[str]:
    drop = (
        r"^var COLLAPSE_KEY",
        r"^var COVER_STYLE_TOAST_KEY",
        r"^\s*var _toastTimer",
    )
    return [line for line in lines if not any(re.match(p, line) for p in drop)]


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    if "./preview-toolbar/shell.js" in text:
        print("shell import already present")
        return

    lines = text.splitlines()
    funcs, order = parse_functions(lines)
    missing = SHELL_FUNCS - set(funcs)
    if missing:
        raise SystemExit(f"missing shell functions: {sorted(missing)}")

    shell_parts = [SHELL_HEADER]
    for name in order:
        if name in SHELL_FUNCS:
            shell_parts.extend(patch_shell_body(funcs[name]))
            shell_parts.append("")
    OUT.write_text("\n".join(shell_parts).rstrip() + "\n", encoding="utf-8")

    rebuilt: list[str] = []
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)function (\w+)", lines[i])
        if m and m.group(2) in SHELL_FUNCS:
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

    rebuilt = strip_shell_state(rebuilt)
    insert_idx = None
    for idx, line in enumerate(rebuilt):
        if line.strip() == '} from "./preview-toolbar/longshot.js";':
            insert_idx = idx + 1
            break
    if insert_idx is None:
        raise SystemExit("longshot import anchor not found")
    rebuilt[insert_idx:insert_idx] = IMPORT_BLOCK.splitlines()

    marker = "  function snapshotEditPanel(el) {"
    patched_text = "\n".join(rebuilt)
    if marker in patched_text and "_layoutPending = false" not in patched_text:
        patched_text = patched_text.replace(marker, STATE_VARS.strip() + "\n\n" + marker, 1)
    rebuilt = patched_text.splitlines()

    SRC.write_text("\n".join(rebuilt) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}; patched entry")


if __name__ == "__main__":
    main()
