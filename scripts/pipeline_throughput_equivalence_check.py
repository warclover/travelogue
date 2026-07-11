"""Pipeline Throughput · live structure equivalence check (M5).

Computes L-struct fingerprints from trip JSON (活 diff), not only pre-filled rates.

Usage:
  python scripts/pipeline_throughput_equivalence_check.py --serial trip-a.json --parallel trip-b.json
  python scripts/pipeline_throughput_equivalence_check.py --from-record --strict
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD = ROOT / "docs" / "acceptance-records" / "pipeline-throughput-perf-eval.json"


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def structure_fingerprint(trip: dict[str, Any]) -> dict[str, Any]:
    """L-struct fields used by NR-PT / AC-PT-03."""
    assets = trip.get("assets") or []
    chapters = trip.get("chapters") or []
    curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
    return {
        "assetIds": [a.get("id") for a in assets],
        "takenAt": [a.get("takenAt") for a in assets],
        "burstGroupId": [a.get("burstGroupId") for a in assets],
        "dedupeGroupId": [a.get("dedupeGroupId") for a in assets],
        "contentSig": [a.get("contentSig") for a in assets],
        "excludedLowRes": list(curation.get("excludedLowResAssetIds") or []),
        "chapterIds": [c.get("id") for c in chapters],
        "coverAssetId": trip.get("coverAssetId"),
    }


def compare_structure(
    serial_trip: dict[str, Any],
    parallel_trip: dict[str, Any],
) -> dict[str, Any]:
    left = structure_fingerprint(serial_trip)
    right = structure_fingerprint(parallel_trip)
    mismatches = [k for k in left if left.get(k) != right.get(k)]
    rate = 1.0 if not mismatches else 0.0
    return {
        "structure_hash_rate_fixed": rate,
        "matched": len(mismatches) == 0,
        "mismatchedKeys": mismatches,
        "serial": left,
        "parallel": right,
        "checkedAt": _now(),
    }


def _load_trip(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _from_record(record_path: Path, *, strict: bool, write: bool) -> tuple[dict[str, Any], int]:
    if not record_path.is_file():
        return {"overallPassed": False, "error": "record not found"}, 2
    record = json.loads(record_path.read_text(encoding="utf-8"))
    nr = record.setdefault("nr_pt", {})
    # Live path expects caller to have written structure_hash_rate_fixed via --serial/--parallel.
    # Here we only validate / surface existing live fields (no silent inventing of 1.0).
    rate = nr.get("structure_hash_rate_fixed")
    prefer_web = nr.get("prefer_web_derivative_in_nr_profile")
    passed = None
    if rate is not None:
        try:
            passed = abs(float(rate) - 1.0) < 1e-12
        except (TypeError, ValueError):
            passed = False
    if prefer_web is True:
        # NR profile should force prefer_web_derivative=false for L-embed.
        nr.setdefault("nr_profile_warning", "prefer_web_derivative_in_nr_profile should be false")
    nr["passed"] = passed
    nr["checkedAt"] = _now()
    summary = {
        "overallPassed": bool(passed) if passed is not None else False,
        "mode": "from-record",
        "structure_hash_rate_fixed": rate,
        "nr_pt_passed": passed,
        "strict": strict,
        "note": "Provide --serial/--parallel for live diff; from-record only reads computed rates",
    }
    if write:
        record_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    if passed is None and strict:
        return summary, 2
    return summary, (0 if passed else 1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline Throughput equivalence (live L-struct)")
    parser.add_argument("--serial", type=Path, help="trip.json from parallel_ingest=false")
    parser.add_argument("--parallel", type=Path, help="trip.json from parallel_ingest=true")
    parser.add_argument("--from-record", action="store_true")
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    parser.add_argument("--write", action="store_true", help="persist nr_pt into record")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    if args.serial or args.parallel:
        if not (args.serial and args.parallel):
            parser.error("--serial and --parallel must be used together")
        result = compare_structure(_load_trip(args.serial), _load_trip(args.parallel))
        summary = {
            "overallPassed": bool(result["matched"]),
            "mode": "live-diff",
            **{k: result[k] for k in ("structure_hash_rate_fixed", "matched", "mismatchedKeys", "checkedAt")},
        }
        if args.write and args.record.is_file():
            record = json.loads(args.record.read_text(encoding="utf-8"))
            nr = record.setdefault("nr_pt", {})
            nr["structure_hash_rate_fixed"] = result["structure_hash_rate_fixed"]
            nr["passed"] = result["matched"]
            nr["checkedAt"] = result["checkedAt"]
            nr["prefer_web_derivative_in_nr_profile"] = False
            args.record.write_text(
                json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0 if result["matched"] else 1

    if args.from_record:
        summary, rc = _from_record(args.record, strict=args.strict, write=args.write)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return rc

    parser.error("specify --serial/--parallel or --from-record")
    return 2


if __name__ == "__main__":
    sys.exit(main())
