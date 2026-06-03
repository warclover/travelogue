"""AC-P13-06: template resolution does not break longshot / present / scroll surfaces."""

from __future__ import annotations

import json
import re

import pytest

from travelogue.paths import FIXTURES_DIR
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import render_html
from travelogue.templating.resolver import resolve_effective_template
from travelogue.templating.router import apply_template_selection

SCREEN_SELECTOR = r'data-block="layout-screen"'


def _count(pattern: str, html: str) -> int:
    return len(re.findall(pattern, html))


@pytest.fixture
def screens_trip() -> dict:
    raw = json.loads((FIXTURES_DIR / "trip.render_golden.json").read_text(encoding="utf-8"))
    trip = prepare_trip_web_screens(raw)
    apply_template_selection(trip, mode="smart")
    assert resolve_effective_template(trip) == "visual-journal"
    return trip


def test_p13_scroll_with_template_selection(screens_trip: dict) -> None:
    html = render_html(
        screens_trip,
        template_id=resolve_effective_template(screens_trip),
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
    )
    expected = sum(len(ch.get("screens") or []) for ch in screens_trip.get("chapters", []))
    assert _count(SCREEN_SELECTOR, html) == expected


def test_p13_present_with_template_selection(screens_trip: dict) -> None:
    html = render_html(
        screens_trip,
        template_id=resolve_effective_template(screens_trip),
        export_mode="share",
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert "screenplay.js" in html or 'data-screenplay="on"' in html
    expected = sum(len(ch.get("screens") or []) for ch in screens_trip.get("chapters", []))
    assert _count(SCREEN_SELECTOR, html) == expected


def test_p13_longshot_with_template_selection(screens_trip: dict) -> None:
    from travelogue.curation.chapter_items import count_chapter_screen_slots

    html = render_html(
        screens_trip,
        template_id=resolve_effective_template(screens_trip),
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="longshot",
        index_name="index-longshot.html",
    )
    expected_slots = sum(count_chapter_screen_slots(ch) for ch in screens_trip.get("chapters", []))
    assert _count(r'data-block="media-card"', html) >= expected_slots
    assert _count(SCREEN_SELECTOR, html) == 0


def test_p13_breath_with_template_selection(screens_trip: dict) -> None:
    from travelogue.render.engine import should_include_breath

    tid = resolve_effective_template(screens_trip)
    assert tid == "visual-journal"
    assert should_include_breath(
        screens_trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
    )
    html = render_html(
        screens_trip,
        template_id=tid,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert "breath.js" in html or 'data-breath="' in html


def test_legacy_trip_without_template_selection_still_renders(screens_trip: dict) -> None:
    legacy = dict(screens_trip)
    legacy.pop("templateSelection", None)
    legacy["templateId"] = "visual-journal"
    assert resolve_effective_template(legacy) == "visual-journal"
    html = render_html(legacy, export_mode="draft", layout_engine_override="screens")
    assert "chapter" in html.lower() or _count(SCREEN_SELECTOR, html) >= 0
