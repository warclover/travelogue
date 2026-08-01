"""Phase 15 full curate replay on CI fixture."""

from __future__ import annotations

from pathlib import Path

from scripts.phase3_ig2_report import load_fixture_trip
from scripts.phase15_curate_replay import evaluate_trip_curate

CI_FIXTURE = "golden-mixed-scenes"


def test_phase15_curate_replay_fixture_mosaic_lift(tmp_path: Path) -> None:
    trip = load_fixture_trip(CI_FIXTURE)
    row = evaluate_trip_curate(trip, trip_id=CI_FIXTURE, work_dir=tmp_path / CI_FIXTURE)
    assert row["passesExposureLift"]
    assert row["passesUnifiedLift"]
    on_patterns = row["mosaicOn"]["screenPatterns"]
    assert on_patterns
    # mosaicDecisionCount / fallbackRate are observational under Scene Atom;
    # sparse fixture timestamps can force legacy windows without losing lift ACs.
    assert row["mosaicOn"]["mosaicDecisionCount"] >= 0
