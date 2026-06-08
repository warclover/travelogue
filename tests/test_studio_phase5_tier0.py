"""Phase 5 Tier-0 UX fixes · shared JS / schema smoke (post M21-e2)."""

from __future__ import annotations

from pathlib import Path

from tests._studio_js import read_studio_js

ROOT = Path(__file__).resolve().parents[1]
PREVIEW_JS = ROOT / "templates" / "studio" / "preview-toolbar.js"


def test_p5_14_job_busy_toast_and_retry() -> None:
    js = read_studio_js()
    assert "withJobBusyRetry" in js
    assert "isJobBusyResponse" in js
    assert "E_STUDIO_JOB_BUSY" in js
    assert "排队中，请稍候" in js


def test_p5_32_preview_longshot_busy_retry() -> None:
    js = PREVIEW_JS.read_text(encoding="utf-8")
    assert "postJsonBusyRetry" in js
    assert './js/http.js"' in js
    assert "排队中，请稍候" in js


def test_preview_toolbar_longshot_integrated_to_top_bar() -> None:
    js = PREVIEW_JS.read_text(encoding="utf-8")
    css = (ROOT / "templates" / "studio" / "preview-toolbar.css").read_text(encoding="utf-8")
    client = (ROOT / "templates" / "studio" / "js" / "longshot-client.js").read_text(
        encoding="utf-8"
    )
    for token in (
        "preview-toolbar__longshot-caret",
        "preview-toolbar__longshot-preview-row",
        "openLongshotExportOptions",
        "openStudioLongshotExportPanel",
        "preview-toolbar__export-popover",
        "preview-toolbar__icon-btn",
        "preview-toolbar__ctl",
        "buildLongshotRequestFromPage",
        "resolveCopyDisplayFromDom",
        "syncLongshotPreviewChips",
        "openLongshotResultDrawer",
        "bindLongshotExportMeta",
        "longshotProgressPct",
    ):
        assert token in js, f"missing preview toolbar longshot marker: {token}"
    assert 'html[data-preview-toolbar="on"] .longshot-toolbar' in css
    assert 'html[data-preview-toolbar="on"] .screenplay-toolbar' in css
    assert "preview-toolbar__export-meta--action" in css
    assert "resolveCopyDisplayFromDom" in client
    assert "segmentMode" in client
    assert "normalizeSegmentMode" in js


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
