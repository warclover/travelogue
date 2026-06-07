"""P17 golden fixture catalog smoke tests."""

from __future__ import annotations

from scripts.phase3_ig2_report import load_fixture_trip
from tests.clustering_fixtures import load_fixture_assets
from tests.p17_golden_fixtures import (
    P17_CONTROLLED_PARITY_FIXTURES,
    P17_LANDSCAPE_FIXTURES,
    P17_PORTRAIT_FIXTURES,
)


def test_p17_golden_fixtures_exist() -> None:
    assert len(P17_PORTRAIT_FIXTURES) >= 2
    assert len(P17_LANDSCAPE_FIXTURES) >= 2
    for fixture_id in P17_CONTROLLED_PARITY_FIXTURES:
        assets = load_fixture_assets(fixture_id)
        assert len(assets) >= 6, fixture_id
        trip = load_fixture_trip(fixture_id)
        assert trip["tripId"] == fixture_id


def test_p17_portrait_fixtures_are_vertical() -> None:
    for fixture_id in P17_PORTRAIT_FIXTURES:
        for asset in load_fixture_assets(fixture_id):
            assert asset["height"] > asset["width"], fixture_id


def test_p17_landscape_fixtures_are_horizontal() -> None:
    for fixture_id in P17_LANDSCAPE_FIXTURES:
        for asset in load_fixture_assets(fixture_id):
            assert asset["width"] > asset["height"], fixture_id
