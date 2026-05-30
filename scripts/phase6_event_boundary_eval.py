"""Phase 6 event-boundary quick evaluator.

Usage:
  python scripts/phase6_event_boundary_eval.py --baseline 0.52 --candidate 0.61
  python scripts/phase6_event_boundary_eval.py --from-fixture golden-kyoto-gps --write
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD_PATH = ROOT / "docs" / "acceptance-records" / "phase6-quality-eval.json"
FIXTURES = ROOT / "tests" / "fixtures" / "clustering"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _lift_pct(base: float, cur: float) -> float | None:
    if base == 0:
        return None
    return (cur - base) / base * 100.0


def _eval_fixture_agreement(trip_id: str) -> dict:
    sys.path.insert(0, str(ROOT))
    from travelogue.config import GeoClusterConfig
    from travelogue.curation.cluster_eval import geo_segment_agreement_rate, segments_to_eval_dict
    from travelogue.curation.geo_events import detect_geo_events
    from tests.clustering_fixtures import load_fixture_assets, load_fixture_golden_segments

    assets = load_fixture_assets(trip_id)
    golden = load_fixture_golden_segments(trip_id)
    fixed_segs, _ = detect_geo_events(assets, cfg=GeoClusterConfig(event_gap_mode="fixed"))
    auto_segs, _ = detect_geo_events(assets, cfg=GeoClusterConfig(event_gap_mode="auto"))
    baseline = geo_segment_agreement_rate(golden, segments_to_eval_dict(fixed_segs))
    candidate = geo_segment_agreement_rate(golden, segments_to_eval_dict(auto_segs))
    return {
        "fixture": trip_id,
        "baselineF1Proxy": baseline,
        "candidateF1Proxy": candidate,
        "liftPct": _lift_pct(baseline, candidate),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Phase 6 event boundary lift")
    parser.add_argument("--baseline", type=float)
    parser.add_argument("--candidate", type=float)
    parser.add_argument("--from-fixture", type=str, help="clustering fixture id e.g. golden-kyoto-gps")
    parser.add_argument("--record", type=Path, default=RECORD_PATH)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    if args.from_fixture:
        stats = _eval_fixture_agreement(args.from_fixture)
        lift = stats.get("liftPct")
        passed = lift is not None and lift >= 10.0
        out = {**stats, "target": ">=10%", "passed": passed}
        print(json.dumps(out, indent=2, ensure_ascii=False))
        if args.write and args.record.is_file():
            data = _load(args.record)
            data.setdefault("kpiBaseline", {})["eventBoundaryF1"] = stats["baselineF1Proxy"]
            data.setdefault("kpiPhase6", {})["eventBoundaryF1"] = stats["candidateF1Proxy"]
            ac = data.setdefault("acChecks", {}).setdefault("AC-P6-03", {})
            ac["eventBoundaryF1LiftPct"] = lift
            ac["passed"] = passed
            _save(args.record, data)
        return 0 if passed else 1

    if args.baseline is None or args.candidate is None:
        parser.error("--baseline/--candidate or --from-fixture is required")

    lift = _lift_pct(args.baseline, args.candidate)
    passed = lift is not None and lift >= 10.0
    out = {
        "baselineF1": args.baseline,
        "candidateF1": args.candidate,
        "liftPct": lift,
        "target": ">=10%",
        "passed": passed,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))

    if args.write:
        if not args.record.is_file():
            print(f"record not found: {args.record}", file=sys.stderr)
            return 2
        data = _load(args.record)
        data.setdefault("kpiBaseline", {})["eventBoundaryF1"] = args.baseline
        data.setdefault("kpiPhase6", {})["eventBoundaryF1"] = args.candidate
        ac = data.setdefault("acChecks", {}).setdefault("AC-P6-03", {})
        ac["eventBoundaryF1LiftPct"] = lift
        ac["passed"] = passed
        _save(args.record, data)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

