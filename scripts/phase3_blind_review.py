"""Prepare blind A/B review package for Phase-3 layout (I-G4).

Generates two rendered variants (legacy vs v2_adaptive+phase3b), randomly
labels them A/B, and writes a reviewer landing page + score template.

Usage:
  python scripts/phase3_blind_review.py mao
  python scripts/phase3_blind_review.py mao --seed 42
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import secrets
import shutil
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.config import LayoutScoringConfig
from travelogue.curation.layout_metrics import compute_layout_metrics
from travelogue.curation.layout_scoring import PHASE3B_WEIGHTS, PHASE3_WEIGHTS
from travelogue.render.engine import (
    LONGSHOT_INDEX_NAME,
    render_trip_surfaces,
    write_longshot_sidecar,
)
from travelogue.services.trip import TripService
from scripts.phase3_layout_acceptance import (
    _has_color_metrics,
    _layout_snapshot,
    _run_curate,
    _weights_dict,
)

REVIEW_DIR_NAME = "_blind-review"
_PROTECTED_INDEX = ("index.html", "index-mobile.html", LONGSHOT_INDEX_NAME)


def _backup_index_files(trip_root: Path) -> dict[str, bytes | None]:
    out: dict[str, bytes | None] = {}
    for name in _PROTECTED_INDEX:
        path = trip_root / name
        out[name] = path.read_bytes() if path.is_file() else None
    return out


def _restore_index_files(trip_root: Path, backup: dict[str, bytes | None]) -> None:
    for name, data in backup.items():
        path = trip_root / name
        if data is None:
            if path.is_file():
                path.unlink()
        else:
            path.write_bytes(data)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _curate_variants(trip_path: Path, *, layout: str = "web") -> tuple[dict, dict, dict]:
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    weights = PHASE3B_WEIGHTS if _has_color_metrics(trip) else PHASE3_WEIGHTS
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
    phase3 = _run_curate(
        copy.deepcopy(trip),
        layout=layout,
        scoring=scoring_on,
        arc_mode="v2_adaptive",
        trip_dir=trip_path.parent,
    )
    meta = {
        "weightsPreset": "phase3b" if weights is PHASE3B_WEIGHTS else "phase3",
        "identicalToLegacy": _layout_snapshot(legacy.get("chapters") or [])
        == _layout_snapshot(phase3.get("chapters") or []),
        "legacyMetrics": compute_layout_metrics(legacy.get("chapters") or []),
        "phase3Metrics": compute_layout_metrics(phase3.get("chapters") or []),
        "arcProfile": (phase3.get("curation") or {}).get("arcProfile"),
    }
    return legacy, phase3, meta


def _write_trip_variant(trip_root: Path, name: str, trip: dict) -> Path:
    path = trip_root / f".ab-{name}.json"
    path.write_text(json.dumps(trip, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _render_variant(trip_json: Path, trip_root: Path, *, label: str) -> dict[str, str]:
    web_name = f"index-blind-{label.lower()}.html"
    mobile_name = f"index-blind-{label.lower()}-mobile.html"
    longshot_name = f"index-blind-{label.lower()}-longshot.html"
    backup = _backup_index_files(trip_root)
    try:
        render_trip_surfaces(trip_json, trip_root, export_mode="draft", validate=True)
        trip = TripService().load(trip_json)
        write_longshot_sidecar(trip, trip_root, export_mode="draft", trip_root=trip_root)
        for src_name, dst_name in (
            ("index.html", web_name),
            ("index-mobile.html", mobile_name),
            (LONGSHOT_INDEX_NAME, longshot_name),
        ):
            src = trip_root / src_name
            if src.is_file():
                shutil.copy2(src, trip_root / dst_name)
    finally:
        _restore_index_files(trip_root, backup)
    return {
        "web": web_name,
        "mobile": mobile_name,
        "longshot": longshot_name if (trip_root / longshot_name).is_file() else "",
    }


def _write_landing_page(
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
  <title>{trip_id} · 排版盲评 A/B</title>
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
  <h1>{trip_id} · 排版盲评（I-G4）</h1>
  <p>请先浏览 A、B 两版，再填写 <code>subjective_eval.json</code>。勿查看 <code>key.json</code> 直至打分完成。</p>
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
    <strong>客观对照（供记录，盲评时可忽略）</strong><br/>
    布局签名相同: {"是" if objective.get("identicalToLegacy") else "否"} ·
    屏数 legacy={objective.get("legacyScreens")} phase3={objective.get("phase3Screens")} ·
    preset={objective.get("weightsPreset")}
  </div>
  <p class="note">本地服务: <code>python -m travelogue serve trips/{trip_id}</code>
  → 打开 <code>/_blind-review/index.html</code></p>
</body>
</html>
"""
    (review_dir / "index.html").write_text(html, encoding="utf-8")


