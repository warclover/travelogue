"""Layout planner: aspect kinds and row packing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from travelogue.curation.layout_planner import (
    _apply_gallery_layout,
    _card,
    _row,
    plan_chapter_items,
    summarize_orientations,
)
from travelogue.curation.mobile_layout_state import (
    MOBILE_GRID4_ROW_LAYOUT,
    MOBILE_GRID8_ROW_LAYOUT,
    MOBILE_PERSON_GRID4_HINT,
    MOBILE_PUZZLE_MIN_PHOTOS,
    MobilePuzzlePlannerState,
    mobile_grid4_max_for_trip,
    mobile_grid8_max_for_trip,
)
from travelogue.media.image_ops import classify_aspect


def _asset(aid: str, w: int, h: int) -> dict:
    return {"id": aid, "width": w, "height": h, "type": "image", "aspectKind": classify_aspect(w, h)}


def test_classify_panorama_and_tall():
    assert classify_aspect(3000, 1000) == "panorama"
    assert classify_aspect(900, 1600) == "portrait"
    assert classify_aspect(900, 2500) == "tall"
    assert classify_aspect(1080, 1080) == "square"


def test_summarize_five_kinds():
    assets = [
        _asset("a1", 2000, 1000),
        _asset("a2", 1000, 1000),
        _asset("a3", 900, 1600),
        _asset("a4", 800, 2400),
    ]
    s = summarize_orientations(assets, export_layout="mobile")
    assert s.panorama == 1
    assert s.square == 1
    assert s.portrait == 1
    assert s.tall == 1


def test_mobile_landscapes_are_single_cards():
    ids = ["l1", "l2", "l3", "pano"]
    aspects = {
        "l1": "landscape",
        "l2": "landscape",
        "l3": "landscape",
        "pano": "panorama",
    }
    items = plan_chapter_items(ids, aspects, export_layout="mobile")
    assert all(it["type"] == "media-card" for it in items)
    assert [it["assetId"] for it in items] == ids
    assert items[3]["layout"]["slot"] == "panorama"
    assert "slot" not in items[0]["layout"]
    assert not any(it.get("type") == "media-row" for it in items)


def test_mobile_panorama_alone():
    items = plan_chapter_items(["p1"], {"p1": "panorama"}, export_layout="mobile")
    assert items[0]["type"] == "media-card"
    assert items[0]["layout"]["slot"] == "panorama"


def test_mobile_squares_are_single_cards():
    ids = ["s1", "s2", "s3"]
    aspects = {x: "square" for x in ids}
    items = plan_chapter_items(ids, aspects, export_layout="mobile")
    assert all(it["type"] == "media-card" for it in items)
    assert all(it["layout"]["slot"] == "square" for it in items)


def test_web_groups_three_portraits():
    ids = ["p1", "p2", "p3", "l1"]
    aspects = {x: "portrait" for x in ("p1", "p2", "p3")}
    aspects["l1"] = "landscape"
    items = plan_chapter_items(ids, aspects, export_layout="web")
    assert items[0]["rowLayout"] == "portrait-triple"
    assert items[0]["assetIds"] == ["p1", "p2", "p3"]
    assert items[1]["type"] == "media-card"


def test_web_groups_two_portraits_as_pair():
    ids = ["p1", "p2", "l1"]
    aspects = {"p1": "portrait", "p2": "portrait", "l1": "landscape"}
    items = plan_chapter_items(ids, aspects, export_layout="web")
    assert items[0]["rowLayout"] == "portrait-pair"
    assert items[1]["type"] == "media-card"


def test_tall_never_paired_on_web():
    ids = ["t1", "p1"]
    aspects = {"t1": "tall", "p1": "portrait"}
    items = plan_chapter_items(ids, aspects, export_layout="web")
    assert items[0]["layout"]["slot"] == "tall"
    assert items[1]["type"] == "media-card"


def test_mobile_portraits_are_single_cards():
    ids = ["p1", "p2", "l1"]
    aspects = {"p1": "portrait", "p2": "portrait", "l1": "landscape"}
    items = plan_chapter_items(ids, aspects, export_layout="mobile")
    assert all(it["type"] == "media-card" for it in items)
    assert items[0]["assetId"] == "p1"


def test_gallery_layout_preserves_media_row_on_web():
    row = _row(["a1", "a2", "a3"], "landscape-triple")
    cards = [_card("c1"), _card("c2"), _card("c3")]
    merged = _apply_gallery_layout(cards + [row], export_layout="web")
    assert merged[0]["type"] == "media-scroll"
    assert merged[1]["type"] == "media-row"
    assert merged[1]["assetIds"] == ["a1", "a2", "a3"]


def test_gallery_layout_scroll_on_mobile():
    cards = [_card("c1"), _card("c2"), _card("c3")]
    merged = _apply_gallery_layout(cards, export_layout="mobile")
    assert len(merged) == 1
    assert merged[0]["type"] == "media-scroll"
    assert merged[0]["assetIds"] == ["c1", "c2", "c3"]


def test_mobile_grid8_limits_by_trip_size():
    assert mobile_grid8_max_for_trip(30) == 0
    assert mobile_grid8_max_for_trip(31) == 2
    assert mobile_grid8_max_for_trip(100) == 5
    assert mobile_grid8_max_for_trip(200) == 8


def test_mobile_grid4_limits_by_trip_size():
    assert mobile_grid4_max_for_trip(30) == 0
    assert mobile_grid4_max_for_trip(31) == 4
    assert mobile_grid4_max_for_trip(100) == 8
    assert mobile_grid4_max_for_trip(200) == 12


def test_mobile_no_grid8_when_trip_at_most_30():
    ids = [f"l{i}" for i in range(8)]
    aspects = {x: "landscape" for x in ids}
    items = plan_chapter_items(
        ids,
        aspects,
        export_layout="mobile",
        trip_photo_total=MOBILE_PUZZLE_MIN_PHOTOS,
    )
    assert all(it["type"] == "media-card" for it in items)


def test_mobile_grid8_on_eight_landscape_burst():
    ids = [f"l{i}" for i in range(8)]
    aspects = {x: "landscape" for x in ids}
    base = datetime(2025, 7, 1, 12, 0, 0, tzinfo=UTC)
    assets = {
        aid: {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
        }
        for i, aid in enumerate(ids)
    }
    items = plan_chapter_items(
        ids,
        aspects,
        export_layout="mobile",
        assets=assets,
        trip_photo_total=50,
    )
    assert len(items) == 1
    assert items[0]["type"] == "media-row"
    assert items[0]["rowLayout"] == MOBILE_GRID8_ROW_LAYOUT
    assert items[0]["assetIds"] == ids


def test_mobile_grid8_ten_landscapes_yields_grid_plus_two_cards():
    ids = [f"l{i}" for i in range(10)]
    aspects = {x: "landscape" for x in ids}
    base = datetime(2025, 7, 1, 12, 0, 0, tzinfo=UTC)
    assets = {
        aid: {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
        }
        for i, aid in enumerate(ids)
    }
    items = plan_chapter_items(
        ids,
        aspects,
        export_layout="mobile",
        assets=assets,
        trip_photo_total=50,
    )
    assert items[0]["rowLayout"] == MOBILE_GRID8_ROW_LAYOUT
    assert items[1]["type"] == "media-card"
    assert items[2]["type"] == "media-card"


def test_mobile_grid4_on_four_portrait_burst():
    ids = [f"p{i}" for i in range(4)]
    aspects = {x: "portrait" for x in ids}
    base = datetime(2025, 8, 1, 9, 0, 0, tzinfo=UTC)
    assets = {
        aid: {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
        }
        for i, aid in enumerate(ids)
    }
    items = plan_chapter_items(
        ids,
        aspects,
        export_layout="mobile",
        assets=assets,
        trip_photo_total=50,
    )
    assert len(items) == 1
    assert items[0]["rowLayout"] == MOBILE_GRID4_ROW_LAYOUT
    assert items[0]["assetIds"] == ids
    assert "layoutHint" not in items[0]


def test_mobile_grid4_person_hint_when_tagged():
    ids = [f"p{i}" for i in range(4)]
    aspects = {x: "portrait" for x in ids}
    base = datetime(2025, 8, 1, 9, 0, 0, tzinfo=UTC)
    assets = {
        aid: {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
            "tags": ["person"],
        }
        for i, aid in enumerate(ids)
    }
    items = plan_chapter_items(
        ids,
        aspects,
        export_layout="mobile",
        assets=assets,
        trip_photo_total=50,
    )
    assert items[0]["layoutHint"] == MOBILE_PERSON_GRID4_HINT


def test_mobile_grid4_five_portraits_grid_plus_card():
    ids = [f"p{i}" for i in range(5)]
    aspects = {x: "portrait" for x in ids}
    base = datetime(2025, 8, 1, 9, 0, 0, tzinfo=UTC)
    assets = {
        aid: {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
        }
        for i, aid in enumerate(ids)
    }
    items = plan_chapter_items(
        ids,
        aspects,
        export_layout="mobile",
        assets=assets,
        trip_photo_total=50,
    )
    assert items[0]["rowLayout"] == MOBILE_GRID4_ROW_LAYOUT
    assert items[1]["type"] == "media-card"


def test_mobile_no_grid4_when_trip_at_most_30():
    ids = [f"p{i}" for i in range(4)]
    aspects = {x: "portrait" for x in ids}
    items = plan_chapter_items(
        ids,
        aspects,
        export_layout="mobile",
        trip_photo_total=MOBILE_PUZZLE_MIN_PHOTOS,
    )
    assert all(it["type"] == "media-card" for it in items)


def test_mobile_grid8_respects_trip_quota():
    ids = [f"l{i}" for i in range(24)]
    aspects = {x: "landscape" for x in ids}
    base = datetime(2025, 7, 1, 12, 0, 0, tzinfo=UTC)
    assets = {
        aid: {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
        }
        for i, aid in enumerate(ids)
    }
    items = plan_chapter_items(
        ids,
        aspects,
        export_layout="mobile",
        assets=assets,
        trip_photo_total=50,
    )
    grids = [it for it in items if it.get("rowLayout") == MOBILE_GRID8_ROW_LAYOUT]
    assert len(grids) == 1
    assert sum(1 for it in items if it["type"] == "media-card") == 16


def test_mobile_grid8_per_chapter_then_trip_quota():
    ids_a = [f"a{i}" for i in range(8)]
    ids_b = [f"b{i}" for i in range(8)]
    aspects = {x: "landscape" for x in ids_a + ids_b}
    base = datetime(2025, 7, 1, 12, 0, 0, tzinfo=UTC)
    assets = {}
    for i, aid in enumerate(ids_a + ids_b):
        assets[aid] = {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
        }
    state = MobilePuzzlePlannerState.from_trip_total(50)
    items_a = plan_chapter_items(
        ids_a, aspects, export_layout="mobile", assets=assets, trip_photo_total=50, puzzle_state=state
    )
    state.begin_chapter()
    items_b = plan_chapter_items(
        ids_b, aspects, export_layout="mobile", assets=assets, trip_photo_total=50, puzzle_state=state
    )
    assert sum(1 for it in items_a + items_b if it.get("rowLayout") == MOBILE_GRID8_ROW_LAYOUT) == 2
