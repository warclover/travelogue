"""Phase 4 Studio A11Y · AC-P4-A11Y-02 sheet focus trap."""

from __future__ import annotations

from pathlib import Path

from tests._studio_js import read_studio_js

ROOT = Path(__file__).resolve().parents[1]
STUDIO_HTML = ROOT / "templates" / "studio" / "studio.html"


def test_ac_p4_a11y_02_sheet_dialog_semantics() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    assert 'id="studio-import-sheet"' in html
    assert 'role="dialog"' in html
    assert 'aria-modal="true"' in html
    assert 'aria-labelledby="studio-sheet-title"' in html
    assert 'id="studio-sheet-title"' in html


def test_ac_p4_a11y_02_sheet_focus_trap_and_escape() -> None:
    js = read_studio_js()
    assert "trapSheetFocus" in js
    assert "releaseSheetFocusTrap" in js
    assert "SHEET_FOCUSABLE" in js
    assert "_sheetPreviousFocus = document.activeElement" in js
    assert 'e.key === "Escape" && S._sheetOpen' in js