def _write_eval_template(review_dir: Path, *, trip_id: str) -> Path:
    template = {
        "tripId": trip_id,
        "evalVersion": "1.0",
        "createdAt": _utc_now(),
        "reviewers": [
            {
                "reviewerId": "reviewer-1",
                "scores": {
                    "A": {"rhythm": None, "coherence": None, "comfort": None, "wouldShare": None},
                    "B": {"rhythm": None, "coherence": None, "comfort": None, "wouldShare": None},
                },
                "preferred": None,
                "notes": "",
            }
        ],
        "instructions": {
            "rhythm": "1-5 首章节奏 / 密度变化",
            "coherence": "1-5 横竖混排 / 色调连贯",
            "comfort": "1-5 整体观感舒适",
            "wouldShare": "yes / no / maybe",
            "preferred": "A / B / tie",
        },
    }
    path = review_dir / "subjective_eval.template.json"
    path.write_text(json.dumps(template, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def prepare_blind_review(
    trip_path: Path,
    *,
    layout: str = "web",
    seed: int | None = None,
) -> dict:
    trip_id = trip_path.parent.name
    trip_root = trip_path.parent
    review_dir = trip_root / REVIEW_DIR_NAME
    review_dir.mkdir(parents=True, exist_ok=True)

    legacy_trip, phase3_trip, meta = _curate_variants(trip_path, layout=layout)
    legacy_json = _write_trip_variant(trip_root, "legacy", legacy_trip)
    phase3_json = _write_trip_variant(trip_root, "phase3", phase3_trip)

    rng = random.Random(seed if seed is not None else secrets.randbelow(2**31))
    if rng.random() < 0.5:
        mapping = {"A": "legacy", "B": "phase3"}
    else:
        mapping = {"A": "phase3", "B": "legacy"}

    pages: dict[str, dict[str, str]] = {}
    for label, variant in mapping.items():
        src = legacy_json if variant == "legacy" else phase3_json
        pages[label] = _render_variant(src, trip_root, label=label)

    key = {
        "tripId": trip_id,
        "generatedAt": _utc_now(),
        "seed": seed,
        "mapping": mapping,
        "objective": {
            **meta,
            "legacyScreens": meta["legacyMetrics"].get("screenCount"),
            "phase3Screens": meta["phase3Metrics"].get("screenCount"),
        },
    }
    (review_dir / "key.json").write_text(json.dumps(key, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    objective = key["objective"]
    _write_landing_page(review_dir, trip_id=trip_id, pages=pages, objective=objective)
    eval_path = _write_eval_template(review_dir, trip_id=trip_id)

    record = {
        "tripId": trip_id,
        "reviewDir": str(review_dir.relative_to(ROOT)).replace("\\", "/"),
        "mappingSealedIn": f"{REVIEW_DIR_NAME}/key.json",
        "evalTemplate": f"{REVIEW_DIR_NAME}/subjective_eval.template.json",
        "pages": pages,
        "objective": objective,
    }
    out = ROOT / "docs" / "acceptance-records" / "phase3-blind-review.json"
    existing: list[dict] = []
    if out.is_file():
        existing = json.loads(out.read_text(encoding="utf-8"))
    existing = [r for r in existing if r.get("tripId") != trip_id]
    existing.append({k: v for k, v in record.items() if k != "pages"})
    out.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase-3 blind A/B review package")
    parser.add_argument("trip_ids", nargs="+")
    parser.add_argument("--layout", default="web")
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    parser.add_argument("--seed", type=int, default=None, help="Fix A/B assignment for reproducibility")
    args = parser.parse_args()

    for tid in args.trip_ids:
        path = args.trips_dir / tid / "trip.json"
        if not path.is_file():
            print(f"SKIP {tid}")
            continue
        print(f"Blind review {tid} ...", flush=True)
        r = prepare_blind_review(path, layout=args.layout, seed=args.seed)
        obj = r["objective"]
        tag = "SAME" if obj.get("identicalToLegacy") else "DIFF"
        print(f"  {tag}  screens={obj.get('legacyScreens')}  landing={r['reviewDir']}/index.html")
        print(f"  eval template: {r['evalTemplate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
