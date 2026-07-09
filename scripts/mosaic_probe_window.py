#!/usr/bin/env python3
"""Probe MCS window candidates — show whether a template was rejected and why.

Examples:
  # Synthetic 5×landscape (Plate 63 class)
  python scripts/mosaic_probe_window.py --synthetic-landscape-5

  # Trip screen by global plate index (1-based, all chapters)
  python scripts/mosaic_probe_window.py path/to/trip.json --plate 63

  # Trip screen that used a given pattern (first match)
  python scripts/mosaic_probe_window.py path/to/trip.json --pattern screen-mosaic-5-hero-3-2-plus-4
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HERO_3_2 = "screen-mosaic-5-hero-3-2-plus-4"


def _synthetic_landscape_five() -> tuple[list[str], dict, dict]:
    aspects: dict[str, str] = {}
    assets_map: dict[str, dict] = {}
    asset_ids: list[str] = []
    for i in range(5):
        aid = f"synthetic-land-{i}"
        asset_ids.append(aid)
        aspects[aid] = "landscape"
        assets_map[aid] = {
            "id": aid,
            "width": 4000,
            "height": 2250,
            "takenAt": f"2024-06-01T10:0{i}:00Z",
            "quality": {"sharpness": 0.85},
        }
    return asset_ids, aspects, assets_map


def _load_trip(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _screen_at_plate(trip: dict, plate: int) -> tuple[dict, int, int]:
    """Return (screen, chapter_idx, screen_idx) for 1-based global plate number."""
    if plate < 1:
        raise ValueError("plate must be >= 1")
    n = 0
    for ci, ch in enumerate(trip.get("chapters") or []):
        for si, screen in enumerate(ch.get("screens") or []):
            n += 1
            if n == plate:
                return screen, ci, si
    raise ValueError(f"plate {plate} not found (total screens={n})")


def _find_screen_by_pattern(trip: dict, pattern_id: str) -> tuple[dict, int, int]:
    for ci, ch in enumerate(trip.get("chapters") or []):
        for si, screen in enumerate(ch.get("screens") or []):
            if str(screen.get("patternId") or "") == pattern_id:
                return screen, ci, si
    raise ValueError(f"pattern {pattern_id!r} not found in trip")


def _assets_from_trip(trip: dict, screen: dict) -> tuple[list[str], dict, dict]:
    from travelogue.curation.layout_planner import aspect_kind_for_asset

    assets_map = {str(a["id"]): a for a in trip.get("assets") or [] if a.get("id")}
    asset_ids = [
        str(slot["assetId"])
        for slot in screen.get("slots") or []
        if slot.get("assetId")
    ]
    if not asset_ids:
        raise ValueError("screen has no slot assetIds — re-curate with layout applied first")
    aspects = {
        aid: aspect_kind_for_asset(assets_map.get(aid, {"id": aid}))
        for aid in asset_ids
    }
    return asset_ids, aspects, assets_map


def probe(
    asset_ids: list[str],
    aspects: dict,
    assets_map: dict,
    *,
    hero_weighted_geometry_guard: bool | None = None,
) -> dict:
    from dataclasses import replace

    from travelogue.config import MosaicConfig
    from travelogue.layout_engine.mosaic.candidates import (
        generate_window_candidates_with_rejections,
    )
    from travelogue.layout_engine.mosaic.compose import pick_best_window
    from travelogue.layout_engine.mosaic.runtime import (
        reset_mosaic_config_override,
        set_mosaic_config_override,
    )

    cfg = MosaicConfig(log_level="debug")
    if hero_weighted_geometry_guard is not None:
        cfg = replace(cfg, hero_weighted_geometry_guard=hero_weighted_geometry_guard)
        set_mosaic_config_override(cfg)
    try:
        bundle = generate_window_candidates_with_rejections(
            asset_ids, aspects, assets_map, cfg=cfg
        )
        pick = pick_best_window(
            asset_ids,
            aspects,
            assets_map,
            cfg=cfg,
            window_size=len(asset_ids),
        )
    finally:
        reset_mosaic_config_override()

    hero_cand = next(
        (c for c in bundle.candidates if c.pattern_id == HERO_3_2),
        None,
    )
    hero_rejects = [
        r for r in bundle.rejected if r.get("templateId") == HERO_3_2
    ]
    valid = [c for c in bundle.candidates if c.hard_valid]
    return {
        "windowSize": len(asset_ids),
        "orientations": {
            aid: aspects.get(aid) for aid in asset_ids
        },
        "heroWeightedGeometryGuard": cfg.hero_weighted_geometry_guard,
        "hero32": {
            "inCandidates": hero_cand is not None,
            "hardValid": bool(hero_cand and hero_cand.hard_valid),
            "rejections": hero_rejects,
        },
        "winnerPatternId": pick.log.winner_pattern_id or None,
        "fallbackUsed": pick.log.fallback_used,
        "fallbackReason": pick.log.fallback_reason,
        "validCandidatePatterns": [c.pattern_id for c in valid],
        "allRejections": bundle.rejected,
    }


def _print_report(label: str, report: dict) -> None:
    print(f"=== {label} ===")
    print(f"window: {report['windowSize']} photos")
    print(f"orientations: {list(report['orientations'].values())}")
    print(f"hero_weighted_geometry_guard: {report['heroWeightedGeometryGuard']}")
    h = report["hero32"]
    print(f"\n[{HERO_3_2}]")
    print(f"  considered: {h['inCandidates']}")
    print(f"  hard_valid: {h['hardValid']}")
    if h["rejections"]:
        for r in h["rejections"]:
            print(f"  rejected: {r.get('reason')} {r.get('detail') or ''}".strip())
    elif h["inCandidates"] and h["hardValid"]:
        print("  status: eligible (would compete in scoring)")
    elif h["inCandidates"]:
        print("  status: candidate exists but geometry/scorer blocked")
    else:
        print("  status: not in candidate set (ordering failed or disabled)")

    print(f"\nwinner: {report['winnerPatternId'] or '(none)'}")
    if report["fallbackUsed"]:
        print(f"fallback: {report['fallbackReason']}")
    print(f"valid patterns ({len(report['validCandidatePatterns'])}): "
          f"{', '.join(report['validCandidatePatterns'][:8])}"
          f"{'…' if len(report['validCandidatePatterns']) > 8 else ''}")

    if h["rejections"] and any(r.get("reason") == "geometry_invalid" for r in h["rejections"]):
        print("\n[OK] geometry guard fired — hero-3-2 blocked for this window (expected for Plate 63)")
    elif not h["hardValid"] and h["inCandidates"]:
        print("\n[OK] hero-3-2 not selected (hard_valid=false)")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe MCS template rejections for a window")
    parser.add_argument("trip_json", nargs="?", type=Path, help="trip.json path")
    parser.add_argument("--plate", type=int, help="1-based global screen index")
    parser.add_argument("--pattern", help="find first screen with this patternId")
    parser.add_argument(
        "--synthetic-landscape-5",
        action="store_true",
        help="probe synthetic 5×landscape window (Plate 63 class)",
    )
    parser.add_argument(
        "--no-guard",
        action="store_true",
        help="set mosaic.hero_weighted_geometry_guard=false (rollback preview)",
    )
    args = parser.parse_args()

    guard = False if args.no_guard else None

    if args.synthetic_landscape_5 or not args.trip_json:
        report = probe(*_synthetic_landscape_five(), hero_weighted_geometry_guard=guard)
        _print_report("synthetic 5×landscape", report)
        return 0

    trip = _load_trip(args.trip_json)
    if args.plate:
        screen, ci, si = _screen_at_plate(trip, args.plate)
        label = f"trip {trip.get('tripId')} plate {args.plate} (ch{ci} sc{si})"
    elif args.pattern:
        screen, ci, si = _find_screen_by_pattern(trip, args.pattern)
        label = f"trip {trip.get('tripId')} pattern {args.pattern} (ch{ci} sc{si})"
    else:
        parser.error("provide --plate, --pattern, or --synthetic-landscape-5")
        return 2

    asset_ids, aspects, assets_map = _assets_from_trip(trip, screen)
    report = probe(asset_ids, aspects, assets_map, hero_weighted_geometry_guard=guard)
    print(f"screen patternId (current): {screen.get('patternId')}")
    _print_report(label, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
