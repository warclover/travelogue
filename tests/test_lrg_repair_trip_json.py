"""Unit tests for scripts/lrg_repair_trip_json.py."""

from __future__ import annotations

import pytest

from scripts.lrg_repair_trip_json import backfill_missing_screen_ids


@pytest.mark.unit
def test_backfill_missing_screen_ids_only_on_tmp_dict() -> None:
    trip = {
        "chapters": [
            {
                "id": "ch-02",
                "screens": [
                    {"screenId": "ch-02-sc-01", "patternId": "screen-landscape-1"},
                    {"patternId": "screen-portrait-1"},
                ],
            }
        ]
    }
    fixed = backfill_missing_screen_ids(trip)
    assert fixed == ["ch-02-sc-gap-01"]
    assert trip["chapters"][0]["screens"][1]["screenId"] == "ch-02-sc-gap-01"
