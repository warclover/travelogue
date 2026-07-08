"""Phase 5 Tier-0 UX fixes · shared JS / schema smoke (post M21-e2)."""



from __future__ import annotations
from tests._repo_root import repo_root

from pathlib import Path

from tests._studio_js import read_studio_js

ROOT = repo_root(__file__)
PREVIEW_JS = ROOT / "templates" / "studio" / "preview-toolbar.js"
LONGSHOT_JS = ROOT / "templates" / "studio" / "preview-toolbar" / "longshot.js"


def test_p5_14_job_busy_toast_and_retry() -> None:
    js = read_studio_js()
    assert "withJobBusyRetry" in js
    assert "isJobBusyResponse" in js
    assert "E_STUDIO_JOB_BUSY" in js
    assert "排队中，请稍候" in js


def test_p5_32_preview_longshot_busy_retry() -> None:
    js = PREVIEW_JS.read_text(encoding="utf-8")
    longshot = LONGSHOT_JS.read_text(encoding="utf-8")
    bundle = js + longshot
    assert "postJsonBusyRetry" in bundle
    assert './js/http.js"' in longshot or './js/http.js"' in js
    assert "排队中，请稍候" in bundle


def test_preview_toolbar_longshot_integrated_to_top_bar() -> None:
    js = PREVIEW_JS.read_text(encoding="utf-8")
    longshot = LONGSHOT_JS.read_text(encoding="utf-8")
    bundle = js + longshot
    css = (ROOT / "templates" / "studio" / "preview-toolbar.css").read_text(encoding="utf-8")
    client = (ROOT / "templates" / "studio" / "js" / "longshot-client.js").read_text(
        encoding="utf-8"
    )
    for token in (
        "preview-toolbar--v4",
        "mountPreviewTaskDock",
        "mountPreviewUnifiedSheet",
        "preview-toolbar-v3-task-dock.js",
        "preview-toolbar-v3-sheet.js",
        "openLongshotExportOptions",
        "openStudioLongshotExportPanel",
        "buildLongshotRequestFromPage",
        "resolveCopyDisplayFromDom",
        "syncLongshotPreviewChips",
        "longshotProgressPct",
        "preview-task-dock",
        "preview-sheet",
        "showG1",
        "SHEET_HINT_KEY",
        "mountTemplateControls",
        "trapFocus",
        "data-copy-preset",
        "导出长图",
    ):
        assert token in bundle or token in css, f"missing preview toolbar v3/longshot marker: {token}"
    assert 'html[data-preview-toolbar="on"] .longshot-toolbar' in css
    assert 'html[data-preview-toolbar="on"] .screenplay-toolbar' in css
    assert "resolveCopyDisplayFromDom" in client
    assert "segmentMode" in client
    assert "normalizeSegmentMode" in bundle


def test_p5_a4_shared_http_module() -> None:
    js = read_studio_js()
    assert "export function postJson" in js or "function postJson" in js
    assert "export function patchJson" in js
    assert "postJsonBusyRetry" in js
    http = (ROOT / "templates" / "studio" / "js" / "http.js").read_text(encoding="utf-8")
    assert "export function postJson" in http
    assert "export function patchJson" in http


def test_studio_constants_is_generic_place() -> None:
    js = (ROOT / "templates" / "studio" / "js" / "constants.js").read_text(encoding="utf-8")
    assert "isGenericPlace" in js
    assert "GENERIC_PLACES" in js


def test_trip_schema_allows_places_user_set() -> None:
    schema = (ROOT / "schemas" / "trip.schema.json").read_text(encoding="utf-8")
    assert "placesUserSet" in schema
