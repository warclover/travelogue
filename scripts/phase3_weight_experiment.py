"""Phase-3 weight experiments: try diversity↑ / burst↓ presets vs legacy.

Usage:
  python scripts/phase3_weight_experiment.py linzhi
  python scripts/phase3_weight_experiment.py linzhi --write diversity_aggressive --render
"""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.phase3_layout_acceptance import (
    _layout_snapshot,
    _run_curate,
    _weights_dict,
)
from travelogue.config import LayoutScoringConfig, get_config
from travelogue.curation.bucket_planning import group_assets_by_segments
from travelogue.curation.curate import layout_eligible_assets, sync_trip_covers
from travelogue.curation.layout_candidates import bucket_has_mosaic_window
from travelogue.curation.layout_metrics import compute_layout_metrics
from travelogue.curation.layout_planner import aspect_kind_for_asset
from travelogue.curation.layout_scoring import PHASE3B_WEIGHTS, ScoringWeights

# Raw weights (normalized at runtime). Base: PHASE3B with diversity/burst tweaks.
WEIGHT_PRESETS: dict[str, dict[str, float]] = {
    "phase3b_baseline": _weights_dict(PHASE3B_WEIGHTS),
    "diversity_boost": {
        "aspect_match": 0.10,
        "sharpness": 0.05,
        "temporal_coherence": 0.09,
        "burst_integrity": 0.02,
        "diversity": 0.18,
        "arc_fit": 0.09,
        "hero_separation": 0.06,
        "luminance_continuity": 0.06,
        "tone_continuity": 0.08,
        "subject_run": 0.05,
    },
    "diversity_aggressive": {
        "aspect_match": 0.06,
        "sharpness": 0.04,
        "temporal_coherence": 0.07,
        "burst_integrity": 0.01,
        "diversity": 0.28,
        "arc_fit": 0.08,
        "hero_separation": 0.05,
        "luminance_continuity": 0.05,
        "tone_continuity": 0.07,
        "subject_run": 0.04,
    },
    "anti_burst": {
        "aspect_match": 0.11,
        "sharpness": 0.05,
        "temporal_coherence": 0.08,
        "burst_integrity": 0.005,
        "diversity": 0.16,
        "arc_fit": 0.08,
        "hero_separation": 0.06,
        "luminance_continuity": 0.06,
        "tone_continuity": 0.08,
        "subject_run": 0.05,
    },
    "diversity_only_push": {
        "aspect_match": 0.04,
        "sharpness": 0.03,
        "temporal_coherence": 0.05,
        "burst_integrity": 0.01,
        "diversity": 0.40,
        "arc_fit": 0.06,
        "hero_separation": 0.04,
        "luminance_continuity": 0.04,
        "tone_continuity": 0.05,
        "subject_run": 0.03,
    },
    "low_aspect_high_diversity": {
        "aspect_match": 0.02,
        "sharpness": 0.05,
        "temporal_coherence": 0.08,
        "burst_integrity": 0.02,
        "diversity": 0.35,
        "arc_fit": 0.10,
        "hero_separation": 0.08,
        "luminance_continuity": 0.08,
        "tone_continuity": 0.10,
        "subject_run": 0.06,
    },
}


def _normalized_weights_dict(raw: dict[str, float]) -> dict[str, float]:
    w = ScoringWeights.from_dict(raw).normalized()
    return _weights_dict(w)


def _count_bucket_changes(decision_logs: list[dict]) -> int:
    n = 0
    for log in decision_logs:
        for ev in log.get("events") or []:
            if ev.get("type") != "beam_pick":
                continue
            if ev.get("changed"):
                n += 1
    return n


def _bucket_diagnostics(trip: dict) -> dict:
    """Why weight tweaks may not flip picks: mosaic windows, gallery freeze, candidate dedup."""
    layout_assets = layout_eligible_assets(trip)
    cover_id = sync_trip_covers(trip, export_layout="web", assets=layout_assets)
    cur_cfg = get_config().curate
    buckets, *_ = group_assets_by_segments(
        layout_assets,
        cover_id,
        trip.get("meta") or {},
        segment_gap_days=cur_cfg.segment_gap_days,
        city_gap_days=cur_cfg.city_gap_days,
        min_bucket_size=cur_cfg.min_bucket_size,
    )
    aspects = {a["id"]: aspect_kind_for_asset(a) for a in layout_assets}
    assets_by_id = {a["id"]: a for a in layout_assets}
    chapters = trip.get("chapters") or []
    rows: list[dict] = []
    mosaic_buckets = 0
    for i, bucket in enumerate(b for b in buckets if b):
        has_m = bucket_has_mosaic_window(
            bucket,
            aspects,
            assets_by_id,
            mixed_proximity_seconds=12.0,
            trip_photo_total=len(layout_assets),
        )
        if has_m:
            mosaic_buckets += 1
        ch = chapters[i] if i < len(chapters) else {}
        rows.append(
            {
                "bucketIndex": i + 1,
                "chapterPattern": ch.get("patternId"),
                "assetCount": len(bucket),
                "hasMosaicWindow": has_m,
                "beamEligible": ch.get("patternId") != "gallery",
            }
        )
    return {
        "layoutEligibleAssets": len(layout_assets),
        "bucketCount": len(rows),
        "mosaicBucketCount": mosaic_buckets,
        "galleryChapterCount": sum(1 for r in rows if r["chapterPattern"] == "gallery"),
        "buckets": rows,
    }


