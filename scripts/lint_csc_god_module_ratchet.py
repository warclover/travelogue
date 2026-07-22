#!/usr/bin/env python3
"""CSC W2b/c · god-module line-count ratchet (curate / studio_pipeline).

Fails when tracked files grow above baseline. Intentional growth must refresh
baseline in the same PR with review (only-down preferred; growth needs explicit
--allow-growth).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "docs" / "acceptance-records" / "csc-w2b-god-module-ratchet-baseline.json"
TARGETS = (
    "travelogue/curation/curate.py",
    "travelogue/web/studio_pipeline.py",
)


def _line_count(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def scan() -> dict[str, int]:
    out: dict[str, int] = {}
    for rel in TARGETS:
        path = ROOT / rel
        if not path.is_file():
            raise SystemExit(f"missing target: {rel}")
        out[rel] = _line_count(path)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument(
        "--allow-growth",
        action="store_true",
        help="Permit baseline update even when one or more files grew",
    )
    args = parser.parse_args()

    current = scan()
    if args.update_baseline:
        if BASELINE.is_file() and not args.allow_growth:
            old = json.loads(BASELINE.read_text(encoding="utf-8")).get("lines") or {}
            grew = {k: current[k] for k in current if current[k] > int(old.get(k, 0))}
            if grew:
                print("refusing baseline update; growth without --allow-growth:", file=sys.stderr)
                for k, v in grew.items():
                    print(f"  {k}: {old.get(k)} -> {v}", file=sys.stderr)
                return 1
        report = {"lines": current}
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("baseline updated:", json.dumps(current))
        return 0

    if not BASELINE.is_file():
        print("missing baseline; run with --update-baseline", file=sys.stderr)
        print(json.dumps({"lines": current}, indent=2))
        return 1

    old = json.loads(BASELINE.read_text(encoding="utf-8")).get("lines") or {}
    regressions: list[str] = []
    improvements: list[str] = []
    for rel, n in current.items():
        base = int(old.get(rel, n))
        print(f"{rel}: {n} lines (ceiling {base})")
        if n > base:
            regressions.append(f"{rel}: {n} > {base}")
        elif n < base:
            improvements.append(f"{rel}: {base} -> {n}")
    if improvements:
        print("improved:", "; ".join(improvements))
    if regressions:
        print("REGRESSION: god-module grew beyond ratchet ceiling", file=sys.stderr)
        for r in regressions:
            print(f"  {r}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
