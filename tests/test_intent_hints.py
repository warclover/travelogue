"""M19 · editorial intent hints and curate scoring."""

from __future__ import annotations

from travelogue.curation.curate_scoring import (
    anchor_match_multiplier,
    effective_hero_score,
    pick_chapter_hero,
)
from travelogue.curation.intent_hints import (
    apply_editorial_intent_hints,
    arc_segment_for_chapter_with_intent,
    evaluate_intent_keyword_coverage,
    extract_user_notes_keywords,
    peak_chapter_hints,
)
from travelogue.curation.arc_patterns import ARC_RISE


def test_extract_user_notes_keywords() -> None:
    words = extract_user_notes_keywords("带娃慢走，不要导游词")
    assert "带娃" in words
    assert "慢走" in words


def test_peak_chapter_hints_day_marker() -> None:
    assert peak_chapter_hints("第2天最难忘", 4) == {2}


def test_peak_chapter_hints_climax_fallback() -> None:
    assert peak_chapter_hints("高潮在中间", 5) == {3}


def test_apply_editorial_intent_hints() -> None:
    trip = {
        "userNotes": "带娃慢走",
        "assets": [{"id": "a1", "userTier": "featured"}],
        "intent": {"folders": {"featuredDetected": True}},
        "curation": {"intentHints": {"planCities": ["京都"]}},
    }
    hints = apply_editorial_intent_hints(trip)
    assert hints["planCities"] == ["京都"]
    assert "带娃" in hints["userNotesKeywords"]
    assert hints["featuredBoost"] is True


def test_arc_segment_for_chapter_with_intent_uses_profile_not_intent_override() -> None:
    seg = arc_segment_for_chapter_with_intent(2, 4, profile="dynamic", peak_chapters={2})
    assert seg == ARC_RISE


def test_anchor_match_multiplier() -> None:
    asset = {"id": "a1", "tags": ["temple", "雨"], "width": 1200, "height": 800}
    assert anchor_match_multiplier(asset, ["雨"]) > 1.0
    assert anchor_match_multiplier(asset, ["雪"]) == 1.0


def test_effective_hero_score_anchor_boost() -> None:
    asset = {
        "id": "a1",
        "width": 1600,
        "height": 900,
        "mediaClass": "photo",
        "tags": ["landscape"],
    }
    tagged = {**asset, "tags": ["landscape", "寺"]}
    plain_score = effective_hero_score(asset)
    boosted_score = effective_hero_score(tagged, memory_anchors=["寺"])
    plain_with_anchor = effective_hero_score(asset, memory_anchors=["寺"])
    assert boosted_score > plain_score
    assert plain_with_anchor == plain_score


def test_pick_chapter_hero_prefers_anchor_match() -> None:
    assets_by_id = {
        "plain": {
            "id": "plain",
            "width": 1600,
            "height": 900,
            "mediaClass": "photo",
            "tags": ["street"],
        },
        "tagged": {
            "id": "tagged",
            "width": 1580,
            "height": 890,
            "mediaClass": "photo",
            "tags": ["temple", "寺"],
        },
    }
    hero = pick_chapter_hero(
        ["plain", "tagged"],
        assets_by_id,
        memory_anchors=["寺"],
    )
    assert hero == "tagged"


def test_evaluate_intent_keyword_coverage() -> None:
    trip = {
        "userNotes": "带娃慢走",
        "curation": {"intentHints": {"userNotesKeywords": ["带娃", "慢走"]}},
        "chapters": [
            {"title": "抵达", "lead": "带娃的一天"},
            {"title": "尾声", "lead": "普通结尾"},
            {"title": "补记", "lead": "慢走回忆"},
        ],
    }
    out = evaluate_intent_keyword_coverage(trip)
    assert out["hitChapters"] == 2
    assert out["ratio"] >= 0.6
    assert out["passesGP403"] is True
