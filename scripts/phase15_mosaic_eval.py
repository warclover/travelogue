#!/usr/bin/env python3
"""Compare mosaic5 exposure: mosaic.enabled on vs off (Phase 15 acceptance)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests._golden.helpers import build_mosaic_eligible_trip, plan_legacy_screens
from travelogue.config import get_config
from travelogue.curation.chapter_items import summarize_screen_patterns
from travelogue.layout_engine.mosaic.hook import drain_mosaic_logs
from travelogue.layout_engine.mosaic.metrics import (
    compute_mosaic_metrics,
    mcs_unified_exposure_rate,
    mosaic5_exposure_rate,
)


def _plan_with_mosaic(enabled: bool):
    buckets, aspects, assets = build_mosaic_eligible_trip()
    cfg = get_config()
    cfg = replace(
        cfg,
        mosaic=replace(
            cfg.mosaic,
            enabled=enabled,
            enabled_window_sizes=(3, 4, 5, 6, 8, 9),
            unified_mode=True,
            scorer_version="p15-s2",
            min_candidate_score=0.0,
        ),
    )
    import travelogue.config as config_mod

    orig = config_mod.get_config
    config_mod.get_config = lambda: cfg  # type: ignore[assignment]
    try:
        drain_mosaic_logs()
        chapters = plan_legacy_screens(buckets, aspects, assets)
        logs = drain_mosaic_logs() if enabled else []
    finally:
        config_mod.get_config = orig
    return chapters, logs, assets


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", type=Path, default=None)
    args = ap.parse_args()

    ch_off, _, _ = _plan_with_mosaic(False)
    ch_on, logs_on, _ = _plan_with_mosaic(True)
    rate_off = mosaic5_exposure_rate(ch_off)
    rate_on = mosaic5_exposure_rate(ch_on)
    rate_u_on = mcs_unified_exposure_rate(ch_on)
    out = {
        "mosaic5ExposureRateOff": rate_off,
        "mosaic5ExposureRateOn": rate_on,
        "mcsUnifiedExposureRateOn": rate_u_on,
        "enabledWindowSizes": [3, 4, 5, 6, 8, 9],
        "scorerVersion": "p15-s2",
        "lift": round(rate_on - rate_off, 6),
        "liftRatio": round(rate_on / rate_off, 4) if rate_off > 0 else None,
        "patternsOff": summarize_screen_patterns(ch_off),
        "patternsOn": summarize_screen_patterns(ch_on),
        "metricsOn": compute_mosaic_metrics(ch_on, mosaic_logs=logs_on),
    }
    text = json.dumps(out, indent=2, ensure_ascii=False)
    print(text)
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
