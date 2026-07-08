"""M-C5 · extract preview feature helpers from preview-toolbar.js."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "templates" / "studio" / "preview-toolbar.js"
OUT = ROOT / "templates" / "studio" / "preview-toolbar" / "features.js"

FEATURES_FUNCS = {
    "toggleAdvancedMenu",
    "initTitleEdit",
    "initDisplayedAestheticTitles",
    "initG1V3",
    "initG1Banner",
    "startFeaturedPresent",
    "initCollageMediaControls",
    "initFeaturedStars",
    "revealTripFolder",
    "readCoverOpeningStyleFromDom",
    "mountCoverStyleControls",
    "mountTemplateControls",
    "initTemplateBadge",
    "snapshotReadingPayload",
    "applyReaderSurfaceMode",
    "initPreviewModeSeg",
}

FEATURES_HEADER = '''/**
 * Preview toolbar · template, featured, reader mode, cover style UX.
 */
"use strict";

import {
  postJsonConflictRetry,
  patchJsonConflictRetry,
} from "../js/http.js";
import { trackStudioEvent } from "../js/analytics.js";
import { presentAutoplayHref } from "./dock.js";
import { saveMagazineTitle } from "./inline-edit.js";
import { formatAestheticPurposeLine } from "./drawers.js";
import {
  revealTripPath,
  refreshStaleHint,
  syncLongshotPreviewRowVisibility,
} from "./longshot.js";
import {
  showToolbarToast,
  tripApiBase,
  toolbarBody,
} from "./shell.js";
import {
  activateG1Pending,
  applyLayoutRerender,
  fetchEntry,
  refreshPreviewAfterCopySave,
  refreshTaskDockState,
  setLayoutPending,
  syncCoverOpeningStyleInDom,
} from "./core.js";

var COVER_OPENING_STYLE_OPTIONS = [
  { id: "card-br", label: "书名卡" },
  { id: "split-mat", label: "分屏衬纸" },
  { id: "magazine-head", label: "杂志顶题" },
];
var READER_VIEW_KEY = "travelogue.studio.readerView";

'''

IMPORT_BLOCK = '''import {
  initTitleEdit,
  initDisplayedAestheticTitles,
  initG1V3,
  startFeaturedPresent,
  initCollageMediaControls,
  initFeaturedStars,
  revealTripFolder,
  mountCoverStyleControls,
  mountTemplateControls,
  snapshotReadingPayload,
  applyReaderSurfaceMode,
} from "./preview-toolbar/features.js";
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


def patch_features_body(body: list[str]) -> list[str]:
    out: list[str] = []
    for line in body:
        if re.match(r"^  function \w+", line):
            line = re.sub(r"^  function ", "export function ", line, count=1)
        out.append(line)
    return out


def strip_features_constants(lines: list[str]) -> list[str]:
    drop = (r"^var COVER_OPENING_STYLE_OPTIONS",)
    out: list[str] = []
    skipping = False
    for line in lines:
        if re.match(r"^var COVER_OPENING_STYLE_OPTIONS", line):
            skipping = True
            continue
        if skipping:
            if line.strip() == "];":
                skipping = False
            continue
        out.append(line)
    return out


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    if "./preview-toolbar/features.js" in text:
        print("features import already present")
        return

    lines = text.splitlines()
    funcs, order = parse_functions(lines)
    missing = FEATURES_FUNCS - set(funcs)
    if missing:
        raise SystemExit(f"missing features functions: {sorted(missing)}")

    parts = [FEATURES_HEADER]
    for name in order:
        if name in FEATURES_FUNCS:
            parts.extend(patch_features_body(funcs[name]))
            parts.append("")
    OUT.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")

    rebuilt: list[str] = []
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)function (\w+)", lines[i])
        if m and m.group(2) in FEATURES_FUNCS:
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

    rebuilt = strip_features_constants(rebuilt)
    insert_idx = None
    for idx, line in enumerate(rebuilt):
        if line.strip() == '} from "./preview-toolbar/bootstrap.js";':
            insert_idx = idx + 1
            break
    if insert_idx is None:
        raise SystemExit("bootstrap import anchor not found")
    rebuilt[insert_idx:insert_idx] = IMPORT_BLOCK.splitlines()

    SRC.write_text("\n".join(rebuilt) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}; patched entry")


if __name__ == "__main__":
    main()
