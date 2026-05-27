"""LS-P2-01 · measure P0 longshot success rate across trip workspaces.

Usage:
  python scripts/phase2_longshot_stability.py trips/linzhi
  python scripts/phase2_longshot_stability.py trips --min-success 0.8
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.export.longshot import LongshotExportError, export_trip_longshot
from travelogue.render.engine import LONGSHOT_INDEX_NAME


def _iter_trip_dirs(root: Path) -> list[Path]:
    root = root.resolve()
    if (root / "trip.json").is_file() and (root / LONGSHOT_INDEX_NAME).is_file():
        return [root]
    rows: list[Path] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        if (child / "trip.json").is_file() and (child / LONGSHOT_INDEX_NAME).is_file():
            rows.append(child)
    return rows


def run_stability(
    root: Path,
    *,
    scale: int = 1,
    min_success: float = 0.8,
) -> int:
    trips = _iter_trip_dirs(root)
    if not trips:
        print(f"No renderable trips under {root}", file=sys.stderr)
        return 2

    results: list[dict] = []
    for trip_dir in trips:
        row = {"tripId": trip_dir.name, "ok": False, "method": "", "outputs": 0, "error": ""}
        try:
            result = export_trip_longshot(trip_dir, scale=scale, watermark=True)
            row["ok"] = bool(result.outputs)
            row["method"] = result.capture_method
            row["outputs"] = len(result.outputs)
        except LongshotExportError as exc:
            row["error"] = exc.code
        except Exception as exc:
            row["error"] = str(exc)
        results.append(row)

    ok_count = sum(1 for row in results if row["ok"])
    rate = ok_count / len(results)
    print(json.dumps({"trips": len(results), "ok": ok_count, "rate": round(rate, 3), "results": results}, ensure_ascii=False, indent=2))
    if rate < min_success:
        print(
            f"LS-P2-01 FAIL: P0 success rate {rate:.0%} < {min_success:.0%} ({ok_count}/{len(results)})",
            file=sys.stderr,
        )
        return 1
    print(f"LS-P2-01 PASS: P0 success rate {rate:.0%} ({ok_count}/{len(results)})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2 longshot stability gate (LS-P2-01)")
    parser.add_argument("trips_root", type=Path, help="trip dir or trips/ root")
    parser.add_argument("--scale", type=int, default=1)
    parser.add_argument("--min-success", type=float, default=0.8)
    args = parser.parse_args()
    return run_stability(args.trips_root, scale=args.scale, min_success=args.min_success)


if __name__ == "__main__":
    raise SystemExit(main())
