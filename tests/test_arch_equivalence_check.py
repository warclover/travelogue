"""Tests for scripts/arch_equivalence_check.py (M-B0)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.arch_equivalence_check import (
    check_self_reflexivity,
    diff_normalized,
    normalize_trip,
)

ROOT = Path(__file__).resolve().parents[1]


def test_normalize_strips_timing_and_screen_ids() -> None:
    trip = {
        "meta": {"updatedAt": "2026-01-01T00:00:00Z", "title": "x"},
        "curation": {
            "aestheticAlignment": {"appliedAt": "2026-01-01T00:00:00Z", "score": 0.5},
            "cullSummary": {"cpuMs": 0.42, "kept": 3},
        },
        "pipeline": {"timings": {"curateMs": 12.3}, "status": "rendered"},
        "chapters": [
            {
                "id": "ch-1",
                "screens": [{"screenId": "breath-deadbeef", "patternId": "open"}],
            }
        ],
    }
    normalized = normalize_trip(trip)
    assert "updatedAt" not in normalized["meta"]
    assert "appliedAt" not in normalized["curation"]["aestheticAlignment"]
    assert "timings" not in normalized["pipeline"]
    assert "screenId" not in normalized["chapters"][0]["screens"][0]
    assert "cpuMs" not in normalized["curation"]["cullSummary"]


def test_self_reflexivity_render_golden_fixture(tmp_path: Path) -> None:
    report = check_self_reflexivity(
        str(ROOT / "schemas/fixtures/trip.render_golden.json"),
        work_dir=tmp_path / "render-golden",
    )
    assert report.ok
    assert not report.l3a_diff


def test_self_reflexivity_golden_mixed_scenes(tmp_path: Path) -> None:
    report = check_self_reflexivity("golden-mixed-scenes", work_dir=tmp_path / "gms")
    assert report.ok
    assert not report.l3a_diff
    assert not report.l3b_diff


def test_diff_normalized_reports_field_paths() -> None:
    left = normalize_trip({"meta": {"title": "a"}})
    right = normalize_trip({"meta": {"title": "b"}})
    diffs = diff_normalized(left, right)
    assert any("meta.title" in item for item in diffs)
