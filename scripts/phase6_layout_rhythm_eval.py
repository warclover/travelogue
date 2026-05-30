"""Phase 6 layout rhythm and diversity evaluator.

Usage:
  python scripts/phase6_layout_rhythm_eval.py --baseline-repeat 4.0 --candidate-repeat 2.8
  python scripts/phase6_layout_rhythm_eval.py --from-trip trips/demo/trip.json --write
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD_PATH = ROOT / "docs" / "acceptance-records" / "phase6-quality-eval.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _drop_pct(base: float, cur: float) -> float | None:
    if base == 0:
        return None
    return (base - cur) / base * 100.0


def _thresholds():
    from travelogue.config import get_config

    return get_config().phase6.ac


def metrics_from_trip(trip_path: Path) -> dict:
    trip = _load(trip_path)
    chapters = trip.get("chapters") or []
    assets = trip.get("assets") or []
    from travelogue.curation.layout_metrics import compute_layout_metrics

    return compute_layout_metrics(chapters, assets)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Phase 6 layout rhythm improvements")
    parser.add_argument("--baseline-repeat", type=float)
    parser.add_argument("--candidate-repeat", type=float)
    parser.add_argument("--candidate-variety", type=float, help="optional variety score")
    parser.add_argument("--from-trip", type=Path, help="compute metrics from trip.json")
    parser.add_argument("--record", type=Path, default=RECORD_PATH)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    if args.from_trip:
        stats = metrics_from_trip(args.from_trip)
        out = {
            "trip": str(args.from_trip),
            "layoutRepeatStreak": stats.get("layoutRepeatStreak"),
            "gravityBalance": stats.get("gravityBalance"),
            "longshotVisualVariety": stats.get("longshotVisualVariety"),
            "patternDiversity": stats.get("patternDiversity"),
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        if args.write and args.record.is_file():
            data = _load(args.record)
            data.setdefault("kpiPhase6", {})["layoutRepeatStreak"] = stats.get("layoutRepeatStreak")
            if stats.get("gravityBalance") is not None:
                data["kpiPhase6"]["gravityBalance"] = stats.get("gravityBalance")
            if stats.get("longshotVisualVariety") is not None:
                data["kpiPhase6"]["longshotVisualVariety"] = stats.get("longshotVisualVariety")
            runs = data.setdefault("runs", [])
            runs.append({"kind": "layout_rhythm_from_trip", **out})
            _save(args.record, data)
        return 0

    if args.baseline_repeat is None or args.candidate_repeat is None:
        parser.error("--baseline-repeat and --candidate-repeat are required unless --from-trip is set")

    ac_cfg = _thresholds()
    drop = _drop_pct(args.baseline_repeat, args.candidate_repeat)
    passed = drop is not None and drop >= ac_cfg.layout_repeat_streak_drop_pct
    out = {
        "baselineRepeatStreak": args.baseline_repeat,
        "candidateRepeatStreak": args.candidate_repeat,
        "repeatStreakDropPct": drop,
        "candidateVarietyScore": args.candidate_variety,
        "target": f"repeat streak drop >={ac_cfg.layout_repeat_streak_drop_pct}%",
        "passed": passed,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))

    if args.write:
        if not args.record.is_file():
            print(f"record not found: {args.record}", file=sys.stderr)
            return 2
        data = _load(args.record)
        data.setdefault("kpiBaseline", {})["layoutRepeatStreak"] = args.baseline_repeat
        data.setdefault("kpiPhase6", {})["layoutRepeatStreak"] = args.candidate_repeat
        ac = data.setdefault("acChecks", {}).setdefault("AC-P6-05", {})
        ac["layoutRepeatStreakDropPct"] = drop
        ac["passed"] = passed
        _save(args.record, data)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
