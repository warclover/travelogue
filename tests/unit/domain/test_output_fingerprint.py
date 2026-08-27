"""OLT M1 · four-part fingerprints (QA-OLT-02 / AC-OLT-08/09/27).

Clones ``trip.render_golden.json`` only (BLK-OLT-07). No dogfood / editorial fixtures.
"""

from __future__ import annotations

import copy

import pytest

from travelogue.domain.output_fingerprint import (
    copy_fp,
    options_fp,
    source_snapshot,
    structure_fp,
)
from travelogue.export.output_ledger import lookup_output_meta
from travelogue.render.golden_regression import load_golden_trip

pytestmark = [pytest.mark.unit, pytest.mark.pipeline_isolation]


def _clone(*, edition: str = "journal") -> dict:
    trip = copy.deepcopy(load_golden_trip())
    studio = trip.setdefault("studio", {})
    studio["edition"] = edition
    if edition == "portfolio":
        studio["portfolio"] = {"pageCount": 32}
    return trip


def _is_ready(trip: dict, profile: str, recorded: dict) -> bool:
    meta = lookup_output_meta(profile)
    assert meta is not None
    current = source_snapshot(
        trip, bundle_fp=str(recorded["bundleFp"]), stale_options=meta.stale_options
    )
    key = {
        "structure": "structureFp",
        "copy": "copyFp",
        "bundle": "bundleFp",
        "options": "optionsFp",
    }
    for segment in meta.stale_inputs:
        if current[key[segment]] != recorded[key[segment]]:
            return False
    return True


def test_same_trip_twice_is_stable() -> None:
    trip = _clone()
    assert structure_fp(trip) == structure_fp(trip)
    assert copy_fp(trip) == copy_fp(trip)
    assert options_fp(trip, ("longshotDensity",)) == options_fp(
        trip, ("longshotDensity",)
    )


def test_pattern_id_changes_structure_only() -> None:
    trip = _clone()
    before_s, before_c = structure_fp(trip), copy_fp(trip)
    trip["chapters"][0]["patternId"] = "changed-open"
    assert structure_fp(trip) != before_s
    assert copy_fp(trip) == before_c


def test_caption_changes_copy_only() -> None:
    trip = _clone()
    before_s, before_c = structure_fp(trip), copy_fp(trip)
    trip["chapters"][0]["items"][0]["caption"] = "改过的图注"
    assert copy_fp(trip) != before_c
    assert structure_fp(trip) == before_s


def test_cover_asset_changes_structure() -> None:
    trip = _clone()
    before = structure_fp(trip)
    trip["coverAssetId"] = "asset-001"
    assert structure_fp(trip) != before


def test_updated_at_does_not_change_fingerprints() -> None:
    trip = _clone()
    snap = (
        structure_fp(trip),
        copy_fp(trip),
        options_fp(trip, ("copyDisplay", "breathMode", "longshotDensity")),
    )
    trip["updatedAt"] = "2099-01-01T00:00:00Z"
    trip["status"] = "rendered"
    assert (
        structure_fp(trip),
        copy_fp(trip),
        options_fp(trip, ("copyDisplay", "breathMode", "longshotDensity")),
    ) == snap


def test_longshot_density_stays_out_of_structure() -> None:
    trip = _clone()
    before = structure_fp(trip)
    trip.setdefault("export", {})["longshotDensity"] = "compact"
    assert structure_fp(trip) == before
    assert options_fp(trip, ("longshotDensity",)) != options_fp(
        {"export": {}}, ("longshotDensity",)
    )


def test_longshot_density_does_not_stale_portfolio_pages() -> None:
    trip = _clone(edition="portfolio")
    recorded = source_snapshot(
        trip,
        bundle_fp="lse16f41315f6a",
        stale_options=("copyDisplay", "breathMode"),
    )
    assert _is_ready(trip, "portfolio_pages", recorded)
    trip.setdefault("export", {})["longshotDensity"] = "compact"
    assert _is_ready(trip, "portfolio_pages", recorded)
    scroll = source_snapshot(
        trip,
        bundle_fp="lse16f41315f6a",
        stale_options=("copyDisplay", "breathMode", "longshotDensity"),
    )
    trip["export"]["longshotDensity"] = "default"
    assert not _is_ready(trip, "wechat_moments", scroll)


def test_journal_and_portfolio_clones_are_distinct() -> None:
    journal = _clone(edition="journal")
    portfolio = _clone(edition="portfolio")
    assert structure_fp(journal) != structure_fp(portfolio)
