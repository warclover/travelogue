"""Chapter items[] and screens[] must cover the same asset ids."""

from __future__ import annotations

import pytest

from travelogue.curation.chapter_items import item_stub_for_screen
from travelogue.layout_engine.planner.screen_planner import (
    _collect_asset_ids_from_chapter,
    attach_screens_to_chapters,
)


def _stub(pattern_id: str, asset_ids: list[str]) -> dict:
    screen = {
        "patternId": pattern_id,
        "slots": [{"assetId": aid} for aid in asset_ids],
    }
    return item_stub_for_screen(screen) or {}


@pytest.mark.parametrize(
    ("pattern_id", "asset_ids", "expected"),
    [
        # Pure single-family grids keep their family label.
        ("screen-portrait-3", ["p1", "p2", "p3"], "portrait-triple"),
        ("screen-portrait-2", ["p1", "p2"], "portrait-pair"),
        ("screen-square-3", ["s1", "s2", "s3"], "square-triple"),
        ("screen-landscape-4", ["a", "b", "c", "d"], "landscape-triple"),
        # Mixed and mosaic screens are landscape-dominant: must NOT be labelled
        # portrait-* just because the pattern id contains the "portrait" token.
        ("screen-portrait-1-landscape-2", ["p1", "l1", "l2"], "landscape-triple"),
        (
            "screen-mosaic-5-main-portrait-3land",
            ["p1", "m", "l1", "l2", "l3"],
            "landscape-triple",
        ),
    ],
)
def test_row_layout_label_for_mixed_and_mosaic_screens(
    pattern_id: str, asset_ids: list[str], expected: str
) -> None:
    assert _stub(pattern_id, asset_ids)["rowLayout"] == expected


def _asset_ids_from_screens(ch: dict) -> set[str]:
    ids: set[str] = set()
    for sc in ch.get("screens") or []:
        for slot in sc.get("slots") or []:
            aid = slot.get("assetId")
            if aid:
                ids.add(aid)
    return ids


def test_attach_screens_items_same_asset_set():
    chapters = [
        {
            "id": "ch-01",
            "items": [
                {"type": "media-card", "assetId": "p1"},
                {
                    "type": "media-row",
                    "assetIds": ["l1", "l2", "l3"],
                    "rowLayout": "landscape-triple",
                },
            ],
        },
    ]
    aspects = {
        "p1": "portrait",
        "l1": "landscape",
        "l2": "landscape",
        "l3": "landscape",
    }
    out = attach_screens_to_chapters(
        chapters,
        aspects,
        plan_scope="day",
        day_buckets=[["p1", "l1", "l2", "l3"]],
    )
    from_items = set(_collect_asset_ids_from_chapter(out[0]))
    from_screens = _asset_ids_from_screens(out[0])
    assert from_items == from_screens
    assert len(from_screens) >= 1
