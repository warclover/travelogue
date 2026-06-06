"""Phase 11 · decorLine + copyIntent tests."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from travelogue.config import AppConfig, NarrativeConfig
from travelogue.services.decor_line import (
    apply_decor_lines,
    generate_decor_line_candidates,
    pick_best_decor_line,
    validate_copy_intent,
    validate_decor_line,
)
from travelogue.services.narrate import run_narrate
from travelogue.services.narrative_validate import validate_narrative


def _sample_trip() -> dict:
    return {
        "tripId": "p11-test",
        "meta": {"title": "测试", "places": ["京都"], "tone": "relaxed"},
        "assets": [
            {
                "id": "a1",
                "type": "image",
                "tags": ["寺庙", "雨"],
                "place": {"city": "京都"},
            }
        ],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "patternId": "open",
                "title": "雨后",
                "items": [{"type": "media-card", "assetId": "a1"}],
                "curation": {"memoryAnchors": ["鸭川"], "places": ["京都"]},
            }
        ],
    }


def test_decor_line_max_length() -> None:
    trip = _sample_trip()
    cfg = AppConfig(narrative=NarrativeConfig(decor_line_enabled=True))
    updated = apply_decor_lines(trip, cfg=cfg)
    assert updated == ["chapters[1].decorLine"]
    line = trip["chapters"][0]["decorLine"]
    assert len(line) <= 30


def test_decor_line_allow_empty() -> None:
    trip = {
        "tripId": "empty",
        "meta": {"title": "空"},
        "assets": [],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "patternId": "open",
                "title": "",
                "items": [],
            }
        ],
    }
    cfg = AppConfig(
        narrative=NarrativeConfig(
            decor_line_enabled=True,
            decor_line_allow_empty=True,
        )
    )
    apply_decor_lines(trip, cfg=cfg)
    assert trip["chapters"][0].get("decorLine", "") == ""


def test_decor_line_edited_chapter_protected() -> None:
    trip = _sample_trip()
    trip["chapters"][0]["edited"] = True
    trip["chapters"][0]["decorLine"] = "保留句。"
    cfg = AppConfig(narrative=NarrativeConfig(decor_line_enabled=True))
    updated = apply_decor_lines(trip, regenerate=True, cfg=cfg)
    assert updated == []
    assert trip["chapters"][0]["decorLine"] == "保留句。"


def test_copy_intent_enum_validation() -> None:
    trip = _sample_trip()
    trip["chapters"][0].setdefault("curation", {})["copyIntent"] = {
        "mood": "无效",
        "focus": "人",
        "note": "x" * 31,
    }
    errs = validate_copy_intent(trip["chapters"][0], chapter_index=0)
    assert any("mood" in e for e in errs)
    assert any("note" in e for e in errs)


def test_copy_intent_boosts_candidate() -> None:
    chapter = _sample_trip()["chapters"][0]
    trip = _sample_trip()
    chapter = copy.deepcopy(chapter)
    chapter.setdefault("curation", {})["copyIntent"] = {
        "mood": "平静",
        "focus": "地方",
        "note": "雨停后风很轻",
    }
    trip["chapters"] = [chapter]
    cfg = AppConfig(narrative=NarrativeConfig(decor_line_intent_enabled=True))
    cands = generate_decor_line_candidates(chapter, trip, cfg=cfg)
    picked = pick_best_decor_line(cands, chapter, trip, cfg=cfg)
    assert picked
    assert len(picked) <= 30


def test_decor_line_disabled_skips() -> None:
    trip = _sample_trip()
    cfg = AppConfig(narrative=NarrativeConfig(decor_line_enabled=False))
    assert apply_decor_lines(trip, cfg=cfg) == []
    assert "decorLine" not in trip["chapters"][0]


def test_validate_decor_line_banned_phrase() -> None:
    chapter = _sample_trip()["chapters"][0]
    errs = validate_decor_line("综上所述，雨很好。", chapter)
    assert errs


def test_run_narrate_stub_writes_decor_line() -> None:
    trip = _sample_trip()
    run_narrate(trip, provider="stub")
    assert "decorLine" in trip["chapters"][0]
    assert trip.setdefault("curation", {}).get("copyStyle", {}).get("phase") == "p11-lite-line"


def test_copy_intent_handler_to_narrate_integration(tmp_path: Path) -> None:
    """M11-2h: PATCH copyIntent -> narrate stub consumes intent."""
    from travelogue.services.trip import TripService
    from travelogue.services.trip_factory import create_trip
    from travelogue.web.studio_handlers.trip_handlers import handle_patch_copy_intent
    from tests.studio_test_helpers import MockStudioHandler

    trips_dir = tmp_path / "trips"
    trip_json = create_trip("p11-intent", trips_dir, title="测试", place="京都")
    svc = TripService(root=trips_dir.parent)
    trip = svc.load(trip_json)
    trip["chapters"] = [
        {
            "id": "ch-01",
            "index": 1,
            "patternId": "open",
            "title": "雨后",
            "items": [{"type": "media-card", "assetId": "a1"}],
            "curation": {"places": ["京都"]},
        }
    ]
    trip["assets"] = [
        {"id": "a1", "type": "image", "tags": ["寺庙"], "place": {"city": "京都"}}
    ]
    svc.save(trip, trip_json)

    handler = MockStudioHandler(
        trips_dir,
        json_body={"mood": "平静", "focus": "地方", "note": "雨停后风很轻"},
    )
    handle_patch_copy_intent(handler, "p11-intent", "ch-01")
    assert handler.response is not None
    assert handler.response[0] == 200

    trip = svc.load(trip_json)
    run_narrate(trip, provider="stub")
    assert trip["chapters"][0].get("decorLine")
    assert trip["chapters"][0]["curation"]["copyIntent"]["note"] == "雨停后风很轻"
    svc.save(trip, trip_json)


def test_validate_narrative_accepts_decor_line() -> None:
    trip = _sample_trip()
    apply_decor_lines(trip)
    issues = [i for i in validate_narrative(trip) if not i.startswith("WARN:")]
    assert issues == []
