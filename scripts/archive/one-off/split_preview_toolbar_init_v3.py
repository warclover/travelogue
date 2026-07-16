"""M-C5 · extract initToolbarV3 from preview-toolbar.js into init-v3.js."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "templates" / "studio" / "preview-toolbar.js"
OUT = ROOT / "templates" / "studio" / "preview-toolbar" / "init-v3.js"

ENTRY = '''/**
 * Travelogue Studio · preview page toolbar (ESM).
 */
"use strict";

import { initToolbarV3 } from "./preview-toolbar/init-v3.js";
import {
  registerBootstrapBridge,
  bootstrapPreviewToolbarWhenReady,
} from "./preview-toolbar/bootstrap.js";

registerBootstrapBridge({ initToolbarV3: initToolbarV3 });
bootstrapPreviewToolbarWhenReady();
'''


def main() -> None:
    if OUT.is_file() and 'from "./preview-toolbar/init-v3.js"' in SRC.read_text(encoding="utf-8"):
        print("init-v3 split already applied")
        return
    if not OUT.is_file():
        raise SystemExit(f"missing {OUT.relative_to(ROOT)} — create module before running patch")
    SRC.write_text(ENTRY, encoding="utf-8")
    print(f"Patched entry; init module at {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
