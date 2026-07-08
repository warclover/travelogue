"""P0 dual-engine regression: legacy vs screens."""



from __future__ import annotations
from tests._repo_root import repo_root

import json
import shutil
from pathlib import Path

import pytest

from travelogue.paths import FIXTURES_DIR
from travelogue.render.dual_layout_regression import (
    check_legacy_render_contract,
    check_screens_render_contract,
    prepare_trip_web_legacy,
    prepare_trip_web_screens,
    run_dual_engine_checks,
    screen_pattern_sequence,
)
from travelogue.render.engine import render_html, should_include_long_shot
from travelogue.render.golden_regression import check_golden_dom, load_golden_trip
from travelogue.services.layout import format_layout_summary


@pytest.fixture
def golden_trip() -> dict:
    return load_golden_trip()


def test_golden_fixture_legacy_dom_unchanged(golden_trip: dict) -> None:
    """Mobile/auto golden fixture must still pass legacy golden DOM gate."""
    assert not check_golden_dom(trip=golden_trip)


def test_web_legacy_has_no_layout_screen(golden_trip: dict) -> None:
    trip = prepare_trip_web_legacy(golden_trip)
    html = render_html(trip, export_mode="draft")
    assert not check_legacy_render_contract(html)


def test_web_screens_contract(golden_trip: dict) -> None:
    trip = prepare_trip_web_screens(golden_trip)
    html = render_html(trip, export_mode="draft", layout_engine_override="screens")
    assert not check_screens_render_contract(html)
    patterns = screen_pattern_sequence(html)
    assert patterns
    assert any(p.startswith("screen-") for p in patterns)


def test_run_dual_engine_checks_golden(golden_trip: dict) -> None:
    assert not run_dual_engine_checks(golden_trip)


def test_format_layout_summary_includes_screens(golden_trip: dict) -> None:
    trip = prepare_trip_web_screens(golden_trip)
    summary = (trip.get("curation") or {}).get("orientationSummary") or {
        "total": 10,
        "landscape": 4,
        "portrait": 4,
        "export_layout": "web",
    }
    text = format_layout_summary(summary, trip["chapters"])
    assert "screens" in text or "屏" in text
    assert "screen-" in text or "宫格" in text or "三联" in text


def test_longshot_disabled_for_screens_engine(golden_trip: dict) -> None:
    trip = prepare_trip_web_screens(golden_trip)
    assert should_include_long_shot(trip) is False
    html = render_html(trip, export_mode="draft", layout_engine_override="screens")
    assert 'data-longshot="on"' not in html
    assert 'data-longshot-bridge="on"' in html
    assert "longshot-bridge" in html
    assert "longshot-bridge.js" in html


def test_longshot_bridge_writes_longshot_sidecar(tmp_path: Path) -> None:
    from travelogue.render.engine import LONGSHOT_INDEX_NAME, render_trip

    fixture = FIXTURES_DIR / "trip.render_golden.json"
    trip = json.loads(fixture.read_text(encoding="utf-8"))
    demo = repo_root(__file__) / "templates" / "visual-journal" / "assets"
    if not demo.is_dir():
        pytest.skip("demo assets not present")
    trip = prepare_trip_web_screens(trip)
    ws = tmp_path / "bridge-trip"
    ws.mkdir()
    shutil.copytree(demo, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    render_trip(ws / "trip.json", validate=False, layout_engine="screens")
    assert (ws / LONGSHOT_INDEX_NAME).is_file()
    assert (ws / "longshot.js").is_file()
    assert (ws / "longshot-bridge.js").is_file()
    longshot = (ws / LONGSHOT_INDEX_NAME).read_text(encoding="utf-8")
    assert 'data-longshot="on"' in longshot
    assert "longshot-save" in longshot
    assert 'data-block="layout-screen"' not in longshot
    main = (ws / "index.html").read_text(encoding="utf-8")
    assert 'data-longshot-bridge="on"' in main
    assert "longshot-bridge" in main
    assert f'data-longshot-mobile-url="{LONGSHOT_INDEX_NAME}"' in main


def test_screenplay_enabled_for_screens_engine(golden_trip: dict) -> None:
    trip = prepare_trip_web_screens(golden_trip)
    from travelogue.render.engine import should_include_screenplay

    assert should_include_screenplay(trip, export_mode="share") is True
    assert should_include_screenplay(trip, export_mode="draft") is False
    draft_html = render_html(trip, export_mode="draft", layout_engine_override="screens")
    assert 'data-screenplay="on"' not in draft_html
    assert "screenplay.js" not in draft_html
    assert 'data-inline-edit="on"' in draft_html
    assert 'data-longshot-bridge="on"' in draft_html
    assert 'data-present-preview-url="index-present.html"' in draft_html
    share_html = render_html(trip, export_mode="share", layout_engine_override="screens")
    assert 'data-screenplay="on"' in share_html
    assert "screenplay-start" in share_html
    assert "screenplay.js" in share_html
    assert "screenplay.css" in share_html


def test_screenplay_photos_mode_keeps_copy_in_dom_for_toggle(golden_trip: dict):
    """Interactive screens bundle keeps narrative in HTML; CSS/JS toggles visibility."""
    from travelogue.render.dual_layout_regression import prepare_trip_web_screens

    trip = prepare_trip_web_screens(golden_trip)
    trip.setdefault("export", {})["copyDisplay"] = "photos"
    html = render_html(trip, export_mode="draft", layout_engine_override="screens")
    assert 'data-copy-display="photos"' in html
    assert 'data-copy-toggle="on"' in html
    assert "copy-display-toggle" in html
    assert "copy-toggle.js" in html
    assert trip["meta"]["hook"] in html
    assert 'data-block="hook-line"' in html


def test_screenplay_disabled_for_legacy_web(golden_trip: dict) -> None:
    trip = prepare_trip_web_legacy(golden_trip)
    from travelogue.render.engine import should_include_screenplay

    assert should_include_screenplay(trip) is False
    html = render_html(trip, export_mode="draft")
    assert 'data-screenplay="on"' not in html
    assert "screenplay-start" not in html


def test_longshot_enabled_for_legacy_web(golden_trip: dict) -> None:
    trip = prepare_trip_web_legacy(golden_trip)
    trip.setdefault("export", {})["longShot"] = True
    assert should_include_long_shot(trip) is True


def test_dual_render_fixture_trip(tmp_path: Path) -> None:
    """Write legacy + screens HTML from render_golden fixture (offline assets)."""
    fixture = FIXTURES_DIR / "trip.render_golden.json"
    trip = json.loads(fixture.read_text(encoding="utf-8"))
    demo = repo_root(__file__) / "templates" / "visual-journal" / "assets" / "demo"
    if not demo.is_dir():
        pytest.skip("demo assets not present")
    ws = tmp_path / "dual"
    ws.mkdir()
    (ws / "assets").mkdir()
    # minimal: render without asset existence check uses render_html only
    legacy = prepare_trip_web_legacy(trip)
    screens = prepare_trip_web_screens(trip)
    h_legacy = render_html(legacy, export_mode="draft")
    h_screens = render_html(screens, export_mode="draft", layout_engine_override="screens")
    (ws / "index-legacy.html").write_text(h_legacy, encoding="utf-8")
    (ws / "index-screens.html").write_text(h_screens, encoding="utf-8")
    assert (ws / "index-legacy.html").stat().st_size > 500
    assert (ws / "index-screens.html").stat().st_size > 500
    assert "layout-screen" in h_screens
    assert "layout-screen" not in h_legacy or 'data-block="layout-screen"' not in h_legacy
