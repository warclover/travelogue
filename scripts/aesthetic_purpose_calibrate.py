"""AA · GAP-04 · purpose preset weight grid search.

Usage:
  python scripts/aesthetic_purpose_calibrate.py --trip-dir trips/demo-2025-6 --labels docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json
  python scripts/aesthetic_purpose_calibrate.py --trip-dir trips/demo-2025-6 --labels ... --write docs/acceptance-records/aesthetic-purpose-cal.demo-2025-6.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.env import load_dotenv_files  # noqa: E402

load_dotenv_files()

from travelogue.curation.aesthetic_purpose_calibrate import (
    run_purpose_weight_calibration,  # noqa: E402
)
from travelogue.curation.photo_cull_ml import pyiqa_available  # noqa: E402


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AA GAP-04 · purpose weight grid search")
    parser.add_argument("--trip-dir", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--metric", type=str, default="nima")
    parser.add_argument("--no-cpu", action="store_true")
    parser.add_argument("--emphasis-min", type=float, default=0.10)
    parser.add_argument("--emphasis-max", type=float, default=0.40)
    parser.add_argument("--emphasis-step", type=float, default=0.05)
    parser.add_argument("--write", type=Path, default=None)
    args = parser.parse_args(argv)

    if not pyiqa_available():
        print('E_AA_PURPOSE: pyiqa not installed. Run: pip install -e ".[cull-ml]"', file=sys.stderr)
        return 2

    labels_raw = _load_json(_resolve(args.labels))
    rows = labels_raw if isinstance(labels_raw, list) else list(labels_raw.get("rows") or [])

    out = run_purpose_weight_calibration(
        trip_dir=_resolve(args.trip_dir),
        label_rows=rows,
        metric=str(args.metric),
        allow_cpu=not args.no_cpu,
        emphasis_min=float(args.emphasis_min),
        emphasis_max=float(args.emphasis_max),
        emphasis_step=float(args.emphasis_step),
    )

    text = json.dumps(out, indent=2, ensure_ascii=False)
    if args.write:
        path = _resolve(args.write)
        _save_json(path, out)
        print(path)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
