"""PA · SRCC + blind-review export (design §8 acceptance).

Usage:
  python scripts/pa_aesthetic_acceptance.py --init-labels docs/acceptance-records/pa-human-labels.example.json
  python scripts/pa_aesthetic_acceptance.py --srcc docs/acceptance-records/pa-human-labels.example.json
  python scripts/pa_aesthetic_acceptance.py --trip-dir trips/demo-album --write out.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def init_labels_template(path: Path) -> dict:
    data = {
        "version": "1",
        "notes": "humanScore ∈ [0,1] or 1–10 (normalized in script); predictedOverall from quality.aesthetic.overall",
        "rows": [
            {"assetId": "asset-001", "humanScore": 0.8, "predictedOverall": 0.71},
            {"assetId": "asset-002", "humanScore": 0.5, "predictedOverall": 0.55},
            {"assetId": "asset-003", "humanScore": 0.9, "predictedOverall": 0.62},
        ],
    }
    _save_json(path, data)
    return data


def cmd_srcc(path: Path) -> dict:
    from travelogue.curation.pa_acceptance import srcc_from_label_rows

    raw = _load_json(path)
    rows = raw if isinstance(raw, list) else list(raw.get("rows") or [])
    for row in rows:
        if "humanScore" in row:
            try:
                hs = float(row["humanScore"])
                if hs > 1.0:
                    row["humanScore"] = hs / 10.0
            except (TypeError, ValueError):
                pass
    return srcc_from_label_rows(rows)


def cmd_export(trip_dir: Path, *, export_layout: str) -> dict:
    from travelogue.curation.pa_acceptance import export_pa_blind_review

    trip_path = trip_dir / "trip.json"
    trip = _load_json(trip_path)
    assets = list(trip.get("assets") or [])
    return export_pa_blind_review(assets, export_layout=export_layout)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PA aesthetic acceptance (SRCC + blind export)")
    parser.add_argument("--init-labels", type=Path, metavar="PATH")
    parser.add_argument("--srcc", type=Path, metavar="LABELS_JSON")
    parser.add_argument("--trip-dir", type=Path, default=None)
    parser.add_argument("--export-layout", type=str, default="mobile")
    parser.add_argument("--write", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.init_labels:
        init_labels_template(args.init_labels)
        print(args.init_labels)
        return 0

    out: dict | None = None
    if args.srcc:
        out = {"source": str(args.srcc), **cmd_srcc(args.srcc)}
    elif args.trip_dir:
        out = cmd_export(args.trip_dir.resolve(), export_layout=args.export_layout)
    else:
        parser.error("Provide --srcc LABELS_JSON or --trip-dir")
        return 2

    text = json.dumps(out, indent=2, ensure_ascii=False)
    if args.write:
        _save_json(args.write, out)
        print(args.write)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
