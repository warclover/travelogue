"""Phase 23 moment blind-review helper (AC-P23-16 · M1/M2).

Usage:
  python scripts/phase23_moment_blind_review.py --init-template
  python scripts/phase23_moment_blind_review.py --trip-dir trips/demo-xxx
  python scripts/phase23_moment_blind_review.py --from-json docs/acceptance-records/phase23-moment-blind-review.json
  python scripts/phase23_moment_blind_review.py --yes 4 --total 8 --phase M1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW_PATH = ROOT / "docs" / "acceptance-records" / "phase23-moment-blind-review.json"
QUESTION = "这一张最能代表这趟旅行的决定性瞬间吗？"
M1_TARGET_PCT = 50.0
M2_TARGET_PCT = 60.0
M2_POOL_COVERAGE_MIN = 3


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def export_trip_moment_row(trip_dir: Path, *, export_layout: str = "web") -> dict[str, Any] | None:
    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        return None
    trip = _load(trip_json)
    curation = trip.get("curation") or {}
    pool = list(curation.get("momentPoolIds") or [])
    signature = str(trip.get("momentAssetId") or "").strip()
    if curation.get("momentSkipped") or not pool or not signature:
        return None

    from travelogue.curation.moment_scoring import score_ranked_moment_pool

    layout_assets = [a for a in trip.get("assets") or [] if a.get("layoutEligible", True)]
    ranked = score_ranked_moment_pool(trip, layout_assets, trip.get("chapters") or [], top_n=10)
    return {
        "tripId": trip.get("tripId") or trip_dir.name,
        "exportLayout": export_layout,
        "momentAssetId": signature,
        "momentPoolIds": pool,
        "scoreRankedMomentTop3": ranked[:3],
        "scoreRankedMomentTop10": ranked[:10],
        "momentCandidates": list(curation.get("momentCandidates") or []),
        "verdict": None,
        "poolCoverage": None,
        "notes": "Fill verdict=yes|no after blind review; poolCoverage = |userTop5 ∩ pool|",
    }


def init_review_template(path: Path, trip_dirs: list[Path] | None = None) -> dict[str, Any]:
    samples: list[dict[str, Any]] = []
    dirs = trip_dirs or []
    if not dirs:
        for candidate in ("demo-d66fe642a9", "linzhi", "mao"):
            trip_dir = ROOT / "trips" / candidate
            if (trip_dir / "trip.json").is_file():
                dirs.append(trip_dir)

    for trip_dir in dirs:
        row = export_trip_moment_row(trip_dir)
        if row:
            samples.append(row)

    template: dict[str, Any] = {
        "recordId": "phase23-moment-blind-review",
        "phase": "P23-PeakMoment",
        "question": QUESTION,
        "instructions": (
            "Blind review: show only the signature moment image (no pool order labels). "
            "Set verdict=yes|no. For M2, also record poolCoverage (user top-5 ∩ momentPoolIds)."
        ),
        "thresholds": {
            "M1": {"minSamples": 5, "yesRatePct": M1_TARGET_PCT},
            "M2": {
                "minSamples": 8,
                "yesRatePct": M2_TARGET_PCT,
                "poolCoverageMin": M2_POOL_COVERAGE_MIN,
            },
        },
        "samples": samples,
        "summary": {
            "judged": 0,
            "yesCount": 0,
            "yesRatePct": None,
            "passedM1": None,
            "passedM2": None,
            "notes": "Complete human blind review before release sign-off.",
        },
    }
    _save(path, template)
    return template


def eval_from_json(path: Path, *, phase: str = "M1") -> dict[str, Any]:
    data = _load(path)
    samples = data.get("samples") or []
    judged = [s for s in samples if s.get("verdict") in ("yes", "no")]
    yes_count = sum(1 for s in judged if s.get("verdict") == "yes")
    total = len(judged)
    yes_rate = (yes_count / total * 100.0) if total else 0.0
    target = M1_TARGET_PCT if phase.upper() == "M1" else M2_TARGET_PCT
    passed = yes_rate >= target if total else False
    pool_ok = True
    if phase.upper() == "M2":
        coverage_rows = [s for s in judged if isinstance(s.get("poolCoverage"), int)]
        pool_ok = all(c >= M2_POOL_COVERAGE_MIN for c in (s["poolCoverage"] for s in coverage_rows)) if coverage_rows else False
        passed = passed and pool_ok

    return {
        "phase": phase.upper(),
        "judged": total,
        "yesCount": yes_count,
        "yesRatePct": round(yes_rate, 2),
        "targetPct": target,
        "poolCoverageOk": pool_ok if phase.upper() == "M2" else None,
        "passed": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 23 moment blind-review export and scoring")
    parser.add_argument("--init-template", nargs="?", const=str(DEFAULT_REVIEW_PATH), help="write review JSON template")
    parser.add_argument("--trip-dir", type=Path, action="append", help="export one trip row (repeatable)")
    parser.add_argument("--from-json", type=Path, help="tally completed review JSON")
    parser.add_argument("--phase", choices=["M1", "M2"], default="M1")
    parser.add_argument("--yes", type=int, help="manual yes count")
    parser.add_argument("--total", type=int, help="manual judged total")
    parser.add_argument("--write", action="store_true", help="merge stats into review JSON summary")
    parser.add_argument("--out", type=Path, default=DEFAULT_REVIEW_PATH)
    args = parser.parse_args()

    if args.init_template:
        trip_dirs = [Path(p) for p in (args.trip_dir or [])]
        template = init_review_template(Path(args.init_template), trip_dirs or None)
        print(json.dumps({"written": args.init_template, "samples": len(template["samples"])}, indent=2))
        return 0

    if args.trip_dir and not args.init_template:
        rows = []
        for trip_dir in args.trip_dir:
            row = export_trip_moment_row(Path(trip_dir))
            if row:
                rows.append(row)
        print(json.dumps({"exported": len(rows), "rows": rows}, indent=2, ensure_ascii=False))
        return 0

    if args.from_json:
        stats = eval_from_json(args.from_json, phase=args.phase)
    elif args.yes is not None and args.total is not None:
        if args.total <= 0 or args.yes < 0 or args.yes > args.total:
            print("invalid --yes/--total", file=sys.stderr)
            return 2
        yes_rate = args.yes / args.total * 100.0
        target = M1_TARGET_PCT if args.phase == "M1" else M2_TARGET_PCT
        stats = {
            "phase": args.phase,
            "judged": args.total,
            "yesCount": args.yes,
            "yesRatePct": round(yes_rate, 2),
            "targetPct": target,
            "passed": yes_rate >= target,
        }
    else:
        parser.print_help()
        return 1

    print(json.dumps(stats, indent=2, ensure_ascii=False))
    if args.write and args.from_json:
        data = _load(args.from_json)
        data["summary"] = {**data.get("summary", {}), **stats}
        _save(args.from_json, data)
    return 0 if stats.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
