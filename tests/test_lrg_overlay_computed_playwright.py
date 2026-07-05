"""LRG-W2 · AC-LRG-08 computed-style guards for ticket stub + EXIF overlay."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from tests.test_moment_render import _moment_trip
from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.engine import render_html

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]

FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
DEMO_ASSETS = TEMPLATE_VISUAL_JOURNAL / "assets"
VIEWPORT = {"width": 1280, "height": 900}


def _journal_css_bundle() -> str:
    journal = (TEMPLATE_VISUAL_JOURNAL / "journal.css").read_text(encoding="utf-8")
    screens = (TEMPLATE_VISUAL_JOURNAL / "journal-screens.css").read_text(encoding="utf-8")
    return f"<style>{journal}\n{screens}</style>"


def _screens_trip(tmp_path: Path) -> Path:
    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ws = tmp_path / "trips" / "lrg-computed"
    ws.mkdir(parents=True)
    shutil.copytree(DEMO_ASSETS, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    trip["exportLayout"] = "web"
    trip["layoutEngine"] = "screens"
    from travelogue.curation.layout_planner import aspect_kind_for_asset
    from travelogue.curation.screen_planner import attach_screens_to_chapters

    aspects = {a["id"]: aspect_kind_for_asset(a) for a in trip.get("assets", [])}
    trip["chapters"] = attach_screens_to_chapters(trip.get("chapters", []), aspects)
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws


def test_ticket_title_computed_font_bounded(tmp_path: Path) -> None:
    """AC-LRG-08 · ticket chapter title must stay ≤24px (overlay missing → no 48px cascade)."""
    ws = _screens_trip(tmp_path)
    trip = json.loads((ws / "trip.json").read_text(encoding="utf-8"))
    html = render_html(
        trip,
        export_mode="draft",
        trip_root=ws,
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
    )
    wrapped = _journal_css_bundle() + html
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)
        page.set_content(wrapped, wait_until="domcontentloaded")
        title = page.locator(".chapter-separator--ticket .chapter-separator__title").first
        assert title.count() >= 1
        px = title.evaluate(
            "el => parseFloat(getComputedStyle(el).fontSize)"
        )
        assert px <= 24.0, f"ticket title font-size {px}px exceeds 24px guard"
        browser.close()


def test_exif_bar_computed_styles_lrg() -> None:
    """AC-LRG-08 · moment EXIF bar background + font-size guard (reuses moment fixture)."""
    trip = _moment_trip()
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
    )
    wrapped = _journal_css_bundle() + html
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)
        page.set_content(wrapped, wait_until="domcontentloaded")
        exif = page.locator(".moment-exif-bar").first
        assert exif.count() >= 1
        bg = exif.evaluate("el => getComputedStyle(el).backgroundColor")
        assert bg in ("rgb(10, 10, 10)", "rgba(10, 10, 10, 1)")
        px = exif.evaluate("el => parseFloat(getComputedStyle(el).fontSize)")
        assert px <= 14.0, f"EXIF font-size {px}px exceeds 14px guard"
        browser.close()
