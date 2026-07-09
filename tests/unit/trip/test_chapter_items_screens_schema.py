"""Schema-safe items[] when layoutEngine=screens."""

from __future__ import annotations

import copy

from travelogue.curation.chapter_items import MAX_CHAPTER_ITEMS, compact_chapter_items_for_screens
from travelogue.curation.layout_planner import aspect_kind_for_asset, build_chapters_from_plan
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.golden_regression import load_golden_trip
from travelogue.services.validate import validate_trip


def test_compact_items_caps_blocks():
    chapters = [
        {
            "screens": [
                {
                    "slots": [
                        {"assetId": f"a{i}"} for i in range(12)
                    ]
                }
            ],
            "items": [{"type": "media-card", "assetId": "x"}] * 20,
        }
    ]
    compact_chapter_items_for_screens(chapters)
    assert len(chapters[0]["items"]) <= MAX_CHAPTER_ITEMS


def test_build_chapters_screens_items_within_schema():
    asset_ids = [f"asset-{i:03d}" for i in range(1, 61)]
    aspects = {aid: "landscape" for aid in asset_ids}
    assets = [
        {"id": aid, "type": "image", "aspectKind": "landscape", "displayFile": f"assets/{aid}.webp"}
        for aid in asset_ids
    ]
    chapters, _ = build_chapters_from_plan(
        asset_ids,
        aspects,
        export_layout="web",
        layout_engine="screens",
        assets=assets,
    )
    assert chapters
    for ch in chapters:
        assert len(ch.get("items") or []) <= MAX_CHAPTER_ITEMS
        assert ch.get("screens")


def test_golden_screens_trip_passes_schema():
    trip = prepare_trip_web_screens(load_golden_trip())
    errs = [e for e in validate_trip(trip, level="schema") if not e.startswith("WARN:")]
    assert not errs, errs


def test_attach_screens_then_compact_passes_schema():
    trip = copy.deepcopy(load_golden_trip())
    trip["exportLayout"] = "web"
    trip["layoutEngine"] = "screens"
    from travelogue.curation.screen_planner import attach_screens_to_chapters

    aspects = {a["id"]: aspect_kind_for_asset(a) for a in trip.get("assets", [])}
    trip["chapters"] = attach_screens_to_chapters(trip.get("chapters", []), aspects)
    compact_chapter_items_for_screens(trip["chapters"])
    errs = [e for e in validate_trip(trip, level="schema") if not e.startswith("WARN:")]
    assert not errs, errs
