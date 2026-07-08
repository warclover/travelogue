"""PDF export via Playwright."""



from __future__ import annotations
from tests._repo_root import repo_root

import json
import shutil
from pathlib import Path

import pytest

from travelogue.export.pdf import PdfExportError, export_trip_pdf
from travelogue.paths import FIXTURES_DIR
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import render_trip

pytest.importorskip("playwright")


@pytest.fixture
def pdf_workspace(tmp_path: Path) -> Path:
    demo = repo_root(__file__) / "templates" / "visual-journal" / "assets"
    if not demo.is_dir():
        pytest.skip("demo assets not present")
    ws = tmp_path / "pdf-export"
    ws.mkdir()
    shutil.copytree(demo, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    trip = prepare_trip_web_screens(
        json.loads((FIXTURES_DIR / "trip.render_golden.json").read_text(encoding="utf-8"))
    )
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    render_trip(ws / "trip.json", validate=False, layout_engine="screens")
    assert (ws / "index.html").is_file()
    return ws


def test_export_trip_pdf_missing_index(tmp_path: Path) -> None:
    with pytest.raises(PdfExportError, match="index.html not found"):
        export_trip_pdf(tmp_path)


@pytest.mark.e2e
@pytest.mark.playwright_serial
def test_export_trip_pdf_writes_file(pdf_workspace: Path) -> None:
    out = pdf_workspace / "out.pdf"
    path = export_trip_pdf(pdf_workspace, output=out)
    assert path == out
    assert out.stat().st_size > 1024
