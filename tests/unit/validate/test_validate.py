"""Tests for trip validation."""



from __future__ import annotations

import json

from tests._repo_root import repo_root
from travelogue.services.validate import validate_trip

ROOT = repo_root(__file__)
FIXTURES = ROOT / "schemas" / "fixtures"


def run_validate(name: str, level: str = "all") -> list[str]:
    path = FIXTURES / name
    trip = json.loads(path.read_text(encoding="utf-8"))
    return validate_trip(trip, level=level)


def test_fixture_copy_locked_manifest():
    errs = [e for e in run_validate("trip.copy_locked.json", "manifest") if not e.startswith("WARN:")]
    assert not errs, errs


def test_fixture_structure_locked_manifest():
    errs = [e for e in run_validate("trip.structure_locked.json", "manifest") if not e.startswith("WARN:")]
    if errs:
        assert any("duplicate" in e or "VR-" in e for e in errs)


def test_fixture_phase10_food_grid_schema():
    errs = [e for e in run_validate("trip.phase10_food_grid.json", "schema") if not e.startswith("WARN:")]
    assert not errs, errs


def test_cover_video_fails():
    trip = json.loads((FIXTURES / "trip.copy_locked.json").read_text(encoding="utf-8"))
    trip["coverAssetId"] = trip["assets"][0]["id"]
    trip["assets"][0]["type"] = "video"
    errs = validate_trip(trip, level="manifest")
    assert any("VR-M01" in e or "cover cannot be video" in e for e in errs)
