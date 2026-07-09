"""Breath cinematic scrub + gallery pin (PRD-EXPERIENCE E8)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.engine import render_trip
from travelogue.render.reading_profile import resolve_reading_payload

FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
DEMO_ASSETS = TEMPLATE_VISUAL_JOURNAL / "assets"
BREATH_JS = TEMPLATE_VISUAL_JOURNAL / "breath.js"
BREATH_GSAP_JS = TEMPLATE_VISUAL_JOURNAL / "breath-gsap.js"
BREATH_CSS = TEMPLATE_VISUAL_JOURNAL / "breath.css"
SCREENPLAY_JS = TEMPLATE_VISUAL_JOURNAL / "screenplay.js"


@pytest.fixture
def screens_workspace(tmp_path: Path) -> Path:
    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ws = tmp_path / "trips" / "cinematic-demo"
    ws.mkdir(parents=True)
    shutil.copytree(DEMO_ASSETS, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    trip["exportLayout"] = "web"
    trip["layoutEngine"] = "screens"
    from travelogue.curation.layout_planner import aspect_kind_for_asset
    from travelogue.layout_engine.planner.screen_planner import attach_screens_to_chapters

    aspects = {a["id"]: aspect_kind_for_asset(a) for a in trip.get("assets", [])}
    trip["chapters"] = attach_screens_to_chapters(trip.get("chapters", []), aspects)
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws


def test_breath_gsap_asset_exists() -> None:
    js = BREATH_GSAP_JS.read_text(encoding="utf-8")
    assert "TravelogueScrub" in js
    assert "setupCinematic" in js or "setupGalleryPins" in js
    assert "setupGalleryScreenPins" in js
    assert "gallery" in js


def test_breath_js_wires_scrub_engine() -> None:
    js = BREATH_JS.read_text(encoding="utf-8")
    assert "TravelogueScrub" in js
    assert "initScrubMotion" in js
    assert "destroyScrub" in js
    assert '"cinematic"' in js
    assert '"gallery"' in js


def test_breath_css_cinematic_gallery_rules() -> None:
    css = BREATH_CSS.read_text(encoding="utf-8")
    assert "breath-scrub-active" in css
    assert 'data-breath="gallery"' in css
    assert "breath-gallery-screens-rail" in css


def test_reading_payload_accepts_cinematic_and_gallery() -> None:
    cinematic = resolve_reading_payload(
        {"export": {"reading": {"scroll": {"breath": "cinematic"}}}}, export_layout_override="web"
    )
    gallery = resolve_reading_payload(
        {"export": {"reading": {"scroll": {"breath": "gallery"}}}}, export_layout_override="web"
    )
    assert cinematic["scroll"]["breath"] == "cinematic"
    assert gallery["scroll"]["breath"] == "gallery"


def test_cinematic_renders_scrub_bundle(screens_workspace: Path) -> None:
    trip = json.loads((screens_workspace / "trip.json").read_text(encoding="utf-8"))
    trip.setdefault("export", {})["reading"] = {
        "scroll": {"breath": "cinematic", "folio": "lite", "breathEngine": "gsap"},
    }
    (screens_workspace / "trip.json").write_text(
        json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    render_trip(
        screens_workspace / "trip.json",
        validate=False,
        layout_engine="screens",
        export_layout_override="web",
    )
    assert (screens_workspace / "breath-gsap.js").is_file()
    assert (screens_workspace / "breath-lenis.js").is_file()
    assert (screens_workspace / "breath-highlight.js").is_file()
    assert (screens_workspace / "breath-image.js").is_file()
    html = (screens_workspace / "index.html").read_text(encoding="utf-8")
    assert 'data-breath="cinematic"' in html
    assert "breath-gsap.js" in html
    assert "breath-lenis.js" in html
    assert "breath-highlight.js" in html
    assert "breath-image.js" in html


def test_gallery_renders_scrub_bundle(screens_workspace: Path) -> None:
    trip = json.loads((screens_workspace / "trip.json").read_text(encoding="utf-8"))
    trip.setdefault("export", {})["reading"] = {"scroll": {"breath": "gallery", "folio": "off"}}
    (screens_workspace / "trip.json").write_text(
        json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    render_trip(
        screens_workspace / "trip.json",
        validate=False,
        layout_engine="screens",
        export_layout_override="web",
    )
    html = (screens_workspace / "index.html").read_text(encoding="utf-8")
    assert 'data-breath="gallery"' in html
    assert "breath-gsap.js" in html


def test_default_hybrid_skips_scrub_bundle(screens_workspace: Path) -> None:
    render_trip(
        screens_workspace / "trip.json",
        validate=False,
        layout_engine="screens",
        export_layout_override="web",
    )
    assert not (screens_workspace / "breath-gsap.js").exists()
    html = (screens_workspace / "index.html").read_text(encoding="utf-8")
    assert "breath-gsap.js" not in html


def test_screenplay_pauses_via_breath_scrub_hooks() -> None:
    breath = BREATH_JS.read_text(encoding="utf-8")
    screenplay = SCREENPLAY_JS.read_text(encoding="utf-8")
    assert "pauseScrub" in breath
    assert "pauseBreath" in screenplay
