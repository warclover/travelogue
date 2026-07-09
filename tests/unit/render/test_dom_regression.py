"""DOM structure regression vs golden.html."""

from __future__ import annotations

import pytest

from travelogue.paths import GOLDEN_HTML
from travelogue.render.engine import render_html
from travelogue.render.golden_regression import (
    check_golden_dom,
    check_golden_structure,
    load_golden_trip,
    pattern_sequence,
)


@pytest.fixture
def trip() -> dict:
    return load_golden_trip()


def test_pattern_sequence_matches_golden(trip: dict) -> None:
    golden = GOLDEN_HTML.read_text(encoding="utf-8")
    rendered = render_html(trip, export_mode="draft")
    assert pattern_sequence(rendered) == pattern_sequence(golden)


def test_golden_structure_contract(trip: dict) -> None:
    assert not check_golden_structure(trip)


def test_block_inventory_matches_golden(trip: dict) -> None:
    assert not check_golden_dom(trip=trip)
