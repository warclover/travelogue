"""Phase 17 strategy eval probe · AC-P17-11 + render error gate.

Usage:
  python scripts/phase17_strategy_eval.py tests/fixtures/clustering/golden-mixed-scenes
  python scripts/phase17_strategy_eval.py --trips-dir tests/fixtures/phase16-dogfood --strict
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from travelogue.paths import ROOT


def eval_trip_dir(trip_dir: Path) -> dict:
    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        raise FileNotFoundError(trip_json)
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    from travelogue.layout_engine.mosaic.render_check import compute_layout_render_error_rate

    render = compute_layout_render_error_rate(trip.get("chapters") or [])
    layout_strategy = (trip.get("curation") or {}).get("layoutStrategy") or {}
    screens = sum(len(ch.get("screens") or []) for ch in trip.get("chapters") or [])
    return {
        "tripId": trip.get("tripId") or trip_dir.name,
        "screenCount": screens,
        "layoutStrategy": layout_strategy,
        **render,
    }


def collect_trip_dirs(trips_dir: Path) -> list[Path]:
    if not trips_dir.is_dir():
        return []
    return sorted(p.parent for p in trips_dir.glob("*/trip.json"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 17 LSE strategy eval probe")
    parser.add_argument("trip_dirs", nargs="*", type=Path, help="Trip directories with trip.json")
    parser.add_argument(
        "--trips-dir",
        type=Path,
        help="Parent directory containing trip folders (alternative to positional dirs)",
    )
    parser.add_argument("--strict", action="store_true", help="Exit 1 when render error rate > 0")
    parser.add_argument("--out", type=Path, default=ROOT / ".cache" / "phase17-strategy-eval.json")
    args = parser.parse_args()

    dirs: list[Path] = list(args.trip_dirs)
    if args.trips_dir:
        dirs.extend(collect_trip_dirs(args.trips_dir))
    if not dirs:
        parser.error("provide trip_dirs and/or --trips-dir")

    results = [eval_trip_dir(Path(p)) for p in dirs]
    payload = {"results": results}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.strict and any(r.get("layout.render.error_rate", 0) > 0 for r in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
