#!/usr/bin/env python3
"""MCR P1 · Mosaic config diagnostic — window sizes, policy members, trip hints.

Examples:
  python scripts/mosaic_config_diag.py
  python scripts/mosaic_config_diag.py --strict
  python scripts/mosaic_config_diag.py --trip trips/demo-80301df45c
  python scripts/mosaic_config_diag.py --compare-baseline .cache/mcr-eval/chuanzang-studio.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_WINDOW_SIZES = (3, 4, 5, 6, 8, 9)
_HERO_MOSAIC_PATTERNS = frozenset(
    {
        "screen-mosaic-5-main-hero-plus-4",
        "screen-mosaic-6-main-hero-plus-5",
    }
)

_POLICY_GROUPS = (
    "MOSAIC_3_PATTERN_IDS",
    "MOSAIC_4_PATTERN_IDS",
    "MOSAIC_5_PATTERN_IDS",
    "MOSAIC_6_PATTERN_IDS",
    "MOSAIC_8_PATTERN_IDS",
    "MOSAIC_9_PATTERN_IDS",
)


def _deprecated_mosaic_ids() -> list[str]:
    from travelogue.layout_templates.registry import get_engine

    engine = get_engine()
    out: list[str] = []
    for tid in sorted(engine._templates):
        if "mosaic" not in tid:
            continue
        tpl = engine._templates[tid]
        if tpl.status == "deprecated":
            out.append(tid)
    return out


def _aspect_family(kind: str) -> str:
    if kind in ("portrait", "tall"):
        return "portrait"
    if kind in ("landscape", "panorama"):
        return "landscape"
    return "square"


def _scan_1p4l_windows(
    asset_ids: list[str],
    aspects: dict[str, str],
    assets_map: dict[str, dict],
    *,
    burst_seconds: float,
) -> dict[str, int]:
    from travelogue.curation.burst_utils import time_near_chain

    geometry = 0
    burst_pass = 0
    burst_fail = 0
    for i in range(len(asset_ids) - 4):
        window = asset_ids[i : i + 5]
        kinds = [_aspect_family(aspects.get(aid, "square")) for aid in window]
        n_p = sum(1 for k in kinds if k == "portrait")
        n_l = sum(1 for k in kinds if k == "landscape")
        if n_p != 1 or n_l != 4:
            continue
        geometry += 1
        if time_near_chain(window, assets_map, burst_seconds=burst_seconds):
            burst_pass += 1
        else:
            burst_fail += 1
    return {
        "windows_1p4l_geometry": geometry,
        "windows_1p4l_burst_pass": burst_pass,
        "windows_1p4l_burst_fail": burst_fail,
    }


def _ordered_asset_ids(trip: dict) -> list[str]:
    curation = trip.get("curation") or {}
    displayed = curation.get("displayedAssetIds")
    if isinstance(displayed, list) and displayed:
        return [str(x) for x in displayed if x]
    assets = trip.get("assets") or []
    assets_map = {str(a["id"]): a for a in assets if a.get("id")}

    def _ts(aid: str) -> float:
        from travelogue.curation.burst_utils import parse_taken_ts

        return parse_taken_ts(assets_map.get(aid) or {}) or 0.0

    return sorted(assets_map, key=_ts)


def _decision_log_exposure(trip: dict) -> dict[int, dict[str, Any]]:
    logs = (trip.get("curation") or {}).get("mosaicDecisionLog") or []
    by_size: dict[int, dict[str, Any]] = {}
    for raw in logs:
        if not isinstance(raw, dict):
            continue
        size = int(raw.get("windowSize") or raw.get("window_size") or 0)
        if size <= 0:
            continue
        bucket = by_size.setdefault(
            size,
            {"decisions": 0, "winners": 0, "fallbacks": 0, "patterns": []},
        )
        bucket["decisions"] += 1
        if raw.get("fallbackUsed"):
            bucket["fallbacks"] += 1
        winner = str(raw.get("winnerPatternId") or "")
        if winner:
            bucket["winners"] += 1
            bucket["patterns"].append(winner)
    return by_size


def _trip_summary(trip: dict, *, burst_seconds: float) -> dict[str, Any]:
    from travelogue.curation.layout_planner import aspect_kind_for_asset

    mosaic_screens: list[str] = []
    hero_mosaic_screens: list[str] = []
    for ch in trip.get("chapters") or []:
        for screen in ch.get("screens") or []:
            pid = str(screen.get("patternId") or "")
            if "mosaic" in pid or pid in {
                "screen-portrait-6",
                "screen-landscape-6",
                "screen-portrait-4",
                "screen-landscape-4",
                "screen-portrait-9",
                "screen-landscape-9",
            }:
                mosaic_screens.append(pid)
            if pid in _HERO_MOSAIC_PATTERNS:
                hero_mosaic_screens.append(pid)
    assets = trip.get("assets") or []
    assets_map = {str(a["id"]): a for a in assets if a.get("id")}
    aspects = {aid: aspect_kind_for_asset(a) for aid, a in assets_map.items()}
    portrait = sum(1 for k in aspects.values() if _aspect_family(k) == "portrait")
    landscape = sum(1 for k in aspects.values() if _aspect_family(k) == "landscape")
    ordered = _ordered_asset_ids(trip)
    window_stats = _scan_1p4l_windows(ordered, aspects, assets_map, burst_seconds=burst_seconds)
    curation = trip.get("curation") or {}
    layout_metrics = curation.get("layoutMetrics") if isinstance(curation.get("layoutMetrics"), dict) else {}
    return {
        "tripId": trip.get("tripId"),
        "assetCount": len(assets),
        "portraitCount": portrait,
        "landscapeCount": landscape,
        "portraitRatio": round(portrait / len(assets), 4) if assets else 0.0,
        "mosaicScreenCount": len(mosaic_screens),
        "heroMosaicScreenCount": len(hero_mosaic_screens),
        "mosaicPatterns": sorted(set(mosaic_screens)),
        "heroMosaicPatterns": sorted(set(hero_mosaic_screens)),
        "burstSeconds": burst_seconds,
        "layoutMetrics": layout_metrics,
        **window_stats,
    }


def _print_decision_log_exposure(trip: dict) -> None:
    by_size = _decision_log_exposure(trip)
    if not by_size:
        print("MCS decision log: (none — re-curate to populate)")
        return
    print("MCS decision log exposure by window:")
    for size in sorted(by_size):
        b = by_size[size]
        patterns = sorted(set(b["patterns"]))
        print(
            f"  window {size}: decisions={b['decisions']} winners={b['winners']} "
            f"fallbacks={b['fallbacks']} patterns={patterns or '—'}"
        )
    w4 = by_size.get(4)
    if w4:
        print(
            f"window 4 exposure (D11): {w4['winners']} winning decisions / "
            f"{w4['decisions']} total"
        )


def _print_trip_summary(summary: dict[str, Any]) -> None:
    print()
    print(f"=== Trip: {summary['tripId']} ===")
    print(
        f"assets: {summary['assetCount']} "
        f"(portrait={summary['portraitCount']}, landscape={summary['landscapeCount']}, "
        f"ratio={summary['portraitRatio']})"
    )
    print(f"mosaic screens: {summary['mosaicScreenCount']} (hero: {summary['heroMosaicScreenCount']})")
    if summary["mosaicPatterns"]:
        print("patterns:", ", ".join(summary["mosaicPatterns"]))
    if summary["heroMosaicPatterns"]:
        print("hero patterns:", ", ".join(summary["heroMosaicPatterns"]))
    print(
        f"1P+4L windows (size-5 slide): geometry={summary['windows_1p4l_geometry']} "
        f"burst_pass={summary['windows_1p4l_burst_pass']} "
        f"burst_fail={summary['windows_1p4l_burst_fail']} "
        f"(mixed_proximity={summary['burstSeconds']}s)"
    )
    if summary["windows_1p4l_geometry"] and summary["windows_1p4l_burst_fail"] == summary["windows_1p4l_geometry"]:
        print("hint: all 1P+4L windows fail burst/time gate — mosaic-5-main-portrait-3land unlikely (MCR D13)")
    elif summary["portraitCount"] > summary["landscapeCount"] and summary["heroMosaicScreenCount"] == 0:
        print("hint: portrait-dominant album — zero hero mosaic may be expected (MCR D13)")
    lm = summary.get("layoutMetrics") or {}
    if lm:
        dense = lm.get("dense_collage_count") or lm.get("denseCollageCount")
        if dense is not None:
            print(f"layoutMetrics.dense_collage_count: {dense}")


def _compare_layout_metrics(baseline_path: Path, current: dict[str, Any] | None = None) -> None:
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    before = payload.get("before") or payload.get("layoutMetricsBefore") or {}
    after = payload.get("after") or payload.get("layoutMetricsAfter") or current or {}
    if not before and not after:
        before = payload.get("layoutMetrics") or payload
    skip_keys = frozenset({"patternIds", "mosaic5WinnerPatterns"})
    keys = sorted(
        k
        for k in set(before) | set(after)
        if k not in skip_keys and not isinstance(before.get(k), (list, dict))
    )
    print()
    print(f"=== layoutMetrics compare: {baseline_path.name} ===")
    for key in keys:
        b = before.get(key)
        a = after.get(key)
        if b == a:
            continue
        print(f"  {key}: {b!r} -> {a!r}")
    for label, block in (("before", before), ("after", after)):
        hero = block.get("heroMosaicScreenCount")
        patterns = block.get("heroMosaicPatterns")
        if hero is not None:
            print(f"  [{label}] heroMosaicScreenCount={hero} patterns={patterns}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Mosaic MCS config diagnostic (MCR P1)")
    parser.add_argument("--trip", type=Path, help="Trip directory or trip.json path")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when window size 6 is disabled in mosaic config",
    )
    parser.add_argument(
        "--compare-baseline",
        type=Path,
        help="Compare before/after layoutMetrics JSON from .cache/mcr-eval/",
    )
    args = parser.parse_args()

    if args.compare_baseline:
        if not args.compare_baseline.is_file():
            print(f"[error] baseline not found: {args.compare_baseline}", file=sys.stderr)
            return 1
        _compare_layout_metrics(args.compare_baseline)
        return 0

    from travelogue.config import get_config
    from travelogue.curation.mosaic.constants import (
        MOSAIC_3_PATTERN_IDS,
        MOSAIC_4_PATTERN_IDS,
        MOSAIC_5_PATTERN_IDS,
        MOSAIC_6_PATTERN_IDS,
        MOSAIC_8_PATTERN_IDS,
        MOSAIC_9_PATTERN_IDS,
    )
    from travelogue.curation.mosaic.lte_adapter import mosaic_pattern_disabled
    from travelogue.curation.mosaic.runtime import mosaic_window_size_enabled

    cfg = get_config().mosaic
    burst_seconds = float(get_config().layout.mixed_proximity_seconds)
    group_map = {
        "MOSAIC_3_PATTERN_IDS": MOSAIC_3_PATTERN_IDS,
        "MOSAIC_4_PATTERN_IDS": MOSAIC_4_PATTERN_IDS,
        "MOSAIC_5_PATTERN_IDS": MOSAIC_5_PATTERN_IDS,
        "MOSAIC_6_PATTERN_IDS": MOSAIC_6_PATTERN_IDS,
        "MOSAIC_8_PATTERN_IDS": MOSAIC_8_PATTERN_IDS,
        "MOSAIC_9_PATTERN_IDS": MOSAIC_9_PATTERN_IDS,
    }

    print("=== Mosaic Config (MCR diag) ===")
    print(f"mosaic.enabled: {cfg.enabled}")
    print(f"enabled_window_sizes: {cfg.enabled_window_sizes}")
    print(f"mixed_proximity_seconds: {burst_seconds}")
    print()
    print("Window size gates:")
    for size in _WINDOW_SIZES:
        enabled = mosaic_window_size_enabled(size, cfg)
        print(f"  window {size}: enabled={enabled}")
    w6 = mosaic_window_size_enabled(6, cfg)
    print()
    print(f"window 6 enabled: {w6}")

    print()
    print("Policy MOSAIC_* members:")
    for name in _POLICY_GROUPS:
        members = group_map[name]
        print(f"  {name} ({len(members)}):")
        for pid in members:
            disabled = mosaic_pattern_disabled(pid, cfg=cfg)
            flag = "DISABLED" if disabled else "ok"
            print(f"    - {pid} [{flag}]")

    deprecated = _deprecated_mosaic_ids()
    print()
    print(f"Deprecated mosaic templates ({len(deprecated)}):")
    for pid in deprecated:
        print(f"  - {pid}")

    if args.trip:
        trip_path = args.trip
        if trip_path.is_dir():
            trip_path = trip_path / "trip.json"
        if not trip_path.is_file():
            print(f"\n[warn] trip.json not found: {trip_path}", file=sys.stderr)
        else:
            trip = json.loads(trip_path.read_text(encoding="utf-8"))
            summary = _trip_summary(trip, burst_seconds=burst_seconds)
            _print_trip_summary(summary)
            _print_decision_log_exposure(trip)

    if args.strict and not w6:
        print("\n[FAIL] --strict: window 6 is disabled", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
