"""Phase 4 M15 · Intent layer regression tests.

Covers:
- apply_intent double-write invariant (AC-P4-09): intent mirrors meta.title /
  meta.places / top-level userNotes, and NEVER writes meta.userNotes
- narrative_brief unified userNotes/plan source (M15-09, AC-P4-04 wiring)
- studio pipeline persists trip.intent and the result still passes schema
  validation (would have caught the meta.userNotes schema regression)
- schema accepts a trip with intent, and old trips without intent still validate
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.integration.studio.test_studio_server import _distinct_album
from travelogue.services.narrative_brief import (
    build_chapter_brief,
    build_meta_brief,
    resolve_date_range,
    resolve_plan_summary,
    resolve_travel_notes,
    resolve_user_notes,
)
from travelogue.services.trip import TripService, apply_intent
from travelogue.services.validate import validate_trip
from travelogue.web.studio_pipeline import _build_date_range_weak_hint, run_studio_pipeline

# ── apply_intent · double-write invariant (AC-P4-09) ──────────────────────────


def test_apply_intent_mirrors_meta_and_usernotes() -> None:
    trip: dict = {"meta": {}}
    intent = apply_intent(
        trip, title="雨后京都", places=["京都", "大阪"], user_notes="带娃慢走"
    )
    assert intent["version"] == "1"
    assert intent["title"] == "雨后京都" == trip["meta"]["title"]
    assert trip["meta"]["displayTitle"] == "雨后京都"
    assert intent["places"] == ["京都", "大阪"] == trip["meta"]["places"]
    assert intent["userNotes"] == "带娃慢走" == trip["userNotes"]
    # userNotes must live at top level, NOT under meta (meta has no such field)
    assert "userNotes" not in trip["meta"]
    assert "submittedAt" in intent


def test_apply_intent_clamps_lengths() -> None:
    trip: dict = {}
    apply_intent(trip, title="标" * 40, user_notes="字" * 300)
    assert len(trip["intent"]["title"]) == 20
    assert len(trip["intent"]["userNotes"]) == 200
    assert len(trip["meta"]["title"]) == 20


def test_apply_intent_none_clears_fields() -> None:
    trip: dict = {}
    apply_intent(trip, user_notes="带娃")
    assert trip["intent"]["userNotes"] == "带娃"
    assert trip["userNotes"] == "带娃"
    apply_intent(trip, user_notes=None)
    assert "userNotes" not in trip["intent"]
    assert "userNotes" not in trip


def test_apply_intent_only_touches_passed_args() -> None:
    trip: dict = {}
    apply_intent(trip, title="京都", user_notes="慢走")
    apply_intent(trip, folders={"featuredDetected": True})
    assert trip["intent"]["title"] == "京都"
    assert trip["intent"]["userNotes"] == "慢走"
    assert trip["intent"]["folders"] == {"featuredDetected": True}


def test_apply_intent_layout_density() -> None:
    trip: dict = {"meta": {"places": ["旅途"]}}
    apply_intent(trip, layout_density="hero_first")
    assert trip["intent"]["layoutDensity"] == "hero_first"
    apply_intent(trip, layout_density=None)
    assert "layoutDensity" not in trip["intent"]


def test_apply_intent_photo_cull_enabled() -> None:
    trip: dict = {"meta": {"places": ["旅途"]}}
    apply_intent(trip, photo_cull_enabled=False)
    assert trip["intent"]["photoCullEnabled"] is False
    apply_intent(trip, photo_cull_enabled=True)
    assert trip["intent"]["photoCullEnabled"] is True


def test_apply_intent_accepts_travel_notes_and_date_range() -> None:
    trip: dict = {}
    apply_intent(
        trip,
        travel_notes="这次旅程最喜欢的是雨夜散步",
        date_range={"start": "2025-04-02", "end": "2025-04-06", "source": "user"},
    )
    intent = trip.get("intent") or {}
    assert intent.get("travelNotes") == "这次旅程最喜欢的是雨夜散步"
    assert intent.get("dateRange") == {
        "start": "2025-04-02",
        "end": "2025-04-06",
        "source": "user",
    }


def test_apply_intent_travel_notes_and_date_range_can_clear() -> None:
    trip: dict = {}
    apply_intent(
        trip,
        travel_notes="记录一下这次旅途见闻",
        date_range={"start": "2025-04-02"},
    )
    apply_intent(trip, travel_notes=None, date_range=None)
    intent = trip.get("intent") or {}
    assert "travelNotes" not in intent
    assert "dateRange" not in intent


def test_apply_intent_empty_places_keeps_schema_meta_placeholder() -> None:
    trip: dict = {"meta": {"places": ["旅途"]}}
    apply_intent(trip, places=[], places_user_set=False)
    assert "places" not in trip["intent"]
    assert trip["meta"]["places"] == ["旅途"]


def test_tripservice_exposes_apply_intent() -> None:
    trip: dict = {}
    TripService.apply_intent(trip, title="x")
    assert trip["intent"]["title"] == "x"


# ── narrative_brief · unified source (M15-09) ─────────────────────────────────


def test_resolve_user_notes_priority() -> None:
    assert resolve_user_notes({"userNotes": "慢走"}) == "慢走"
    assert resolve_user_notes({"intent": {"userNotes": "带娃"}}) == "带娃"
    assert resolve_user_notes({"userNotes": "顶层", "intent": {"userNotes": "意图"}}) == "顶层"
    assert resolve_user_notes({}) is None
    assert resolve_user_notes({"userNotes": "   "}) is None


def test_resolve_plan_summary() -> None:
    assert resolve_plan_summary({"intent": {"travelPlan": {"summary": "D1 大阪"}}}) == "D1 大阪"
    assert resolve_plan_summary({}) is None
    assert resolve_plan_summary({"intent": {"travelPlan": {}}}) is None


def test_resolve_travel_notes_and_date_range() -> None:
    trip = {
        "intent": {
            "travelNotes": "在鸭川边慢慢散步，雨停后风很轻。",
            "dateRange": {"start": "2025-04-02", "end": "2025-04-06", "source": "user"},
        }
    }
    assert resolve_travel_notes(trip) == "在鸭川边慢慢散步，雨停后风很轻。"
    assert resolve_date_range(trip) == {
        "start": "2025-04-02",
        "end": "2025-04-06",
        "source": "user",
    }


def test_resolve_date_range_fail_open_on_invalid() -> None:
    trip = {
        "intent": {
            "dateRange": {"start": "2025-04-09", "end": "2025-04-06", "source": "user"}
        }
    }
    assert resolve_date_range(trip) is None


def test_meta_brief_injects_usernotes_and_plan() -> None:
    trip = {
        "meta": {"title": "T", "places": ["京都"]},
        "userNotes": "慢走慢看",
        "intent": {"version": "1", "travelPlan": {"summary": "D1 大阪 → D2 京都"}},
    }
    brief = build_meta_brief(trip, tone="relaxed")
    assert brief["trip"]["userNotes"] == "慢走慢看"
    assert brief["trip"]["travelPlanSummary"] == "D1 大阪 → D2 京都"


def test_meta_brief_usernotes_falls_back_to_intent() -> None:
    trip = {"meta": {"title": "T", "places": []}, "intent": {"userNotes": "带娃"}}
    brief = build_meta_brief(trip, tone="relaxed")
    assert brief["trip"]["userNotes"] == "带娃"


def test_chapter_brief_injects_usernotes() -> None:
    trip = {
        "meta": {"places": ["京都"]},
        "intent": {"userNotes": "带娃"},
        "chapters": [],
        "assets": [],
    }
    chapter = {"id": "ch-01", "index": 0, "patternId": "p", "title": "t", "items": []}
    brief = build_chapter_brief(trip, chapter, tone="relaxed")
    assert brief["trip"]["userNotes"] == "带娃"


def test_meta_and_chapter_brief_inject_travel_notes_and_date_range() -> None:
    trip = {
        "meta": {"places": ["京都"]},
        "intent": {
            "travelNotes": "见闻：清晨市场很热闹，夜里小巷很安静。",
            "dateRange": {"start": "2025-04-02", "end": "2025-04-06", "source": "user"},
        },
        "chapters": [],
        "assets": [],
    }
    chapter = {"id": "ch-01", "index": 0, "patternId": "p", "title": "t", "items": []}
    meta_brief = build_meta_brief(trip, tone="relaxed")
    chapter_brief = build_chapter_brief(trip, chapter, tone="relaxed")
    assert meta_brief["trip"]["travelNotes"] == "见闻：清晨市场很热闹，夜里小巷很安静。"
    assert meta_brief["trip"]["dateRange"]["start"] == "2025-04-02"
    assert chapter_brief["trip"]["travelNotes"] == "见闻：清晨市场很热闹，夜里小巷很安静。"
    assert chapter_brief["trip"]["dateRange"]["end"] == "2025-04-06"


def test_date_range_weak_hint_when_far_from_inferred_dates() -> None:
    hint = _build_date_range_weak_hint(
        user_date_range={"start": "2023-04-01", "end": "2023-04-03", "source": "user"},
        inferred_start="2026-04-01",
        inferred_end="2026-04-03",
    )
    assert "差异较大" in hint


def test_date_range_weak_hint_empty_when_close_or_unavailable() -> None:
    assert (
        _build_date_range_weak_hint(
            user_date_range={"start": "2026-04-01", "end": "2026-04-03", "source": "user"},
            inferred_start="2026-04-05",
            inferred_end="2026-04-07",
        )
        == ""
    )
    assert (
        _build_date_range_weak_hint(
            user_date_range={"source": "user"},
            inferred_start="2026-04-05",
            inferred_end="2026-04-07",
        )
        == ""
    )


# ── schema acceptance (M15-01) ────────────────────────────────────────────────


def _minimal_valid_trip() -> dict:
    return {
        "version": "0.2",
        "tripId": "demo-intent",
        "templateId": "visual-journal",
        "exportLayout": "auto",
        "meta": {
            "title": "雨后京都",
            "dateStart": "2026-05-01",
            "dateEnd": "2026-05-03",
            "places": ["京都"],
            "tone": "relaxed",
        },
        "coverAssetId": "a1",
        "assets": [],
        "chapters": [],
        "privacy": {
            "level": "private",
            "stripExifOnExport": True,
            "confirmedAt": "2026-05-01T00:00:00Z",
        },
        "pipeline": {"status": "ingest_ready", "locks": {"structure": False, "copy": False}},
        "createdAt": "2026-05-01T00:00:00Z",
        "updatedAt": "2026-05-01T00:00:00Z",
    }


def test_schema_accepts_intent_object() -> None:
    trip = _minimal_valid_trip()
    apply_intent(trip, title="雨后京都", places=["京都"], user_notes="带娃慢走")
    apply_intent(
        trip,
        travel_notes="见闻：祇园避雨，鸭川散步。",
        date_range={"start": "2025-04-02", "end": "2025-04-06", "source": "user"},
    )
    trip["intent"]["travelPlan"] = {
        "format": "text",
        "filename": "plan.txt",
        "summary": "D1 大阪 → D2 京都",
        "cities": ["大阪", "京都"],
    }
    errors = validate_trip(trip, level="schema")
    assert errors == [], errors


def test_schema_old_trip_without_intent_still_valid() -> None:
    trip = _minimal_valid_trip()
    assert "intent" not in trip
    errors = validate_trip(trip, level="schema")
    assert errors == [], errors


# ── pipeline integration (M15-05 · AC-P4-01/09) ───────────────────────────────


@pytest.mark.integration
def test_pipeline_default_place_passes_schema(tmp_path: Path) -> None:
    """Default generic place must keep meta.places valid for export/validate."""
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    result = run_studio_pipeline(album, trips_dir=trips_dir, dedupe=False)
    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))
    assert trip["meta"].get("places")
    errors = validate_trip(trip, level="schema")
    assert errors == [], errors


@pytest.mark.integration
def test_pipeline_persists_intent_and_passes_schema(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    result = run_studio_pipeline(
        album,
        trips_dir=trips_dir,
        title="雨后京都",
        place="京都",
        user_notes="带娃慢走",
        dedupe=False,
    )
    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))

    intent = trip.get("intent") or {}
    assert intent.get("title") == "雨后京都"
    assert intent.get("userNotes") == "带娃慢走"
    assert intent.get("folders", {}).get("featuredDetected") in (True, False)

    # double-write invariant after a full pipeline run
    assert trip.get("userNotes") == "带娃慢走"
    assert intent.get("title") == trip["meta"]["title"]
    assert "京都" in (trip["meta"].get("places") or [])
    assert "userNotes" not in (trip.get("meta") or {})

    # full trip must pass schema (guards the meta.userNotes / intent regressions)
    errors = validate_trip(trip, level="schema")
    assert errors == [], errors
