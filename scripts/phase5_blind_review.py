"""P5-8.1 · P-EVAL blind A/B package (legacy vs Phase 5 beam).

Generates two rendered variants, randomly labels A/B, writes reviewer landing page.

Usage:
  python scripts/phase5_blind_review.py mao
  python scripts/phase5_blind_review.py mao --seed 42
  python scripts/phase5_blind_review.py mao --objective-only
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.config import LayoutScoringConfig
from travelogue.curation.layout_metrics import compute_layout_metrics
from travelogue.curation.layout_scoring import PHASE3B_WEIGHTS, PHASE3_WEIGHTS
from travelogue.eval.peval import append_peval_pair, build_layout_peval_objective

from scripts.phase3_blind_review import (
    _render_variant,
    _utc_now,
    _write_eval_template,
    _write_trip_variant,
)
from scripts.phase3_layout_acceptance import (
    _has_color_metrics,
    _layout_snapshot,
    _run_curate,
    _weights_dict,
)

PEVAL_REVIEW_DIR = "_peval-review"


def _curate_peval_variants(trip_path: Path, *, layout: str = "web") -> tuple[dict, dict, dict]:
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    weights = PHASE3B_WEIGHTS if _has_color_metrics(trip) else PHASE3_WEIGHTS
    preset = "phase3b" if weights is PHASE3B_WEIGHTS else "phase3"
    scoring_off = LayoutScoringConfig(enabled=False)
    scoring_on = LayoutScoringConfig(
        enabled=True,
        beam_width=5,
        search_timeout_ms=5000,
        max_candidates_per_bucket=16,
        max_evaluations_per_trip=800,
        allow_burst_split=False,
        subject_run_tolerance=1,
        weights=_weights_dict(weights),
    )
    legacy = _run_curate(copy.deepcopy(trip), layout=layout, scoring=scoring_off, arc_mode="legacy")
    beam = _run_curate(
        copy.deepcopy(trip),
        layout=layout,
        scoring=scoring_on,
        arc_mode="v2_adaptive",
        trip_dir=trip_path.parent,
    )
    identical = _layout_snapshot(legacy.get("chapters") or []) == _layout_snapshot(
        beam.get("chapters") or []
    )
    legacy_metrics = compute_layout_metrics(legacy.get("chapters") or [])
    beam_metrics = compute_layout_metrics(beam.get("chapters") or [])
    objective = build_layout_peval_objective(
        legacy,
        beam,
        weights_preset=preset,
        identical=identical,
        legacy_metrics=legacy_metrics,
        beam_metrics=beam_metrics,
    )
    return legacy, beam, objective


def _write_peval_landing_page(
    review_dir: Path,
    *,
    trip_id: str,
    pages: dict[str, dict[str, str]],
    objective: dict,
) -> None:
    a = pages["A"]
    b = pages["B"]
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>{trip_id} · P5 排版盲评 A/B</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; }}
    h1 {{ font-size: 1.25rem; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
    .card {{ border: 1px solid #ccc; border-radius: 8px; padding: 1rem; }}
    .card h2 {{ margin-top: 0; }}
    a {{ display: block; margin: 0.35rem 0; }}
    .note {{ color: #666; font-size: 0.9rem; margin-top: 1.5rem; }}
    .obj {{ background: #f6f6f6; padding: 0.75rem; border-radius: 6px; font-size: 0.85rem; }}
  </style>
</head>
<body>
  <h1>{trip_id} · P5-8.1 排版盲评</h1>
  <p>对比 <strong>经典排版</strong> 与 <strong>P5 beam 实验</strong>。请先浏览 A、B，再填写
  <code>subjective_eval.json</code>。打分前勿查看 <code>key.json</code>。</p>
  <div class="grid">
    <div class="card">
      <h2>版本 A</h2>
      <a href="../{a['web']}" target="_blank">Web 屏读</a>
      <a href="../{a['longshot']}" target="_blank">长图预览</a>
      <a href="../{a['mobile']}" target="_blank">Mobile</a>
    </div>
    <div class="card">
      <h2>版本 B</h2>
      <a href="../{b['web']}" target="_blank">Web 屏读</a>
      <a href="../{b['longshot']}" target="_blank">长图预览</a>
      <a href="../{b['mobile']}" target="_blank">Mobile</a>
    </div>
  </div>
  <div class="note obj">
    <strong>客观对照（盲评时可忽略）</strong><br/>
    布局相同: {"是" if objective.get("identicalToLegacy") else "否"} ·
    beam 调整屏序: {objective.get("beamPickChanged", 0)} 段 ·
    屏数 legacy={objective.get("legacyScreens")} beam={objective.get("beamScreens")} ·
    preset={objective.get("weightsPreset")}
  </div>
  <p class="note">本地服务: <code>python -m travelogue serve trips/{trip_id}</code>
  → 打开 <code>/{PEVAL_REVIEW_DIR}/index.html</code></p>
</body>
</html>
"""
    (review_dir / "index.html").write_text(html, encoding="utf-8")


