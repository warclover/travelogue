#!/usr/bin/env python3
"""G8 automated prereq check (Studio template create + API smoke)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_checks() -> dict:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_studio_template_create.py",
        "tests/test_studio_import_template_mode.py",
        "tests/test_template_platform.py",
        "-q",
        "--tb=no",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "pytest_ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "tail": (proc.stdout or proc.stderr or "")[-400:],
        "manualStillRequired": [
            "docs/reports/phase13-g8-studio-walkthrough.md 产品/前端签字",
            "浏览器验证 template_selector_impression / 三态 toast",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 13 G8 automation prereq")
    parser.add_argument(
        "--write",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "phase13-g8-signoff.json",
    )
    parser.add_argument("--merge-signoff", action="store_true", help="更新 g8 signoff 的 automatedPrereq")
    args = parser.parse_args()

    result = run_checks()
    if args.merge_signoff and args.write.is_file():
        doc = json.loads(args.write.read_text(encoding="utf-8"))
        doc["automatedPrereq"] = {
            **(doc.get("automatedPrereq") or {}),
            "pass": result["pytest_ok"],
            "checkedAt": result["generatedAt"],
            "pytest_tail": result["tail"],
        }
        if result["pytest_ok"] and doc.get("status") == "pending_human":
            doc["status"] = "automated_pass_pending_signoff"
        out = doc
    else:
        out = result
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(text, encoding="utf-8")
        print(f"wrote {args.write} (pytest_ok={result['pytest_ok']})")
    else:
        print(text)
    return 0 if result["pytest_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
