"""Export / publish tests."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from travelogue.export.packager import ExportError, export_trip
from travelogue.orchestrator.pipeline import publish_trip
from travelogue.paths import ROOT
from travelogue.render.engine import render_trip

FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"


@pytest.fixture
def trip_workspace(tmp_path: Path):
    import shutil

    from travelogue.paths import TEMPLATE_VISUAL_JOURNAL

    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ws = tmp_path / "trips" / "render-golden-demo"
    ws.mkdir(parents=True)
    shutil.copytree(TEMPLATE_VISUAL_JOURNAL / "assets", ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws


def test_export_requires_privacy(trip_workspace: Path) -> None:
    render_trip(trip_workspace / "trip.json", validate=False)
    with pytest.raises(ExportError) as exc:
        export_trip(trip_workspace / "trip.json", confirm_privacy=False, validate=False)
    assert exc.value.code == "E_EXPORT_PRIVACY"


def test_export_creates_zip(trip_workspace: Path) -> None:
    zip_path = export_trip(
        trip_workspace / "trip.json",
        confirm_privacy=True,
        validate=False,
    )
    assert zip_path.is_file()
    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    assert trip["pipeline"]["status"] == "exported"
    assert trip["privacy"]["confirmedAt"]

    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        assert "index.html" in names
        assert "journal.css" in names
        assert "preview.jpg" in names
        html = zf.read("index.html").decode("utf-8")
        assert 'data-export="share"' in html
        assert "data-editable" not in html
        assert "longshot.js" in names
        assert "longshot-save" in html


def test_publish_end_to_end(trip_workspace: Path) -> None:
    result = publish_trip(trip_workspace / "trip.json", validate=False)
    assert result.zip_path.is_file()
    assert result.index_html.is_file()
    assert result.preview_jpg and result.preview_jpg.is_file()
