"""arcSegment screen-level gradient (Phase 4 M16)."""

from __future__ import annotations

from travelogue.curation.arc_patterns import ARC_FALL, ARC_OPEN, ARC_PEAK, ARC_RISE
from travelogue.curation.arc_screen_tags import (
    screen_arc_segments_for_chapter,
    stamp_screen_arc_segments,
)


def _content_screen(pattern_id: str = "screen-portrait-1", *, asset_id: str = "a0") -> dict:
    return {
        "screenId": f"s-{asset_id}",
        "patternId": pattern_id,
        "slots": [{"assetId": asset_id}],
    }


def _chapter(screens: list[dict], **curation) -> dict:
    ch: dict = {"id": "ch-01", "screens": screens}
    if curation:
        ch["curation"] = curation
    return ch


def test_peak_chapter_caps_peak_screens_at_three() -> None:
    content = [_content_screen(asset_id=f"a{i}") for i in range(67)]
    chapter = _chapter(content, heroAssetId="a33")
    segs = screen_arc_segments_for_chapter(chapter, ARC_PEAK)
    assert len(segs) == 67
    assert segs.count(ARC_PEAK) <= 3
    assert segs[0] == ARC_RISE
    assert segs[-1] == ARC_FALL


def test_peak_chapter_marks_hero_as_peak() -> None:
    content = [_content_screen(asset_id=f"a{i}") for i in range(20)]
    chapter = _chapter(content, heroAssetId="a10")
    segs = screen_arc_segments_for_chapter(chapter, ARC_PEAK)
    assert segs[10] == ARC_PEAK


def test_open_chapter_inherits_segment_for_all_screens() -> None:
    content = [_content_screen(asset_id=f"a{i}") for i in range(10)]
    chapter = _chapter(content)
    segs = screen_arc_segments_for_chapter(chapter, ARC_OPEN)
    assert segs == [ARC_OPEN] * 10


def test_intent_peak_on_non_peak_chapter_tags_hero_only() -> None:
    content = [_content_screen(asset_id=f"a{i}") for i in range(8)]
    chapter = _chapter(content, heroAssetId="a5")
    segs = screen_arc_segments_for_chapter(chapter, ARC_RISE, intent_peak_chapter=True)
    assert segs.count(ARC_PEAK) == 1
    assert segs[5] == ARC_PEAK
    assert segs[0] == ARC_RISE


def test_stamp_skips_breath_screens() -> None:
    trip = {
        "chapters": [
            {
                "id": "ch-01",
                "screens": [
                    _content_screen(asset_id="a1"),
                    {"screenId": "b1", "patternId": "screen-breath-pause", "slots": []},
                    _content_screen(asset_id="a2"),
                ],
            }
        ]
    }
    stamp_screen_arc_segments(trip, arc_profile="dynamic")
    screens = trip["chapters"][0]["screens"]
    assert screens[0]["arcSegment"] == ARC_OPEN
    assert "arcSegment" not in screens[1]
    assert screens[2]["arcSegment"] == ARC_OPEN


def test_stamp_three_chapter_dynamic_middle_gets_peak_gradient() -> None:
    trip = {
        "chapters": [
            _chapter([_content_screen(asset_id=f"a{i}") for i in range(5)]),
            _chapter([_content_screen(asset_id=f"b{i}") for i in range(67)], heroAssetId="b30"),
            _chapter([_content_screen(asset_id=f"c{i}") for i in range(5)]),
        ]
    }
    stamp_screen_arc_segments(trip, arc_profile="dynamic")
    ch2_segs = [
        sc.get("arcSegment")
        for sc in trip["chapters"][1]["screens"]
        if sc.get("slots")
    ]
    assert ch2_segs.count(ARC_PEAK) <= 3
    assert ch2_segs.count(ARC_PEAK) >= 1


def test_stamp_intent_peak_chapter_sets_curation_flag() -> None:
    trip = {
        "userNotes": "第2天最难忘",
        "chapters": [
            _chapter([_content_screen(asset_id="a1")]),
            _chapter([_content_screen(asset_id=f"b{i}") for i in range(6)], heroAssetId="b3"),
            _chapter([_content_screen(asset_id="c1")]),
        ],
    }
    stamp_screen_arc_segments(trip, arc_profile="dynamic")
    ch2 = trip["chapters"][1]
    assert ch2["curation"]["intentPeakChapter"] is True
    segs = [sc["arcSegment"] for sc in ch2["screens"]]
    assert segs.count(ARC_PEAK) == 1
    assert segs[3] == ARC_PEAK
