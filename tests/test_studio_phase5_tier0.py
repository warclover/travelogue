"""Phase 5 Tier-0 UX fixes · P5-1.4/1.6/1.7, P5-3.2, P5-H4."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests._studio_js import read_studio_js

ROOT = Path(__file__).resolve().parents[1]
STUDIO_HTML = ROOT / "templates" / "studio" / "studio.html"
PREVIEW_JS = ROOT / "templates" / "studio" / "preview-toolbar.js"
pytestmark = pytest.mark.legacy_homepage


def test_p5_16_single_album_upload_input() -> None:
    html = STUDIO_HTML.read_text(encoding="utf-8")
    matches = re.findall(r'id="album-upload"', html)
    assert len(matches) == 1, f"expected one #album-upload, found {len(matches)}"
    assert 'for="album-upload"' in html


def test_p5_14_job_busy_toast_and_retry() -> None:
    js = read_studio_js()
    assert "withJobBusyRetry" in js
    assert "isJobBusyResponse" in js
    assert "E_STUDIO_JOB_BUSY" in js
    assert "排队中，请稍候" in js


def test_p5_17_sample_modal_focus_trap() -> None:
    js = read_studio_js()
    assert "trapSheetFocus(modal)" in js
    assert "releaseModalFocusTrap" in js


def test_p5_h4_returning_recent_path_hint() -> None:
    js = read_studio_js()
    assert "renderRecentPathHint" in js
    assert "继续使用" in js


def test_p5_32_preview_longshot_busy_retry() -> None:
    js = PREVIEW_JS.read_text(encoding="utf-8")
    assert "postJsonBusyRetry" in js
    assert './js/http.js"' in js
    assert "排队中，请稍候" in js


def test_p5_a4_shared_http_module() -> None:
    js = read_studio_js()
    assert "export function postJson" in js or "function postJson" in js
    assert "export function patchJson" in js
    assert "postJsonBusyRetry" in js
    http = (ROOT / "templates" / "studio" / "js" / "http.js").read_text(encoding="utf-8")
    assert "export function postJson" in http
    assert "export function patchJson" in http


def test_studio_nested_import_success_guard() -> None:
    flow = (ROOT / "templates" / "studio" / "js" / "import-flow.js").read_text(encoding="utf-8")
    assert "if (!job) return" in flow
    job_mod = (ROOT / "templates" / "studio" / "js" / "import-job.js").read_text(encoding="utf-8")
    assert "normalizeCompletedImportJob" in job_mod


def test_studio_intent_scoped_by_album_path() -> None:
    sheet = (ROOT / "templates" / "studio" / "js" / "sheet.js").read_text(encoding="utf-8")
    assert "albumPath" in sheet
    assert "sameAlbum" in sheet
    assert "placeUserSet" in sheet


def test_studio_constants_is_generic_place() -> None:
    js = (ROOT / "templates" / "studio" / "js" / "constants.js").read_text(encoding="utf-8")
    assert "isGenericPlace" in js
    assert "GENERIC_PLACES" in js


def test_import_flow_g1_pending_success_copy() -> None:
    js = (ROOT / "templates" / "studio" / "js" / "import-flow.js").read_text(encoding="utf-8")
    assert "g1Pending" in js
    assert "待确认章节结构" in js


def test_trip_schema_allows_places_user_set() -> None:
    schema = (ROOT / "schemas" / "trip.schema.json").read_text(encoding="utf-8")
    assert "placesUserSet" in schema


def test_p5_a1_studio_entry_loads_render_module() -> None:
    entry = (ROOT / "templates" / "studio" / "studio.js").read_text(encoding="utf-8")
    assert 'import "./js/render.js"' in entry


def test_p5_esm_cycle_break() -> None:
    render = (ROOT / "templates" / "studio" / "js" / "render.js").read_text(encoding="utf-8")
    sheet = (ROOT / "templates" / "studio" / "js" / "sheet.js").read_text(encoding="utf-8")
    api = (ROOT / "templates" / "studio" / "js" / "api.js").read_text(encoding="utf-8")
    assert "import-bridge.js" in render
    assert "import-flow.js" not in render
    assert "import-bridge.js" in sheet
    assert "import-flow.js" not in sheet
    assert "navigation.js" in api
    assert "render.js" not in api
    assert "pollJobUntilDone" in api
