#!/usr/bin/env python3
"""Curate Phase 16 dogfood fixtures from golden MCS planners (PRD §13.3).

Static ``tests/fixtures/phase16-dogfood/*/trip.json`` files are **patternId exposure
fixtures** for ``phase16_template_eval.py``. This script regenerates them from the
same golden trip builders used in ``tests/_golden`` so CI dogfood stays aligned with
curate/MCS behaviour without requiring a full ingest pipeline in CI.

Policy: docs/acceptance-records/phase16-dogfood-curate-policy.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests._golden.helpers import (
    build_mosaic_landscape6_trip,
    build_portrait_heavy_trip,
    layout_snapshot,
    plan_mosaic_screens,
)

DEFAULT_OUT = ROOT / "tests" / "fixtures" / "phase16-dogfood"


def _trip_from_planner(
    trip_id: str,
    builder: Callable[[], tuple[list[list[str]], dict[str, str], list[dict]]],
    *,
    trip_photo_total: int | None = None,
) -> dict[str, Any]:
    buckets, aspects, assets = builder()
    chapters = plan_mosaic_screens(
        buckets,
        aspects,
        assets,
        trip_photo_total=trip_photo_total or len(assets),
    )
    snap = layout_snapshot(chapters)
    screens_out: list[dict[str, str]] = []
    for ch in snap.get("chapters") or []:
        for screen in ch.get("screens") or []:
            pid = screen.get("patternId")
            if pid:
                screens_out.append({"patternId": pid})
    return {"tripId": trip_id, "chapters": [{"id": "ch-01", "screens": screens_out}]}


def _static_spec(trip_id: str, pattern_ids: list[str]) -> dict[str, Any]:
    return {
        "tripId": trip_id,
        "chapters": [
            {
                "id": "ch-01",
                "screens": [{"patternId": pid} for pid in pattern_ids],
            }
        ],
    }


DOGFOOD_SPECS: dict[str, dict[str, Any]] = {
    "portrait-heavy": {
        "source": "curate",
        "tripId": "phase16-dogfood-portrait",
        "builder": build_portrait_heavy_trip,
    },
    "portrait-grid": {
        "source": "static",
        "tripId": "phase16-dogfood-portrait-grid",
        "patterns": ["screen-portrait-3", "screen-portrait-4", "screen-portrait-grid-8"],
    },
    "landscape-heavy": {
        "source": "curate",
        "tripId": "phase16-dogfood-landscape",
        "builder": build_mosaic_landscape6_trip,
        "trip_photo_total": 60,
    },
    "landscape-grid": {
        "source": "static",
        "tripId": "phase16-dogfood-landscape-grid",
        "patterns": ["screen-landscape-6", "screen-landscape-9"],
    },
    "mixed-layout": {
        "source": "static",
        "tripId": "phase16-dogfood-mixed",
        "patterns": [
            "screen-portrait-3",
            "screen-mosaic-5-2p3l-equal",
            "screen-portrait-1-landscape-2",
            "screen-landscape-1",
            "screen-mosaic-5-hero-3-2-plus-4",
        ],
    },
    "mixed-layout-alt": {
        "source": "static",
        "tripId": "phase16-dogfood-mixed-alt",
        "patterns": ["screen-mosaic-5-2p3l-equal", "screen-portrait-3"],
    },
}


def build_dogfood_trip(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    if spec.get("source") == "curate":
        builder = spec["builder"]
        return _trip_from_planner(
            str(spec["tripId"]),
            builder,
            trip_photo_total=spec.get("trip_photo_total"),
        )
    return _static_spec(str(spec["tripId"]), list(spec.get("patterns") or []))


def write_dogfood(out_dir: Path, *, names: list[str] | None = None) -> list[Path]:
    written: list[Path] = []
    selected = names or sorted(DOGFOOD_SPECS)
    for name in selected:
        spec = DOGFOOD_SPECS.get(name)
        if spec is None:
            raise KeyError(f"unknown dogfood spec: {name}")
        trip = build_dogfood_trip(name, spec)
        dest = out_dir / name / "trip.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(trip, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(dest)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate phase16 dogfood trip.json fixtures")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--name", action="append", dest="names", help="Fixture folder name (repeatable)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if args.dry_run:
        for name in args.names or sorted(DOGFOOD_SPECS):
            trip = build_dogfood_trip(name, DOGFOOD_SPECS[name])
            print(json.dumps({name: trip}, indent=2, ensure_ascii=False))
        return 0

    paths = write_dogfood(args.out, names=args.names)
    for path in paths:
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
