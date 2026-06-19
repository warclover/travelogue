"""G3 dogfood · recurate + albumProfile + aesthetic alignment refresh."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config import get_config  # noqa: E402
from travelogue.curation.aesthetic_score import apply_aesthetic_alignment  # noqa: E402
from travelogue.curation.album_profile import write_album_profile  # noqa: E402
from travelogue.curation.curate import run_curate  # noqa: E402

DOGFOOD = [
    ("demo-2025-6", "trips/demo-2025-6"),
    ("demo-fc8b3a5c08", "trips/demo-fc8b3a5c08"),
    ("demo-1a737d6205", "trips/demo-1a737d6205"),
]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, trip: dict) -> None:
    path.write_text(json.dumps(trip, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def refresh_trip(trip_id: str, trip_dir_rel: str, *, recurate: bool) -> dict[str, Any]:
    trip_dir = ROOT / trip_dir_rel
    trip_path = trip_dir / "trip.json"
    trip = _load(trip_path)
    assets = copy.deepcopy(list(trip.get("assets") or []))
    app_cfg = get_config()

    profile = write_album_profile(trip)
    aesthetic_report = apply_aesthetic_alignment(
        assets,
        trip_dir=trip_dir,
        cfg=app_cfg,
        trip=trip,
    )
    trip["assets"] = assets
    _save(trip_path, trip)

    curate_summary: dict[str, Any] | None = None
    if recurate:
        result = run_curate(trip, export_layout="mobile", trip_dir=trip_dir)
        curate_summary = {
            "chapterCount": result.chapter_count,
            "layoutSummary": result.layout_summary,
        }
        _save(trip_path, trip)

    return {
        "tripId": trip_id,
        "albumProfile": profile,
        "aestheticAlignment": aesthetic_report,
        "curate": curate_summary,
        "purposeProfileKind": (trip.get("curation") or {}).get("purposeProfileKind"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G3 dogfood recurate")
    parser.add_argument("--no-curate", action="store_true", help="Only refresh aesthetic + profile")
    parser.add_argument("--write", type=Path, default=Path("docs/acceptance-records/aesthetic-g3-dogfood-recurate.v4.json"))
    args = parser.parse_args(argv)

    report: dict[str, Any] = {
        "recordedAt": datetime.now(UTC).isoformat(),
        "trips": [],
    }
    for trip_id, trip_dir in DOGFOOD:
        try:
            entry = refresh_trip(trip_id, trip_dir, recurate=not args.no_curate)
            report["trips"].append(entry)
            print(trip_id, "ok", entry.get("curate") or "profile-only")
        except Exception as exc:
            report["trips"].append({"tripId": trip_id, "error": str(exc)})
            print(trip_id, "error", exc)

    out = args.write if args.write.is_absolute() else ROOT / args.write
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("report", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
