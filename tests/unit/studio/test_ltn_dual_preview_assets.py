"""LTN R-B3 · dual preview assets present on export path."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_dual_preview_module_and_wiring():
    dual = (ROOT / "templates/studio/preview-toolbar/dual-preview.js").read_text(
        encoding="utf-8"
    )
    assert "CAPTURE_WIDTH = 428" in dual
    assert "export function openDualPreview" in dual
    assert "index-longshot.html" in dual

    panel = (ROOT / "templates/studio/js/longshot-export-panel.js").read_text(
        encoding="utf-8"
    )
    assert "data-ltn-dual-preview" in panel
    assert "对比网页与长图" in panel

    ls = (ROOT / "templates/studio/preview-toolbar/longshot.js").read_text(encoding="utf-8")
    assert 'from "./dual-preview.js"' in ls
    assert "openDualPreview(_tripIdFromPath())" in ls

    css = (ROOT / "templates/studio/preview-toolbar/longshot.css").read_text(encoding="utf-8")
    assert ".ltn-dual-preview" in css
