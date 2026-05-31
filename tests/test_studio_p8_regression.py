"""Phase 8 · 3 entry paths × 5 UI states regression matrix (static asserts)."""

from __future__ import annotations

from pathlib import Path

from tests._studio_js import read_studio_js

ROOT = Path(__file__).resolve().parents[1]
STUDIO_HTML = ROOT / "templates" / "studio" / "studio.html"
STUDIO_CSS = ROOT / "templates" / "studio" / "studio.css"

ENTRY_PATHS = {
    "path": ["studio-submit-path", "album-path", "submitPathImport"],
    "upload": ["album-upload", "uploadAndImport"],
    "demo": ["studio-demo-album", "useDemoAlbum"],
}

UI_STATES = {
    "Empty": ["studio-hero-empty", 'variant = "empty"'],
    "Returning": ["studio-hero-returning", 'variant = "returning"'],
    "Importing": ["studio-hero-importing", 'variant = "importing"'],
    "Success": ["studio-success", 'variant = "success"'],
    "Failed": ["studio-failure", 'variant = "failed"'],
}


def test_p8_three_entry_paths_present() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    js = read_studio_js()
    for path_name, markers in ENTRY_PATHS.items():
        for marker in markers:
            assert marker in html or marker in js, f"{path_name}: missing {marker}"


def test_p8_five_ui_state_shells_present() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    js = read_studio_js()
    for state_name, markers in UI_STATES.items():
        for marker in markers:
            assert marker in html or marker in js, f"{state_name}: missing {marker}"


def test_p8_skip_link_returning_target_sync() -> None:
    js = read_studio_js()
    assert "updateSkipLinkTarget" in js
    assert "studio-open-sheet-returning" in js
    assert 'targetId = "studio-open-sheet-returning"' in js


def test_p8_980_recent_list_single_column() -> None:
    css = STUDIO_CSS.read_text(encoding="utf-8")
    block_980 = css.split("@media (max-width: 980px)")[1].split("@media")[0]
    assert ".studio-hero__recent-list" in block_980
    assert "grid-template-columns: 1fr" in block_980
    block_768 = css.split("@media (max-width: 768px)")[1].split("@media")[0]
    assert "repeat(3, 1fr)" not in block_768


def test_p8_success_countdown_removed() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    js = read_studio_js()
    css = STUDIO_CSS.read_text(encoding="utf-8")
    assert "studio-success__countdown" not in html
    assert "clearSuccessTimer" not in js
    assert "studio-success__countdown" not in css


def test_p9_empty_first_screen_progressive() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    css = STUDIO_CSS.read_text(encoding="utf-8")
    assert "studio-hero__journey-details" in html
    assert "studio-hero__proof--deferred" in html
    assert "studio-hero__sample-strip--deferred" in html
    assert "studio-hero__proof--deferred" in css


def test_p9_demo_convert_and_entry_tiers() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    js = read_studio_js()
    assert 'id="studio-demo-convert"' in html
    assert 'id="studio-gallery-convert"' in html
    assert "shouldShowDemoConvert" in js
    assert 'data-entry-tier="primary"' in html
    assert 'data-entry-tier="tertiary"' in html


def test_p9_failure_next_hint() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    js = read_studio_js()
    assert 'id="studio-failure-hint"' in html
    assert "failureNextHint" in js
    assert "E_INGEST_EMPTY" in js


def test_p9_stage_labels_colloquial() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    js = read_studio_js()
    assert "读取照片" in html
    assert "第 " in js and "步，共" in js
    assert "正在读取你的照片" in js


def test_p9_success_extras_collapsed() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    js = read_studio_js()
    assert 'id="studio-success-extras"' in html
    assert "studio-success-extras" in js


def test_p9_returning_prep_guide_removed() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    returning = html.split('id="studio-hero-returning"')[1].split("<!-- ③ Importing")[0]
    assert "studio-prep-guide" not in returning


def test_p9_skip_link_overlay_states() -> None:
    js = read_studio_js()
    assert "studio-retry" in js
    assert "studio-success-longshot" in js
    assert "studio-cancel" in js
    assert 'targetId = "studio-retry"' in js or "studio-retry" in js.split("updateSkipLinkTarget")[1][:800]


def test_p9_is_demo_trip_helper() -> None:
    js = read_studio_js()
    assert "isDemoTrip" in js
    assert "sampleViewed" in js


