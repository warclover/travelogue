#!/usr/bin/env python3
"""P19 VLM pairwise judge (mock or API).

Usage:
  python scripts/book_quality_vlm_judge.py --baseline .cache/book-quality/baseline --candidate .cache/book-quality/p19
  python scripts/book_quality_vlm_judge.py --mock
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.eval.vlm_judge import aggregate_judge_report, mock_pairwise_judge


def _load_manifest(root: Path) -> dict[str, Any]:
    path = root / "manifest.json"
    if not path.is_file():
        raise FileNotFoundError(f"manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="P19 book quality VLM judge")
    parser.add_argument("--baseline", type=Path, default=ROOT / ".cache" / "book-quality" / "baseline")
    parser.add_argument("--candidate", type=Path, default=ROOT / ".cache" / "book-quality" / "p19")
    parser.add_argument("--out", type=Path, default=ROOT / ".cache" / "book-quality" / "judge")
    parser.add_argument("--mock", action="store_true", help="Use deterministic mock judge")
    parser.add_argument("--prompt-version", default="v1")
    args = parser.parse_args()

    base_manifest = _load_manifest(args.baseline)
    cand_manifest = _load_manifest(args.candidate) if args.candidate.is_dir() else {"trips": []}
    cand_map = {t["tripId"]: t for t in cand_manifest.get("trips") or []}

    args.out.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    for trip_row in base_manifest.get("trips") or []:
        tid = trip_row.get("tripId")
        if not tid or trip_row.get("status") != "ok":
            continue
        cand = cand_map.get(tid, trip_row)
        if args.mock:
            verdict = mock_pairwise_judge(tid, trip_row, cand)
        else:
            verdict = {
                "tripId": tid,
                "overallWinner": "tie",
                "dimensions": {},
                "confidence": 0.0,
                "briefReason": "API judge not configured; use --mock",
                "mode": "unconfigured",
            }
        results.append(verdict)

    summary = aggregate_judge_report(
        results,
        mode="mock" if args.mock else "api",
        prompt_version=args.prompt_version,
        repo_root=ROOT,
    )
    out_json = args.out / "judge_report.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Judge report: {out_json}")
    print(
        f"Candidate win rate: {summary['candidateWinRate']:.1%} "
        f"({summary['candidateWins']}/{summary['tripCount']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
