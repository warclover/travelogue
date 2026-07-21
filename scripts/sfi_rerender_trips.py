#!/usr/bin/env python3
"""Share-Face Integrity W0 · 存量册批量重渲（BE-SFI-05）。

失败时保留旧 HTML（render 写失败不删旧文件）。默认扫描 trips/ 下含 trip.json 的目录。

用法::

    python scripts/sfi_rerender_trips.py
    python scripts/sfi_rerender_trips.py --trips-dir trips --only demo-album,demo-e863ec0da9
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SFI W0 · batch re-render trips")
    parser.add_argument(
        "--trips-dir",
        type=Path,
        default=_repo_root() / "trips",
        help="Trips root (default: <repo>/trips)",
    )
    parser.add_argument(
        "--only",
        type=str,
        default="",
        help="Comma-separated trip dir names to include",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List targets only",
    )
    args = parser.parse_args(argv)

    trips_dir = args.trips_dir.resolve()
    if not trips_dir.is_dir():
        print(f"trips dir not found: {trips_dir}", file=sys.stderr)
        return 2

    only = {x.strip() for x in args.only.split(",") if x.strip()}
    targets: list[Path] = []
    for child in sorted(trips_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        if only and child.name not in only:
            continue
        trip_json = child / "trip.json"
        if trip_json.is_file():
            targets.append(trip_json)

    print(f"targets: {len(targets)}")
    if args.dry_run:
        for t in targets:
            print(f"  {t.parent.name}")
        return 0

    # Import after path resolve so dry-run works without heavy deps
    sys.path.insert(0, str(_repo_root()))
    from travelogue.web.rerender import rerender_draft_trip

    ok = 0
    failed: list[tuple[str, str]] = []
    for trip_json in targets:
        name = trip_json.parent.name
        try:
            written = rerender_draft_trip(trip_json)
            print(f"OK  {name}: {', '.join(written)}")
            ok += 1
        except Exception as exc:  # noqa: BLE001 — batch must continue
            failed.append((name, str(exc)))
            print(f"FAIL {name}: {exc}", file=sys.stderr)

    print(f"done: ok={ok} fail={len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
