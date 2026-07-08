"""Tests for scripts/lint_trip_json.py (AC-ARC-11)."""



from __future__ import annotations
from tests._repo_root import repo_root

import json
from pathlib import Path

import pytest

from scripts.lint_trip_json import (
    DEFAULT_MAX_BYTES,
    DEFAULT_WARN_BYTES,
    lint_trip_data,
    lint_trip_path,
    main,
)

ROOT = repo_root(__file__)
FIXTURE = ROOT / "schemas/fixtures/trip.example.json"


def test_all_schema_fixtures_pass_lint() -> None:
    for path in sorted((ROOT / "schemas/fixtures").glob("trip*.json")):
        report = lint_trip_path(path)
        assert report.ok, f"{path}: {report.failures}"


def test_all_tests_fixtures_pass_lint() -> None:
    for path in sorted((ROOT / "tests/fixtures").rglob("trip.json")):
        report = lint_trip_path(path)
        assert report.ok, f"{path}: {report.failures}"


def test_denylist_layout_decision_log_fails() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data.setdefault("curation", {})["layoutDecisionLog"] = [{"chapterId": "c1", "decision": "x"}]
    report = lint_trip_data(data, path="fixture", size_bytes=1000)
    assert not report.ok
    assert any("layoutDecisionLog" in item for item in report.failures)


def test_denylist_top_level_telemetry_fails() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["telemetry"] = {"events": []}
    report = lint_trip_data(data, path="fixture", size_bytes=1000)
    assert not report.ok
    assert any("telemetry" in item for item in report.failures)


def test_size_warn_and_fail_thresholds() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    warn_payload = "x" * (DEFAULT_WARN_BYTES + 1)
    data["userNotes"] = warn_payload
    warn_report = lint_trip_data(
        data,
        path="fixture",
        size_bytes=len(json.dumps(data).encode("utf-8")),
        warn_bytes=DEFAULT_WARN_BYTES,
        max_bytes=DEFAULT_MAX_BYTES,
    )
    assert warn_report.ok
    assert warn_report.warnings

    fail_data = dict(data)
    fail_data["userNotes"] = "y" * (DEFAULT_MAX_BYTES + 1)
    fail_size = len(json.dumps(fail_data).encode("utf-8"))
    fail_report = lint_trip_data(
        fail_data,
        path="fixture",
        size_bytes=fail_size,
        warn_bytes=DEFAULT_WARN_BYTES,
        max_bytes=DEFAULT_MAX_BYTES,
    )
    assert not fail_report.ok
    assert any("size:" in item for item in fail_report.failures)


def test_main_json_output(tmp_path: Path) -> None:
    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    path = tmp_path / "trip.json"
    path.write_text(json.dumps(trip), encoding="utf-8")
    assert main([str(path), "--json"]) == 0


def test_version_outside_window_fails() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["version"] = "9.9"
    report = lint_trip_data(data, path="fixture", size_bytes=1000)
    assert not report.ok
    assert any("outside supported window" in item for item in report.failures)


def test_version_current_passes() -> None:
    from travelogue.curation.trip_migration import CURRENT_TRIP_VERSION

    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["version"] = CURRENT_TRIP_VERSION
    report = lint_trip_data(data, path="fixture", size_bytes=1000)
    assert report.ok
