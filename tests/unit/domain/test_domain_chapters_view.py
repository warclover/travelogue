"""Tests for domain chapters view (M-C4)."""

from __future__ import annotations

from travelogue.domain.chapters_view import (
    chapter_ids,
    find_screen,
    iter_screens,
    screen_asset_ids,
)


def test_chapter_traversal_helpers() -> None:
    trip = {
        "chapters": [
            {
                "id": "c1",
                "screens": [
                    {
                        "screenId": "s1",
                        "slots": [{"assetId": "a1"}, {"assetId": "a2"}],
                    }
                ],
            },
            {"id": "c2", "screens": [{"screenId": "s2", "slots": []}]},
        ]
    }
    assert chapter_ids(trip) == ["c1", "c2"]
    screens = list(iter_screens(trip))
    assert len(screens) == 2
    assert screens[0][0] == "c1"
    assert screens[0][1]["screenId"] == "s1"
    assert screen_asset_ids(trip) == ["a1", "a2"]
    found = find_screen(trip, "s1")
    assert found is not None
    ch, scr = found
    assert ch["id"] == "c1"
    assert scr["screenId"] == "s1"
    assert find_screen(trip, "missing") is None
