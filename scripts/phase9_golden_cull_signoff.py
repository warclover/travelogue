#!/usr/bin/env python3
"""NR-P9-04 · re-ingest golden trips with cull-on and write signoff metrics."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config import get_config
from travelogue.curation.curate import layout_eligible_assets, run_curate
from travelogue.media.ingest import ingest_into_trip
from travelogue.media.ingest_report import format_ingest_report
from travelogue.services.trip import TripService
from travelogue.services.trip_factory import create_trip

DEFAULT_ALBUMS: dict[str, str] = {
    "mao": r"D:\Photos\mao",
    "maomi": r"D:\Photos\maomi",
}


def _load_trip(trip_id: str, trips_dir: Path) -> tuple[Path, Path, dict]:
    trip_json = trips_dir / trip_id / "trip.json"
    trip_dir = trip_json.parent
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    return trip_json, trip_dir, trip


def _cull_metrics(trip: dict) -> dict:
    assets = [a for a in trip.get("assets") or [] if a.get("type", "image") != "video"]
    n_scan = len(assets)
    featured = [a for a in assets if a.get("userTier") == "featured"]
    eligible = layout_eligible_assets(trip)
    non_feat_eligible = [
        a for a in eligible if a.get("userTier") != "featured"
    ]
    cull = (trip.get("curation") or {}).get("cullSummary") or {}
    ratio = (len(non_feat_eligible) / n_scan) if n_scan else 1.0
    floor = float(cull.get("keepRatioFloor") or 0.90)
    return {
        "scanned": n_scan,
        "featuredCount": len(featured),
        "layoutEligibleCount": len(eligible),
        "nonFeaturedEligibleCount": len(non_feat_eligible),
        "nonFeaturedKeepRatio": round(ratio, 4),
        "keepRatioFloor": floor,
        "floorMet": ratio >= floor or bool(cull.get("pass3Skipped")),
        "pass3Skipped": cull.get("pass3Skipped"),
        "floorNotMet": cull.get("floorNotMet", False),
        "excludedByCull": cull.get("excludedByCull", 0),
        "excludedByReason": cull.get("excludedByReason") or {},
        "cullUserLine": (trip.get("curation") or {}).get("cullUserLine"),
        "mode": cull.get("mode"),
        "mlFallbackRateL1": float(cull.get("mlFallbackRateL1") or 0.0),
        "branchFallbackRateL2": float(cull.get("branchFallbackRateL2") or 0.0),
        "branchFallbackByReasonL2": cull.get("branchFallbackByReasonL2") or {},
        "failOpenRateL3": float(cull.get("failOpenRateL3") or 0.0),
        "branchPortraitRatio": cull.get("branchPortraitRatio"),
        "branchLandscapeRatio": cull.get("branchLandscapeRatio"),
        "branchGrayRatio": cull.get("branchGrayRatio"),
        "cpuMs": cull.get("cpuMs"),
    }


def run_signoff(
    trip_id: str,
    album: Path,
    *,
    trips_dir: Path,
    config_path: Path | None,
    title: str,
    place: str,
    curate_smoke: bool,
) -> dict:
    if config_path:
        get_config(reload=True, path=config_path)
    cfg = get_config()
    trips_dir.mkdir(parents=True, exist_ok=True)
    project_root = trips_dir.parent

    trip_dir = trips_dir / trip_id
    if trip_dir.exists():
        shutil.rmtree(trip_dir)

    t0 = time.monotonic()
    trip_json = create_trip(trip_id, trips_dir, title=title, place=place)
    trip_dir = trips_dir / trip_id
    svc = TripService(root=project_root)
    trip = svc.load(trip_json)

    result = ingest_into_trip(
        trip,
        trip_dir,
        from_dir=album,
        app_cfg=cfg,
    )
    svc.save(trip, trip_json)
    ingest_ms = round((time.monotonic() - t0) * 1000.0, 1)

    metrics = _cull_metrics(trip)
    metrics["ingestMs"] = ingest_ms
    metrics["ingestAdded"] = result.added
    metrics["ingestSkipped"] = result.skipped
    metrics["report"] = format_ingest_report(result, trip)

    curate_ok = True
    curate_chapters = 0
    if curate_smoke:
        try:
            cur = run_curate(trip, export_layout="mobile", trip_dir=trip_dir, cfg=cfg)
            svc.save(trip, trip_json)
            curate_chapters = cur.chapter_count
        except Exception as exc:
            curate_ok = False
            metrics["curateError"] = str(exc)
    metrics["curateSmokeOk"] = curate_ok
    metrics["curateChapters"] = curate_chapters

    return {
        "tripId": trip_id,
        "albumPath": str(album),
        "signedOffAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "phase": "P9-QualityGate",
        "baseline": "cull-on",
        "metrics": metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 9 golden cull signoff")
    parser.add_argument("trip_id", nargs="?", help="mao | maomi")
    parser.add_argument("--album", type=Path, help="photo folder")
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    parser.add_argument("--config", type=Path, default=ROOT / "config.demo.yaml")
    parser.add_argument("--title", default=None)
    parser.add_argument("--place", default=None)
    parser.add_argument("--no-curate", action="store_true")
    parser.add_argument(
        "--write",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "phase9-golden-cull-signoff.json",
    )
    parser.add_argument("--all", action="store_true", help="run mao + maomi")
    args = parser.parse_args()

    targets: list[tuple[str, Path]] = []
    if args.all:
        for tid, ap in DEFAULT_ALBUMS.items():
            targets.append((tid, Path(ap)))
    elif args.trip_id:
        album = args.album or Path(DEFAULT_ALBUMS.get(args.trip_id, ""))
        if not album.is_dir():
            raise SystemExit(f"album not found: {album}")
        targets.append((args.trip_id, album))
    else:
        parser.error("trip_id or --all required")

    out: dict = {"schemaVersion": "1", "runs": []}
    if args.write.is_file():
        out = json.loads(args.write.read_text(encoding="utf-8"))

    for trip_id, album in targets:
        print(f"== signoff {trip_id} from {album}", flush=True)
        payload = run_signoff(
            trip_id,
            album,
            trips_dir=args.trips_dir,
            config_path=args.config if args.config.is_file() else None,
            title=args.title or trip_id,
            place=args.place or trip_id,
            curate_smoke=not args.no_curate,
        )
        out["runs"] = [r for r in out.get("runs", []) if r.get("tripId") != trip_id]
        out["runs"].append(payload)
        m = payload["metrics"]
        print(
            f"  scanned={m['scanned']} eligible={m['layoutEligibleCount']} "
            f"nonFeatRatio={m['nonFeaturedKeepRatio']} floorMet={m['floorMet']} "
            f"curate={m['curateSmokeOk']}",
            flush=True,
        )

    args.write.parent.mkdir(parents=True, exist_ok=True)
    args.write.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.write}", flush=True)


if __name__ == "__main__":
    main()
