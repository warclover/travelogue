"""Phase-1 real-trip equivalence (slow; requires trips/ data on disk)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TRIPS = ROOT / "trips"


@pytest.mark.parametrize("trip_id", ["mao", "linzhi"])
def test_phase1_aspect_only_equivalent_on_real_trip(trip_id: str):
    trip_path = TRIPS / trip_id / "trip.json"
    if not trip_path.is_file():
        pytest.skip(f"{trip_path} not present")

    from scripts.phase1_layout_equivalence import compare_trip

    result = compare_trip(trip_path, layout="web")
    assert result["equivalent"], (
        f"{trip_id}: scoring(aspect_match=1.0) differs from legacy — "
        f"screens legacy={result['legacyScreenCount']} scored={result['scoredScreenCount']}"
    )


def test_phase1_results_file_if_present():
    """When acceptance script has been run, recorded results should all pass."""
    path = ROOT / "docs" / "acceptance-records" / "phase1-layout-equivalence.json"
    if not path.is_file():
        pytest.skip("phase1 results not generated yet")
    rows = json.loads(path.read_text(encoding="utf-8"))
    for row in rows:
        assert row.get("equivalent") is True, row.get("tripId")
