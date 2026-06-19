"""Hybrid minimal package assets (PRD-EXPERIENCE E2)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.engine import render_trip

FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
DEMO_ASSETS = TEMPLATE_VISUAL_JOURNAL / "assets"
BREATH_JS = TEMPLATE_VISUAL_JOURNAL / "breath.js"
BREATH_CSS = TEMPLATE_VISUAL_JOURNAL / "breath.css"
SCREENS_CSS = TEMPLATE_VISUAL_JOURNAL / "journal-screens.css"


@pytest.fixture
def screens_workspace(tmp_path: Path) -> Path:
    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ws = tmp_path / "trips" / "hybrid-demo"
    ws.mkdir(parents=True)
    shutil.copytree(DEMO_ASSETS, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    trip["exportLayout"] = "web"
    trip["layoutEngine"] = "screens"
    from travelogue.curation.layout_planner import aspect_kind_for_asset
    from travelogue.curation.screen_planner import attach_screens_to_chapters

    aspects = {a["id"]: aspect_kind_for_asset(a) for a in trip.get("assets", [])}
    trip["chapters"] = attach_screens_to_chapters(trip.get("chapters", []), aspects)
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws


def test_breath_assets_exist() -> None:
    js = BREATH_JS.read_text(encoding="utf-8")
    assert "TravelogueBreath" in js
    assert "IntersectionObserver" in js
    css = BREATH_CSS.read_text(encoding="utf-8")
    assert ".breath-reveal" in css


def test_default_hybrid_renders_breath_bundle(screens_workspace: Path) -> None:
    render_trip(
        screens_workspace / "trip.json",
        validate=False,
        layout_engine="screens",
        export_layout_override="web",
    )
    assert (screens_workspace / "breath.js").is_file()
    assert (screens_workspace / "breath.css").is_file()
    html = (screens_workspace / "index.html").read_text(encoding="utf-8")
    assert 'data-breath="soft"' in html
    assert 'data-snap="proximity"' in html
    assert 'data-folio="lite"' in html
    assert "breath.js" in html
    assert "folio-plate-meta" in html


def test_legacy_profile_skips_breath_bundle(screens_workspace: Path) -> None:
    render_trip(
        screens_workspace / "trip.json",
        validate=False,
        layout_engine="screens",
        export_layout_override="web",
        reading_profile_override="legacy",
    )
    assert not (screens_workspace / "breath.js").exists()
    html = (screens_workspace / "index.html").read_text(encoding="utf-8")
    assert "breath.js" not in html
    assert "data-breath=" not in html
    assert "folio-plate-meta" not in html


def test_journal_screens_has_snap_and_folio_rules() -> None:
    css = SCREENS_CSS.read_text(encoding="utf-8")
    assert '[data-snap="proximity"]' in css
    assert '[data-folio="lite"]' in css
    assert ".folio-plate-meta" in css
    assert 'html[data-snap="proximity"] {' in css
    assert '.cover-closing[data-block="cover-closing"]' in css
    assert "scroll-snap-align: start" in css


def test_chapter_sprocket_is_decoration_only() -> None:
    css = SCREENS_CSS.read_text(encoding="utf-8")
    sprocket = css.split(".chapter-separator__sprocket")[1].split(".chapter-separator--ticket[style")[0]
    assert "display: block" in sprocket
    assert "overflow: hidden" in sprocket
    assert "justify-content: center" not in sprocket
    assert ".chapter-separator__perforation" not in css
    assert ".chapter-separator__progress-dot" in css


def test_chapter_ticket_centers_pull_not_index() -> None:
    css = SCREENS_CSS.read_text(encoding="utf-8")
    assert ".chapter-separator--ticket[data-block=\"chapter-separator\"]" in css
    assert ".chapter-separator__ticket--has-pull .chapter-separator__pull-wrap" in css
    assert "justify-content: center" in css.split(".chapter-separator__ticket--has-pull .chapter-separator__pull-wrap")[1].split(".chapter-separator__mark-num")[0]
    mark = css.split(".chapter-separator__mark-num")[1].split(".chapter-separator--ticket[style")[0]
    assert "justify-content: flex-start" in mark
    overlays = (TEMPLATE_VISUAL_JOURNAL / "journal-screens-overlays.css").read_text(encoding="utf-8")
    assert ':not(.chapter-separator--ticket)' in overlays


def test_lenis_flow_disables_scroll_snap() -> None:
    css = (TEMPLATE_VISUAL_JOURNAL / "breath.css").read_text(encoding="utf-8")
    assert "html.lenis-flow" in css
    assert "scroll-snap-type: none" in css
