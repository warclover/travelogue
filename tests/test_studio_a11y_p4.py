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


def test_ac_p4_a11y_03_skip_link_and_progressbar_semantics() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    js = read_studio_js()
    assert 'class="studio-skip-link"' in html
    assert 'href="#studio-open-sheet"' in html
    assert "updateSkipLinkTarget" in js
    assert 'id="studio-progress-bar"' in html
    assert 'role="progressbar"' in html
    assert 'aria-valuemin="0"' in html
    assert 'aria-valuemax="100"' in html
    assert 'aria-valuenow="0"' in html


def test_ac_p4_a11y_04_sheet_trigger_expanded_state_sync() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    assert 'id="studio-open-sheet"' in html
    assert 'id="studio-open-sheet-returning"' in html
    assert 'id="studio-path-toggle"' in html
    assert 'aria-controls="studio-import-sheet"' in html
    assert 'aria-expanded="false"' in html

    js = read_studio_js()
    assert "setSheetTriggersExpanded" in js
    assert 'setAttribute("aria-expanded", expanded ? "true" : "false")' in js


def test_ac_p4_a11y_05_sheet_background_inert() -> None:
    js = read_studio_js()
    assert "setStudioBackgroundInert" in js
    assert 'setAttribute("inert", "")' in js
    assert 'setAttribute("aria-hidden", "true")' in js
    assert "studio-hero" in js
    assert "studio-below" in js
    assert "studio-sheet-root" in js
    assert "setStudioBackgroundInert(true)" in js
    assert "setStudioBackgroundInert(false)" in js


def test_ac_p4_import_thumbs_progress_linkage() -> None:
    js = read_studio_js()
    assert "updateImportThumbs" in js
    assert "fetchImportThumbsFromAlbumPath" in js
    assert "/__travelogue/album-preview" in js
    assert "studio-import__thumbs--linked" in js
    assert "ingestTotal" in js
    assert "已处理" in js


def test_ac_p4_success_cover_transition() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    assert 'id="studio-success-cover"' in html
    assert 'id="studio-cover-transition"' in html

    js = read_studio_js()
    assert "playSuccessCoverTransition" in js
    assert "applySuccessCover" in js
    assert "resetSuccessCover" in js
    assert "resolveSuccessCoverUrl" in js
    assert "/preview.jpg" in js


def test_ac_hp_prep_guide_and_new_import_copy() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    assert "不知道选哪个文件夹？" in html
    assert 'class="studio-prep-guide"' in html
    assert 'class="studio-hero__new-import-note"' in html
    assert "不会覆盖已有游记" in html
    assert 'id="studio-sheet-prep"' in html
    assert "分两次导入" in html
    assert "手机照片" in html

    js = read_studio_js()
    assert "notifyPick" in js
    assert "已扫描" in js
