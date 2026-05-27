"""Screen order contract across scroll / present / longshot (PRD-EXPERIENCE E0)."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from travelogue.curation.chapter_items import count_chapter_screen_slots
from travelogue.paths import FIXTURES_DIR, ROOT
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import render_html

SCREEN_SELECTOR = r'data-block="layout-screen"'
CARD_SELECTOR = r'data-block="media-card"'
LINZHI = ROOT / "trips" / "linzhi"
LINZHI_CI = FIXTURES_DIR / "trip.linzhi_screens.json"


def _count(pattern: str, html: str) -> int:
    return len(re.findall(pattern, html))


def _expected_screen_count(trip: dict) -> int:
    return sum(len(ch.get("screens") or []) for ch in trip.get("chapters", []))


def _screen_indices(html: str) -> list[int]:
    return [int(x) for x in re.findall(r'data-screen-index="(\d+)"', html)]


def assert_screen_order_contract(trip: dict, html: str) -> None:
    """Shared E0 / AC-EXP-01 checks for scroll DOM vs trip screens[]."""
    expected = _expected_screen_count(trip)
    assert _count(SCREEN_SELECTOR, html) == expected
    indices = _screen_indices(html)
    assert len(indices) == expected
    assert indices == list(range(1, expected + 1))


@pytest.fixture
def screens_trip() -> dict:
    raw = json.loads((FIXTURES_DIR / "trip.render_golden.json").read_text(encoding="utf-8"))
    return prepare_trip_web_screens(raw)


def test_scroll_screen_count_matches_trip_screens(screens_trip: dict) -> None:
    html = render_html(
        screens_trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert_screen_order_contract(screens_trip, html)


def test_present_uses_same_layout_screen_dom(screens_trip: dict) -> None:
    """screenplay.js collects the same layout-screen nodes as scroll (share surface)."""
    html = render_html(
        screens_trip,
        export_mode="share",
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert "screenplay.js" in html or 'data-screenplay="on"' in html
    assert_screen_order_contract(screens_trip, html)


def test_longshot_card_count_matches_screen_slots(screens_trip: dict) -> None:
    html = render_html(
        screens_trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="longshot",
        index_name="index-longshot.html",
    )
    expected_slots = sum(count_chapter_screen_slots(ch) for ch in screens_trip.get("chapters", []))
    cards = _count(CARD_SELECTOR, html)
    # Longshot 展平 screens slots；fixture 可能含封面等额外 card，至少覆盖全部 slot
    assert cards >= expected_slots
    assert _count(SCREEN_SELECTOR, html) == 0


def test_screen_index_attributes_are_sequential(screens_trip: dict) -> None:
    html = render_html(
        screens_trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert_screen_order_contract(screens_trip, html)


@pytest.fixture
def linzhi_ci_workspace(tmp_path: Path) -> tuple[Path, dict]:
    trip = json.loads(LINZHI_CI.read_text(encoding="utf-8"))
    ws = tmp_path / "trips" / "linzhi-ci"
    ws.mkdir(parents=True)
    from travelogue.paths import TEMPLATE_VISUAL_JOURNAL

    shutil.copytree(TEMPLATE_VISUAL_JOURNAL / "assets", ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws, trip


def test_linzhi_ci_screen_order_contract(linzhi_ci_workspace: tuple[Path, dict]) -> None:
    """E0-3 / AC-EXP-01: CI-sized linzhi fixture (5章 · 20屏) 屏序契约."""
    ws, trip = linzhi_ci_workspace
    html = render_html(
        trip,
        export_mode="share",
        trip_root=ws,
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert_screen_order_contract(trip, html)
    assert 'data-screenplay="on"' in html
    assert len(trip["chapters"]) == 5


@pytest.mark.skipif(not (LINZHI / "trip.json").is_file(), reason="local trips/linzhi missing")
def test_linzhi_screen_order_contract() -> None:
    """E0-3 / AC-EXP-01: 林芝 web scroll 屏序与 trip screens[] 一致."""
    trip = json.loads((LINZHI / "trip.json").read_text(encoding="utf-8"))
    html = render_html(
        trip,
        export_mode="share",
        trip_root=LINZHI,
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert_screen_order_contract(trip, html)
    assert 'data-screenplay="on"' in html
