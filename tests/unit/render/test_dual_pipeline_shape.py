"""DPI W0 · HTML shape assertions (AC-DPI-07/08 · IE-DPI-05/10).

W0 covers three faces. W1 adds CSS filename / @import assertions (FE-DPI-05).
"""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from travelogue.curation.layout_planner import aspect_kind_for_asset
from travelogue.layout_engine.planner.screen_planner import attach_screens_to_chapters
from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.engine import render_html, render_trip

pytestmark = [pytest.mark.unit, pytest.mark.pipeline_isolation]

FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
DEMO_ASSETS = TEMPLATE_VISUAL_JOURNAL / "assets"


def _workspace(tmp_path: Path, name: str) -> Path:
    ws = tmp_path / "trips" / name
    ws.mkdir(parents=True)
    shutil.copytree(DEMO_ASSETS, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    return ws


def _journal_trip() -> dict:
    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    trip["exportLayout"] = "web"
    trip["layoutEngine"] = "screens"
    aspects = {a["id"]: aspect_kind_for_asset(a) for a in trip.get("assets", [])}
    trip["chapters"] = attach_screens_to_chapters(trip.get("chapters", []), aspects)
    return trip


def _portfolio_trip() -> dict:
    """Identity-neutral golden + injected edition; one page-* screen already attached."""
    trip = copy.deepcopy(_journal_trip())
    trip["studio"] = {"edition": "portfolio"}
    first = next(ch for ch in trip["chapters"] if ch.get("screens"))
    first["screens"] = [
        {
            "screenId": "dpi-page-hero",
            "patternId": "page-1-hero-port",
            "slots": [{"assetId": "asset-001", "slot": 0, "fit": "cover"}],
        }
    ]
    return trip


@pytest.fixture
def journal_ws(tmp_path: Path) -> tuple[Path, dict]:
    ws = _workspace(tmp_path, "dpi-journal")
    trip = _journal_trip()
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws, trip


@pytest.fixture
def portfolio_ws(tmp_path: Path) -> tuple[Path, dict]:
    ws = _workspace(tmp_path, "dpi-portfolio")
    trip = _portfolio_trip()
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws, trip


def test_journal_web_shape(journal_ws: tuple[Path, dict]) -> None:
    ws, trip = journal_ws
    html = render_html(
        trip,
        export_mode="draft",
        trip_root=ws,
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert 'data-block="chapter-header"' in html
    assert 'data-block="layout-screen"' in html
    assert 'data-pattern="screen-' in html
    assert 'data-edition="portfolio"' not in html
    assert 'data-pattern="page-' not in html


def test_journal_longshot_shape(journal_ws: tuple[Path, dict]) -> None:
    ws, trip = journal_ws
    html = render_html(
        trip,
        export_mode="draft",
        trip_root=ws,
        layout_engine_override="screens",
        export_layout_override="longshot",
    )
    assert 'data-layout="longshot"' in html
    assert 'data-block="chapter-header"' in html
    assert 'data-block="media-card"' in html or 'data-block="media-row"' in html
    assert 'data-block="layout-screen"' not in html
    assert 'data-edition="portfolio"' not in html
    assert 'data-pattern="page-' not in html


def test_portfolio_web_shape(portfolio_ws: tuple[Path, dict]) -> None:
    ws, trip = portfolio_ws
    html = render_html(
        trip,
        export_mode="draft",
        trip_root=ws,
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert 'data-edition="portfolio"' in html
    assert 'data-pattern="page-' in html
    assert 'data-block="chapter-header"' not in html
    assert 'data-block="chapter-separator"' not in html
    assert 'data-block="divider-place"' not in html


def test_journal_render_imports_journal_screens(journal_ws: tuple[Path, dict]) -> None:
    ws, trip = journal_ws
    render_trip(
        ws / "trip.json",
        ws,
        trip=trip,
        validate=False,
        copy_css=True,
        write_index=True,
        layout_engine="screens",
        export_layout_override="web",
    )
    css = (ws / "journal.css").read_text(encoding="utf-8")
    assert "journal-screens.css" in css
    assert "portfolio-pages.css" not in css
    assert (ws / "journal-screens.css").is_file()
    assert not (ws / "portfolio-pages.css").is_file()
    journal_family = (ws / "journal-screens.css").read_text(encoding="utf-8")
    assert "display: grid" in journal_family
    assert "page-" not in journal_family


def test_portfolio_render_imports_portfolio_pages(portfolio_ws: tuple[Path, dict]) -> None:
    ws, trip = portfolio_ws
    render_trip(
        ws / "trip.json",
        ws,
        trip=trip,
        validate=False,
        copy_css=True,
        write_index=True,
        layout_engine="screens",
        export_layout_override="web",
    )
    css = (ws / "journal.css").read_text(encoding="utf-8")
    assert "portfolio-pages.css" in css
    assert (ws / "portfolio-pages.css").is_file()
    assert not (ws / "journal-screens.css").is_file()
    portfolio_family = (ws / "portfolio-pages.css").read_text(encoding="utf-8")
    assert "display: grid" in portfolio_family
    assert "object-fit: cover" in portfolio_family
    assert "screen-" not in portfolio_family
