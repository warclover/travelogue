"""Phase-3 acceptance: legacy vs v2_adaptive + PHASE3(B) scoring.

Usage:
  python scripts/phase3_layout_acceptance.py mao
  python scripts/phase3_layout_acceptance.py mao --write --render
"""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from dataclasses import asdict, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.config import LayoutScoringConfig, config_override, get_config
from travelogue.curation.curate import run_curate
from travelogue.curation.layout_metrics import compute_layout_metrics
from travelogue.curation.layout_scoring import PHASE3B_WEIGHTS, PHASE3_WEIGHTS, score_aspect_match


def _weights_dict(w) -> dict[str, float]:
    return {k: round(v, 4) for k, v in asdict(w).items()}


def _prepare_trip(trip: dict) -> dict:
    t = copy.deepcopy(trip)
    t.setdefault("pipeline", {})["status"] = "structure_draft"
    t.pop("chapters", None)
    return t


def _run_curate(
    trip: dict,
    *,
    layout: str,
    scoring: LayoutScoringConfig,
    arc_mode: str,
    trip_dir: Path | None = None,
) -> dict:
    base = get_config(reload=True)
    layout_cfg = replace(base.layout, scoring=scoring)
    curate_cfg = replace(base.curate, arc_mode=arc_mode)
    cfg = replace(base, layout=layout_cfg, curate=curate_cfg)
    with config_override(cfg):
        t = _prepare_trip(trip)
        run_curate(t, export_layout=layout, apply_layout=True, trip_dir=trip_dir)
        return t


def _has_color_metrics(trip: dict) -> bool:
    for a in trip.get("assets") or []:
        if a.get("dominantTone") and (a.get("quality") or {}).get("meanLuma") is not None:
            return True
    return False


def _layout_snapshot(chapters: list[dict]) -> list[dict]:
    return [
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


def accept_trip(
    trip_path: Path,
    *,
    layout: str = "web",
    use_phase3b: bool | None = None,
) -> dict:
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    aspects = {
        a["id"]: a.get("aspectKind") or "landscape"
        for a in trip.get("assets") or []
        if a.get("id")
    }
    weights = PHASE3B_WEIGHTS if (use_phase3b if use_phase3b is not None else _has_color_metrics(trip)) else PHASE3_WEIGHTS
    scoring_off = LayoutScoringConfig(enabled=False)
    scoring_on = LayoutScoringConfig(
        enabled=True,
        beam_width=5,
        search_timeout_ms=5000,
        max_candidates_per_bucket=16,
        max_evaluations_per_trip=800,
        allow_burst_split=False,
        subject_run_tolerance=1,
        weights=_weights_dict(weights),
    )

    legacy = _run_curate(trip, layout=layout, scoring=scoring_off, arc_mode="legacy")
    phase3 = _run_curate(
        trip,
        layout=layout,
        scoring=scoring_on,
        arc_mode="v2_adaptive",
        trip_dir=trip_path.parent,
    )
    legacy_ch = legacy.get("chapters") or []
    p3_ch = phase3.get("chapters") or []
    legacy_m = compute_layout_metrics(legacy_ch)
    p3_m = compute_layout_metrics(p3_ch)

    def aspect_rate(chapters: list[dict]) -> float:
        total = 0
        hits = 0.0
        for ch in chapters:
            for s in ch.get("screens") or []:
                hits += score_aspect_match(s, aspects)  # type: ignore[arg-type]
                total += 1
        return hits / total if total else 0.0

    return {
        "tripId": trip.get("tripId", trip_path.parent.name),
        "weightsPreset": "phase3b" if weights is PHASE3B_WEIGHTS else "phase3",
        "arcProfile": (phase3.get("curation") or {}).get("arcProfile"),
        "identicalToLegacy": _layout_snapshot(legacy_ch) == _layout_snapshot(p3_ch),
        "legacy": {"screens": legacy_m["screenCount"], "aspectMatchRate": round(aspect_rate(legacy_ch), 4)},
        "phase3": {
            "screens": p3_m["screenCount"],
            "aspectMatchRate": round(aspect_rate(p3_ch), 4),
            "patternDiversity": p3_m["patternDiversity"],
            "replanApplied": True,
        },
        "phase3_trip": phase3,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase-3 layout acceptance")
    parser.add_argument("trip_ids", nargs="+")
    parser.add_argument("--layout", default="web")
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    parser.add_argument("--write", action="store_true", help="Write phase3 curate result to trip.json")
    parser.add_argument("--render", action="store_true", help="Render after --write")
    parser.add_argument("--phase3b", action="store_true", help="Force PHASE3B weights")
    args = parser.parse_args()

    results: list[dict] = []
    for tid in args.trip_ids:
        path = args.trips_dir / tid / "trip.json"
        if not path.is_file():
            print(f"SKIP {tid}")
            continue
        print(f"Acceptance {tid} ...", flush=True)
        r = accept_trip(path, layout=args.layout, use_phase3b=args.phase3b or None)
        results.append({k: v for k, v in r.items() if k != "phase3_trip"})
        tag = "SAME" if r["identicalToLegacy"] else "DIFF"
        arc = (r.get("arcProfile") or {}).get("profile", "?")
        print(
            f"  {tag}  preset={r['weightsPreset']}  arc={arc}  "
            f"screens={r['legacy']['screens']}"
        )
        if args.write:
            out_trip = r["phase3_trip"]
            path.write_text(json.dumps(out_trip, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"  wrote {path}")
            if args.render:
                subprocess.run(
                    [sys.executable, "-m", "travelogue", "render", str(path), "--dual"],
                    cwd=ROOT,
                    check=False,
                )
                print("  render invoked")

    out = ROOT / "docs" / "acceptance-records" / "phase3-layout-acceptance.json"
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
