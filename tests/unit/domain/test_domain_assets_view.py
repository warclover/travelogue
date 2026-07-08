"""Tests for domain assets view (M-C4)."""

from __future__ import annotations

import pytest

from travelogue.domain.assets_view import (
    assets_by_id,
    featured_asset_ids,
    get_asset,
    promote_asset_to_featured,
    set_asset_tier,
)


def test_assets_by_id_and_get_asset() -> None:
    trip = {"assets": [{"id": "a1", "tier": "material"}, {"id": "a2"}]}
    assert list(assets_by_id(trip)) == ["a1", "a2"]
    assert get_asset(trip, "a1")["tier"] == "material"
    assert get_asset(trip, "missing") is None


def test_set_asset_tier_and_promote() -> None:
    trip = {"assets": [{"id": "a1", "tier": "material"}]}
    set_asset_tier(trip, "a1", "hero")
    assert trip["assets"][0]["tier"] == "hero"
    promote_asset_to_featured(trip, "a1")
    assert trip["assets"][0]["tier"] == "featured"
    assert featured_asset_ids(trip) == ["a1"]


def test_set_asset_tier_unknown_raises() -> None:
    with pytest.raises(KeyError):
        set_asset_tier({}, "missing", "featured")
