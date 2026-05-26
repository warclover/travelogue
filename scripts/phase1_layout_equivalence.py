"""Phase-1 equivalence check: scoring(aspect_match=1.0) vs legacy on real trips.

Usage:
  python scripts/phase1_layout_equivalence.py linzhi mao
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.config import AppConfig, LayoutScoringConfig, get_config
from travelogue.curation.curate import run_curate


def layout_snapshot(chapters: list[dict]) -> dict:
    return {
        "chapters": [
            {
                "id": ch.get("id"),
                "patternId": ch.get("patternId"),
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


def _prepare_trip(trip: dict) -> dict:
    """In-memory copy with draft pipeline so degradation guard does not block scoring."""
    t = copy.deepcopy(trip)
    pipe = t.setdefault("pipeline", {})
    pipe["status"] = "structure_draft"
    t.pop("chapters", None)
    return t


def _run_curate(trip: dict, *, layout: str, scoring_enabled: bool) -> dict:
    base = get_config(reload=True)
    weights = {
        "aspect_match": 1.0 if scoring_enabled else 0.0,
        "sharpness": 0.0,
        "hero_separation": 0.0,
        "temporal_coherence": 0.0,
        "diversity": 0.0,
        "arc_fit": 0.0,
    }
    scoring = LayoutScoringConfig(enabled=scoring_enabled, weights=weights)
    layout_cfg = replace(base.layout, scoring=scoring)
    cfg = replace(base, layout=layout_cfg)

    import travelogue.config as config_mod

    prev = config_mod._cached
    config_mod._cached = cfg
    try:
        t = _prepare_trip(trip)
        run_curate(t, export_layout=layout, apply_layout=True)
        return layout_snapshot(t.get("chapters") or [])
    finally:
        config_mod._cached = prev


def compare_trip(trip_path: Path, *, layout: str = "web") -> dict:
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    legacy = _run_curate(trip, layout=layout, scoring_enabled=False)
    scored = _run_curate(trip, layout=layout, scoring_enabled=True)
    equal = legacy == scored
    return {
        "tripId": trip.get("tripId", trip_path.parent.name),
        "layout": layout,
        "assetCount": len(trip.get("assets") or []),
        "equivalent": equal,
        "legacyChapterCount": len(legacy.get("chapters") or []),
        "scoredChapterCount": len(scored.get("chapters") or []),
        "legacyScreenCount": sum(len(c.get("screens") or []) for c in legacy.get("chapters") or []),
        "scoredScreenCount": sum(len(c.get("screens") or []) for c in scored.get("chapters") or []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase-1 layout scoring equivalence check")
    parser.add_argument("trip_ids", nargs="+", help="trip folder names under trips/")
    parser.add_argument("--layout", default="web", choices=("auto", "mobile", "web"))
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    args = parser.parse_args()

    results: list[dict] = []
    failed = False
    for tid in args.trip_ids:
        path = args.trips_dir / tid / "trip.json"
        if not path.is_file():
            print(f"SKIP {tid}: {path} not found")
            failed = True
            continue
        print(f"Checking {tid} ...", flush=True)
        r = compare_trip(path, layout=args.layout)
        results.append(r)
        status = "PASS" if r["equivalent"] else "FAIL"
        print(
            f"  {status}  chapters={r['legacyChapterCount']}  "
            f"screens={r['legacyScreenCount']}  assets={r['assetCount']}"
        )
        if not r["equivalent"]:
            failed = True

    out_path = ROOT / "docs" / "acceptance-records" / "phase1-layout-equivalence.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {out_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
