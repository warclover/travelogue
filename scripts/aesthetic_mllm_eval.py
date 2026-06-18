"""AA · M3 MLLM aesthetic SRCC eval (shortlist + optional full corpus).

Usage:
  python scripts/aesthetic_mllm_eval.py --trip-dir trips/demo-2025-6 --labels docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json --dry-run
  python scripts/aesthetic_mllm_eval.py --trip-dir trips/demo-2025-6 --labels ... --provider dashscope --write docs/acceptance-records/aesthetic-m3-eval.demo-2025-6.json
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.env import load_dotenv_files  # noqa: E402

load_dotenv_files()

from travelogue.config import AppConfig  # noqa: E402
from travelogue.curation.aesthetic_learned_eval import (  # noqa: E402
    build_eval_rows,
    srcc_comparison,
)
from travelogue.curation.aesthetic_score import (  # noqa: E402
    apply_aesthetic_ml_calibration,
    refresh_portrait_lite_overall,
)
from travelogue.vision.aesthetic_mllm import (  # noqa: E402
    apply_aesthetic_mllm_scores,
    apply_mllm_oracle_from_labels,
    build_mllm_shortlist,
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def run_mllm_eval(
    *,
    trip_dir: Path,
    label_rows: list[dict[str, Any]],
    provider: str = "dashscope",
    blend: float = 0.38,
    dry_run: bool = False,
    oracle_stub: bool = False,
    use_stratum_blend: bool = False,
    stratum_blends: dict[str, float] | None = None,
    portrait_lite: bool = True,
) -> dict[str, Any]:
    from travelogue.config import DEFAULT_STRATUM_BLENDS

    trip = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    assets = list(trip.get("assets") or [])
    assets_by_id = {str(a["id"]): copy.deepcopy(a) for a in assets if a.get("id")}

    app_cfg = AppConfig()
    blends = dict(DEFAULT_STRATUM_BLENDS)
    if stratum_blends:
        blends.update(stratum_blends)
    ae_cfg = replace(
        app_cfg.aesthetic,
        ml_calibrate=True,
        ml_calibrate_blend=blend,
        source="rules+ml",
        use_stratum_blend=use_stratum_blend,
        stratum_blends=blends,
        portrait_lite_enabled=portrait_lite,
        mllm=replace(
            app_cfg.aesthetic.mllm,
            enabled=True,
            provider=provider,
        ),
    )
    app_cfg = replace(app_cfg, aesthetic=ae_cfg)

    apply_aesthetic_ml_calibration(list(assets_by_id.values()), trip_dir=trip_dir, cfg=app_cfg)
    if portrait_lite:
        for asset in assets_by_id.values():
            refresh_portrait_lite_overall(asset, cfg=ae_cfg)
    shortlist = build_mllm_shortlist(list(assets_by_id.values()), cfg=ae_cfg)
    mllm_report: dict[str, Any] = {"dryRun": dry_run, "shortlistCount": len(shortlist), "shortlist": []}
    for aid, _asset, purpose in shortlist:
        mllm_report["shortlist"].append({"assetId": aid, "purpose": purpose})

    if dry_run:
        return {
            "tripDir": str(trip_dir),
            "useStratumBlend": use_stratum_blend,
            "portraitLite": portrait_lite,
            "mllm": mllm_report,
            "note": "dry-run: shortlist only, no API calls",
        }

    if oracle_stub:
        mllm_report.update(
            apply_mllm_oracle_from_labels(
                list(assets_by_id.values()),
                label_rows,
                cfg=ae_cfg,
            )
        )
    else:
        mllm_report.update(
            apply_aesthetic_mllm_scores(list(assets_by_id.values()), trip_dir=trip_dir, cfg=ae_cfg)
        )
    eval_rows = build_eval_rows(assets_by_id, label_rows, cfg=ae_cfg)
    comparison = srcc_comparison(eval_rows)
    return {
        "tripDir": str(trip_dir),
        "blend": blend,
        "provider": provider if not oracle_stub else "oracle-human",
        "useStratumBlend": use_stratum_blend,
        "stratumBlends": blends if use_stratum_blend else None,
        "portraitLite": portrait_lite,
        "mllm": mllm_report,
        "evalRows": len(eval_rows),
        "comparison": comparison,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AA M3 · MLLM aesthetic eval")
    parser.add_argument("--trip-dir", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--provider", type=str, default="dashscope")
    parser.add_argument("--blend", type=float, default=0.38)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--oracle-stub",
        action="store_true",
        help="Inject human labels as mllmScore on shortlist (offline upper bound)",
    )
    parser.add_argument("--use-stratum-blend", action="store_true")
    parser.add_argument("--stratum-blends", type=Path, default=None)
    parser.add_argument("--no-portrait-lite", action="store_true")
    parser.add_argument("--write", type=Path, default=None)
    args = parser.parse_args(argv)

    labels_raw = _load_json(_resolve(args.labels))
    rows = labels_raw if isinstance(labels_raw, list) else list(labels_raw.get("rows") or [])

    stratum_blends = None
    if args.stratum_blends:
        raw = _load_json(_resolve(args.stratum_blends))
        if isinstance(raw, dict):
            stratum_blends = raw.get("recommendedBlends") or raw.get("stratumCalibration", {}).get(
                "recommendedBlends"
            )

    out = run_mllm_eval(
        trip_dir=_resolve(args.trip_dir),
        label_rows=rows,
        provider=str(args.provider),
        blend=float(args.blend),
        dry_run=bool(args.dry_run),
        oracle_stub=bool(args.oracle_stub),
        use_stratum_blend=bool(args.use_stratum_blend),
        stratum_blends=stratum_blends if isinstance(stratum_blends, dict) else None,
        portrait_lite=not args.no_portrait_lite,
    )

    if args.write:
        path = _resolve(args.write)
        _save_json(path, out)
        print(path)
    else:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
