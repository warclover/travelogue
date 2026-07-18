#!/usr/bin/env python3
"""TPC W1 · AC-TPC-12 shadow diff: mix inverted index vs live try_order sets.

Usage:
  python scripts/layout_contract_shadow_diff.py --golden
  python scripts/layout_contract_shadow_diff.py linzhi
  python scripts/layout_contract_shadow_diff.py --golden --out docs/acceptance-records/tpc-w1-shadow-diff.json

Does not switch the candidate entry. Exit code 2 if any unsigned diff remains
when --strict is set.
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
    for asset in t.get("assets") or []:
        asset.pop("sceneClusterId", None)
        asset.pop("clusterSource", None)
    return t


def _trip_dirs(args: argparse.Namespace) -> list[Path]:
    from travelogue.curation.usage_rules.metrics import URO_GOLDEN_TRIP_IDS

    ids: list[str] = []
    if args.golden:
        ids.extend(URO_GOLDEN_TRIP_IDS)
    ids.extend(args.trip_id or [])
    if not ids:
        ids = ["linzhi"]
    out: list[Path] = []
    for tid in dict.fromkeys(ids):
        d = ROOT / "trips" / tid
        if (d / "trip.json").is_file():
            out.append(d)
        else:
            print(f"skip missing trip: {tid}", file=sys.stderr)
    return out


def _collect_windows_from_chapters(
    chapters: list[dict],
    assets_map: dict[str, dict],
) -> list[tuple[str, list[str]]]:
    """Return (segment_label, asset_ids) for content screens."""
    from travelogue.layout_contract.orientations import aspect_kind_for_asset

    windows: list[tuple[str, list[str]]] = []
    for ch in chapters:
        cid = str(ch.get("id") or "")
        for i, screen in enumerate(ch.get("screens") or []):
            pid = str(screen.get("patternId") or "")
            if not pid or pid.startswith("breath"):
                continue
            aids = [
                str(sl["assetId"])
                for sl in (screen.get("slots") or [])
                if sl.get("assetId")
            ]
            if len(aids) < 3:
                continue
            # ensure aspects resolvable
            for aid in aids:
                aspect_kind_for_asset(assets_map.get(aid) or {})
            windows.append((f"{cid}#{i}:{pid}", aids))
    return windows


def main() -> int:
    parser = argparse.ArgumentParser(description="TPC mix-index shadow diff (AC-TPC-12)")
    parser.add_argument("trip_id", nargs="*")
    parser.add_argument("--golden", action="store_true")
    parser.add_argument(
        "--from-existing",
        action="store_true",
        help="Diff windows from existing trip.json chapters (no re-curate)",
    )
    parser.add_argument("--work", type=Path, default=ROOT / ".cache" / "layout-shadow")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 2 if any hasDiff=true rows remain",
    )
    args = parser.parse_args()

    from travelogue.config import get_config
    from travelogue.curation.clustering import run_clustering_layer
    from travelogue.curation.curate import run_curate
    from travelogue.layout_contract.orientations import aspect_kind_for_asset
    from travelogue.layout_engine.contract.shadow import compute_mix_shadow_diff

    trip_dirs = _trip_dirs(args)
    if not trip_dirs:
        print("no local trips found", file=sys.stderr)
        return 1

    cfg = get_config(reload=True)
    rows: list[dict[str, Any]] = []
    diff_count = 0

    for trip_dir in trip_dirs:
        trip = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
        print(f"shadow · {trip_dir.name} …")
        if args.from_existing and trip.get("chapters"):
            body = trip
        else:
            body = _prepare_trip(trip)
            work = args.work / trip_dir.name
            work.mkdir(parents=True, exist_ok=True)
            run_clustering_layer(body, trip_dir=work / "cluster", cfg=cfg)
            run_curate(body, apply_layout=True, trip_dir=work, cfg=cfg)

        assets_map = {str(a["id"]): a for a in (body.get("assets") or []) if a.get("id")}
        aspects = {
            aid: aspect_kind_for_asset(asset) for aid, asset in assets_map.items()
        }
        windows = _collect_windows_from_chapters(body.get("chapters") or [], assets_map)
        for label, aids in windows:
            diff = compute_mix_shadow_diff(aids, aspects, assets_map)
            row = {
                "tripId": trip_dir.name,
                "window": label,
                "n": len(aids),
                **diff.to_dict(),
                "signOff": None,
                "signOffNote": None,
            }
            rows.append(row)
            if diff.has_diff:
                diff_count += 1

        print(f"  windows={len(windows)} diffs={sum(1 for r in rows if r['tripId']==trip_dir.name and r['hasDiff'])}")

    report = {
        "schemaVersion": "tpc-shadow-diff-v1",
        "feature": "TPC",
        "gate": "AC-TPC-12",
        "generatedAt": _utc_now(),
        "windowCount": len(rows),
        "diffCount": diff_count,
        "allClear": diff_count == 0,
        "rows": rows,
        "notes": (
            "Set signOff=true per row (or bulk) after human review before enabling "
            "mosaic.template_contract.enabled. hasDiff=false rows need no sign-off."
        ),
    }
    out = args.out or (args.work / "tpc_w1_shadow_diff.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\ndiffCount={diff_count}/{len(rows)} allClear={report['allClear']} → {out}")
    if args.strict and diff_count:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
