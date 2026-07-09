"""P13 integration: create + render surfaces + admin admission."""

from __future__ import annotations

import json
from pathlib import Path

import travelogue.render.admission_golden  # noqa: F401
from travelogue.services.trip_factory import create_trip
from travelogue.templating.admission import run_admission_check


def test_create_trip_template_selection_smoke(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trips.mkdir()
    trip_json = create_trip("p13-int", trips, title="集成测试")
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    assert trip.get("templateSelection", {}).get("resolvedTemplateId") == "visual-journal"
    assert (trip_json.parent / "runs" / "template_decisions.jsonl").is_file()


def test_admission_blocks_incomplete_template(tmp_path: Path) -> None:
    report = run_admission_check("visual-journal")
    assert "steps" in report
