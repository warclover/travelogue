"""Narrate --chapter-id scope."""

from __future__ import annotations

import json

import pytest

from travelogue.paths import FIXTURES_DIR
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.services.narrate import NarrateError, run_narrate


def _screens_trip() -> dict:
    trip = json.loads((FIXTURES_DIR / "trip.render_golden.json").read_text(encoding="utf-8"))
    return prepare_trip_web_screens(trip)


def test_narrate_chapter_dry_run_skips_meta() -> None:
    trip = _screens_trip()
    trip["meta"]["hook"] = ""
    result = run_narrate(
        trip,
        provider="deepseek",
        dry_run=True,
        chapter_id="ch-01",
        scope="full",
    )
    assert "meta.hook" not in result.fields_updated
    assert any("assets[" in f for f in result.fields_updated)


def test_narrate_unknown_chapter_raises() -> None:
    trip = _screens_trip()
    with pytest.raises(NarrateError, match="E_NARRATE_CHAPTER"):
        run_narrate(trip, provider="deepseek", dry_run=True, chapter_id="missing")
