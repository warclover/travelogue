"""Dedicated longshot surface: index-longshot.html from screens[]."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from travelogue.curation.chapter_items import (
    count_chapter_screen_slots,
    flatten_screens_to_items,
)
from travelogue.paths import FIXTURES_DIR
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import (
    LONGSHOT_INDEX_NAME,
    render_html,
    render_trip,
    should_include_long_shot,
)


@pytest.fixture
def screens_trip() -> dict:
    trip = json.loads((FIXTURES_DIR / "trip.render_golden.json").read_text(encoding="utf-8"))
    return prepare_trip_web_screens(trip)


def test_flatten_screens_one_card_per_slot(screens_trip: dict) -> None:
    ch = screens_trip["chapters"][0]
    flat = flatten_screens_to_items(ch)
    assert len(flat) == count_chapter_screen_slots(ch)
    assert all(it["type"] == "media-card" for it in flat)


def test_longshot_surface_contract(screens_trip: dict) -> None:
    assert should_include_long_shot(
        screens_trip,
        layout_engine_override="screens",
        export_layout_override="longshot",
    )
    html = render_html(
        screens_trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="longshot",
    )
    assert 'data-layout="longshot"' in html
    assert 'data-longshot="on"' in html
    assert 'data-layout-engine="screens"' not in html
    assert 'data-block="layout-screen"' not in html
    assert 'data-block="media-card"' in html
    assert "longshot-save" in html
    assert "screenplay-start" not in html


def _expected_longshot_cards(trip: dict) -> int:
    total = 0
    for ch in trip.get("chapters") or []:
        if ch.get("screens"):
            total += count_chapter_screen_slots(ch)
            continue
        for it in ch.get("items") or []:
            if it.get("type") == "media-card":
                total += 1
            elif it.get("type") in ("media-row", "media-scroll"):
                total += len(it.get("assetIds") or [])
    return total


def test_longshot_image_count_matches_screen_slots(screens_trip: dict) -> None:
    expected = _expected_longshot_cards(screens_trip)
    html = render_html(
        screens_trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="longshot",
    )
    cards = len(re.findall(r'data-block="media-card"', html))
    assert cards == expected


def test_bridge_points_to_longshot_sidecar(screens_trip: dict) -> None:
    html = render_html(
        screens_trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert f'data-longshot-mobile-url="{LONGSHOT_INDEX_NAME}"' in html


def test_render_trip_writes_longshot_sidecar(tmp_path: Path, screens_trip: dict) -> None:
    demo = Path(__file__).resolve().parents[1] / "templates" / "visual-journal" / "assets"
    if not demo.is_dir():
        pytest.skip("demo assets not present")
    ws = tmp_path / "longshot-trip"
    ws.mkdir()
    shutil.copytree(demo, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    (ws / "trip.json").write_text(
        json.dumps(screens_trip, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    render_trip(ws / "trip.json", validate=False, layout_engine="screens")
    longshot_path = ws / LONGSHOT_INDEX_NAME
    assert longshot_path.is_file()
    longshot = longshot_path.read_text(encoding="utf-8")
    assert 'data-longshot="on"' in longshot
    assert 'data-block="layout-screen"' not in longshot
    main = (ws / "index.html").read_text(encoding="utf-8")
    assert f'data-longshot-mobile-url="{LONGSHOT_INDEX_NAME}"' in main
    assert (ws / "longshot.js").is_file()
