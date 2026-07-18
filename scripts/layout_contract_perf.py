#!/usr/bin/env python3
"""TPC AC-TPC-11 · curate P95 on vs off (template_contract).

Usage:
  python scripts/layout_contract_perf.py --fixture golden-mixed-scenes
  python scripts/layout_contract_perf.py --trip-dir trips/demo-2025-9 --repeats 5 --write
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.config.mosaic import TemplateContractConfig

RECORD_PATH = ROOT / "docs" / "acceptance-records" / "tpc-curate-perf.json"
BUDGET_PCT = 10.0


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _prepare(trip: dict) -> dict:
    body = deepcopy(trip)
    body.setdefault("pipeline", {})["status"] = "structure_draft"
    body.pop("chapters", None)
    cur = body.setdefault("curation", {})
    cur.pop("clustering", None)
    cur.pop("mosaicDecisionLog", None)
    for asset in body.get("assets") or []:
        asset.pop("sceneClusterId", None)
        asset.pop("clusterSource", None)
    return body


def _run_once(trip: dict, *, work: Path, cfg: Any) -> float:
    from travelogue.curation.clustering import run_clustering_layer
    from travelogue.curation.curate import run_curate

    body = _prepare(trip)
    t0 = time.perf_counter()
    run_clustering_layer(body, trip_dir=work / "cluster", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=work, cfg=cfg)
    return (time.perf_counter() - t0) * 1000.0


def _p95(samples: list[float]) -> float:
    if not samples:
        return 0.0
    if len(samples) == 1:
        return samples[0]
    ordered = sorted(samples)
    # nearest-rank
    k = max(0, min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1)))))
    return ordered[k]


def main() -> int:
    parser = argparse.ArgumentParser(description="TPC curate P95 on vs off")
    parser.add_argument("--trip-dir", type=Path)
    parser.add_argument("--fixture", type=str, help="tests/fixtures/phase16-dogfood/<id>")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--out", type=Path, default=RECORD_PATH)
    args = parser.parse_args()

    # Default: clustering golden-mixed-scenes (synthesized via load_fixture_trip).
    # phase16-dogfood/*/trip.json are pattern specs without assets — not curatable.
    fixture_id = args.fixture or "golden-mixed-scenes"
    trip_path: Path | None = None
    trip: dict[str, Any] | None = None

    if args.trip_dir:
        trip_path = Path(args.trip_dir) / "trip.json"
        if not trip_path.is_file():
            print(f"trip.json not found: {trip_path}", file=sys.stderr)
            return 1
        trip = json.loads(trip_path.read_text(encoding="utf-8"))
    else:
        for base in (
            ROOT / "tests" / "fixtures" / "clustering" / fixture_id,
            ROOT / "tests" / "fixtures" / "phase16-dogfood" / fixture_id,
        ):
            candidate = base / "trip.json"
            if candidate.is_file():
                loaded = json.loads(candidate.read_text(encoding="utf-8"))
                if len(loaded.get("assets") or []) >= 4:
                    trip_path = candidate
                    trip = loaded
                    break
        if trip is None:
            try:
                from scripts.phase3_ig2_report import load_fixture_trip

                trip = load_fixture_trip(fixture_id)
                trip_path = (
                    ROOT / "tests" / "fixtures" / "clustering" / fixture_id / "assets-manifest.json"
                )
                print(f"synthesized trip from clustering fixture: {fixture_id}")
            except Exception as exc:
                print(
                    f"trip not found for fixture={fixture_id!r}: {exc}",
                    file=sys.stderr,
                )
                return 1

    assert trip is not None and trip_path is not None
    from travelogue.config import get_config

    base = get_config(reload=True)
    work_root = ROOT / ".cache" / "tpc-curate-perf"
    work_root.mkdir(parents=True, exist_ok=True)

    cfg_off = replace(
        base,
        mosaic=replace(
            base.mosaic,
            template_contract=TemplateContractConfig(enabled=False, shadow_log=False),
        ),
    )
    cfg_on = replace(
        base,
        mosaic=replace(
            base.mosaic,
            template_contract=TemplateContractConfig(enabled=True, shadow_log=False),
        ),
    )
    # Discard cold-start (NIMA/CLIP load) so P95 compares like-for-like.
    print("warm-up …")
    _run_once(trip, work=work_root / "warmup-off", cfg=cfg_off)
    _run_once(trip, work=work_root / "warmup-on", cfg=cfg_on)

    off_ms: list[float] = []
    on_ms: list[float] = []
    for i in range(max(1, args.repeats)):
        off_ms.append(_run_once(trip, work=work_root / f"off-{i}", cfg=cfg_off))
        on_ms.append(_run_once(trip, work=work_root / f"on-{i}", cfg=cfg_on))
        print(f"  repeat {i+1}: off={off_ms[-1]:.1f}ms on={on_ms[-1]:.1f}ms")

    off_p95, on_p95 = _p95(off_ms), _p95(on_ms)
    delta = None if off_p95 <= 0 else round((on_p95 - off_p95) / off_p95 * 100.0, 2)
    ok = delta is not None and delta <= BUDGET_PCT
    try:
        trip_label = str(trip_path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        trip_label = str(trip_path).replace("\\", "/")
    report = {
        "recordedAt": _now(),
        "trip": trip_label,
        "repeats": args.repeats,
        "budgetPct": BUDGET_PCT,
        "offMs": off_ms,
        "onMs": on_ms,
        "offP95Ms": round(off_p95, 2),
        "onP95Ms": round(on_p95, 2),
        "deltaPct": delta,
        "withinBudget": ok,
        "medianOffMs": round(statistics.median(off_ms), 2),
        "medianOnMs": round(statistics.median(on_ms), 2),
    }
    print(
        f"\nP95: off={report['offP95Ms']}ms → on={report['onP95Ms']}ms "
        f"(Δ {delta}% · budget ≤{BUDGET_PCT}% · {'OK' if ok else 'OVER'})"
    )
    if args.write:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {args.out}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
