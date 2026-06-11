"""Smoke tests for P19 book-quality harness."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_p19_golden_manifest_loads() -> None:
    from travelogue.eval.golden_trips import load_p19_golden_trip_ids

    ids = load_p19_golden_trip_ids()
    assert "demo-2025" in ids
    assert len(ids) >= 8


def test_vlm_judge_mock_runs() -> None:
    baseline_dir = ROOT / ".cache" / "book-quality" / "baseline"
    manifest = {
        "label": "test",
        "trips": [
            {
                "tripId": "demo-2025",
                "status": "ok",
                "patternSequence": ["screen-portrait-2", "screen-portrait-1"],
            }
        ],
    }
    baseline_dir.mkdir(parents=True, exist_ok=True)
    (baseline_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    from travelogue.eval.vlm_judge import mock_pairwise_judge

    verdict = mock_pairwise_judge(
        "demo-2025",
        {"patternSequence": ["a", "b"]},
        {"patternSequence": ["a", "b", "c"]},
    )
    assert verdict["tripId"] == "demo-2025"
    assert verdict["mode"] == "mock"

    out = ROOT / ".cache" / "book-quality" / "judge-test"
    report = {
        "mode": "mock",
        "tripCount": 1,
        "trips": [verdict],
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "judge_report.json").write_text(json.dumps(report), encoding="utf-8")
    report = json.loads((out / "judge_report.json").read_text(encoding="utf-8"))
    assert report["mode"] == "mock"
    assert report["tripCount"] == 1
