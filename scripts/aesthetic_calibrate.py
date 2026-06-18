"""AA · M2 blend grid-search calibration vs human labels.

Usage:
  python scripts/aesthetic_calibrate.py --trip-dir trips/demo-2025-6 --labels docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json
  python scripts/aesthetic_calibrate.py --trip-dir trips/demo-2025-6 --labels ... --metric nima --blend-max 0.6 --blend-step 0.05 --write docs/acceptance-records/aesthetic-m2-calibrate.demo-2025-6.json
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

from travelogue.curation.aesthetic_learned_eval import (  # noqa: E402
    run_blend_calibration,
    run_stratum_blend_calibration,
)
from travelogue.curation.photo_cull_ml import pyiqa_available  # noqa: E402


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def _print_stratum_summary(out: dict[str, Any]) -> None:
    cal = out.get("stratumCalibration") or {}
    base = out.get("rulesBaseline") or {}
    full = cal.get("fullCorpus") or {}
    uniform = cal.get("uniformBlend") or {}
    print("=== M2 stratum blend calibration ===")
    print(f"metric: {out.get('metric')}")
    print(f"rules baseline SRCC: {base.get('srcc')} (n={base.get('sampleCount')})")
    print(f"uniform blend SRCC: {uniform.get('srcc')}")
    print(f"stratum blend SRCC: {full.get('srcc')} delta={cal.get('deltaVsUniform')}")
    for stratum, block in (cal.get("strata") or {}).items():
        if block.get("skipped"):
            print(f"  [{stratum}] skipped n={block.get('sampleCount')} ({block.get('reason')})")
        else:
            print(
                f"  [{stratum}] best blend={block.get('bestBlend')} "
                f"SRCC={block.get('bestSrcc')} n={block.get('sampleCount')}"
            )
    print(f"recommended blends: {json.dumps(cal.get('recommendedBlends') or {}, ensure_ascii=False)}")


def _print_summary(out: dict[str, Any]) -> None:
    cal = out.get("calibration") or {}
    base = out.get("rulesBaseline") or {}
    rec = cal.get("recommended") or {}
    print("=== M2 blend calibration ===")
    print(f"metric: {out.get('metric')}")
    print(f"rules baseline SRCC: {base.get('srcc')} (n={base.get('sampleCount')})")
    print(f"learned-only SRCC: {(cal.get('learnedOnly') or {}).get('srcc')}")
    print(f"recommended blend: {rec.get('blend')} -> SRCC {rec.get('srcc')}")
    for purpose, block in (cal.get("purposes") or {}).items():
        print(
            f"  [{purpose}] best blend={block.get('bestBlend')} "
            f"SRCC={block.get('bestSrcc')} delta={block.get('deltaVsBaseline')}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AA M2 · blend grid-search calibration")
    parser.add_argument("--trip-dir", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--metric", type=str, default="nima")
    parser.add_argument("--blend-min", type=float, default=0.0)
    parser.add_argument("--blend-max", type=float, default=0.6)
    parser.add_argument("--blend-step", type=float, default=0.05)
    parser.add_argument("--no-cpu", action="store_true")
    parser.add_argument("--by-stratum", action="store_true", help="Per-stratum blend grid search")
    parser.add_argument("--write", type=Path, default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    if not pyiqa_available():
        print('E_AA_M2: pyiqa not installed. Run: pip install -e ".[cull-ml]"', file=sys.stderr)
        return 2

    labels_raw = _load_json(_resolve(args.labels))
    rows = labels_raw if isinstance(labels_raw, list) else list(labels_raw.get("rows") or [])

    if args.by_stratum:
        out = run_stratum_blend_calibration(
            trip_dir=_resolve(args.trip_dir),
            label_rows=rows,
            metric=str(args.metric),
            allow_cpu=not args.no_cpu,
            blend_min=float(args.blend_min),
            blend_max=float(args.blend_max),
            blend_step=float(args.blend_step),
        )
        print_summary = _print_stratum_summary
    else:
        out = run_blend_calibration(
            trip_dir=_resolve(args.trip_dir),
            label_rows=rows,
            metric=str(args.metric),
            allow_cpu=not args.no_cpu,
            blend_min=float(args.blend_min),
            blend_max=float(args.blend_max),
            blend_step=float(args.blend_step),
        )
        print_summary = _print_summary

    if args.write:
        path = _resolve(args.write)
        _save_json(path, out)
        print(path)
    if not args.quiet:
        if args.write:
            print()
        print_summary(out)
        if not args.write:
            print()
            print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
