#!/usr/bin/env python3
"""P19 layout blind-review helper (human calibration + win-rate summary).

Usage:
  python scripts/book_quality_blind_review.py --init
  python scripts/book_quality_blind_review.py --from-json docs/acceptance-records/p19-judge-calibration.json
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "acceptance-records" / "p19-judge-calibration.template.json"
DEFAULT_OUT = ROOT / "docs" / "acceptance-records" / "p19-judge-calibration.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _summarize(data: dict[str, Any]) -> dict[str, Any]:
    trips = data.get("trips") or []
    human_b = 0
    human_a = 0
    human_tie = 0
    vlm_b = 0
    vlm_a = 0
    story_candidate = 0
    story_total = 0
    agree = 0
    comparable = 0
    for row in trips:
        hw = row.get("humanWinner")
        vw = row.get("vlmWinner")
        if hw == "candidate":
            human_b += 1
        elif hw == "baseline":
            human_a += 1
        elif hw == "tie":
            human_tie += 1
        if vw == "B" or vw == "candidate":
            vlm_b += 1
        elif vw == "A" or vw == "baseline":
            vlm_a += 1
        if hw and vw and hw != "tie" and vw != "tie":
            comparable += 1
            h_norm = "candidate" if hw == "candidate" else "baseline"
            v_norm = "candidate" if vw in ("B", "candidate") else "baseline"
            if h_norm == v_norm:
                agree += 1
        sc = row.get("storyClarity")
        if sc:
            story_total += 1
            if sc == "candidate":
                story_candidate += 1
    n = len(trips) or 1
    summary = data.setdefault("summary", {})
    summary["humanPairwiseWinRate"] = round(human_b / n, 4)
    summary["vlmPairwiseWinRate"] = round(vlm_b / n, 4)
    summary["agreementRate"] = round(agree / comparable, 4) if comparable else None
    summary["storyClarityPreferCandidatePct"] = (
        round(story_candidate / story_total, 4) if story_total else None
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="P19 blind review recorder")
    parser.add_argument("--init", action="store_true", help="Copy template to default out path")
    parser.add_argument("--from-json", type=Path, help="Summarize an existing calibration file")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    if args.init:
        if not TEMPLATE.is_file():
            print(f"Template missing: {TEMPLATE}", file=sys.stderr)
            return 1
        data = _load(TEMPLATE)
        _save(args.out, data)
        print(f"Initialized: {args.out}")
        return 0

    path = args.from_json or args.out
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 1
    data = _load(path)
    summary = _summarize(data)
    _save(path, data)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
