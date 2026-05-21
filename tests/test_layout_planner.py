"""Layout planner: aspect kinds and row packing."""

from __future__ import annotations

from travelogue.curation.layout_planner import (
    _apply_gallery_layout,
    _card,
    _row,
    plan_chapter_items,
    summarize_orientations,
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


def test_gallery_layout_keeps_cards_on_mobile():
    cards = [_card("c1"), _card("c2"), _card("c3")]
    merged = _apply_gallery_layout(cards, export_layout="mobile")
    assert merged == cards
    assert not any(it.get("type") == "media-scroll" for it in merged)
