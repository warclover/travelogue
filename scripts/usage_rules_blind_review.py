#!/usr/bin/env python3
"""AC-URO-BLIND · usage_rules on vs off blind review helper.

Usage:
  python scripts/usage_rules_blind_review.py --init-template
  python scripts/usage_rules_blind_review.py --export demo-2019 chuanzang-studio
  python scripts/usage_rules_blind_review.py --export --golden
  python scripts/usage_rules_blind_review.py --score docs/acceptance-records/usage-rules-blind-review.json
  python scripts/usage_rules_blind_review.py --score review.json --strict
"""

from __future__ import annotations

import argparse
import json
import random
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEMPLATE = ROOT / "docs" / "acceptance-records" / "usage-rules-blind-review.template.json"
EXPORT_MANIFEST = ROOT / "docs" / "acceptance-records" / "usage-rules-blind-export.json"
REVIEW_DIR_NAME = "_uro-blind-review"
AC_URO_BLIND_THRESHOLD = 0.55
STUDIO_VETO_TRIPS = frozenset({"linzhi", "chuanzang-studio"})


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def init_template() -> dict:
    from travelogue.curation.usage_rules.metrics import URO_GOLDEN_TRIP_IDS

    return {
        "schemaVersion": "1",
        "reviewId": "usage-rules-blind-review",
        "feature": "URO",
        "gate": "AC-URO-BLIND",
        "blindThreshold": AC_URO_BLIND_THRESHOLD,
        "reviewer": None,
        "reviewedAt": None,
        "tripPairs": [
            {
                "tripId": tid,
                "presentedOrder": "randomized",
                "preference": None,
                "dimensions": {
                    "layoutMatch": None,
                    "breathRhythm": None,
                    "heroClarity": None,
                },
                "studioVeto": tid in STUDIO_VETO_TRIPS,
                "exportPath": None,
                "notes": "preference=on|off|tie after blind A/B (usage_rules on vs off)",
            }
            for tid in URO_GOLDEN_TRIP_IDS
        ],
        "aggregate": {
            "onPreferredRate": None,
            "passesBlindGate": None,
        },
        "notes": (
            "Complete preference after human blind review; "
            f"aggregate onPreferredRate ≥ {AC_URO_BLIND_THRESHOLD} required for enabled=true merge."
        ),
    }


def score_review(doc: dict) -> dict:
    pairs = doc.get("tripPairs") or []
    scored = 0
    on_wins = 0
    ties = 0
    studio_losses: list[str] = []
    per_trip: list[dict] = []

    for pair in pairs:
        tid = str(pair.get("tripId") or "")
        pref = pair.get("preference")
        row = {"tripId": tid, "preference": pref, "studioVeto": pair.get("studioVeto")}
        if pref is None:
            per_trip.append(row)
            continue
        scored += 1
        p = str(pref).strip().lower()
        if p in ("on", "usage_on", "b", "candidate", "treatment"):
            on_wins += 1
        elif p in ("tie", "same", "draw"):
            ties += 1
        if pair.get("studioVeto") and p in ("off", "baseline", "a", "control"):
            studio_losses.append(tid)
        per_trip.append(row)

    rate = (on_wins / scored) if scored else None
    passes = rate is not None and rate >= AC_URO_BLIND_THRESHOLD and not studio_losses
    return {
        "pairCount": len(pairs),
        "scoredPairs": scored,
        "onPreferred": on_wins,
        "ties": ties,
        "onPreferredRate": round(rate, 4) if rate is not None else None,
        "passesAcUroBlind": passes,
        "studioVetoLosses": studio_losses,
        "perTrip": per_trip,
    }


