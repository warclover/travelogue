"""W3b-09 LSE shadow dual-track."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.phase3_ig2_report import _cfg_for_mode, load_fixture_trip
from travelogue.layout_engine.shadow import SHADOW_SIDECAR, shadow_lse_from_cfg, shadow_metrics


def test_shadow_metrics_shape() -> None:
    report = {
        "diffRate": 0.0,
        "diff": {"changedCount": 0},
        "baseline": {"patternDistribution": {"screen-portrait-1": 0.5}},
        "candidate": {"patternDistribution": {"screen-portrait-1": 0.5, "screen-mosaic-4": 0.1}},
    }
    m = shadow_metrics(report)
    assert m["patternDiversityBaseline"] == 1
    assert m["patternDiversityCandidate"] == 2
    assert m["diffRate"] == 0.0


def test_shadow_writes_sidecar_without_mutating_trip(tmp_path: Path) -> None:
    trip = load_fixture_trip("golden-mixed-scenes")
    trip_path = tmp_path / "trip.json"
    before = json.dumps(trip, sort_keys=True)
    trip_path.write_text(before, encoding="utf-8")

    base = _cfg_for_mode("p3_full")
    work_dir = tmp_path / "runs" / "lse-shadow" / "replay"
    out = shadow_lse_from_cfg(
        trip,
        trip_id="bench-trip",
        base_cfg=base,
        work_dir=work_dir,
        write_sidecar=True,
    )
    assert out.get("shadowActive") is True
    assert out.get("recordOnly") is True
    sidecar = tmp_path / "runs" / "lse-shadow" / SHADOW_SIDECAR
    assert sidecar.is_file()
    saved = json.loads(sidecar.read_text(encoding="utf-8"))
    assert saved["tripId"] == "bench-trip"
    assert "metrics" in saved
    after = trip_path.read_text(encoding="utf-8")
    assert after == before
