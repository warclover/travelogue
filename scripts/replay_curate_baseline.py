#!/usr/bin/env python3
"""Deterministic curate replay for CI baseline checks.

Usage:
  python scripts/replay_curate_baseline.py --write schemas/fixtures/curate_baseline.golden.json
  python scripts/replay_curate_baseline.py --check schemas/fixtures/curate_baseline.golden.json
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config import AppConfig, ClusteringConfig, CullConfig
from travelogue.curation.curate import run_curate


def _baseline_trip() -> dict:
    fixture = ROOT / "schemas" / "fixtures" / "trip.ingest_ready.json"
    trip = json.loads(fixture.read_text(encoding="utf-8"))
    trip = copy.deepcopy(trip)
    trip.pop("chapters", None)
    trip.setdefault("pipeline", {})["status"] = "structure_draft"
    trip.setdefault("curation", {}).pop("algorithmProfile", None)
    for i, asset in enumerate(trip.get("assets") or [], start=1):
        asset["layoutEligible"] = True
        asset["takenAt"] = f"2025-04-0{((i - 1) % 3) + 2}T12:00:00Z"
    return trip


def _deterministic_cfg() -> AppConfig:
    return AppConfig(
        clustering=ClusteringConfig(enabled="false"),
        cull=CullConfig(enabled=False),
    )


def _snapshot(trip: dict) -> dict[str, Any]:
    curation = trip.get("curation") or {}
    profile = curation.get("algorithmProfile") or {}
    chapters = trip.get("chapters") or []
    return {
        "chapterCount": len(chapters),
        "coverAssetId": trip.get("coverAssetId"),
        "exportLayout": trip.get("exportLayout"),
        "algorithmProfile": {
            "profileVersion": profile.get("profileVersion"),
            "cullKeepRatioFloor": profile.get("cullKeepRatioFloor"),
            "aestheticEnabled": profile.get("aestheticEnabled"),
            "coverScoringHash": profile.get("coverScoringHash"),
        },
        "chapterIds": [ch.get("id") for ch in chapters],
    }


def _run() -> dict[str, Any]:
    trip = _baseline_trip()
    cfg = _deterministic_cfg()
    run_curate(
        trip,
        export_layout="mobile",
        apply_layout=False,
        cfg=cfg,
        refresh_algorithms=False,
    )
    return _snapshot(trip)


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay curate baseline for CI")
    parser.add_argument("--write", type=Path, help="write golden JSON")
    parser.add_argument("--check", type=Path, help="compare against golden JSON")
    args = parser.parse_args()

    actual = _run()

    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Wrote {args.write}")
        return 0

    if args.check:
        expected = json.loads(args.check.read_text(encoding="utf-8"))
        if actual != expected:
            print("BASELINE MISMATCH", file=sys.stderr)
            print("expected:", json.dumps(expected, indent=2, sort_keys=True), file=sys.stderr)
            print("actual:", json.dumps(actual, indent=2, sort_keys=True), file=sys.stderr)
            return 1
        print("BASELINE OK")
        return 0

    print(json.dumps(actual, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
