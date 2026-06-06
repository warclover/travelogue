"""Compare stored trip cover vs fresh pick_cover_asset_id replay."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _layout_eligible(trip: dict) -> list[dict]:
    return [a for a in (trip.get("assets") or []) if a.get("layoutEligible", True)]


def main() -> int:
    trip_id = sys.argv[1] if len(sys.argv) > 1 else "demo-1506104ebf"
    trip_path = ROOT / "trips" / trip_id / "trip.json"
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    from travelogue.config import get_config
    from travelogue.curation.aesthetic_score import aesthetic_overall
    from travelogue.curation.curate_scoring import (
        _cover_batch_medians,
        cover_asset_pool,
        effective_cover_score,
        pick_cover_asset_id,
    )
    from travelogue.curation.layout_planner import aspect_kind_for_asset

    cfg = get_config()
    assets = _layout_eligible(trip)
    curation = trip.get("curation") or {}
    stored = {
        "coverAssetId": trip.get("coverAssetId"),
        "coverByLayout": curation.get("coverByLayout"),
    }
    ae_enabled = cfg.aesthetic.enabled
    with_ae = sum(1 for a in assets if aesthetic_overall(a) is not None)

    print(f"trip: {trip_id}  title: {(trip.get('meta') or {}).get('title')}")
    print(f"layout-eligible: {len(assets)}")
    print(f"aesthetic.enabled: {ae_enabled}  ml_calibrate: {cfg.aesthetic.ml_calibrate}")
    print(f"assets with quality.aesthetic.overall: {with_ae}/{len(assets)}")
    print(f"stored coverAssetId: {stored['coverAssetId']}")
    print(f"stored coverByLayout: {stored['coverByLayout']}")
    print()

    for layout in ("mobile", "web"):
        pool = cover_asset_pool(assets, export_layout=layout)
        med_sharp, med_ae = _cover_batch_medians(pool, aesthetic_enabled=None)
        fresh = pick_cover_asset_id(
            assets,
            export_layout=layout,
            enable_phase6_cover_factors=True,
            cover_scoring=cfg.curate.cover_scoring,
            aesthetic_enabled=None,
        )
        stored_id = (stored["coverByLayout"] or {}).get(layout) if stored["coverByLayout"] else stored["coverAssetId"]
        match = fresh == stored_id
        print(f"--- {layout} ---")
        print(f"  pool size: {len(pool)}  median_aesthetic: {med_ae:.4f}")
        print(f"  stored: {stored_id}  fresh: {fresh}  match: {match}")

        scored = []
        for a in pool:
            sc = effective_cover_score(
                a,
                layout,
                median_sharp=med_sharp,
                median_overall=med_ae,
                aesthetic_enabled=None,
                cover_scoring=cfg.curate.cover_scoring,
            )
            scored.append((sc, a["id"], aspect_kind_for_asset(a), aesthetic_overall(a)))
        scored.sort(reverse=True)
        print("  top 5:")
        for sc, aid, kind, ae in scored[:5]:
            mark = " *" if aid == fresh else (" S" if aid == stored_id else "")
            ae_s = f"{ae:.3f}" if ae is not None else "—"
            print(f"    {aid} score={sc:.4f} kind={kind} aesthetic={ae_s}{mark}")
        if not match:
            print("  >> MISMATCH: trip.json cover is stale; re-curate to refresh")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
