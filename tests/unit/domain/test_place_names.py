"""Direct unit tests for domain.place_names (Arch Opt V2 · M2-A1)."""

from __future__ import annotations

from travelogue.domain.place_names import (
    OVERSEAS_PLACE_HINTS,
    allowed_place_names,
    unauthorized_place_mentions,
)


def test_unauthorized_place_mentions_flags_uncovered_hint():
    hits = unauthorized_place_mentions("雨季的京都", {"斯里兰卡"})
    assert "京都" in hits


def test_unauthorized_place_mentions_allows_covered_hint():
    hits = unauthorized_place_mentions("雨季的京都", {"京都", "大阪"})
    assert hits == []


def test_allowed_place_names_uses_meta_and_exif_not_chapter_curation():
    trip = {
        "meta": {"places": ["斯里兰卡"]},
        "assets": [
            {"id": "a1", "place": {"city": "科伦坡"}},
        ],
        "chapters": [
            {"curation": {"places": ["京都"]}},
        ],
    }
    allowed = allowed_place_names(trip)
    assert "斯里兰卡" in allowed
    assert "科伦坡" in allowed
    assert "京都" not in allowed


def test_overseas_place_hints_nonempty():
    assert "京都" in OVERSEAS_PLACE_HINTS
    assert "巴黎" in OVERSEAS_PLACE_HINTS
