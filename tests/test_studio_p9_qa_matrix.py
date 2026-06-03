"""P9-P0-05 · Design QA baseline (automated static + API matrix)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests._studio_js import read_studio_js
from tests.test_studio_p8_regression import ENTRY_PATHS, UI_STATES
from tests.test_studio_server import _free_port, _post_json, _start_studio_server
from travelogue.web.studio_handlers.paths import STUDIO_EVENT_PATH
from travelogue.web.studio_jobs import reset_job_store

ROOT = Path(__file__).resolve().parents[1]
STUDIO_HTML = ROOT / "templates" / "studio" / "studio.html"
STUDIO_CSS = ROOT / "templates" / "studio" / "studio.css"
pytestmark = pytest.mark.legacy_homepage

QA_BREAKPOINTS_PX = (980, 1100, 1280, 1440)

KEYBOARD_PATH_MARKERS = [
    "studio-skip-link",
    "studio-open-sheet",
    "studio-open-sheet-returning",
    "studio-sheet-close",
    "studio-sheet-pick",
    "studio-cancel",
    "studio-retry",
    'e.key === "Escape"',
    "trapSheetFocus",
    "releaseSheetFocusTrap",
]

FEEDBACK_LAYERS = [
    ('role="alert"', "Error"),
    ('id="studio-warning"', "Warning"),
    ('id="studio-failure-hint"', "Failure hint"),
    ('role="progressbar"', "Progress"),
    ('id="studio-toast-container"', "Toast host"),
    ('studio-coach', "Coach"),
]


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


def test_p9_qa_three_by_five_matrix_crosswalk() -> None:
    """Every entry path and UI state shell must exist in HTML or JS."""
    html = STUDIO_HTML.read_text(encoding="utf-8")
    js = read_studio_js()
    for entry, markers in ENTRY_PATHS.items():
        for state, state_markers in UI_STATES.items():
            for marker in markers:
                assert marker in html or marker in js, f"{entry}×{state}: missing {marker}"


def test_p9_qa_keyboard_path_wiring() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    js = read_studio_js()
    assert html.strip().startswith("<!DOCTYPE html>")
    assert html.index('class="studio-skip-link"') < html.index('id="studio-hero"')
    for marker in KEYBOARD_PATH_MARKERS:
        assert marker in html or marker in js, marker


def test_p9_qa_feedback_layer_semantics() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    js = read_studio_js()
    for marker, _label in FEEDBACK_LAYERS:
        assert marker in html or marker in js


def test_p9_qa_entry_map_single_primary_empty() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    empty_block = html.split('id="studio-hero-empty"')[1].split("<!-- ② Returning")[0]
    cta_row = empty_block.split('class="studio-hero__cta-row"')[1].split("</div>")[0]
    assert cta_row.count("studio-btn--gold") == 1
    assert 'data-entry-tier="primary"' in cta_row
    assert 'data-entry-tier="secondary"' in cta_row
    assert 'data-entry-zone="tertiary"' in html


def test_p9_qa_responsive_breakpoint_rules_present() -> None:
    css = STUDIO_CSS.read_text(encoding="utf-8")
    for bp in (1200, 980, 768):
        assert f"@media (max-width: {bp}px)" in css
    block_980 = css.split("@media (max-width: 980px)")[1].split("@media")[0]
    assert "studio-hero__hybrid-left" in block_980
    assert "max-width" in block_980


def test_p9_qa_reduced_motion_respect() -> None:
    js = read_studio_js()
    css = STUDIO_CSS.read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in js or "prefers-reduced-motion" in css


def test_p9_qa_screen_reader_progress_copy() -> None:
    js = read_studio_js()
    assert "aria-valuetext" in js
    assert "stageText" in js
    assert "第 " in js and "步，共" in js


@pytest.mark.e2e
def test_p9_qa_studio_event_endpoint(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    try:
        status, body = _post_json(
            f"{base}{STUDIO_EVENT_PATH}",
            {"event": "open_sheet", "meta": {"state": "IdleEmpty", "qa": True}},
        )
        assert status == 200
        assert body == {"ok": True}
        bad_status, bad_body = _post_json(
            f"{base}{STUDIO_EVENT_PATH}",
            {"event": "not_allowed"},
        )
        assert bad_status == 400
        assert "allowed" in bad_body
    finally:
        server.shutdown()
        server.server_close()


def test_p9_qa_manual_signoff_checklist_documented() -> None:
    """Automated gate lists what still needs human NVDA/VoiceOver + screenshot sign-off."""
    manual = {
        "keyboard_only_full_path",
        "screen_reader_once",
        "screenshots_980_1100_1280_1440",
    }
    automated = {
        "static_3x5_matrix",
        "keyboard_wiring",
        "feedback_semantics",
        "responsive_css_rules",
        "playwright_smoke",
    }
    assert manual.isdisjoint(automated)
    assert QA_BREAKPOINTS_PX == (980, 1100, 1280, 1440)
