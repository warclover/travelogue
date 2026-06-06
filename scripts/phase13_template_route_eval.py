#!/usr/bin/env python3
"""Phase 13 template route eval / replay artifact (release gate G3)."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _load_trip(trip_id: str, trips_dir: Path) -> dict:
    trip_json = trips_dir / trip_id / "trip.json"
    if not trip_json.is_file():
        raise FileNotFoundError(f"trip not found: {trip_json}")
    return json.loads(trip_json.read_text(encoding="utf-8"))


def _load_trip_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_eval(
    *,
    trip_id: str | None = None,
    trips_dir: Path,
    trip_json_path: Path | None = None,
    check_registry: bool = False,
    seed_template_selection: bool = False,
) -> dict[str, Any]:
    from travelogue.templates.registry import check_template_health, get_registry
    from travelogue.templating.router import ROUTER_CONFIG_VERSION, replay_template_decision

    reg = get_registry()
    out: dict[str, Any] = {
        "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "registryVersion": reg.version,
        "routerConfigVersion": ROUTER_CONFIG_VERSION,
        "templates": [],
    }
    for tid in reg.list_ids():
        healthy, errs = check_template_health(tid)
        out["templates"].append({"templateId": tid, "healthy": healthy, "errors": errs})
    if check_registry:
        out["registryHealthOk"] = all(t["healthy"] for t in out["templates"])
        return out

    if not trip_id and not trip_json_path:
        out["replay_match"] = None
        out["note"] = "supply --trip <tripId> or --trip-json <path> for replay eval"
        return out

    if trip_json_path:
        trip = _load_trip_json(trip_json_path)
        trip_id = trip_id or str(trip.get("tripId") or trip_json_path.stem)
    else:
        trip = _load_trip(trip_id or "", trips_dir)

    if seed_template_selection and not trip.get("templateSelection"):
        from travelogue.templating.router import apply_template_selection

        apply_template_selection(trip, mode="smart")

    replay = replay_template_decision(trip)
    sel = trip.get("templateSelection") or {}
    out.update(
        {
            "tripId": trip_id,
            "featureSnapshotVersion": sel.get("featureSnapshotVersion"),
            "registryVersion": sel.get("registryVersion") or reg.version,
            "routerConfigVersion": sel.get("routerConfigVersion") or ROUTER_CONFIG_VERSION,
            "decisionHash": sel.get("decisionHash"),
            "replay_match": replay.get("match"),
            "storedHash": replay.get("storedHash"),
            "replayedHash": replay.get("replayedHash"),
            "fallback_rate": 1.0 if sel.get("fallbackUsed") else 0.0,
            "manual_override_rate": 1.0 if sel.get("mode") == "manual" else 0.0,
            "error_rate": 0.0,
        }
    )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 13 template route eval")
    parser.add_argument("--trip", dest="trip_id", default=None)
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    parser.add_argument("--write", type=Path, default=None)
    parser.add_argument("--check-registry-health", action="store_true")
    parser.add_argument("--trip-json", type=Path, default=None, help="direct trip.json for replay")
    parser.add_argument("--seed-selection", action="store_true", help="apply smart selection if missing")
    parser.add_argument("--replay", action="store_true", help="alias for --trip replay section")
    args = parser.parse_args()

    result = build_eval(
        trip_id=args.trip_id,
        trips_dir=args.trips_dir.resolve(),
        trip_json_path=args.trip_json,
        check_registry=args.check_registry_health,
        seed_template_selection=args.seed_selection,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(text, encoding="utf-8")
        print(f"wrote {args.write}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
