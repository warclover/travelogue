"""End-to-end algorithm integrity checks on a real trip.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _images(trip: dict) -> list[dict]:
    return [a for a in (trip.get("assets") or []) if str(a.get("type") or "image") == "image"]


def _displayed_ids(trip: dict) -> set[str]:
    out: set[str] = set()
    for ch in trip.get("chapters") or []:
        for sc in ch.get("screens") or []:
            for aid in sc.get("assetIds") or []:
                out.add(str(aid))
            for sl in sc.get("slots") or []:
                if isinstance(sl, dict) and sl.get("assetId"):
                    out.add(str(sl["assetId"]))
    return out


def main() -> int:
    trip_id = sys.argv[1] if len(sys.argv) > 1 else "demo-1506104ebf"
    trip = json.loads((ROOT / "trips" / trip_id / "trip.json").read_text(encoding="utf-8"))
    images = _images(trip)
    pool = {a["id"] for a in images if not a.get("excludeReason")}
    displayed = _displayed_ids(trip)
    curation = trip.get("curation") or {}
    cs = curation.get("cullSummary") or {}
    lm = curation.get("layoutMetrics") or {}
    cover = curation.get("coverByLayout") or {}

    issues: list[str] = []
    warnings: list[str] = []

    # Cull funnel
    excluded = len(images) - len(pool)
    if cs.get("excludedByCull") and int(cs["excludedByCull"]) != excluded:
        issues.append(f"cullSummary.excludedByCull {cs.get('excludedByCull')} != actual {excluded}")

    # Coverage chain
    missing_on_screen = sorted(pool - displayed)
    not_in_pool = displayed - pool
    if not_in_pool:
        issues.append(f"displayed but not in pool: {sorted(not_in_pool)[:5]}")

    eligible_cov = lm.get("eligibleToScreenCoverage")
    elig_count = lm.get("layoutEligibleCount")
    disp_count = lm.get("displayedOnScreenCount")
    if elig_count and disp_count is not None and eligible_cov is not None:
        expected = round(int(disp_count) / int(elig_count), 6)
        if abs(expected - float(eligible_cov)) > 0.001:
            issues.append(f"eligibleToScreenCoverage mismatch: stored={eligible_cov} calc={expected}")

    # Cover vs skip_screen
    skip = set()
    if cover.get("web"):
        skip.add(cover["web"])
    for aid in missing_on_screen:
        if aid in skip:
            warnings.append(f"{aid} missing on screen (expected: cover/skip)")

    # Aesthetic coverage
    from travelogue.curation.aesthetic_score import asset_aesthetic

    scored = sum(1 for a in images if asset_aesthetic(a))
    if scored and scored < len(pool):
        warnings.append(f"aesthetic partial: {scored}/{len(pool)} in pool have quality.aesthetic")
    if scored == 0 and len(pool) > 0:
        warnings.append("aesthetic stale: pool has 0 scored assets (re-ingest needed)")

    # Replay cover pick
    from travelogue.config import get_config
    from travelogue.curation.curate_scoring import pick_cover_asset_id

    layout_assets = [a for a in images if a.get("layoutEligible", True)]
    cfg = get_config()
    for layout in ("mobile", "web"):
        stored = cover.get(layout) or trip.get("coverAssetId")
        fresh = pick_cover_asset_id(
            layout_assets,
            export_layout=layout,
            cover_scoring=cfg.curate.cover_scoring,
        )
        if stored and fresh != stored:
            issues.append(f"cover replay mismatch {layout}: stored={stored} fresh={fresh}")

    print(f"trip: {trip_id}")
    print(f"images={len(images)} pool={len(pool)} excluded={excluded}")
    print(f"displayed_on_screen={len(displayed)} missing_from_pool={len(missing_on_screen)}")
    print(f"coverByLayout={cover}")
    print(f"layoutMetrics: eligible={elig_count} displayed={disp_count} coverage={eligible_cov}")
    print(f"patternRepeatRate={lm.get('patternRepeatRate')} diversity={lm.get('patternDiversity')}")
    print()
    if issues:
        print("ISSUES:")
        for x in issues:
            print(f"  - {x}")
    else:
        print("ISSUES: none")
    if warnings:
        print("WARNINGS:")
        for x in warnings:
            print(f"  - {x}")
    else:
        print("WARNINGS: none")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
