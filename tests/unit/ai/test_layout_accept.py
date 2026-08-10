"""ACP §5.3 · accept layout suggestion → chapter-scoped screens replan."""

from __future__ import annotations

import copy

from travelogue.services.layout_accept import apply_accepted_suggestion_to_chapter


def _portrait(aid: str) -> dict:
    return {"id": aid, "width": 800, "height": 1200}


def _landscape(aid: str) -> dict:
    return {"id": aid, "width": 1200, "height": 800}


def _trip_two_chapters() -> dict:
    return {
        "tripId": "t-accept",
        "assets": [
            _portrait("p1"),
            _portrait("p2"),
            _portrait("p3"),
            _landscape("o1"),
        ],
        "chapters": [
            {
                "id": "ch-01",
                "screens": [
                    {
                        "patternId": "screen-portrait-1",
                        "slots": [
                            {"assetId": "p1"},
                            {"assetId": "p2"},
                            {"assetId": "p3"},
                        ],
                    }
                ],
            },
            {
                "id": "ch-02",
                "screens": [
                    {
                        "patternId": "screen-landscape-1",
                        "slots": [{"assetId": "o1"}],
                    }
                ],
            },
        ],
    }


def test_replan_one_chapter_preserves_others() -> None:
    trip = _trip_two_chapters()
    other_screens_before = copy.deepcopy(trip["chapters"][1]["screens"])
    result = apply_accepted_suggestion_to_chapter(
        trip,
        chapter_id="ch-01",
        suggested_pattern_id="screen-portrait-3",
    )
    assert result["ok"] is True
    assert result["reason"] == "ok"
    # 他章 screens 不变（compact stub 可能补 items，不算结构漂移）
    assert trip["chapters"][1]["id"] == "ch-02"
    assert trip["chapters"][1]["screens"] == other_screens_before
    assert len(trip["chapters"]) == 2
    ch1 = trip["chapters"][0]
    assert ch1["curation"].get("preferredPatternId") == "screen-portrait-3"
    assert ch1["curation"].get("layoutSuggestionAccepted") is True
    assert any(
        str(sc.get("patternId") or "") == "screen-portrait-3"
        for sc in (ch1.get("screens") or [])
    ) or result["preferredApplied"]


def test_chapter_not_found() -> None:
    trip = _trip_two_chapters()
    result = apply_accepted_suggestion_to_chapter(trip, chapter_id="missing")
    assert result["ok"] is False
    assert result["reason"] == "chapter_not_found"


def test_empty_chapter() -> None:
    trip = {
        "tripId": "t",
        "assets": [_portrait("p1")],
        "chapters": [{"id": "ch-empty", "screens": []}],
    }
    result = apply_accepted_suggestion_to_chapter(trip, chapter_id="ch-empty")
    assert result["ok"] is False
    assert result["reason"] == "empty_chapter"
