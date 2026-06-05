"""NR-P9-03 · trip.schema.json accepts Phase 9 cull fields."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.services.validate import validate_trip

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"


def _schema_errors(trip: dict) -> list[str]:
    return [e for e in validate_trip(trip, level="schema") if not e.startswith("WARN:")]


def test_schema_accepts_cull_summary_and_asset_fields() -> None:
    trip = json.loads(SCHEMA_FIXTURE.read_text(encoding="utf-8"))
    trip.setdefault("curation", {})
    trip["curation"]["cullUserLine"] = "经挑选 2 张进入排版"
    trip["curation"]["cullSummary"] = {
        "enabled": True,
        "mode": "rules",
        "scanned": 3,
        "layoutEligibleCount": 2,
        "excludedByCull": 1,
        "excludedByReason": {"blur": 1},
        "floorNotMet": False,
        "pass3Skipped": "pool_at_or_below_floor",
    }
    assets = [a for a in trip.get("assets") or [] if a.get("type") == "image"]
    assert len(assets) >= 2
    dropped = assets[-1]
    dropped["layoutEligible"] = False
    dropped["excludeReason"] = "blur"
    dropped.setdefault("quality", {})["cullGroupId"] = "dedupe:g1"
    for asset in assets[:-1]:
        asset.setdefault("quality", {})["cullScore"] = 0.75
        asset.setdefault("quality", {})["cullRank"] = 1
        asset["quality"]["cullBranch"] = "portrait"
        asset["quality"]["cullBranchScore"] = 0.8123
    trip["curation"]["excludedByCullAssetIds"] = [dropped["id"]]
    assert not _schema_errors(trip), _schema_errors(trip)
