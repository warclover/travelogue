"""export.copyDisplay render mode (full vs photos-only)."""

from __future__ import annotations

import json

import pytest

from travelogue.paths import FIXTURES_DIR
from travelogue.render.copy_display import (
    COPY_DISPLAY_PHOTOS,
    is_photos_only,
    resolve_copy_display,
    should_strip_narrative_copy,
)
from travelogue.render.engine import render_html


@pytest.fixture
def copy_locked_trip() -> dict:
    return json.loads((FIXTURES_DIR / "trip.copy_locked.json").read_text(encoding="utf-8"))


def test_resolve_copy_display_defaults_full():
    assert resolve_copy_display({}) == "full"
    assert resolve_copy_display({"export": {}}) == "full"


def test_resolve_copy_display_from_trip():
    trip = {"export": {"copyDisplay": "photos"}}
    assert resolve_copy_display(trip) == "photos"
    assert is_photos_only(resolve_copy_display(trip)) is True


def test_resolve_copy_display_override():
    trip = {"export": {"copyDisplay": "full"}}
    assert resolve_copy_display(trip, override="photos") == "photos"


def test_should_strip_narrative_copy_draft_keeps_dom():
    assert (
        should_strip_narrative_copy(
            photos_only=True,
            include_screenplay=False,
            is_draft=True,
        )
        is False
    )


def test_should_strip_narrative_copy_share_strips():
    assert (
        should_strip_narrative_copy(
            photos_only=True,
            include_screenplay=False,
            is_draft=False,
        )
        is True
    )


def test_render_photos_draft_keeps_narrative_in_dom_for_toggle(copy_locked_trip: dict):
    """Draft + photos: DOM retains copy; CSS/JS toggles visibility (copy-toggle toolbar)."""
    trip = copy_locked_trip
    trip["chapters"][0]["lead"] = "这一章从鸭川开始。"
    photos_html = render_html(
        trip,
        export_mode="draft",
        copy_display_override=COPY_DISPLAY_PHOTOS,
    )

    assert 'data-copy-display="photos"' in photos_html
    assert "copy-toggle.js" in photos_html
    assert 'data-block="hook-line"' in photos_html
    assert trip["meta"]["hook"] in photos_html
    assert "这一章从鸭川开始。" in photos_html
    assert trip["chapters"][0]["lead"] == "这一章从鸭川开始。"


def test_render_photos_share_strips_narrative_copy(copy_locked_trip: dict):
    """Share + photos: narrative omitted from render context (no hook/captions in HTML)."""
    trip = copy_locked_trip
    trip["chapters"][0]["lead"] = "这一章从鸭川开始。"
    full_html = render_html(trip, export_mode="share")
    photos_html = render_html(
        trip,
        export_mode="share",
        copy_display_override=COPY_DISPLAY_PHOTOS,
    )

    assert 'data-block="hook-line"' in full_html
    assert trip["meta"]["hook"] in full_html
    assert "这一章从鸭川开始。" in full_html
    assert "media-card__caption" in full_html

    assert 'data-copy-display="photos"' in photos_html
    assert 'data-block="hook-line"' not in photos_html
    assert trip["meta"]["hook"] not in photos_html
    assert "这一章从鸭川开始。" not in photos_html
    assert "media-card__caption" not in photos_html
    assert "media-row__caption" not in photos_html
    assert 'data-block="epilogue"' not in photos_html
    assert "鞋还是湿的。" not in photos_html

    assert trip["meta"]["title"] in photos_html
    assert 'data-block="chapter-header"' in photos_html
    assert 'data-block="trip-meta"' in photos_html
    assert trip["chapters"][0]["lead"] == "这一章从鸭川开始。"


def test_trip_json_unchanged_after_photos_render(copy_locked_trip: dict):
    hook_before = copy_locked_trip["meta"]["hook"]
    render_html(copy_locked_trip, copy_display_override=COPY_DISPLAY_PHOTOS)
    assert copy_locked_trip["meta"]["hook"] == hook_before
