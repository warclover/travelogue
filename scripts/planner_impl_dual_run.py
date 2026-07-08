#!/usr/bin/env python3
"""Dual-run layout.planner_impl paths (PRD §3.3 · M-B4b DoD).

Runs the arch-equivalence pipeline under layout_engine vs curation planner_impl
and asserts normalized trip + layout_snapshot parity.
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DEFAULT_FIXTURES = (
    "golden-mixed-scenes",
    "schemas/fixtures/trip.render_golden.json",
)


def _run_fixture(impl: str, fixture: str, *, work_dir: Path) -> dict:
    from travelogue.config import get_config
    from travelogue.config.runtime import config_override, reset_config_cache
    from scripts.arch_equivalence_check import (
        _load_trip_fixture,
        _run_arch_pipeline,
        normalize_trip,
    )

    reset_config_cache()
    base = get_config()
    cfg = replace(base, layout=replace(base.layout, planner_impl=impl))
    trip, _source = _load_trip_fixture(fixture)
    with config_override(cfg):
        if trip.get("chapters") and str(_source).endswith("trip.render_golden.json"):
            body = deepcopy(trip)
        else:
            body = _run_arch_pipeline(trip, work_dir=work_dir / impl, label="run")
    return normalize_trip(body)


def compare_fixture(fixture: str, *, work_dir: Path) -> dict:
    from scripts.arch_equivalence_check import diff_normalized
    from tests._golden.helpers import layout_snapshot

    left = _run_fixture("layout_engine", fixture, work_dir=work_dir)
    right = _run_fixture("curation", fixture, work_dir=work_dir)
    l3a = diff_normalized(left, right)
    snap_l = layout_snapshot(left.get("chapters") or [])
    snap_r = layout_snapshot(right.get("chapters") or [])
    l3b_ok = snap_l == snap_r
    return {
        "fixture": fixture,
        "ok": not l3a and l3b_ok,
        "l3aDiff": l3a,
        "l3bOk": l3b_ok,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dual-run layout.planner_impl equivalence")
    parser.add_argument("fixtures", nargs="*", default=list(DEFAULT_FIXTURES))
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".cache" / "planner-impl-dual")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    reports = [compare_fixture(f, work_dir=args.work_dir) for f in args.fixtures]
    payload = {"ok": all(r["ok"] for r in reports), "reports": reports}
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for report in reports:
            status = "OK" if report["ok"] else "FAIL"
            print(f"{status} {report['fixture']}")
            for line in report.get("l3aDiff") or []:
                print(f"  L3a: {line}")
            if not report.get("l3bOk"):
                print("  L3b: layout_snapshot mismatch")
        print("planner_impl_dual_run: OK" if payload["ok"] else "planner_impl_dual_run: FAIL")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