def _write_trip_variant(trip_root: Path, name: str, trip: dict) -> Path:
    path = trip_root / f".uro-ab-{name}.json"
    path.write_text(json.dumps(trip, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _render_uro_variant(trip_json: Path, trip_root: Path, *, label: str) -> dict[str, str]:
    """Render A/B variant HTML (draft · schema-strict off for curate-only fields)."""
    import shutil

    from scripts.phase3_blind_review import _backup_index_files, _restore_index_files
    from travelogue.render.engine import LONGSHOT_INDEX_NAME, render_trip_surfaces, write_longshot_sidecar
    from travelogue.services.trip import TripService

    tag = label.lower()
    web_name = f"index-uro-blind-{tag}.html"
    mobile_name = f"index-uro-blind-{tag}-mobile.html"
    longshot_name = f"index-uro-blind-{tag}-longshot.html"
    backup = _backup_index_files(trip_root)
    try:
        render_trip_surfaces(trip_json, trip_root, export_mode="draft", validate=False)
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
    objective: dict[str, Any],
) -> None:
    a = pages["A"]
    b = pages["B"]
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>{trip_id} · URO 盲评 A/B</title>
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
  <h1>{trip_id} · AC-URO-BLIND（usage_rules off vs on）</h1>
  <p>请先浏览 A、B 两版整书排版，再在盲评 JSON 中填写 <code>preference</code>（on/off/tie）。
  勿查看 <code>key.json</code> 直至打分完成。</p>
  <div class="grid">
    <div class="card">
      <h2>版本 A</h2>
      <a href="../{a['web']}" target="_blank">Web 屏读</a>
      <a href="../{a.get('longshot') or '#'}" target="_blank">长图预览</a>
      <a href="../{a['mobile']}" target="_blank">Mobile</a>
    </div>
    <div class="card">
      <h2>版本 B</h2>
      <a href="../{b['web']}" target="_blank">Web 屏读</a>
      <a href="../{b.get('longshot') or '#'}" target="_blank">长图预览</a>
      <a href="../{b['mobile']}" target="_blank">Mobile</a>
    </div>
  </div>
  <div class="note obj">
    <strong>客观对照（盲评时可忽略）</strong><br/>
    布局签名相同: {"是" if objective.get("layoutSnapshotEqual") else "否"} ·
    屏数 off={objective.get("offScreens")} on={objective.get("onScreens")} ·
    usageRuleRejectCount={objective.get("usageRuleRejectCount")}
  </div>
  <p class="note">本地服务: <code>python -m travelogue serve trips/{trip_id}</code>
  → 打开 <code>/{REVIEW_DIR_NAME}/index.html</code></p>
</body>
</html>
"""
    (review_dir / "index.html").write_text(html, encoding="utf-8")


def _write_preference_template(review_dir: Path, *, trip_id: str) -> Path:
    template = {
        "tripId": trip_id,
        "gate": "AC-URO-BLIND",
        "createdAt": _utc_now(),
        "preference": None,
        "dimensions": {
            "layoutMatch": None,
            "breathRhythm": None,
            "heroClarity": None,
        },
        "notes": "",
        "instructions": {
            "preference": "on | off | tie — 映射关系密封在 key.json，填完后对照 key 写入主盲评 JSON",
            "layoutMatch": "1-5 内容与版式匹配度",
            "breathRhythm": "1-5 呼吸/密度节奏",
            "heroClarity": "1-5 主图/视觉焦点清晰度",
        },
    }
    path = review_dir / "preference.template.json"
    path.write_text(json.dumps(template, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def prepare_blind_export(
    trip_path: Path,
    *,
    work_dir: Path,
    seed: int | None = None,
    render: bool = True,
) -> dict[str, Any]:
    from scripts.usage_rules_eval_common import ensure_trip_screen_ids, run_variant

    trip_id = trip_path.parent.name
    trip_root = trip_path.parent
    review_dir = trip_root / REVIEW_DIR_NAME
    review_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    source_trip = json.loads(trip_path.read_text(encoding="utf-8"))
    off = run_variant(source_trip, usage_enabled=False, work_dir=work_dir / "off", return_trip=True)
    on = run_variant(source_trip, usage_enabled=True, work_dir=work_dir / "on", return_trip=True)
    ensure_trip_screen_ids(off["trip"])
    ensure_trip_screen_ids(on["trip"])
    off_json = _write_trip_variant(trip_root, "off", off["trip"])
    on_json = _write_trip_variant(trip_root, "on", on["trip"])

    rng = random.Random(seed if seed is not None else secrets.randbelow(2**31))
    if rng.random() < 0.5:
        mapping = {"A": "off", "B": "on"}
    else:
        mapping = {"A": "on", "B": "off"}

    pages: dict[str, dict[str, str]] = {}
    if render:
        for label, variant in mapping.items():
            src = off_json if variant == "off" else on_json
            pages[label] = _render_uro_variant(src, trip_root, label=label)
    else:
        for label in ("A", "B"):
            pages[label] = {"web": "", "mobile": "", "longshot": ""}

    objective = {
        "layoutSnapshotEqual": off["layoutSnapshot"] == on["layoutSnapshot"],
        "offScreens": off["metrics"].get("screenCount"),
        "onScreens": on["metrics"].get("screenCount"),
        "usageRuleRejectCount": on["usageRuleRejectCount"],
        "offHeroMismatchRate": off["metrics"].get("heroMismatchRate"),
        "onHeroMismatchRate": on["metrics"].get("heroMismatchRate"),
    }
    key = {
        "tripId": trip_id,
        "generatedAt": _utc_now(),
        "seed": seed,
        "mapping": mapping,
        "variants": {"off": "usage_rules.enabled=false", "on": "usage_rules.enabled=true"},
        "objective": objective,
    }
    (review_dir / "key.json").write_text(
        json.dumps(key, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if render:
        _write_landing_page(review_dir, trip_id=trip_id, pages=pages, objective=objective)
    _write_preference_template(review_dir, trip_id=trip_id)

    rel_review = str(review_dir.relative_to(ROOT)).replace("\\", "/")
    record = {
        "tripId": trip_id,
        "reviewDir": rel_review,
        "mappingSealedIn": f"{REVIEW_DIR_NAME}/key.json",
        "preferenceTemplate": f"{REVIEW_DIR_NAME}/preference.template.json",
        "rendered": render,
        "objective": objective,
    }
    return record


def _update_export_manifest(record: dict[str, Any]) -> None:
    existing: list[dict] = []
    if EXPORT_MANIFEST.is_file():
        existing = json.loads(EXPORT_MANIFEST.read_text(encoding="utf-8"))
    existing = [r for r in existing if r.get("tripId") != record.get("tripId")]
    existing.append(record)
    EXPORT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    EXPORT_MANIFEST.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="AC-URO-BLIND blind review helper")
    parser.add_argument("--init-template", action="store_true", help="Write template JSON")
    parser.add_argument("--export", action="store_true", help="Export off/on A/B render package")
    parser.add_argument("trip_ids", nargs="*", help="Trip ids (trips/{id}/trip.json)")
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    parser.add_argument(
        "--golden",
        action="store_true",
        help="Export all URO_GOLDEN_TRIP_IDS present under trips/",
    )
    parser.add_argument(
        "--no-render",
        action="store_true",
        help="Curate off/on only; skip HTML render (for CI / missing assets)",
    )
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".cache" / "usage-rules-blind")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--out", type=Path, default=TEMPLATE)
    parser.add_argument("review", type=Path, nargs="?", help="Completed blind review JSON")
    parser.add_argument(
        "--score",
        action="store_true",
        help="Score review file (default if path given)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=f"Exit 1 when onPreferredRate < {AC_URO_BLIND_THRESHOLD}",
    )
    args = parser.parse_args()

    if args.init_template:
        doc = init_template()
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {args.out}")
        return 0

    if args.export:
        from travelogue.curation.usage_rules.metrics import URO_GOLDEN_TRIP_IDS

        trip_ids = list(args.trip_ids)
        if args.golden and not trip_ids:
            trip_ids = list(URO_GOLDEN_TRIP_IDS)
        if not trip_ids:
            parser.error("Provide trip_ids or --golden with --export")

        exported = 0
        for tid in trip_ids:
            path = args.trips_dir / tid / "trip.json"
            if not path.is_file():
                print(f"SKIP {tid} (no trips/{tid}/trip.json)", flush=True)
                continue
            print(f"URO blind export {tid} ...", flush=True)
            record = prepare_blind_export(
                path,
                work_dir=args.work_dir / tid,
                seed=args.seed,
                render=not args.no_render,
            )
            _update_export_manifest(record)
            exported += 1
            obj = record["objective"]
            tag = "SAME" if obj.get("layoutSnapshotEqual") else "DIFF"
            print(
                f"  {tag}  ur_rejects={obj.get('usageRuleRejectCount')}  "
                f"landing={record['reviewDir']}/index.html",
                flush=True,
            )
        if exported == 0:
            print("No trips exported.", file=sys.stderr)
            return 1
        print(f"\nWrote manifest {EXPORT_MANIFEST}")
        return 0

    review_path = args.review
    if review_path and review_path.is_file():
        doc = json.loads(review_path.read_text(encoding="utf-8"))
    elif TEMPLATE.is_file():
        doc = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        review_path = TEMPLATE
    else:
        print(json.dumps({"error": "no review file"}, ensure_ascii=False))
        return 1

    result = score_review(doc)
    payload = {
        "template": str(TEMPLATE.relative_to(ROOT)),
        "reviewFile": str(review_path) if review_path else None,
        "threshold": AC_URO_BLIND_THRESHOLD,
        **result,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.strict and not result.get("passesAcUroBlind"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
