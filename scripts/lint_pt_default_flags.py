#!/usr/bin/env python3
"""Lint: product default acceleration flags must match default-flag signoff (M5).

Fails when code defaults enable PT acceleration but signoff is not approved:
  - PipelineConfig.parallel_ingest default is True
  - LlmConfig.narrate_concurrency default is > 1

Usage:
  python scripts/lint_pt_default_flags.py
  python scripts/lint_pt_default_flags.py --signoff path/to/signoff.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SIGNOFF = (
    ROOT / "docs" / "acceptance-records" / "pipeline-throughput-default-flag-signoff.json"
)


def _load_defaults() -> tuple[bool, int]:
    from travelogue.config import LlmConfig, PipelineConfig

    pipe = PipelineConfig()
    llm = LlmConfig()
    return bool(pipe.parallel_ingest), int(llm.narrate_concurrency)


def _signoff_approved(path: Path) -> tuple[bool, dict]:
    if not path.is_file():
        return False, {"error": f"signoff not found: {path}"}
    payload = json.loads(path.read_text(encoding="utf-8"))
    status = str(payload.get("status") or "").strip().lower()
    return status == "approved", payload


def check_defaults(*, signoff: Path) -> tuple[int, dict]:
    parallel_default, narrate_conc = _load_defaults()
    accelerated = parallel_default or narrate_conc > 1
    approved, payload = _signoff_approved(signoff)

    summary = {
        "parallel_ingest_default": parallel_default,
        "narrate_concurrency_default": narrate_conc,
        "acceleratedDefaults": accelerated,
        "signoff": str(signoff),
        "signoffStatus": (payload.get("status") if isinstance(payload, dict) else None),
        "signoffApproved": approved,
    }

    if not accelerated:
        summary["overallPassed"] = True
        summary["note"] = "defaults remain conservative (G0); signoff not required"
        return 0, summary

    if not approved:
        summary["overallPassed"] = False
        summary["error"] = (
            "accelerated product defaults require "
            "docs/acceptance-records/pipeline-throughput-default-flag-signoff.json "
            "status=approved (use gate --check-default-on)"
        )
        return 1, summary

    # When approved, flags in signoff should reflect the intended accelerated values.
    flags = payload.get("flags") if isinstance(payload, dict) else {}
    expected_pi = bool((flags or {}).get("pipeline.parallel_ingest"))
    expected_nc = int((flags or {}).get("llm.narrate_concurrency") or 1)
    if expected_pi != parallel_default or expected_nc != narrate_conc:
        summary["overallPassed"] = False
        summary["error"] = (
            f"signoff flags mismatch code defaults "
            f"(signoff parallel_ingest={expected_pi}, narrate_concurrency={expected_nc}; "
            f"code {parallel_default}, {narrate_conc})"
        )
        return 1, summary

    summary["overallPassed"] = True
    return 0, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint PT default flags ↔ signoff")
    parser.add_argument("--signoff", type=Path, default=DEFAULT_SIGNOFF)
    parser.add_argument("--json", action="store_true", help="print JSON summary")
    args = parser.parse_args()
    rc, summary = check_defaults(signoff=args.signoff)
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    elif rc == 0:
        print("lint_pt_default_flags: OK")
    else:
        print(f"lint_pt_default_flags: FAIL — {summary.get('error')}", file=sys.stderr)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
