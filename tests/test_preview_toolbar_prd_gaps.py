"""PRD gap fixes · D-01/D-02 + MP-WV share chrome regression (non-e2e)."""

from __future__ import annotations

from pathlib import Path

from tests._studio_js import read_preview_toolbar_js
from travelogue.web.studio_chrome import inject_studio_chrome

ROOT = Path(__file__).resolve().parents[1]


def test_d01_apply_layout_main_visible_when_idle() -> None:
    templates = (ROOT / "templates" / "studio" / "preview-toolbar" / "templates.js").read_text(
        encoding="utf-8"
    )
    pending = (ROOT / "templates" / "studio" / "preview-toolbar" / "pending.js").read_text(
        encoding="utf-8"
    )
    assert "preview-toolbar__apply-layout-main preview-toolbar__ctl" in templates
    assert "apply-layout-main preview-toolbar__ctl\" hidden" not in templates
    assert "btn.hidden = false" in pending
    assert "preview-toolbar__apply-layout-main--idle" in pending


def test_d02_more_menu_collapse_entry() -> None:
    js = read_preview_toolbar_js()
    templates = (ROOT / "templates" / "studio" / "preview-toolbar" / "templates.js").read_text(
        encoding="utf-8"
    )
    assert "preview-toolbar__more-collapse" in templates
    assert "收起工具栏" in templates
    assert "preview-toolbar__menu-sep--before-collapse" in templates
    assert "preview-toolbar__more-collapse" in js
    assert "setToolbarCollapsed(root, true)" in js


def test_mp_wv_share_vs_studio_chrome_fork() -> None:
    html = "<html><body><main>hi</main></body></html>"
    studio = inject_studio_chrome(html, share_mode=False)
    share = inject_studio_chrome(html, share_mode=True)
    assert 'data-preview-toolbar="on"' in studio
    assert 'data-preview-toolbar="on"' not in share
    assert 'data-preview-share="on"' in share
    assert "/__studio/preview-toolbar/index.js" in studio
    assert "/__studio/preview-toolbar/index.js" in share


def test_mp_wv_share_minimal_init_path() -> None:
    js = read_preview_toolbar_js()
    css = (ROOT / "templates" / "studio" / "preview-toolbar.css").read_text(encoding="utf-8")
    assert "isSharePreview" in js
    assert "initShareMinimal" in js
    assert "preview-toolbar--share-minimal" in js
    assert "data-preview-share" in css
    assert 'if (isSharePreview())' in js


def test_d04_edit_mode_hint_in_store() -> None:
    js = read_preview_toolbar_js()
    assert "hasSeenEditModeHint" in js
    assert "markEditModeHintSeen" in js
    assert "应用排版" in js
    assert "editModeHintSeen" in js


def test_a12_storage_and_surface_writes_centralized_in_store() -> None:
    pt = ROOT / "templates" / "studio" / "preview-toolbar"
    store = (pt / "store.js").read_text(encoding="utf-8")
    forbidden_tokens = ("sessionStorage", "localStorage", "data-surface-mode")
    for path in sorted(pt.glob("*.js")):
        if path.name == "store.js":
            continue
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in text, f"{path.name} must not write {token}"
    for token in (
        "exportPrefs",
        "syncPendingStore",
        "applyExportCopyPreset",
        "applySurfaceReaderMode",
        "applyExportDraft",
    ):
        assert token in store
