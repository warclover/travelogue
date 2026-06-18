"""AA · GAP-03 · purpose pick blind review + automated proxy win rate.

Usage:
  python scripts/aesthetic_purpose_blind.py --trip-dir trips/demo-2025-6 --labels docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json
  python scripts/aesthetic_purpose_blind.py --trip-dir trips/demo-2025-6 --labels ... --write docs/acceptance-records/aesthetic-purpose-blind.demo-2025-6.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config import AppConfig  # noqa: E402
from travelogue.curation.aesthetic_purpose_blind import (  # noqa: E402
    automated_purpose_win_report,
    export_purpose_blind_signoff,
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AA GAP-03 · purpose pick blind review")
    parser.add_argument("--trip-dir", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--purposes", type=str, default="cover,hero,moment,solo")
    parser.add_argument("--ml-calibrate", action="store_true", help="Aligned pick uses G1 learned blend")
    parser.add_argument("--write", type=Path, default=None)
    args = parser.parse_args(argv)

    trip_dir = _resolve(args.trip_dir)
    trip = _load_json(trip_dir / "trip.json")
    assets = list(trip.get("assets") or [])
    labels_raw = _load_json(_resolve(args.labels))
    rows = labels_raw if isinstance(labels_raw, list) else list(labels_raw.get("rows") or [])

    purposes = tuple(p.strip() for p in args.purposes.split(",") if p.strip())  # type: ignore[assignment]
    app_cfg = AppConfig()
    rules_cfg = replace(app_cfg.aesthetic, ml_calibrate=False)
    aligned_cfg = replace(
        app_cfg.aesthetic,
        ml_calibrate=bool(args.ml_calibrate),
        source="rules+ml" if args.ml_calibrate else "rules",
    )

    automated = automated_purpose_win_report(
        assets,
        rows,
        rules_cfg=rules_cfg,
        aligned_cfg=aligned_cfg,
        purposes=purposes,  # type: ignore[arg-type]
    )
    out = export_purpose_blind_signoff(str(trip.get("tripId") or trip_dir.name), automated)

    text = json.dumps(out, indent=2, ensure_ascii=False)
    if args.write:
        path = _resolve(args.write)
        _save_json(path, out)
        print(path)
    else:
        print(text)
    return 0 if automated.get("passed") is not False else 1


if __name__ == "__main__":
    sys.exit(main())
