"""M-C5 · physical split: dock, share, inline-edit modules from preview-toolbar.js."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "templates" / "studio" / "preview-toolbar.js"
OUT = ROOT / "templates" / "studio" / "preview-toolbar"

DOCK_HEADER = '''/**
 * Preview toolbar · dock icons, screenplay control, dock UX.
 */
"use strict";

'''

SHARE_HEADER = '''/**
 * Preview toolbar · share preview minimal chrome.
 */
"use strict";

import {
  insertScreenplayControl,
} from "./dock.js";

'''

INLINE_HEADER = '''/**
 * Preview toolbar · cover title inline edit (AC-ARC-14b).
 */
"use strict";

import { postJsonConflictRetry } from "../js/http.js";

var _tripApiBase = function (_tripId) {
  return "";
};
var _reloadPreviewAfterLayout = function () {};
var _showToolbarToast = function (_message, _opts) {};
var _isSharePreview = function () {
  return false;
};

export function registerInlineEditBridge(api) {
  if (typeof api.tripApiBase === "function") _tripApiBase = api.tripApiBase;
  if (typeof api.reloadPreviewAfterLayout === "function") {
    _reloadPreviewAfterLayout = api.reloadPreviewAfterLayout;
  }
  if (typeof api.showToolbarToast === "function") _showToolbarToast = api.showToolbarToast;
  if (typeof api.isSharePreview === "function") _isSharePreview = api.isSharePreview;
}

'''


def line_range(lines: list[str], start: int, end: int) -> list[str]:
    return lines[start - 1 : end]


def export_functions(block: list[str]) -> list[str]:
    out: list[str] = []
    for line in block:
        out.append(re.sub(r"^(\s*)function ", r"\1export function ", line, count=1))
    return out


def patch_inline_refs(block: list[str]) -> list[str]:
    repl = {
        "isSharePreview()": "_isSharePreview()",
        "showToolbarToast(": "_showToolbarToast(",
        "tripApiBase(": "_tripApiBase(",
        "reloadPreviewAfterLayout()": "_reloadPreviewAfterLayout()",
        "postJsonConflictRetry(": "postJsonConflictRetry(",
    }
    out: list[str] = []
    for line in block:
        for old, new in repl.items():
            line = line.replace(old, new)
        out.append(line)
    return out


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    lines = text.splitlines()

    dock_blocks = [
        line_range(lines, 44, 182),
        line_range(lines, 329, 429),
    ]
    dock_body: list[str] = []
    for block in dock_blocks:
        dock_body.extend(export_functions(block))
        dock_body.append("")

    share_body = export_functions(line_range(lines, 3588, 3638))
    inline_body = patch_inline_refs(
        export_functions(line_range(lines, 1747, 1888))
    )

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "dock.js").write_text(
        DOCK_HEADER + "\n".join(dock_body) + "\n", encoding="utf-8"
    )
    (OUT / "share.js").write_text(
        SHARE_HEADER + "\n".join(share_body) + "\n", encoding="utf-8"
    )
    (OUT / "inline-edit.js").write_text(
        INLINE_HEADER + "\n".join(inline_body) + "\n", encoding="utf-8"
    )

    import_block = '''import {
  dockIconSvg,
  dockLongshotContentHtml,
  insertScreenplayControl,
  isPreviewToolbarV4,
  isPreviewToolbarV3,
  dockLongshotIconHtml,
  setDockLongshotAria,
  applyDockLongshotIdle,
  updateDockTip,
  ensureDockTooltip,
  syncDockScreenplayTip,
  initDockTooltips,
  initDockScrollFade,
} from "./preview-toolbar/dock.js";
import {
  isSharePreview,
  initShareMinimal,
  ensureCoverMobileFootnote,
} from "./preview-toolbar/share.js";
import {
  registerInlineEditBridge,
  initCoverTitleEdit,
  resolveSplitMatTitleLayoutClass,
  syncCoverTitleLayoutClass,
  saveMagazineTitle,
} from "./preview-toolbar/inline-edit.js";
'''

    # Remove extracted line ranges (reverse order)
    remove_ranges = [(3588, 3638), (1747, 1888), (329, 429), (44, 182)]
    new_lines = lines[:]
    for start, end in remove_ranges:
        new_lines[start - 1 : end] = []

    # Insert imports after existing imports (after line 23 mountPreviewUnifiedSheet)
    insert_at = 23
    new_lines[insert_at:insert_at] = import_block.splitlines()

    # Insert bridge registration before initCoverTitleEdit call site is gone - add in initToolbarV3
    # Find init() and inject register before initToolbarV3 path - inject after tripIdFromPath function
    patched = "\n".join(new_lines)
    bridge_snippet = """
  registerInlineEditBridge({
    tripApiBase: tripApiBase,
    reloadPreviewAfterLayout: reloadPreviewAfterLayout,
    showToolbarToast: showToolbarToast,
    isSharePreview: isSharePreview,
  });
"""
    marker = "  function initToolbarV3(root, tripId) {"
    if marker not in patched:
        raise SystemExit("initToolbarV3 marker not found")
    patched = patched.replace(marker, bridge_snippet + marker, 1)

    SRC.write_text(patched + "\n", encoding="utf-8")
    print("Wrote preview-toolbar/dock.js, share.js, inline-edit.js; patched entry")


if __name__ == "__main__":
    main()
