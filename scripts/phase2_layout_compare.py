"""Phase-2 layout compare: legacy vs beam + multi-signal scoring on real trips.

Usage:
  python scripts/phase2_layout_compare.py mao linzhi maomi
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.config import LayoutScoringConfig, config_override, get_config
from travelogue.curation.curate import run_curate
from travelogue.curation.layout_metrics import compute_layout_metrics
from travelogue.curation.layout_scoring import PHASE2_WEIGHTS, score_aspect_match


def layout_snapshot(chapters: list[dict]) -> dict:
    return {
        "chapters": [
            {
                "id": ch.get("id"),
                "screens": [
                    {
                        "patternId": s.get("patternId"),
                        "slotAssetIds": [
                            slot.get("assetId")
                            for slot in (s.get("slots") or [])
                            if slot.get("assetId")
                        ],
                    }
                    for s in (ch.get("screens") or [])
                ],
            }
            for ch in chapters
        ]
    }


def _aspect_match_rate(chapters: list[dict], aspects: dict[str, str]) -> float:
    hits = 0
    total = 0
    for ch in chapters:
        for screen in ch.get("screens") or []:
            hits += score_aspect_match(screen, aspects)  # type: ignore[arg-type]
            total += 1
    return hits / total if total else 0.0


def _prepare_trip(trip: dict) -> dict:
    t = copy.deepcopy(trip)
    t.setdefault("pipeline", {})["status"] = "structure_draft"
    t.pop("chapters", None)
    return t


def _run_with_weights(trip: dict, *, layout: str, scoring: LayoutScoringConfig) -> dict:
    base = get_config(reload=True)
    layout_cfg = replace(base.layout, scoring=scoring)
    cfg = replace(base, layout=layout_cfg)
    with config_override(cfg):
        t = _prepare_trip(trip)
        run_curate(t, export_layout=layout, apply_layout=True)
        return t


def compare_trip(trip_path: Path, *, layout: str = "web") -> dict:
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    aspects = {
        a["id"]: a.get("aspectKind") or "landscape"
        for a in trip.get("assets") or []
        if a.get("id")
    }

    legacy_trip = _run_with_weights(
        trip,
        layout=layout,
        scoring=LayoutScoringConfig(enabled=False),
    )
    phase2_trip = _run_with_weights(
        trip,
        layout=layout,
        scoring=LayoutScoringConfig(
            enabled=True,
            beam_width=3,
            weights={
                "aspect_match": PHASE2_WEIGHTS.aspect_match,
                "sharpness": PHASE2_WEIGHTS.sharpness,
                "temporal_coherence": PHASE2_WEIGHTS.temporal_coherence,
                "burst_integrity": PHASE2_WEIGHTS.burst_integrity,
                "diversity": PHASE2_WEIGHTS.diversity,
                "arc_fit": PHASE2_WEIGHTS.arc_fit,
                "hero_separation": PHASE2_WEIGHTS.hero_separation,
            },
        ),
    )

    legacy_ch = legacy_trip.get("chapters") or []
    phase2_ch = phase2_trip.get("chapters") or []
    legacy_snap = layout_snapshot(legacy_ch)
    phase2_snap = layout_snapshot(phase2_ch)
    legacy_metrics = compute_layout_metrics(legacy_ch)
    phase2_metrics = compute_layout_metrics(phase2_ch)

    return {
        "tripId": trip.get("tripId", trip_path.parent.name),
        "layout": layout,
        "assetCount": len(trip.get("assets") or []),
        "identicalToLegacy": legacy_snap == phase2_snap,
        "legacy": {
            "screenCount": legacy_metrics["screenCount"],
            "patternDiversity": legacy_metrics["patternDiversity"],
            "aspectMatchRate": round(_aspect_match_rate(legacy_ch, aspects), 4),
        },
        "phase2": {
            "screenCount": phase2_metrics["screenCount"],
            "patternDiversity": phase2_metrics["patternDiversity"],
            "aspectMatchRate": round(_aspect_match_rate(phase2_ch, aspects), 4),
            "replanApplied": (phase2_trip.get("curation") or {}).get("layoutDecisionLog") is not None,
        },
        "delta": {
            "patternDiversity": round(
                phase2_metrics["patternDiversity"] - legacy_metrics["patternDiversity"],
                4,
            ),
            "aspectMatchRate": round(
                _aspect_match_rate(phase2_ch, aspects) - _aspect_match_rate(legacy_ch, aspects),
                4,
            ),
        },
        "weights": {k: round(v, 4) for k, v in asdict(PHASE2_WEIGHTS).items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase-2 layout beam compare")
    parser.add_argument("trip_ids", nargs="+")
    parser.add_argument("--layout", default="web", choices=("auto", "mobile", "web"))
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    args = parser.parse_args()

    results: list[dict] = []
    for tid in args.trip_ids:
        path = args.trips_dir / tid / "trip.json"
        if not path.is_file():
            print(f"SKIP {tid}")
            continue
        print(f"Comparing {tid} ...", flush=True)
        r = compare_trip(path, layout=args.layout)
        results.append(r)
        tag = "SAME" if r["identicalToLegacy"] else "DIFF"
        print(
            f"  {tag}  screens legacy={r['legacy']['screenCount']} "
            f"phase2={r['phase2']['screenCount']}  "
            f"aspect Δ={r['delta']['aspectMatchRate']:+.4f}  "
            f"diversity Δ={r['delta']['patternDiversity']:+.4f}"
        )

    out = ROOT / "docs" / "acceptance-records" / "phase2-layout-compare.json"
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
