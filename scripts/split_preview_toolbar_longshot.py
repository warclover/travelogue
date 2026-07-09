"""M-C5 · extract longshot export domain from preview-toolbar.js."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "templates" / "studio" / "preview-toolbar.js"
OUT = ROOT / "templates" / "studio" / "preview-toolbar" / "longshot.js"

LONGSHOT_FUNCS = {
    "clearLongshotDrawerTimer",
    "scheduleLongshotDrawerAutoHide",
    "longshotApi",
    "readStoredLongshotScale",
    "readStoredLongshotMode",
    "writeStoredLongshotPrefs",
    "readLongshotExportPrefs",
    "formatLongshotExportMetaLabel",
    "refreshLongshotExportMeta",
    "normalizeSegmentMode",
    "buildLongshotRequestFromPage",
    "isReaderSurfaceMode",
    "syncLongshotPreviewRowVisibility",
    "syncLongshotPreviewChips",
    "applyToolbarCopyPreset",
    "toggleToolbarNarrative",
    "toggleToolbarCaptions",
    "initLongshotPreviewRow",
    "closeStudioExportPopover",
    "syncStudioExportPopoverUI",
    "ensureStudioExportPopover",
    "openStudioLongshotExportPanel",
    "openLongshotExportOptions",
    "revealTripPath",
    "longshotProgressPct",
    "pollJob",
    "exportZoneEl",
    "longshotBtnEl",
    "longshotCaretEl",
    "setLongshotControlsDisabled",
    "setLongshotExportMeta",
    "openLongshotResultDrawer",
    "bindLongshotExportMeta",
    "setLongshotExportProgress",
    "longshotSplitEl",
    "setLongshotSplitState",
    "setLongshotExportState",
    "hideLongshotDrawer",
    "getLongshotDrawer",
    "showLongshotDrawer",
    "showStaleHint",
    "hideStaleHint",
    "refreshStaleHint",
    "exportZip",
    "startLongshot",
}

LONGSHOT_HEADER = '''/**
 * Preview toolbar · longshot export (AC-ARC-14c).
 */
"use strict";

import {
  postJson,
  postJsonBusyRetry,
  isJobBusyResponse,
} from "../js/http.js";
import { startJobPollInterval, pollJobUntilDone } from "../js/job-poll.js";
import {
  buildLongshotRequest,
  resolveCopyDisplayFromDom,
} from "../js/longshot-client.js";
import {
  applyDockLongshotIdle,
  dockLongshotContentHtml,
  dockLongshotIconHtml,
  isPreviewToolbarV3,
  isPreviewToolbarV4,
  setDockLongshotAria,
  updateDockTip,
} from "./dock.js";

var isJobBusy409 = isJobBusyResponse;
var LONGSHOT_MODE_KEY = "travelogue:longshotMode";
var LONGSHOT_SCALE_KEY = "travelogue:longshotScale";
var SLOW_JOB_MS = 30000;
var LONGSHOT_DRAWER_AUTO_MS = 3000;

var longshotPollCancel = null;
var narratePollCancel = null;
var longshotJobId = null;
var narrateJobId = null;
var _longshotDrawerTimer = null;
var _studioExportPopoverClose = null;

var _showToolbarToast = function (_message, _opts) {};
var _toolbarConfirm = function (_opts) {
  return Promise.resolve(false);
};
var _toolbarAlert = function (_message, _opts) {};
var _setSlowHint = function (_root, _text, _visible) {};
var _setToolbarCollapsed = function (_root, _collapsed, _persist) {};
var _syncToolbarHeight = function (_root) {};
var _refreshTaskDockState = function (_root) {};
var _getLayoutPending = function () {
  return false;
};

export function registerLongshotBridge(api) {
  if (typeof api.showToolbarToast === "function") _showToolbarToast = api.showToolbarToast;
  if (typeof api.toolbarConfirm === "function") _toolbarConfirm = api.toolbarConfirm;
  if (typeof api.toolbarAlert === "function") _toolbarAlert = api.toolbarAlert;
  if (typeof api.setSlowHint === "function") _setSlowHint = api.setSlowHint;
  if (typeof api.setToolbarCollapsed === "function") {
    _setToolbarCollapsed = api.setToolbarCollapsed;
  }
  if (typeof api.syncToolbarHeight === "function") _syncToolbarHeight = api.syncToolbarHeight;
  if (typeof api.refreshTaskDockState === "function") {
    _refreshTaskDockState = api.refreshTaskDockState;
  }
  if (typeof api.getLayoutPending === "function") _getLayoutPending = api.getLayoutPending;
}

export function cancelPreviewLongshotExport(root) {
  if (longshotPollCancel) {
    longshotPollCancel();
    longshotPollCancel = null;
  }
  if (longshotJobId) {
    postJson("/__travelogue/cancel", { jobId: longshotJobId }).catch(function () {});
    longshotJobId = null;
  }
  setLongshotExportState(root, "idle");
}

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


def patch_longshot_body(body: list[str]) -> list[str]:
    text = "\n".join(body)
    repl = [
        ("showToolbarToast(", "_showToolbarToast("),
        ("toolbarConfirm(", "_toolbarConfirm("),
        ("toolbarAlert(", "_toolbarAlert("),
        ("setSlowHint(", "_setSlowHint("),
        ("setToolbarCollapsed(", "_setToolbarCollapsed("),
        ("syncToolbarHeight(", "_syncToolbarHeight("),
        ("refreshTaskDockState(", "_refreshTaskDockState("),
        ("tripIdFromPath(", "_tripIdFromPath("),
        ("toolbarBody(", "_toolbarBody("),
        ("setLayoutPending(", "_setLayoutPending("),
    ]
    for old, new in repl:
        text = text.replace(old, new)
    text = re.sub(r"(?<![.\w])_layoutPending\b", "_getLayoutPending()", text)
    out: list[str] = []
    for line in text.splitlines():
        if re.match(r"^  function \w+", line):
            line = re.sub(r"^  function ", "  export function ", line, count=1)
        out.append(line)
    return out


def strip_longshot_state(lines: list[str]) -> list[str]:
    drop_patterns = [
        r"^var longshotPollCancel",
        r"^var narratePollCancel",
        r"^var longshotJobId",
        r"^var narrateJobId",
        r"^\s*var _longshotDrawerTimer",
        r"^\s*var LONGSHOT_DRAWER_AUTO_MS",
        r"^\s*var _studioExportPopoverClose",
    ]
    out: list[str] = []
    for line in lines:
        if any(re.match(p, line) for p in drop_patterns):
            continue
        out.append(line)
    return out


IMPORT_BLOCK = '''import {
  registerLongshotBridge,
  cancelPreviewLongshotExport,
  startLongshot,
  setLongshotExportState,
  readLongshotExportPrefs,
  writeStoredLongshotPrefs,
  buildLongshotRequestFromPage,
  refreshLongshotExportMeta,
  openLongshotExportOptions,
  pollJob,
  exportZip,
  revealTripPath,
  isReaderSurfaceMode,
  syncLongshotPreviewRowVisibility,
  syncLongshotPreviewChips,
  refreshStaleHint,
  showStaleHint,
} from "./preview-toolbar/longshot.js";
'''

BRIDGE_SNIPPET = '''
    registerLongshotBridge({
      showToolbarToast: showToolbarToast,
      toolbarConfirm: toolbarConfirm,
      toolbarAlert: toolbarAlert,
      setSlowHint: setSlowHint,
      setToolbarCollapsed: setToolbarCollapsed,
      syncToolbarHeight: syncToolbarHeight,
      refreshTaskDockState: refreshTaskDockState,
      getLayoutPending: function () { return _layoutPending; },
    });
'''

CANCEL_REPLACEMENT = '''      onCancelExport: function () {
        cancelPreviewLongshotExport(root);
        root._exportDockActive = false;
        root._taskDock.hide();
      },'''


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    lines = text.splitlines()
    funcs, order = parse_functions(lines)

    missing = LONGSHOT_FUNCS - set(funcs)
    if missing:
        raise SystemExit(f"missing longshot functions: {sorted(missing)}")

    longshot_parts = [LONGSHOT_HEADER]
    for name in order:
        if name in LONGSHOT_FUNCS:
            longshot_parts.extend(patch_longshot_body(funcs[name]))
            longshot_parts.append("")

    OUT.write_text("\n".join(longshot_parts).rstrip() + "\n", encoding="utf-8")

    if "./preview-toolbar/longshot.js" in text:
        print("longshot import already present")
        return

    new_lines: list[str] = []
    for line in lines:
        if re.match(r"^(\s*)function (\w+)", line):
            name = re.match(r"^(\s*)function (\w+)", line).group(2)
            if name in LONGSHOT_FUNCS:
                continue
        if any(
            line == f"  function {name}("[: len(line)]
            or line.startswith(f"  function {name}(")
            for name in LONGSHOT_FUNCS
        ):
            continue
        new_lines.append(line)

    # Remove longshot function bodies by rebuilding from order
    rebuilt: list[str] = []
    skip_name: str | None = None
    skip_indent = 0
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)function (\w+)", lines[i])
        if m:
            name = m.group(2)
            indent = len(m.group(1))
            if name in LONGSHOT_FUNCS:
                i += 1
                while i < len(lines):
                    m2 = re.match(r"^(\s*)function ", lines[i])
                    if m2 and len(m2.group(1)) == indent:
                        break
                    i += 1
                continue
        rebuilt.append(lines[i])
        i += 1

    rebuilt = strip_longshot_state(rebuilt)

    # insert import after inline-edit import block
    insert_idx = None
    for idx, line in enumerate(rebuilt):
        if line.strip() == '} from "./preview-toolbar/inline-edit.js";':
            insert_idx = idx + 1
            break
    if insert_idx is None:
        raise SystemExit("inline-edit import anchor not found")
    rebuilt[insert_idx:insert_idx] = IMPORT_BLOCK.splitlines()

    patched = "\n".join(rebuilt)
    marker = "    registerInlineEditBridge({"
    if marker not in patched:
        raise SystemExit("inline edit bridge not found")
    patched = patched.replace(
        marker,
        BRIDGE_SNIPPET.strip() + "\n" + marker,
        1,
    )

    old_cancel = """      onCancelExport: function () {
        if (longshotPollCancel) {
          longshotPollCancel();
          longshotPollCancel = null;
        }
        if (longshotJobId) {
          postJson("/__travelogue/cancel", { jobId: longshotJobId }).catch(function () {});
          longshotJobId = null;
        }
        root._exportDockActive = false;
        setLongshotExportState(root, "idle");
        root._taskDock.hide();
      },"""
    if old_cancel not in patched:
        raise SystemExit("onCancelExport block not found")
    patched = patched.replace(old_cancel, CANCEL_REPLACEMENT.strip())

    SRC.write_text(patched + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}; patched entry")


if __name__ == "__main__":
    main()
