"""P17 dogfood admission · shadow + capability probe gates."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.phase17_dogfood_admission import (
    DEFAULT_DOGFOOD_FIXTURES,
    aggregate_observations,
    append_rollout_log,
    observe_trip,
)


def test_default_dogfood_fixtures_include_mixed_and_person() -> None:
    assert "golden-mixed-scenes" in DEFAULT_DOGFOOD_FIXTURES
    assert "golden-p17-mixed-person" in DEFAULT_DOGFOOD_FIXTURES


def test_observe_trip_mixed_scenes_capability_gates(tmp_path: Path) -> None:
    from scripts.phase3_ig2_report import load_fixture_trip

    trip = load_fixture_trip("golden-mixed-scenes")
    out = observe_trip(trip, trip_id="golden-mixed-scenes", work_dir=tmp_path / "mixed")
    gates = out.get("gates") or {}
    assert gates.get("AC-P17-17") is True
    assert gates.get("AC-P17-18") is True
    assert gates.get("AC-P17-16") is True
    assert out.get("diffRate") == 0.0
    assert out.get("patternDiversityOk") is True


def test_observe_trip_person_fixture_face_measurable(tmp_path: Path) -> None:
    """Person fixture: AC-P17-16 via window probe (no full-trip mixed screens by design)."""
    from scripts.phase3_ig2_report import load_fixture_trip

    trip = load_fixture_trip("golden-p17-mixed-person")
    out = observe_trip(trip, trip_id="golden-p17-mixed-person", work_dir=tmp_path / "person")
    assert out.get("diffRate") == 0.0
    assert out.get("faceIntactBaseline") is None
    assert out.get("faceMetricSource") == "ac_p17_16_probe"
    probes = out.get("capabilityProbes") or {}
    assert probes.get("AC-P17-16", {}).get("measurable") is True
    assert probes.get("AC-P17-16", {}).get("passed") is True
    assert (out.get("faceIntactDeltaPp") or 0) >= 3.0
    gates = out.get("gates") or {}
    assert all(gates.get(ac) is not False for ac in ("AC-P17-16", "AC-P17-17", "AC-P17-18"))


def test_aggregate_and_rollout_append(tmp_path: Path) -> None:
    observations = [
        {
            "tripId": "golden-mixed-scenes",
            "faceIntactDeltaPp": None,
            "patternDiversityOk": True,
            "gates": {
                "AC-P17-16": True,
                "AC-P17-17": True,
                "AC-P17-18": True,
            },
        },
        {
            "tripId": "golden-p17-mixed-person",
            "faceIntactDeltaPp": 4.0,
            "patternDiversityOk": True,
            "gates": {
                "AC-P17-16": True,
                "AC-P17-17": True,
                "AC-P17-18": True,
            },
        },
    ]
    agg = aggregate_observations(observations)
    assert agg["capabilityGates"]["AC-P17-16"] is True
    assert agg["faceIntactDeltaPpMedian"] == 4.0

    rollout_path = tmp_path / "p17-rollout-log.json"
    import scripts.phase17_dogfood_admission as mod

    original = mod.ROLLOUT_PATH
    mod.ROLLOUT_PATH = rollout_path
    try:
        rollout = append_rollout_log(observations, aggregate=agg)
    finally:
        mod.ROLLOUT_PATH = original
    assert rollout["gates"]["dogfood_admission"]["passed"] is True
    saved = json.loads(rollout_path.read_text(encoding="utf-8"))
    assert len(saved["observations"]) == 1
