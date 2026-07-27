"""Backfill faces + protectBox on existing trip assets (person-safe crop).

Re-runs Haar (frontal + profile) detection on derivative WebPs — does not
re-export images or require original source files.

Usage:
  python scripts/backfill_faces_protect.py demo-ef0cef1d1d
  python scripts/backfill_faces_protect.py --all --overwrite
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.media.subject_detect import _opencv_available, analyze_subject


def _resolve_detect_image(trip_dir: Path, asset: dict) -> Path | None:
    """Prefer mid-size derivative (≤1600) for Haar; fall back to display/source."""
    srcset = asset.get("srcset") or []
    best: tuple[int, Path] | None = None
    if isinstance(srcset, list):
        for entry in srcset:
            if not isinstance(entry, dict):
                continue
            rel = entry.get("file")
            try:
                width = int(entry.get("width") or 0)
            except (TypeError, ValueError):
                width = 0
            if not rel or width <= 0:
                continue
            path = trip_dir / str(rel).replace("\\", "/")
            if not path.is_file():
                continue
            # Prefer ≤1600, else the smallest available above.
            score = width if width <= 1600 else width + 100_000
            if best is None or score < best[0]:
                best = (score, path)
    if best is not None:
        return best[1]
    for key in ("displayFile", "sourceFile"):
        rel = asset.get(key)
        if not rel:
            continue
        path = trip_dir / str(rel).replace("\\", "/")
        if path.is_file():
            return path
    return None


def backfill_trip(
    trip_path: Path,
    *,
    overwrite: bool = False,
    face_detect_max_edge: int = 1024,
) -> dict:
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    trip_dir = trip_path.parent
    opencv = _opencv_available()
    updated = 0
    skipped = 0
    faces_hit = 0
    for asset in trip.get("assets") or []:
        if asset.get("type") != "image":
            continue
        has_faces = isinstance(asset.get("faces"), list) and len(asset.get("faces") or []) > 0
        has_protect = isinstance(asset.get("protectBox"), dict)
        if has_faces and has_protect and not overwrite:
            skipped += 1
            continue
        img_path = _resolve_detect_image(trip_dir, asset)
        if not img_path:
            skipped += 1
            continue
        with Image.open(img_path) as img:
            img = ImageOps.exif_transpose(img)
            # Map detections back to native/display aspect of the asset file we opened.
            subj = analyze_subject(
                img,
                enabled=True,
                face_detect_max_edge=face_detect_max_edge,
            )
        if subj.has_face and subj.faces_norm:
            asset["faces"] = [dict(f) for f in subj.faces_norm]
            if subj.protect_box:
                asset["protectBox"] = dict(subj.protect_box)
            if subj.salient_box:
                asset["salientBox"] = subj.salient_box
            asset["focalPoint"] = {"x": subj.focal[0], "y": subj.focal[1]}
            q = asset.setdefault("quality", {})
            if isinstance(q, dict):
                q["faceCount"] = int(subj.face_count)
                if subj.salient_box:
                    fr = float(subj.salient_box.get("w", 0.0)) * float(
                        subj.salient_box.get("h", 0.0)
                    )
                    q["faceRatio"] = round(max(0.0, min(1.0, fr)), 4)
            tags = list(asset.get("tags") or [])
            for t in ("person", "face"):
                if t not in tags:
                    tags.append(t)
            asset["tags"] = tags
            faces_hit += 1
        elif overwrite:
            asset.pop("faces", None)
            asset.pop("protectBox", None)
        updated += 1

    trip_path.write_text(
        json.dumps(trip, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    total = sum(1 for a in trip.get("assets") or [] if a.get("type") == "image")
    with_faces = sum(
        1
        for a in trip.get("assets") or []
        if isinstance(a.get("faces"), list) and a.get("faces")
    )
    with_protect = sum(
        1 for a in trip.get("assets") or [] if isinstance(a.get("protectBox"), dict)
    )
    return {
        "tripId": trip.get("tripId"),
        "opencv": opencv,
        "processed": updated,
        "skipped": skipped,
        "facesDetected": faces_hit,
        "withFaces": with_faces,
        "withProtectBox": with_protect,
        "totalImages": total,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill faces + protectBox on trip assets (no image re-export)"
    )
    parser.add_argument("trip_ids", nargs="*", help="Trip ids under trips/")
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    parser.add_argument("--all", action="store_true", help="Process every trip.json")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-detect even when faces/protectBox already present",
    )
    parser.add_argument("--face-detect-max-edge", type=int, default=1024)
    args = parser.parse_args()
    if not _opencv_available():
        print("WARN: OpenCV not installed — faces backfill will no-op")

    trip_ids = list(args.trip_ids)
    if args.all:
        trip_ids = sorted(
            p.parent.name
            for p in args.trips_dir.glob("*/trip.json")
            if p.is_file()
        )
    if not trip_ids:
        print("No trip ids given (pass ids or --all)", file=sys.stderr)
        return 2

    for tid in trip_ids:
        path = args.trips_dir / tid / "trip.json"
        if not path.is_file():
            print(f"SKIP {tid}")
            continue
        r = backfill_trip(
            path,
            overwrite=args.overwrite,
            face_detect_max_edge=int(args.face_detect_max_edge),
        )
        print(
            f"{tid}: processed={r['processed']} faces={r['facesDetected']} "
            f"withFaces={r['withFaces']}/{r['totalImages']} "
            f"withProtect={r['withProtectBox']} opencv={r['opencv']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
