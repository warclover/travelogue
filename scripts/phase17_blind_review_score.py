"""P17 dogfood blind review scorer · §9 准入 ≥90% 通过率检查.

Usage:
  python scripts/phase17_blind_review_score.py docs/acceptance-records/p17-dogfood-blind-review.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "acceptance-records" / "p17-dogfood-blind-review.template.json"
PASS_THRESHOLD = 0.90


def score_review(doc: dict) -> dict:
    pairs = doc.get("tripPairs") or []
    scored = 0
    preferred_candidate = 0
    for pair in pairs:
        pref = pair.get("preference")
        if pref is None:
            continue
        scored += 1
        if str(pref).lower() in ("b", "candidate", "lse", "shadow"):
            preferred_candidate += 1
    rate = (preferred_candidate / scored) if scored else None
    admission = doc.get("admissionDecision") or {}
    approved = admission.get("approved")
    return {
        "pairCount": len(pairs),
        "scoredPairs": scored,
        "candidatePreferred": preferred_candidate,
        "candidatePreferredRate": round(rate, 4) if rate is not None else None,
        "passesThreshold": rate is not None and rate >= PASS_THRESHOLD,
        "explicitlyApproved": approved is True,
        "admissionOk": (rate is not None and rate >= PASS_THRESHOLD) or approved is True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score P17 dogfood blind review JSON")
    parser.add_argument("review", type=Path, nargs="?", help="Completed blind review JSON")
    parser.add_argument("--strict", action="store_true", help="Exit 1 when below 90 percent threshold")
    args = parser.parse_args()

    if args.review and args.review.is_file():
        doc = json.loads(args.review.read_text(encoding="utf-8"))
    elif TEMPLATE.is_file():
        doc = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    else:
        print(json.dumps({"error": "no review file"}, ensure_ascii=False))
        return 1

    result = score_review(doc)
    payload = {
        "template": str(TEMPLATE.relative_to(ROOT)),
        "reviewFile": str(args.review) if args.review else None,
        "threshold": PASS_THRESHOLD,
        **result,
        "notes": "Complete tripPairs.preference before W3b-12; ≥90% candidate preferred or admissionDecision.approved=true.",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.strict and not result.get("admissionOk"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
