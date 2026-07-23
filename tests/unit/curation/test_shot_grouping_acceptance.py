"""SSG · AC-01/02/08/09 + mixed-scenes golden."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from travelogue.config.shot_grouping import shot_grouping_from_dict
from travelogue.curation.shot_group_metrics import (
    same_shot_group_rate,
    shot_group_coverage_ratio,
)
from travelogue.curation.shot_grouping import run_shot_grouping_layer

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "shot-grouping"
    / "mixed-scenes-synthetic"
    / "shot-groups-golden.json"
)


def _cfg():
    ssg = shot_grouping_from_dict(
        {"enabled": "true", "look": {"enabled": "false"}, "scene": {"mergeNoise": True}}
    )
    return type("Cfg", (), {"shot_grouping": ssg})()


def _load_trip() -> tuple[dict, dict]:
    gold = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assets = []
    for row in gold["assets"]:
        assets.append(
            {
                "id": row["id"],
                "takenAt": row["takenAt"],
                "sceneClusterId": row["sceneClusterId"],
                "eventId": row.get("eventId"),
                "sharpness": 0.5,
                "type": "photo",
            }
        )
    return {"assets": assets}, gold


def test_ac01_coverage_at_least_95pct() -> None:
    trip, gold = _load_trip()
    run_shot_grouping_layer(trip, cfg=_cfg())  # type: ignore[arg-type]
    ratio = shot_group_coverage_ratio(trip["assets"])
    assert ratio >= float(gold["minCoverage"]), ratio
    telem = (trip.get("curation") or {}).get("shotGrouping", {}).get("telemetry") or {}
    assert telem.get("coverageRatio", 0) >= float(gold["minCoverage"])


def test_ac02_same_group_rate_at_least_85pct() -> None:
    trip, gold = _load_trip()
    run_shot_grouping_layer(trip, cfg=_cfg())  # type: ignore[arg-type]
    by_id = {a["id"]: a for a in trip["assets"]}
    pairs = [tuple(p) for p in gold["neighborPairs"]]
    rate = same_shot_group_rate(pairs, by_id)  # type: ignore[arg-type]
    assert rate >= float(gold["minSameGroupRate"]), rate
    for a, b in gold["mustDifferPairs"]:
        assert by_id[a].get("shotGroupId") != by_id[b].get("shotGroupId")


def test_ac08_telemetry_summary_present(tmp_path: Path) -> None:
    trip, _gold = _load_trip()
    run_shot_grouping_layer(trip, trip_dir=tmp_path, cfg=_cfg())  # type: ignore[arg-type]
    sg = (trip.get("curation") or {}).get("shotGrouping") or {}
    assert "telemetry" in sg
    assert sg["telemetry"].get("groupCount", 0) >= 2
    log_path = tmp_path / "shot_grouping_decision_log.json"
    assert log_path.is_file()
    body = json.loads(log_path.read_text(encoding="utf-8"))
    assert body.get("kind") == "shot_grouping_summary"


def test_ac09_deterministic_dual_run() -> None:
    trip_a, _ = _load_trip()
    trip_b = copy.deepcopy(trip_a)
    run_shot_grouping_layer(trip_a, cfg=_cfg())  # type: ignore[arg-type]
    run_shot_grouping_layer(trip_b, cfg=_cfg())  # type: ignore[arg-type]
    map_a = {a["id"]: a.get("shotGroupId") for a in trip_a["assets"]}
    map_b = {a["id"]: a.get("shotGroupId") for a in trip_b["assets"]}
    assert map_a == map_b
    groups_a = (trip_a.get("curation") or {}).get("shotGrouping", {}).get("groups")
    groups_b = (trip_b.get("curation") or {}).get("shotGrouping", {}).get("groups")
    assert groups_a == groups_b
