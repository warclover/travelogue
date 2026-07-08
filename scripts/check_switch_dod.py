#!/usr/bin/env python3
"""M-D1 prep · report dual-path switch DoD readiness (PRD §3.3).

Does not delete legacy — run weekly until calendar DoD, then gate M-D1.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SWITCHES = (
    {
        "key": "pipeline.orchestration",
        "legacy_value": "legacy",
        "launch": date(2026, 7, 8),
        "dod": date(2026, 8, 5),
    },
    {
        "key": "layout.planner_impl",
        "legacy_value": "curation",
        "launch": date(2026, 7, 8),
        "dod": date(2026, 8, 5),
    },
)


def _scan_configs_for_legacy() -> list[str]:
    hits: list[str] = []
    example = ROOT / "config.example.yaml"
    if not example.is_file():
        return hits
    text = example.read_text(encoding="utf-8")
    if "orchestration: legacy" in text:
        hits.append("config.example.yaml: pipeline.orchestration=legacy")
    if "planner_impl: curation" in text:
        hits.append("config.example.yaml: layout.planner_impl=curation")
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--as-of",
        default=date.today().isoformat(),
        help="Report date (YYYY-MM-DD)",
    )
    args = parser.parse_args()
    as_of = datetime.strptime(args.as_of, "%Y-%m-%d").date()

    rows = []
    all_calendar_ok = True
    for sw in SWITCHES:
        days_left = (sw["dod"] - as_of).days
        calendar_ok = days_left <= 0
        if not calendar_ok:
            all_calendar_ok = False
        rows.append(
            {
                "key": sw["key"],
                "legacy_value": sw["legacy_value"],
                "launch": sw["launch"].isoformat(),
                "dod": sw["dod"].isoformat(),
                "days_until_dod": days_left,
                "calendar_dod_met": calendar_ok,
            }
        )

    config_hits = _scan_configs_for_legacy()
    report = {
        "as_of": as_of.isoformat(),
        "switches": rows,
        "calendar_dod_all_met": all_calendar_ok,
        "manual_checks_remaining": [
            "weekly orchestration_dual_run diff empty (4 consecutive weeks)",
            "no dogfood rollback requests",
            "legacy values absent from production configs",
        ],
        "config_hits": config_hits,
        "m_d1_ready": all_calendar_ok and not config_hits,
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
