#!/usr/bin/env python3
"""TPC W1 · layout-debt report (legacy rate / mix holes / match rate).

Usage:
  python scripts/layout_debt_report.py --golden
  python scripts/layout_debt_report.py linzhi demo-2025
  python scripts/layout_debt_report.py --golden --out docs/acceptance-records/tpc-w1-debt-baseline.json
  python scripts/layout_debt_report.py --from-trip-json trips/linzhi/trip.json   # reuse existing log

BQP / URO golden trip set is the SSOT (URO_GOLDEN_TRIP_IDS); missing local trips are skipped.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _prepare_trip(trip: dict) -> dict:
    t = copy.deepcopy(trip)
    t.setdefault("pipeline", {})["status"] = "structure_draft"
    t.pop("chapters", None)
    cur = t.setdefault("curation", {})
    cur.pop("clustering", None)
    cur.pop("layoutStrategy", None)
    cur.pop("mosaicDecisionLog", None)
    cur.pop("layoutDecisionLog", None)
    for asset in t.get("assets") or []:
        asset.pop("sceneClusterId", None)
        asset.pop("clusterSource", None)
    return t


def _resolve_trip_dirs(args: argparse.Namespace) -> list[Path]:
    from travelogue.curation.usage_rules.metrics import URO_GOLDEN_TRIP_IDS

    if args.from_trip_json:
        return [Path(args.from_trip_json).resolve().parent]

    ids: list[str] = []
    if args.golden:
        ids.extend(URO_GOLDEN_TRIP_IDS)
    ids.extend(args.trip_id or [])
    # de-dupe preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for tid in ids:
        if tid not in seen:
            seen.add(tid)
            ordered.append(tid)

    if not ordered:
        ordered = ["linzhi"]

    trips_root = ROOT / "trips"
    dirs: list[Path] = []
    for tid in ordered:
        d = trips_root / tid
        if (d / "trip.json").is_file():
            dirs.append(d)
        else:
            print(f"skip missing trip: {tid}", file=sys.stderr)
    return dirs


def _templates():
    from travelogue.layout_templates.registry import get_engine

    engine = get_engine()
    return {t.id: t for t in engine.list_active(enforce_quotas=False)}


def _report_from_existing(trip_dir: Path) -> dict[str, Any] | None:
    from travelogue.curation.layout_metrics import compute_layout_metrics
    from travelogue.layout_engine.contract.debt import build_trip_debt_report

    trip_path = trip_dir / "trip.json"
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    chapters = trip.get("chapters") or []
    assets = trip.get("assets") or []
    logs = (trip.get("curation") or {}).get("mosaicDecisionLog") or []
    if not chapters or not logs:
        return None
    metrics = compute_layout_metrics(chapters, assets)
    return build_trip_debt_report(
        trip_id=trip_dir.name,
        mosaic_logs=list(logs),
        chapters=chapters,
        assets=assets,
        layout_metrics=metrics,
        templates=_templates(),
    )


def _report_via_curate(trip_dir: Path, *, work_root: Path) -> dict[str, Any]:
    from travelogue.config import get_config
    from travelogue.curation.clustering import run_clustering_layer
    from travelogue.curation.curate import run_curate
    from travelogue.curation.layout_metrics import compute_layout_metrics
    from travelogue.layout_engine.contract.debt import build_trip_debt_report

    trip_path = trip_dir / "trip.json"
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    cfg = get_config(reload=True)
    body = _prepare_trip(trip)
    work = work_root / trip_dir.name
    work.mkdir(parents=True, exist_ok=True)
    run_clustering_layer(body, trip_dir=work / "cluster", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=work, cfg=cfg)
    chapters = body.get("chapters") or []
    assets = body.get("assets") or []
    logs = (body.get("curation") or {}).get("mosaicDecisionLog") or []
    metrics = compute_layout_metrics(chapters, assets)
    return build_trip_debt_report(
        trip_id=trip_dir.name,
        mosaic_logs=list(logs),
        chapters=chapters,
        assets=assets,
        layout_metrics=metrics,
        templates=_templates(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="TPC layout-debt report")
    parser.add_argument("trip_id", nargs="*", help="trip folder name(s) under trips/")
    parser.add_argument(
        "--golden",
        action="store_true",
        help="Include URO_GOLDEN_TRIP_IDS (BQP 8+ SSOT)",
    )
    parser.add_argument(
        "--reuse-log",
        action="store_true",
        help="Prefer existing mosaicDecisionLog in trip.json (no re-curate)",
    )
    parser.add_argument(
        "--from-trip-json",
        type=Path,
        help="Single trip.json path (implies --reuse-log when log present)",
    )
    parser.add_argument(
        "--work",
        type=Path,
        default=ROOT / ".cache" / "layout-debt",
        help="Working directory for re-curate",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write corpus JSON report",
    )
    args = parser.parse_args()

    trip_dirs = _resolve_trip_dirs(args)
    if not trip_dirs:
        print("no local trips found", file=sys.stderr)
        return 1

    from travelogue.layout_engine.contract.debt import merge_debt_reports
    from travelogue.layout_engine.contract.mix_index import (
        build_mix_inverted_index,
        format_mix_key,
    )

    trip_reports: list[dict[str, Any]] = []
    for trip_dir in trip_dirs:
        print(f"debt · {trip_dir.name} …")
        rep = None
        if args.reuse_log or args.from_trip_json:
            rep = _report_from_existing(trip_dir)
            if rep is None:
                print("  no reusable log; falling back to curate", file=sys.stderr)
        if rep is None:
            rep = _report_via_curate(trip_dir, work_root=args.work)
        trip_reports.append(rep)
        legacy = rep.get("legacy") or {}
        print(
            f"  windows={legacy.get('windowCount')} legacyRate={legacy.get('legacyRate')} "
            f"match={rep.get('aspectPatternMatchRate')} holes={len(rep.get('mixHoles') or [])}"
        )

    corpus = merge_debt_reports(trip_reports)
    index = build_mix_inverted_index(_templates())
    report = {
        "schemaVersion": "tpc-debt-v1",
        "feature": "TPC",
        "generatedAt": _utc_now(),
        "corpus": corpus,
        "libraryMixIndex": {format_mix_key(k): v for k, v in index.items()},
        "tripReports": trip_reports,
    }

    out = args.out or (args.work / "layout_debt_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\ncorpus legacyRate={corpus.get('legacyRate')} → {out}")
    if corpus.get("mixHoleTop"):
        print("mix holes (top):")
        for row in corpus["mixHoleTop"][:8]:
            print(f"  {row['mix']}  freq={row['windowFreq']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
