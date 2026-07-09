"""Dual HTML surfaces: index.html (web) + index-mobile.html (mobile)."""



from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests._repo_root import repo_root
from travelogue.render.engine import render_trip_surfaces


@pytest.fixture
def trip_workspace(tmp_path: Path) -> Path:
    fixture = repo_root(__file__) / "fixtures" / "trip.render_golden.json"
    if not fixture.is_file():
        pytest.skip("fixture missing")
    ws = tmp_path / "dual-surface"
    ws.mkdir()
    trip = json.loads(fixture.read_text(encoding="utf-8"))
    trip["exportLayout"] = "auto"
    trip["layoutEngine"] = "screens"
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    demo = repo_root(__file__) / "templates" / "visual-journal" / "assets" / "demo"
    if demo.is_dir():
        import shutil

        shutil.copytree(demo, ws / "assets", dirs_exist_ok=True)
    return ws


def test_render_trip_surfaces_writes_both_indexes(trip_workspace: Path) -> None:
    web, mobile, present = render_trip_surfaces(trip_workspace / "trip.json", validate=False)
    assert web.name == "index.html"
    assert mobile.name == "index-mobile.html"
    assert present is not None
    assert present.name == "index-present.html"
    web_html = web.read_text(encoding="utf-8")
    mobile_html = mobile.read_text(encoding="utf-8")
    present_html = present.read_text(encoding="utf-8")
    assert 'data-layout="web"' in web_html or 'data-layout-engine="screens"' in web_html
    assert 'data-layout="mobile"' in mobile_html
    assert "layout-screen" in web_html or 'data-block="layout-screen"' in web_html
    assert 'data-export="draft"' in web_html
    assert 'data-present-preview-url="index-present.html"' in web_html
    assert 'data-export="present-preview"' in present_html
    assert 'data-screenplay="on"' in present_html
    assert 'data-block="surface-nav"' in present_html
    assert "← 返回卷轴" in present_html
    assert "← 返回首页" in present_html
    assert 'data-block="surface-nav"' not in web_html
    assert "screenplay.js" in present_html
    assert "inline-edit.js" not in present_html
    assert 'data-export="draft"' not in present_html or present_html.count('data-export=') == 1
    assert 'data-longshot="on"' in mobile_html or "longshot" in mobile_html.lower()
