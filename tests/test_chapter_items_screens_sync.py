"""Chapter items[] and screens[] must cover the same asset ids."""

from __future__ import annotations

from travelogue.curation.screen_planner import (
    _collect_asset_ids_from_chapter,
    attach_screens_to_chapters,
)


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
