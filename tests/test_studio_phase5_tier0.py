"""Phase 5 Tier-0 UX fixes · P5-1.4/1.6/1.7, P5-3.2, P5-H4."""

from __future__ import annotations

import re
from pathlib import Path

from tests._studio_js import read_studio_js

ROOT = Path(__file__).resolve().parents[1]
STUDIO_HTML = ROOT / "templates" / "studio" / "studio.html"
PREVIEW_JS = ROOT / "templates" / "studio" / "preview-toolbar.js"


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
    assert "排队中，请稍候" in js
    assert "E_STUDIO_JOB_BUSY" in js
