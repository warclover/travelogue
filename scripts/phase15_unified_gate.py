#!/usr/bin/env python3
"""Phase 15 unified_mode rollout gate (DESIGN §12.1) — offline replay records.

Reads acceptance JSON and checks thresholds. Exit 0 = pass for enabling unified_mode.

Usage:
  python scripts/phase15_unified_gate.py
  python scripts/phase15_unified_gate.py --replay docs/acceptance-records/phase15-replay-scenarios.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Calibrated on synthetic replay; tighten for production 24h windows.
GATE = {
    "max_fallback_rate": 0.15,
    "max_render_error_rate": 0.0,
    "min_mosaic5_exposure_lift": 0.0,
    "min_mosaic5_lift_ratio_when_baseline": 1.0,
    "min_mcs_unified_on_mixed_aspects": 1.0,
    "min_eligible_to_screen_coverage": 0.99,
}

# CI fixture：含 breath-pause / 章首 hero，eligible 略多于 displayed
_FIXTURE_COVERAGE_MIN = {
    "golden-mixed-scenes": 0.85,
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_replay_scenarios(data: dict) -> list[str]:
    failures: list[str] = []
    scenarios = (data.get("scenarios") or {})
    mixed = scenarios.get("mixed_aspects", {})
    metrics = mixed.get("metricsOn") or {}
    fb = float(metrics.get("mosaicFallbackRate") or metrics.get("layout.mosaic_v2.fallback_rate") or 0)
    mcs = float(mixed.get("mcsUnifiedExposureRateOn") or 0)
    render_err = float(metrics.get("layout.render.error_rate") or 0)
    if fb > GATE["max_fallback_rate"]:
        failures.append(f"mixed_aspects fallback_rate {fb} > {GATE['max_fallback_rate']}")
    if mcs < GATE["min_mcs_unified_on_mixed_aspects"]:
        failures.append(f"mixed_aspects mcs_unified {mcs} < {GATE['min_mcs_unified_on_mixed_aspects']}")
    if render_err > GATE["max_render_error_rate"]:
        failures.append(f"mixed_aspects render_error_rate {render_err}")

    eligible = scenarios.get("mosaic5_eligible", {})
    m5_metrics = eligible.get("metricsOn") or {}
    if float(m5_metrics.get("mosaicFallbackRate") or 0) > GATE["max_fallback_rate"]:
        failures.append("mosaic5_eligible fallback_rate too high")
    return failures


def _check_curate_replay(data: dict) -> list[str]:
    failures: list[str] = []
    for trip in data.get("trips") or []:
        on = trip.get("mosaicOn") or {}
        metrics = on.get("mosaicMetrics") or on.get("layoutMetrics") or {}
        fb = float(metrics.get("mosaicFallbackRate") or metrics.get("layout.mosaic_v2.fallback_rate") or 0)
        render_err = float(metrics.get("layout.render.error_rate") or 0)
        lift = (trip.get("lift") or {}).get("mosaic5ExposureRate", 0)
        if fb > GATE["max_fallback_rate"]:
            failures.append(f"{trip.get('tripId')}: fallback_rate {fb}")
        if render_err > GATE["max_render_error_rate"]:
            failures.append(f"{trip.get('tripId')}: render_error_rate {render_err}")
        if float(lift) < GATE["min_mosaic5_exposure_lift"]:
            failures.append(f"{trip.get('tripId')}: mosaic5 lift {lift}")
        off_m5 = float((trip.get("mosaicOff") or {}).get("mosaic5ExposureRate") or 0)
        on_m5 = float((trip.get("mosaicOn") or {}).get("mosaic5ExposureRate") or 0)
        if off_m5 > 0 and on_m5 / off_m5 < GATE["min_mosaic5_lift_ratio_when_baseline"]:
            failures.append(
                f"{trip.get('tripId')}: mosaic5 lift ratio {on_m5 / off_m5:.4f} "
                f"< {GATE['min_mosaic5_lift_ratio_when_baseline']}"
            )
        tid = trip.get("tripId") or ""
        cov_min = _FIXTURE_COVERAGE_MIN.get(tid, GATE["min_eligible_to_screen_coverage"])
        cov_val = float(
            trip.get("eligibleToScreenCoverageOn")
            or (trip.get("mosaicOn") or {}).get("layoutMetrics", {}).get(
                "eligible_to_screen_coverage", 1.0
            )
            or 1.0
        )
        if cov_val < cov_min:
            failures.append(
                f"{tid}: eligible_to_screen_coverage {cov_val} < {cov_min}"
            )
    return failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--replay",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "phase15-replay-scenarios.json",
    )
    ap.add_argument(
        "--curate",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "phase15-curate-replay.json",
    )
    args = ap.parse_args()

    failures: list[str] = []
    if args.replay.is_file():
        failures.extend(_check_replay_scenarios(_load(args.replay)))
    else:
        print(f"SKIP missing {args.replay}", file=sys.stderr)

    if args.curate.is_file():
        failures.extend(_check_curate_replay(_load(args.curate)))
    else:
        print(f"SKIP missing {args.curate}", file=sys.stderr)

    if failures:
        print("FAIL unified_mode gate:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS unified_mode gate (offline replay)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