def prepare_peval_review(
    trip_path: Path,
    *,
    layout: str = "web",
    seed: int | None = None,
    render: bool = True,
) -> dict:
    trip_id = trip_path.parent.name
    trip_root = trip_path.parent
    review_dir = trip_root / PEVAL_REVIEW_DIR
    review_dir.mkdir(parents=True, exist_ok=True)

    legacy_trip, beam_trip, objective = _curate_peval_variants(trip_path, layout=layout)
    legacy_json = _write_trip_variant(trip_root, "legacy", legacy_trip)
    beam_json = _write_trip_variant(trip_root, "p5-beam", beam_trip)

    rng = random.Random(seed if seed is not None else secrets.randbelow(2**31))
    if rng.random() < 0.5:
        mapping = {"A": "legacy", "B": "p5-beam"}
    else:
        mapping = {"A": "p5-beam", "B": "legacy"}

    pages: dict[str, dict[str, str]] = {}
    if render:
        for label, variant in mapping.items():
            src = legacy_json if variant == "legacy" else beam_json
            pages[label] = _render_variant(src, trip_root, label=label)
    else:
        pages = {"A": {"web": "(not rendered)"}, "B": {"web": "(not rendered)"}}

    key = {
        "tripId": trip_id,
        "generatedAt": _utc_now(),
        "seed": seed,
        "mapping": mapping,
        "objective": objective,
    }
    (review_dir / "key.json").write_text(json.dumps(key, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if render:
        _write_peval_landing_page(review_dir, trip_id=trip_id, pages=pages, objective=objective)
        eval_rel = f"{PEVAL_REVIEW_DIR}/subjective_eval.template.json"
        _write_eval_template(review_dir, trip_id=trip_id)
    else:
        eval_rel = ""

    record = {
        "tripId": trip_id,
        "generatedAt": key["generatedAt"],
        "reviewDir": str(review_dir.relative_to(ROOT)).replace("\\", "/"),
        "mappingSealedIn": f"{PEVAL_REVIEW_DIR}/key.json",
        "evalTemplate": eval_rel,
        "rendered": render,
        "objective": objective,
        "preferred": None,
        "notes": "",
    }
    append_peval_pair(record)
    return {**record, "pages": pages}


def main() -> int:
    parser = argparse.ArgumentParser(description="P5-8.1 P-EVAL blind A/B review package")
    parser.add_argument("trip_ids", nargs="+")
    parser.add_argument("--layout", default="web")
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--objective-only",
        action="store_true",
        help="curate + record objective metrics without rendering HTML",
    )
    args = parser.parse_args()

    for tid in args.trip_ids:
        path = args.trips_dir / tid / "trip.json"
        if not path.is_file():
            print(f"SKIP {tid}")
            continue
        print(f"P-EVAL {tid} ...", flush=True)
        result = prepare_peval_review(
            path,
            layout=args.layout,
            seed=args.seed,
            render=not args.objective_only,
        )
        obj = result["objective"]
        tag = "SAME" if obj.get("identicalToLegacy") else "DIFF"
        print(
            f"  {tag}  beamChanged={obj.get('beamPickChanged')}  "
            f"screens={obj.get('legacyScreens')}  landing={result['reviewDir']}/index.html"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