def test_p9_open_samples_scrolls_gallery() -> None:
    js = read_studio_js()
    assert "markSampleEngaged" in js
    assert "studio-gallery" in js
    assert "scrollIntoView" in js
    studio_js = (ROOT / "templates" / "studio" / "studio.js").read_text(encoding="utf-8")
    handler = studio_js.split("openSamplesBtn")[1].split("});")[0]
    assert "openSamplePreview" not in handler


def test_p9_analytics_events() -> None:
    js = read_studio_js()
    assert "trackStudioEvent" in js
    assert "/__travelogue/studio-event" in js
    assert 'trackStudioEvent("open_sheet"' in js
    assert 'trackStudioEvent("import_success"' in js


# ── P10 · Studio dual-layout contract (see docs/PRD-STUDIO-DUAL-LAYOUT.md) ──

def test_p8_p10_viewport_module_and_layout_attr() -> None:
    js = read_studio_js()
    assert "initViewport" in js
    assert "syncStudioLayout" in js
    assert "data-studio-layout" in js
    assert "layoutTierForWidth" in js
    assert (ROOT / "templates" / "studio" / "js" / "viewport.js").is_file()


def test_p8_p10_import_eyebrow_dom() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    assert 'id="studio-stage-eyebrow"' in html
    assert "studio-import__step-eyebrow" in html


def test_p8_p10_apply_import_stage_copy() -> None:
    js = read_studio_js()
    assert "applyImportStageCopy" in js
    assert "getStudioLayout" in js
    progress = (ROOT / "templates" / "studio" / "js" / "progress.js").read_text(encoding="utf-8")
    assert "travelogue:studio-layout" in progress
    assert "refreshImportStageOnLayoutChange" in progress


def test_p8_p10_compact_loading_css() -> None:
    css = STUDIO_CSS.read_text(encoding="utf-8")
    block = css.split("/* Success / Failure / Loading overlays */")[1].split(".studio-loading__label")[0]
    assert "#studio-hero-loading" in block
    assert 'html[data-studio-layout="compact"] #studio-hero-loading' in css


def test_p8_p10_pick_folder_cap_css() -> None:
    css = STUDIO_CSS.read_text(encoding="utf-8")
    assert 'html[data-cap-pick-folder="off"] #studio-browse-folder' in css
    assert "#studio-sheet-pick" in css


def test_p8_p10_wide_import_panel_css() -> None:
    css = STUDIO_CSS.read_text(encoding="utf-8")
    wide_block = css.split("/* ── P10 · Studio layout tiers")[1].split(".studio-loading__label")[0]
    assert 'html[data-studio-layout="wide"]' in wide_block
    assert "#studio-hero-importing" in wide_block
    assert "min(920px" in wide_block
    assert "white-space: nowrap" in wide_block


def test_p8_p10_compact_eyebrow_css() -> None:
    css = STUDIO_CSS.read_text(encoding="utf-8")
    assert 'html[data-studio-layout="compact"]' in css
    assert "studio-import__step-eyebrow" in css
    assert "display: block" in css.split('html[data-studio-layout="compact"]')[1]


def test_p8_p10_layout_breakpoints_match_media() -> None:
    js = read_studio_js()
    css = STUDIO_CSS.read_text(encoding="utf-8")
    assert "768" in js
    assert "980" in js
    assert "max-width: 980px" in css
    assert "max-width: 768px" in css


def test_p8_p10_studio_js_inits_viewport() -> None:
    entry = (ROOT / "templates" / "studio" / "studio.js").read_text(encoding="utf-8")
    assert "initViewport" in entry
    assert "from \"./js/viewport.js\"" in entry or "from './js/viewport.js'" in entry
    assert "initStudioCapabilities" in entry


def test_p8_p10_overlay_wide_css() -> None:
    css = STUDIO_CSS.read_text(encoding="utf-8")
    block = css.split("/* Success / Failure / Loading overlays */")[1].split(".studio-loading__label")[0]
    assert "#studio-success" in block
    assert "#studio-failure" in block
    assert "min(720px" in block


def test_p8_p10_capabilities_module() -> None:
    js = read_studio_js()
    assert "initStudioCapabilities" in js
    assert "data-cap-pick-folder" in js
    assert "applyStudioCapabilities" in js
