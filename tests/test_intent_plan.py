"""M18 · travel plan parsing and Studio pipeline integration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.curation.chapter_explain import build_chapter_explain
from travelogue.curation.chapter_titles import chapter_titles
from travelogue.services.intent_plan import (
    MAX_PLAN_BYTES,
    apply_plan_parse,
    cities_match,
    ingest_travel_plan,
    parse_plan_bytes,
    parse_plan_text,
)
from travelogue.services.validate import validate_trip
from travelogue.web.studio_pipeline import run_studio_pipeline
from tests.test_studio_server import _distinct_album


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "intent"


def test_parse_plan_kyoto_fixture_cities() -> None:
    raw = (FIXTURES / "plan-kyoto.txt").read_bytes()
    result = parse_plan_bytes(raw, filename="plan.txt")
    assert result.ok is True
    assert result.cities == ("大阪", "京都")
    assert result.summary
    assert "大阪" in result.summary
    assert "京都" in result.summary


def test_parse_plan_golden_city_hit_rate() -> None:
    raw = (FIXTURES / "plan-kyoto.txt").read_bytes()
    result = parse_plan_bytes(raw)
    expected = ["大阪", "京都"]
    hits = sum(1 for city in expected if city in result.cities)
    assert hits / len(expected) >= 0.9


def test_parse_plan_fail_open_empty_fixture() -> None:
    raw = (Path(__file__).resolve().parent / "fixtures" / "intent" / "plan-empty.txt").read_bytes()
    result = parse_plan_bytes(raw)
    assert result.ok is False
    assert result.cities == ()


def test_parse_plan_fail_open_empty() -> None:
    result = parse_plan_text("   \n\n")
    assert result.ok is False
    assert result.cities == ()


def test_parse_plan_fail_open_oversize() -> None:
    result = parse_plan_bytes(b"x" * (MAX_PLAN_BYTES + 1))
    assert result.ok is False
    assert result.warn == "plan_too_large"


def test_parse_plan_fail_open_garbage() -> None:
    result = parse_plan_bytes(b"\xff\xfe\xfd" * 40)
    assert result.ok is False


def test_cities_match_alias_and_contains() -> None:
    assert cities_match("京都", "京都")
    assert cities_match("Kyoto", "京都")
    assert cities_match("京都", "京都市")


def test_apply_plan_parse_writes_intent_and_hints() -> None:
    trip: dict = {"meta": {"title": "测试", "places": ["旅途"]}, "curation": {}}
    raw = (FIXTURES / "plan-kyoto.txt").read_bytes()
    result = parse_plan_bytes(raw)
    apply_plan_parse(trip, result)
    assert trip["intent"]["travelPlan"]["cities"] == ["大阪", "京都"]
    assert trip["curation"]["intentHints"]["planCities"] == ["大阪", "京都"]


def test_apply_plan_parse_fail_open_clears_city_hints() -> None:
    trip: dict = {
        "meta": {"title": "测试", "places": ["旅途"]},
        "curation": {"intentHints": {"planCities": ["旧"]}},
    }
    apply_plan_parse(trip, parse_plan_text(""))
    hints = (trip.get("curation") or {}).get("intentHints") or {}
    assert "planCities" not in hints


def test_chapter_titles_use_plan_cities_in_order() -> None:
    assets = [
        {"id": "a1", "takenAt": "2026-05-01T12:00:00Z"},
        {"id": "a2", "takenAt": "2026-05-02T12:00:00Z"},
        {"id": "a3", "takenAt": "2026-05-03T12:00:00Z"},
        {"id": "a4", "takenAt": "2026-05-04T12:00:00Z"},
    ]
    titles = chapter_titles(
        [["a1"], ["a2"], ["a3"], ["a4"]],
        assets,
        {"places": ["关西"]},
        plan_cities=["大阪", "京都"],
    )
    assert titles[0] == "大阪"
    assert titles[1] == "京都"


def test_chapter_explain_mentions_plan_route() -> None:
    trip = {
        "chapters": [{"id": "c1"}, {"id": "c2"}],
        "intent": {"travelPlan": {"cities": ["大阪", "京都"]}},
        "curation": {
            "intentHints": {"planCities": ["大阪", "京都"]},
            "clustering": {
                "segmentMode": "geo_event",
                "segments": [
                    {"name": "大阪", "assetIds": ["a1"]},
                    {"name": "京都", "assetIds": ["a2"]},
                ],
            },
        },
    }
    out = build_chapter_explain(trip)
    assert any("行程单" in line for line in out["details"])
    assert "大阪" in " ".join(out["details"])


def test_ingest_travel_plan_saves_file(tmp_path: Path) -> None:
    trip: dict = {"meta": {"title": "测试", "places": ["旅途"]}}
    raw = (FIXTURES / "plan-kyoto.txt").read_bytes()
    ingest_travel_plan(trip, tmp_path, raw_bytes=raw)
    assert (tmp_path / "source" / "intent" / "plan.txt").is_file()


@pytest.mark.integration
def test_pipeline_with_plan_text_persists_intent(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    plan_text = (FIXTURES / "plan-kyoto.txt").read_text(encoding="utf-8")
    result = run_studio_pipeline(
        album,
        trips_dir=trips_dir,
        title="关西之旅",
        place="关西",
        dedupe=False,
        plan_text=plan_text,
    )
    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))
    plan = (trip.get("intent") or {}).get("travelPlan") or {}
    hints = (trip.get("curation") or {}).get("intentHints") or {}
    assert plan.get("cities") == ["大阪", "京都"]
    assert hints.get("planCities") == ["大阪", "京都"]
    assert (result.trip_dir / "source" / "intent" / "plan.txt").is_file()
    titles = [ch.get("title") for ch in trip.get("chapters") or []]
    assert any("大阪" in (t or "") for t in titles)
    assert any("京都" in (t or "") for t in titles)
    errors = validate_trip(trip, level="schema")
    assert errors == [], errors


@pytest.mark.integration
def test_pipeline_with_bad_plan_still_succeeds(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    result = run_studio_pipeline(
        album,
        trips_dir=trips_dir,
        dedupe=False,
        plan_text="",
    )
    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))
    hints = (trip.get("curation") or {}).get("intentHints") or {}
    assert "planCities" not in hints
    assert result.trip_id
