"""AC-P4-TEL-01 · studio intent telemetry."""

from __future__ import annotations

import json
from pathlib import Path

from tests.test_studio_server import _distinct_album
from travelogue.web.studio_intent_telemetry import (
    build_studio_intent_telemetry,
    write_studio_intent_telemetry,
)
from travelogue.web.studio_pipeline import run_studio_pipeline


def test_build_studio_intent_telemetry_fields() -> None:
    trip = {
        "tripId": "demo",
        "userNotes": "带娃慢走",
        "intent": {
            "travelPlan": {"cities": ["京都"]},
            "title": "京都",
            "photoCullEnabled": False,
        },
        "assets": [{"userTier": "featured"}, {"userTier": "material"}],
        "chapters": [{"curation": {"memoryAnchors": ["寺", "雨"]}}],
        "pipeline": {"status": "rendered"},
        "curation": {
            "cullSummary": {
                "finalLayoutEligibleCount": 55,
                "layoutEligibleCount": 58,
            },
        },
    }
    payload = build_studio_intent_telemetry(trip, tier_mode="dual", g1_pending=False)
    assert payload["hasUserNotes"] is True
    assert payload["featuredCount"] == 1
    assert payload["tierMode"] == "dual"
    assert payload["planUploaded"] is True
    assert payload["anchorCount"] == 2
    assert payload["g1Pending"] is False
    assert payload["layoutDensity"] == "balanced"
    assert payload["layoutDensityEffect"] == "ignored_quick"
    assert payload["nineQuotaAdjusted"]["baseMin"] == 0
    assert payload["photoCullEnabled"] is False
    assert payload["layoutEligibleFinal"] == 55


def test_write_studio_intent_telemetry_file(tmp_path: Path) -> None:
    trip = {"tripId": "demo", "assets": [], "chapters": []}
    path = write_studio_intent_telemetry(trip, tmp_path, tier_mode="single")
    assert path == tmp_path / "runs" / "studio-intent.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["tripId"] == "demo"
    assert payload["tierMode"] == "single"


def test_pipeline_writes_studio_intent_telemetry(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    result = run_studio_pipeline(
        album,
        trips_dir=trips_dir,
        user_notes="慢走",
        dedupe=False,
    )
    tel_path = result.trip_dir / "runs" / "studio-intent.json"
    assert tel_path.is_file()
    payload = json.loads(tel_path.read_text(encoding="utf-8"))
    assert payload["hasUserNotes"] is True
    assert payload["tripId"] == result.trip_id
    assert result.tier_mode
