"""M-C5 · extract preview toolbar bootstrap (init + DOM ready)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "templates" / "studio" / "preview-toolbar.js"
OUT = ROOT / "templates" / "studio" / "preview-toolbar" / "bootstrap.js"

BOOTSTRAP = '''/**
 * Preview toolbar · entry bootstrap (v4 shell mount + DOM ready).
 */
"use strict";

import { dockIconSvg } from "./dock.js";
import {
  isSharePreview,
  initShareMinimal,
  ensureCoverMobileFootnote,
} from "./share.js";
import { tripIdFromPath } from "./shell.js";

var _initToolbarV3 = function (_root, _tripId) {};

export function registerBootstrapBridge(api) {
  if (typeof api.initToolbarV3 === "function") _initToolbarV3 = api.initToolbarV3;
}

export function initPreviewToolbar() {
  if (isSharePreview()) {
    initShareMinimal();
    return;
  }

  document.documentElement.setAttribute("data-preview-toolbar", "on");

  var root = document.createElement("div");
  root.className = "preview-toolbar preview-toolbar--v4";
  root.innerHTML =
    '<nav class="preview-toolbar__dock" aria-label="预览快捷操作">' +
    '<a class="preview-toolbar__dock-btn preview-toolbar__dock-btn--back preview-toolbar__ctl" href="/" aria-label="返回" title="返回 Studio 首页">' +
    dockIconSvg("back") +
    "</a>" +
    '<span class="preview-toolbar__dock-divider" aria-hidden="true"></span>' +
    '<div class="preview-toolbar__menu-wrap">' +
    '<button type="button" class="preview-toolbar__menu-btn preview-toolbar__dock-btn preview-toolbar__dock-btn--menu preview-toolbar__dock-btn--folio" aria-haspopup="dialog" aria-expanded="false" aria-label="编辑与设置" title="编辑与设置">' +
    dockIconSvg("settings") +
    "</button>" +
    "</div>" +
    "</nav>";

  document.body.insertBefore(root, document.body.firstChild);
  ensureCoverMobileFootnote();
  var tripId = tripIdFromPath();
  if (!tripId) return;
  _initToolbarV3(root, tripId);
}

export function bootstrapPreviewToolbarWhenReady() {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPreviewToolbar);
  } else {
    initPreviewToolbar();
  }
}
'''

IMPORT_BLOCK = '''import {
  registerBootstrapBridge,
  bootstrapPreviewToolbarWhenReady,
} from "./preview-toolbar/bootstrap.js";
'''

INIT_OLD = '''  function init() {
    if (isSharePreview()) {
      initShareMinimal();
      return;
    }

    document.documentElement.setAttribute("data-preview-toolbar", "on");

    var root = document.createElement("div");
    root.className = "preview-toolbar preview-toolbar--v4";
    root.innerHTML =
      '<nav class="preview-toolbar__dock" aria-label="预览快捷操作">' +
      '<a class="preview-toolbar__dock-btn preview-toolbar__dock-btn--back preview-toolbar__ctl" href="/" aria-label="返回" title="返回 Studio 首页">' +
      dockIconSvg("back") +
      "</a>" +
      '<span class="preview-toolbar__dock-divider" aria-hidden="true"></span>' +
      '<div class="preview-toolbar__menu-wrap">' +
      '<button type="button" class="preview-toolbar__menu-btn preview-toolbar__dock-btn preview-toolbar__dock-btn--menu preview-toolbar__dock-btn--folio" aria-haspopup="dialog" aria-expanded="false" aria-label="编辑与设置" title="编辑与设置">' +
      dockIconSvg("settings") +
      "</button>" +
      "</div>" +
      "</nav>";

    document.body.insertBefore(root, document.body.firstChild);
    ensureCoverMobileFootnote();
    var tripId = tripIdFromPath();
    if (!tripId) return;
    initToolbarV3(root, tripId);
  }

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
'''

TAIL_NEW = '''
registerBootstrapBridge({ initToolbarV3: initToolbarV3 });
bootstrapPreviewToolbarWhenReady();
'''


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    if "./preview-toolbar/bootstrap.js" in text:
        print("bootstrap import already present")
        return
    if INIT_OLD not in text:
        raise SystemExit("init bootstrap block not found")

    OUT.write_text(BOOTSTRAP, encoding="utf-8")

    text = text.replace(INIT_OLD, TAIL_NEW)
    anchor = '} from "./preview-toolbar/core.js";'
    if anchor not in text:
        raise SystemExit("core import anchor not found")
    text = text.replace(anchor, anchor + "\n" + IMPORT_BLOCK, 1)
    SRC.write_text(text, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}; patched entry")


if __name__ == "__main__":
    main()
