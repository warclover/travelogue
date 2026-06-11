#!/usr/bin/env python3
"""P19 · run golden-trip automated gates and archive summary.

Runs rhythm audit, curate profile (vs P16), screen signatures, subset audit;
writes consolidated report for acceptance records.

Usage:
  python scripts/p19_golden_gate_run.py
  python scripts/p19_golden_gate_run.py --skip-baseline-compare
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "book-quality"
ACCEPTANCE = ROOT / "docs" / "acceptance-records"


def _run(cmd: list[str]) -> int:
    print(f"\n>> {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="P19 golden gate batch")
    parser.add_argument(
        "--skip-baseline-compare",
        action="store_true",
        help="Skip screen signature diff vs baseline manifest",
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=ACCEPTANCE / "p19-gate-run.json",
    )
    args = parser.parse_args()

    py = sys.executable
    scripts = ROOT / "scripts"
    failures: list[str] = []

    rc = _run([py, str(scripts / "p19_rhythm_audit.py")])
    if rc:
        failures.append("rhythm_audit")

    rc = _run([py, str(scripts / "p19_curate_profile.py"), "--compare-p16"])
    if rc:
        failures.append("curate_profile")

    rc = _run([py, str(scripts / "p19_subset_golden_audit.py")])
    if rc:
        failures.append("subset_audit")

    sig_rc = _run([py, str(scripts / "book_quality_screen_signatures.py")])
    baseline_manifest = CACHE / "baseline" / "manifest.json"
    if not args.skip_baseline_compare and baseline_manifest.is_file():
        sig_rc = _run(
            [
                py,
                str(scripts / "book_quality_screen_signatures.py"),
                "--compare",
                str(baseline_manifest),
            ]
        )
        if sig_rc:
            failures.append("screen_signatures_diff")
    elif sig_rc:
        failures.append("screen_signatures")

    rhythm = json.loads((CACHE / "rhythm-audit" / "report.json").read_text(encoding="utf-8"))
    profile = json.loads((CACHE / "curate-profile.json").read_text(encoding="utf-8"))
    subset = json.loads((CACHE / "subset-golden-audit.json").read_text(encoding="utf-8"))

    sig_diff_path = CACHE / "screens-signatures" / "diff_report.json"
    sig_diff = None
    if sig_diff_path.is_file():
        sig_diff = json.loads(sig_diff_path.read_text(encoding="utf-8"))

    p16_p95 = profile.get("p16Baseline", {}).get("p95Seconds") or 0
    cur_p95 = profile.get("current", {}).get("p95Seconds") or 0
    p95_increase_pct = (
        round((cur_p95 - p16_p95) / p16_p95 * 100, 2) if p16_p95 > 0 else None
    )
    p95_within_gate = cur_p95 <= p16_p95 * 1.15 if p16_p95 > 0 else None

    summary = {
        "schema": "travelogue.acceptance.p19-gate-run",
        "version": 1,
        "program": "Phase 19 · LQU",
        "date": date.today().isoformat(),
        "branch": "phase19/lean-quality-uplift",
        "gates": {
            "rhythmAudit": {
                "ok": rhythm.get("ok"),
                "totalViolations": rhythm.get("totalViolations"),
                "artifact": ".cache/book-quality/rhythm-audit/report.json",
            },
            "curateProfile": {
                "p16P95Seconds": p16_p95,
                "currentP95Seconds": cur_p95,
                "p95IncreasePct": p95_increase_pct,
                "p95WithinGate": p95_within_gate,
                "gateThreshold": "current_p95 <= p16_p95 * 1.15",
                "artifact": ".cache/book-quality/curate-profile.json",
            },
            "subsetMedian": {
                "medianActualReduction": subset.get("medianActualReduction"),
                "withinGate": subset.get("withinGate"),
                "gateRange": [0.25, 0.40],
                "artifact": ".cache/book-quality/subset-golden-audit.json",
            },
            "screenSignatures": {
                "baselineCompareSkipped": args.skip_baseline_compare or not baseline_manifest.is_file(),
                "diffOk": sig_diff.get("ok") if sig_diff else None,
                "mismatches": sig_diff.get("mismatches") if sig_diff else None,
                "artifact": ".cache/book-quality/screens-signatures/signatures.json",
            },
        },
        "failures": failures,
        "ok": not failures and rhythm.get("ok") and (p95_within_gate is not False),
    }

    args.archive.parent.mkdir(parents=True, exist_ok=True)
    args.archive.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nArchived gate summary -> {args.archive}")
    print(f"Overall ok={summary['ok']} failures={failures}")
    return 1 if failures or not summary["ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
