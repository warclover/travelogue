#!/usr/bin/env python3
"""Phase 15 multi-scenario replay (PRD §9.3 · synthetic + fixture trips)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config import get_config
from travelogue.curation.chapter_items import summarize_screen_patterns
from travelogue.curation.mosaic.hook import drain_mosaic_logs
from travelogue.curation.mosaic.metrics import compute_mosaic_metrics, mcs_unified_exposure_rate

from tests._golden.helpers import (
    build_mosaic_eligible_trip,
    build_mosaic_landscape9_trip,
    build_mosaic_portrait8_trip,
    build_mixed_aspects_trip,
    build_portrait_heavy_trip,
    plan_legacy_screens,
    plan_mosaic_screens,
)

SCENARIOS = {
    "mosaic5_eligible": lambda: build_mosaic_eligible_trip(),
    "portrait_heavy": lambda: build_portrait_heavy_trip(),
    "mixed_aspects": lambda: build_mixed_aspects_trip(),
    "portrait_grid8": lambda: build_mosaic_portrait8_trip(),
    "landscape_nine": lambda: build_mosaic_landscape9_trip(),
}


def _plan(name: str, enabled: bool):
    buckets, aspects, assets = SCENARIOS[name]()
    cfg = get_config()
    cfg = replace(
        cfg,
        mosaic=replace(
            cfg.mosaic,
            enabled=enabled,
            enabled_window_sizes=(3, 4, 5, 6, 8, 9),
            unified_mode=True,
            min_candidate_score=0.0,
        ),
    )
    import travelogue.config as config_mod

    orig = config_mod.get_config
    config_mod.get_config = lambda: cfg  # type: ignore[assignment]
    try:
        drain_mosaic_logs()
        kw: dict = {}
        if name == "portrait_grid8":
            kw = {
                "trip_photo_total": 60,
                "orientation_summary": {"portrait": 8, "landscape": 0},
            }
        elif name == "landscape_nine":
            kw = {"trip_photo_total": 60}
        plan_fn = plan_mosaic_screens if enabled else plan_legacy_screens
        chapters = plan_fn(buckets, aspects, assets, **kw)
        logs = drain_mosaic_logs() if enabled else []
    finally:
        config_mod.get_config = orig
    return chapters, logs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", type=Path, default=None)
    ap.add_argument("--scenario", choices=list(SCENARIOS), default=None)
    args = ap.parse_args()
    names = [args.scenario] if args.scenario else list(SCENARIOS)
    out: dict = {"scenarios": {}}
    for name in names:
        ch_off, _ = _plan(name, False)
        ch_on, logs = _plan(name, True)
        out["scenarios"][name] = {
            "patternsOff": summarize_screen_patterns(ch_off),
            "patternsOn": summarize_screen_patterns(ch_on),
            "mcsUnifiedExposureRateOn": mcs_unified_exposure_rate(ch_on),
            "metricsOn": compute_mosaic_metrics(ch_on, mosaic_logs=logs),
        }
    text = json.dumps(out, indent=2, ensure_ascii=False)
    print(text)
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
