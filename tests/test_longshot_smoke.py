"""Playwright smoke for index-longshot.html (optional dependency)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from travelogue.paths import FIXTURES_DIR
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import LONGSHOT_INDEX_NAME, render_trip

pytest.importorskip("playwright")

from travelogue.web.longshot_smoke import run_longshot_smoke  # noqa: E402

pytestmark = pytest.mark.playwright_serial


@pytest.fixture
def longshot_workspace(tmp_path: Path) -> Path:
    demo = Path(__file__).resolve().parents[1] / "templates" / "visual-journal" / "assets"
    if not demo.is_dir():
        pytest.skip("demo assets not present")
    ws = tmp_path / "longshot-smoke"
    ws.mkdir()
    shutil.copytree(demo, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    trip = prepare_trip_web_screens(
        json.loads((FIXTURES_DIR / "trip.render_golden.json").read_text(encoding="utf-8"))
    )
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    render_trip(ws / "trip.json", validate=False, layout_engine="screens")
    assert (ws / LONGSHOT_INDEX_NAME).is_file()
    return ws


def test_longshot_smoke(longshot_workspace: Path) -> None:
    result = run_longshot_smoke(longshot_workspace, capture_first_chapter=True)
    assert result["chapter_count"] >= 1
    assert result["media_card_count"] >= 1
    assert result.get("first_chapter_blob_bytes", 0) > 1024 or result.get("capture_skipped")
