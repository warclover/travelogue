"""CCF dogfood helper: inspect trips, render on/off craft, capture cover screenshots."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TRIP_CANDIDATES = [
    "demo-0ebda73294",
    "demo-3ee2727aea",
    "demo-65db8fd377",
    "demo-album",
    "linzhi",
    "demo-20ecc928d6",
    "demo-817f1f8801",
]


def _load_trip(trip_id: str) -> dict | None:
    p = ROOT / "trips" / trip_id / "trip.json"
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def inspect_trips() -> list[dict]:
    rows = []
    for tid in TRIP_CANDIDATES:
        trip = _load_trip(tid)
        if not trip:
            continue
        meta = trip.get("meta") or {}
        rows.append(
            {
                "tripId": tid,
                "style": meta.get("coverOpeningStyle"),
                "title": meta.get("title"),
                "coverAssetId": trip.get("coverAssetId"),
                "hasIndex": (ROOT / "trips" / tid / "index.html").is_file(),
            }
        )
    return rows


def main() -> int:
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "inspect").strip()
    if cmd == "inspect":
        for row in inspect_trips():
            print(
                f"{row['tripId']}: style={row['style']} "
                f"title={row['title']!r} cover={row['coverAssetId']} index={row['hasIndex']}"
            )
        return 0

    if cmd == "assignable":
        from travelogue.config import get_config, reset_config_cache
        from travelogue.cover_engine import assignable_style_ids

        reset_config_cache()
        cfg = get_config()
        print("cover_craft.enabled=", cfg.cover_craft.enabled)
        print("assignable=", assignable_style_ids())
        print("env TRAVELOGUE_COVER_CRAFT=", os.environ.get("TRAVELOGUE_COVER_CRAFT"))
        return 0

    if cmd == "render":
        # usage: render <tripId> on|off
        trip_id = sys.argv[2]
        mode = sys.argv[3]  # on|off
        os.environ["TRAVELOGUE_COVER_CRAFT"] = "1" if mode == "on" else "0"
        from travelogue.config import reset_config_cache

        reset_config_cache()
        from travelogue.cli import main as cli_main

        # Prefer module CLI if available
        sys.argv = ["travelogue", "render", trip_id]
        try:
            from travelogue.__main__ import main as pkg_main

            return int(pkg_main() or 0)
        except Exception:
            import subprocess

            return subprocess.call(
                [sys.executable, "-m", "travelogue", "render", trip_id], cwd=str(ROOT)
            )

    print("usage: inspect | assignable | render <tripId> on|off")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
