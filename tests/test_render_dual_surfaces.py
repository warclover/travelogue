"""Dual HTML surfaces: index.html (web) + index-mobile.html (mobile)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.render.engine import render_trip_surfaces


@pytest.fixture
def trip_workspace(tmp_path: Path) -> Path:
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "trip.render_golden.json"
    if not fixture.is_file():
        pytest.skip("fixture missing")
    ws = tmp_path / "dual-surface"
    ws.mkdir()
    trip = json.loads(fixture.read_text(encoding="utf-8"))
    trip["exportLayout"] = "auto"
    trip["layoutEngine"] = "screens"
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    demo = Path(__file__).resolve().parents[1] / "templates" / "visual-journal" / "assets" / "demo"
    if demo.is_dir():
        import shutil

        shutil.copytree(demo, ws / "assets", dirs_exist_ok=True)
    return ws


def test_render_trip_surfaces_writes_both_indexes(trip_workspace: Path) -> None:
    web, mobile = render_trip_surfaces(trip_workspace / "trip.json", validate=False)
    assert web.name == "index.html"
    assert mobile.name == "index-mobile.html"
    web_html = web.read_text(encoding="utf-8")
    mobile_html = mobile.read_text(encoding="utf-8")
    assert 'data-layout="web"' in web_html or 'data-layout-engine="screens"' in web_html
    assert 'data-layout="mobile"' in mobile_html
    assert "layout-screen" in web_html or 'data-block="layout-screen"' in web_html
    assert 'data-longshot="on"' in mobile_html or "longshot" in mobile_html.lower()
