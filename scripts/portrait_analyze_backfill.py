"""Backfill quality.portrait on existing trips (PC-M1 · no full re-ingest)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image

from travelogue.config import get_config
from travelogue.curation.aesthetic_score import (
    compute_aesthetic,
    compute_aesthetic_signals,
)
from travelogue.media.portrait_analyze import analyze_portrait
from travelogue.media.subject_detect import detect_faces_in_image


def _load_trip(trip_dir: Path) -> dict:
    return json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))


def _save_trip(trip_dir: Path, trip: dict) -> None:
    (trip_dir / "trip.json").write_text(
        json.dumps(trip, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _resolve_source(trip_dir: Path, asset: dict) -> Path | None:
    rel = asset.get("sourceFile") or asset.get("displayFile")
    if not rel:
        return None
    path = trip_dir / str(rel)
    return path if path.is_file() else None


def backfill_trip(
    trip_dir: Path,
    *,
    dry_run: bool = False,
    recompute_aesthetic: bool = True,
) -> dict:
    app_cfg = get_config()
    portrait_cfg = app_cfg.cull.portrait
    ingest_cfg = app_cfg.ingest
    ae_cfg = app_cfg.aesthetic
    trip = _load_trip(trip_dir)
    assets = list(trip.get("assets") or [])
    stats = {
        "tripId": trip.get("tripId") or trip_dir.name,
        "assets": len(assets),
        "faces": 0,
        "portraitAnalyzed": 0,
        "aestheticRefreshed": 0,
    }
    for asset in assets:
        if asset.get("type", "image") == "video":
            continue
        src = _resolve_source(trip_dir, asset)
        if src is None:
            continue
        try:
            img = Image.open(src)
        except OSError:
            continue
        faces = detect_faces_in_image(
            img,
            min_size=ingest_cfg.face_min_size_px,
            max_edge=ingest_cfg.face_detect_max_edge,
        )
        if not faces:
            continue
        stats["faces"] += 1
        result = analyze_portrait(
            img,
            faces,
            cfg=portrait_cfg,
            min_face_px=ingest_cfg.face_min_size_px,
        )
        block = result.to_quality_dict(cfg=portrait_cfg)
        q = asset.setdefault("quality", {})
        if not isinstance(q, dict):
            continue
        q["portrait"] = block
        q["faceCount"] = len(faces)
        if result.eyes_open_score is not None:
            q["portraitEyesOpenScore"] = round(result.eyes_open_score, 4)
        stats["portraitAnalyzed"] += 1
        if recompute_aesthetic and ae_cfg.enabled:
            signals = compute_aesthetic_signals(img, asset, cfg=ae_cfg)
            q["aesthetic"] = compute_aesthetic(
                asset,
                signals=signals,
                cfg=ae_cfg,
                portrait_cfg=portrait_cfg,
            )
            stats["aestheticRefreshed"] += 1
    if not dry_run:
        _save_trip(trip_dir, trip)
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill portrait_analyze on existing trips")
    parser.add_argument("--trip-dir", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    trip_dir = args.trip_dir if args.trip_dir.is_absolute() else (ROOT / args.trip_dir).resolve()
    stats = backfill_trip(trip_dir, dry_run=args.dry_run)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