def run_experiment(
    trip_path: Path,
    *,
    layout: str = "web",
    presets: list[str] | None = None,
) -> list[dict]:
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    names = presets or [k for k in WEIGHT_PRESETS if k != "phase3b_baseline"]
    if "phase3b_baseline" not in names:
        names = ["phase3b_baseline"] + names

    scoring_off = LayoutScoringConfig(enabled=False)
    legacy = _run_curate(trip, layout=layout, scoring=scoring_off, arc_mode="legacy")
    legacy_snap = _layout_snapshot(legacy.get("chapters") or [])

    results: list[dict] = []
    for name in names:
        raw = WEIGHT_PRESETS.get(name)
        if raw is None:
            print(f"  SKIP unknown preset {name}")
            continue
        weights = _normalized_weights_dict(raw)
        scoring_on = LayoutScoringConfig(
            enabled=True,
            beam_width=5,
            search_timeout_ms=8000,
            max_candidates_per_bucket=16,
            max_evaluations_per_trip=1200,
            allow_burst_split=False,
            subject_run_tolerance=1,
            weights=weights,
        )
        exp_trip = _run_curate(
            copy.deepcopy(trip),
            layout=layout,
            scoring=scoring_on,
            arc_mode="v2_adaptive",
            trip_dir=trip_path.parent,
        )
        ch = exp_trip.get("chapters") or []
        snap = _layout_snapshot(ch)
        curation = exp_trip.get("curation") or {}
        logs = curation.get("layoutDecisionLog") or []
        metrics = compute_layout_metrics(ch)
        identical = snap == legacy_snap
        bucket_changes = _count_bucket_changes(logs)
        row = {
            "preset": name,
            "weights": weights,
            "identicalToLegacy": identical,
            "bucketPicksChanged": bucket_changes,
            "totalBuckets": len(logs),
            "screens": metrics["screenCount"],
            "patternDiversity": metrics["patternDiversity"],
            "arcProfile": curation.get("arcProfile"),
            "searchBudget": curation.get("layoutSearchBudget"),
        }
        if not identical:
            row["diffSummary"] = _diff_summary(legacy_snap, snap)
        results.append(row)
        tag = "SAME" if identical else "DIFF"
        print(
            f"  {name:28} {tag}  buckets_changed={bucket_changes}/{len(logs)}  "
            f"diversity={metrics['patternDiversity']:.3f}"
        )
    return results, _bucket_diagnostics(trip)


def _diff_summary(legacy: list[dict], exp: list[dict]) -> dict:
    legacy_patterns: list[str] = []
    exp_patterns: list[str] = []
    for ch_l, ch_e in zip(legacy, exp):
        for s in ch_l.get("screens") or []:
            legacy_patterns.append(s.get("patternId") or "")
        for s in ch_e.get("screens") or []:
            exp_patterns.append(s.get("patternId") or "")
    pattern_diffs = sum(1 for a, b in zip(legacy_patterns, exp_patterns) if a != b)
    slot_diffs = 0
    for ch_l, ch_e in zip(legacy, exp):
        for s_l, s_e in zip(ch_l.get("screens") or [], ch_e.get("screens") or []):
            if s_l.get("slotAssetIds") != s_e.get("slotAssetIds"):
                slot_diffs += 1
    return {
        "patternDiffScreens": pattern_diffs,
        "slotDiffScreens": slot_diffs,
        "legacyScreenCount": len(legacy_patterns),
        "expScreenCount": len(exp_patterns),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase-3 weight experiment")
    parser.add_argument("trip_ids", nargs="+")
    parser.add_argument("--layout", default="web")
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    parser.add_argument("--preset", action="append", dest="presets", help="Run only these presets")
    parser.add_argument("--write", metavar="PRESET", help="Write winning preset curate to trip.json")
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()

    all_results: list[dict] = []
    for tid in args.trip_ids:
        path = args.trips_dir / tid / "trip.json"
        if not path.is_file():
            print(f"SKIP {tid}")
            continue
        print(f"Weight experiment {tid} ...", flush=True)
        rows, diag = run_experiment(path, layout=args.layout, presets=args.presets)
        all_results.append({"tripId": tid, "diagnostics": diag, "presets": rows})
        print(
            f"  assets={diag['layoutEligibleAssets']} buckets={diag['bucketCount']} "
            f"mosaic={diag['mosaicBucketCount']} gallery={diag['galleryChapterCount']}"
        )

        if args.write:
            target = next((r for r in rows if r["preset"] == args.write), None)
            if target is None:
                print(f"  --write preset {args.write!r} not found in results")
            else:
                trip = json.loads(path.read_text(encoding="utf-8"))
                weights = target["weights"]
                scoring_on = LayoutScoringConfig(
                    enabled=True,
                    beam_width=5,
                    search_timeout_ms=8000,
                    max_candidates_per_bucket=16,
                    max_evaluations_per_trip=1200,
                    allow_burst_split=False,
                    subject_run_tolerance=1,
                    weights=weights,
                )
                out = _run_curate(
                    trip,
                    layout=args.layout,
                    scoring=scoring_on,
                    arc_mode="v2_adaptive",
                    trip_dir=path.parent,
                )
                path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                print(f"  wrote {path} (preset={args.write})")
                if args.render:
                    subprocess.run(
                        [sys.executable, "-m", "travelogue", "render", str(path), "--dual"],
                        cwd=ROOT,
                        check=False,
                    )

    out_path = ROOT / "docs" / "acceptance-records" / "phase3-weight-experiment.json"
    out_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {out_path}")
    diff_presets = [
        f"{r['tripId']}/{p['preset']}"
        for r in all_results
        for p in r["presets"]
        if not p["identicalToLegacy"]
    ]
    if diff_presets:
        print("DIFF presets:", ", ".join(diff_presets))
    else:
        print("All presets SAME as legacy — try more aggressive weights or allow_burst_split.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
