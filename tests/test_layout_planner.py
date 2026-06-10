"""Layout planner: aspect kinds and row packing."""

from __future__ import annotations

from travelogue.curation.layout_planner import (
    _apply_gallery_layout,
    _card,
    _row,
    plan_chapter_items,
    portrait_group_sizes,
    summarize_orientations,
)
from travelogue.curation.mobile_layout_state import (
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


def test_mobile_landscapes_stack_in_one_column():
    # 连续 3 横图 → 一列三行纵向拼图（landscape-triple）；全景仍单卡。
    ids = ["l1", "l2", "l3", "pano"]
    aspects = {
        "l1": "landscape",
        "l2": "landscape",
        "l3": "landscape",
        "pano": "panorama",
    }
    items = plan_chapter_items(ids, aspects, export_layout="mobile")
    assert items[0]["type"] == "media-row"
    assert items[0]["rowLayout"] == "landscape-triple"
    assert items[0]["assetIds"] == ["l1", "l2", "l3"]
    assert items[1]["type"] == "media-card"
    assert items[1]["layout"]["slot"] == "panorama"


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


def test_mobile_single_landscape_falls_back_to_card():
    items = plan_chapter_items(["l1"], {"l1": "landscape"}, export_layout="mobile")
    assert len(items) == 1
    assert items[0]["type"] == "media-card"
    assert items[0]["assetId"] == "l1"


def test_mobile_two_landscapes_stack_as_pair():
    ids = ["l0", "l1"]
    aspects = {x: "landscape" for x in ids}
    items = plan_chapter_items(ids, aspects, export_layout="mobile")
    assert len(items) == 1
    assert items[0]["type"] == "media-row"
    assert items[0]["rowLayout"] == "landscape-pair"
    assert items[0]["assetIds"] == ids


def test_mobile_landscape_run_triple_first_then_single_tail():
    # 4 横图 → 三联 + 单卡（仅尾部 1 张落单）。
    ids = [f"l{i}" for i in range(4)]
    aspects = {x: "landscape" for x in ids}
    items = plan_chapter_items(ids, aspects, export_layout="mobile")
    assert items[0]["rowLayout"] == "landscape-triple"
    assert items[0]["assetIds"] == ["l0", "l1", "l2"]
    assert items[1]["type"] == "media-card"
    assert items[1]["assetId"] == "l3"


def test_mobile_five_landscapes_triple_then_pair():
    ids = [f"l{i}" for i in range(5)]
    aspects = {x: "landscape" for x in ids}
    items = plan_chapter_items(ids, aspects, export_layout="mobile")
    assert [it.get("rowLayout") for it in items] == ["landscape-triple", "landscape-pair"]


def test_mobile_portraits_never_collage_even_on_large_trip():
    # 竖版恒单图：禁用任何竖版拼图，无论游记张数。
    ids = [f"p{i}" for i in range(4)]
    aspects = {x: "portrait" for x in ids}
    items = plan_chapter_items(ids, aspects, export_layout="mobile", trip_photo_total=200)
    assert all(it["type"] == "media-card" for it in items)
    assert not any(it.get("type") == "media-row" for it in items)


def test_portrait_group_sizes_pair_first_with_triple_filler():
    # Web 竖版优先级：pair > triple > single（单张仅孤张兜底）。
    assert portrait_group_sizes(1) == [1]
    assert portrait_group_sizes(2) == [2]
    assert portrait_group_sizes(3) == [3]
    assert portrait_group_sizes(4) == [2, 2]
    assert portrait_group_sizes(5) == [2, 3]
    assert portrait_group_sizes(6) == [2, 2, 2]
    assert portrait_group_sizes(7) == [2, 2, 3]


def test_web_four_portraits_prefer_two_pairs():
    ids = [f"p{i}" for i in range(4)]
    aspects = {x: "portrait" for x in ids}
    items = plan_chapter_items(ids, aspects, export_layout="web")
    assert [it["rowLayout"] for it in items] == ["portrait-pair", "portrait-pair"]


def test_web_five_portraits_pair_then_triple():
    ids = [f"p{i}" for i in range(5)]
    aspects = {x: "portrait" for x in ids}
    items = plan_chapter_items(ids, aspects, export_layout="web")
    assert [it["rowLayout"] for it in items] == ["portrait-pair", "portrait-triple"]
