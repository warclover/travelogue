#!/usr/bin/env python3
"""Generate P16-default baseline renders for P19 golden trips.

Usage:
  python scripts/book_quality_baseline.py
  python scripts/book_quality_baseline.py demo-2025 demo-1506104ebf
  python scripts/book_quality_baseline.py --skip-curate
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import travelogue.curation.screen_planner  # noqa: F401
from travelogue.config import AppConfig, get_config
from travelogue.config.layout import LayoutStrategyEngineConfig
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.curate import run_curate
from travelogue.curation.layout_metrics import compute_layout_metrics
from travelogue.eval.golden_trips import resolve_existing_golden_trips
from travelogue.eval.screen_sampler import sample_screens, screens_signature
from travelogue.render.engine import render_trip
from travelogue.curation.screen_planner import LAYOUT_ENGINE_SCREENS

from lse_flags_curate_compare import _pattern_sequence, _prepare_trip, _screen_signatures


def _p16_cfg(base: AppConfig) -> AppConfig:
    se = replace(base.layout.strategy_engine, enabled=False)
    layout = replace(base.layout, strategy_engine=se)
    scoring = replace(base.layout.scoring, enabled=False)
    layout = replace(layout, scoring=scoring)
    return replace(base, layout=layout)


def _curate_trip(trip: dict, *, work_dir: Path, cfg: AppConfig) -> dict:
    body = _prepare_trip(trip)
    run_clustering_layer(body, trip_dir=work_dir / "cluster", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=work_dir, cfg=cfg)
    return body


def _render_trip(trip_dir: Path, body: dict) -> Path:
    trip_path = trip_dir / "trip.json"
    trip_path.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
    render_trip(
        trip_path,
        trip_dir,
        trip=body,
        validate=False,
        copy_css=True,
        index_name="index.html",
        layout_engine=LAYOUT_ENGINE_SCREENS,
        export_layout_override="web",
        update_pipeline=False,
    )
    return trip_dir / "index.html"


def main() -> int:
    parser = argparse.ArgumentParser(description="P19 golden baseline (P16 default path)")
    parser.add_argument("trip_id", nargs="*", help="Optional subset of golden trip ids")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / ".cache" / "book-quality" / "baseline",
        help="Output root",
    )
    parser.add_argument("--skip-curate", action="store_true", help="Only render existing trip.json")
    parser.add_argument(
        "--skip-render",
        action="store_true",
        help="Curate only; skip HTML render (signature gate)",
    )
    parser.add_argument(
        "--p19-candidate",
        action="store_true",
        help="Full config (P19 candidate) instead of P16-default baseline path",
    )
    args = parser.parse_args()

    rows = resolve_existing_golden_trips(root=ROOT)
    if args.trip_id:
        wanted = set(args.trip_id)
        rows = [r for r in rows if r["tripId"] in wanted]

    base_cfg = get_config(reload=True)
    cfg = base_cfg if args.p19_candidate else _p16_cfg(base_cfg)
    manifest_trips: list[dict[str, Any]] = []
    args.out.mkdir(parents=True, exist_ok=True)

    for row in rows:
        tid = row["tripId"]
        trip_dir = Path(row["tripDir"])
        if not row["exists"]:
            manifest_trips.append({"tripId": tid, "status": "missing", "tripDir": str(trip_dir)})
            print(f"SKIP missing: {tid}")
            continue

        trip = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
        work = args.out / tid
        work.mkdir(parents=True, exist_ok=True)

        if args.skip_curate:
            body = trip
        else:
            print(f"Curate {tid}...")
            body = _curate_trip(trip, work_dir=work / "curate", cfg=cfg)

        chapters = body.get("chapters") or []
        if args.skip_render:
            html_path = None
            metrics = compute_layout_metrics(chapters, body.get("assets") or [])
        else:
            print(f"Render {tid}...")
            html_path = _render_trip(trip_dir, body)
            metrics = compute_layout_metrics(chapters, body.get("assets") or [])
        sig = screens_signature(chapters, trip_id=tid)
        sampled = sample_screens(chapters, trip_id=tid, max_screens=12)

        entry = {
            "tripId": tid,
            "status": "ok",
            "tripDir": str(trip_dir),
            "html": str(html_path) if html_path else None,
            "screenCount": sum(len(ch.get("screens") or []) for ch in chapters),
            "screensSignature": sig,
            "patternSequence": _pattern_sequence(chapters),
            "screenSignatures": _screen_signatures(chapters),
            "sampledScreens": sampled,
            "metrics": metrics,
        }
        (work / "trip_summary.json").write_text(
            json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        manifest_trips.append(entry)
        print(f"  OK screens={entry['screenCount']} signature={sig}")

    manifest = {
        "label": "P19-candidate" if args.p19_candidate else "P16-default",
        "path": str(args.out),
        "trips": manifest_trips,
    }
    (args.out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nManifest: {args.out / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
