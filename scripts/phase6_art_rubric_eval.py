"""Phase 6 art-rubric evaluator.

Usage:
  python scripts/phase6_art_rubric_eval.py --story 4.2 --rhythm 4.1 --magazine 4.3 --abrupt-negative 0.08
"""

from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Phase 6 art rubric thresholds")
    parser.add_argument("--story", type=float, required=True, help="narrative score, 1-5")
    parser.add_argument("--rhythm", type=float, required=True, help="rhythm score, 1-5")
    parser.add_argument("--magazine", type=float, required=True, help="magazine feel score, 1-5")
    parser.add_argument(
        "--abrupt-negative",
        type=float,
        required=True,
        help="abruptness negative feedback ratio, e.g. 0.08",
    )
    args = parser.parse_args()

    checks = {
        "ART-AC-01_story": args.story >= 4.0,
        "ART-AC-02_rhythm": args.rhythm >= 4.0,
        "ART-AC-03_magazine": args.magazine >= 4.0,
        "ART-AC-05_abrupt_negative": args.abrupt_negative < 0.10,
    }
    pass_count = sum(1 for v in checks.values() if v)
    result = {
        "inputs": {
            "story": args.story,
            "rhythm": args.rhythm,
            "magazine": args.magazine,
            "abruptNegativeRatio": args.abrupt_negative,
        },
        "checks": checks,
        "passedCount": pass_count,
        "threshold": ">=3/4",
        "passed": pass_count >= 3,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

