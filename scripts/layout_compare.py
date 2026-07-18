#!/usr/bin/env python3
"""TPC W4 · Compare curate: template_contract off vs on (AC-TPC-08).

Usage:
  python scripts/layout_compare.py linzhi
  python scripts/layout_compare.py --trip-dir trips/linzhi
  python scripts/layout_compare.py --recent 3
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
sys.path.insert(0, str(ROOT))

import travelogue.layout_engine.planner.screen_planner  # noqa: F401
from travelogue.config import AppConfig
from travelogue.config.mosaic import TemplateContractConfig
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.curate import run_curate
from travelogue.curation.layout_metrics import compute_layout_metrics


def _prepare_trip(trip: dict) -> dict:
    t = copy.deepcopy(trip)
    t.setdefault("pipeline", {})["status"] = "structure_draft"
    t.pop("chapters", None)
    cur = t.setdefault("curation", {})
    cur.pop("clustering", None)
    cur.pop("layoutStrategy", None)
    cur.pop("mosaicDecisionLog", None)
    cur.pop("layoutDecisionLog", None)
    for asset in t.get("assets") or []:
        asset.pop("sceneClusterId", None)
        asset.pop("clusterSource", None)
    return t


def _cfg_variant(base: AppConfig, *, contract_enabled: bool) -> AppConfig:
    mosaic = replace(
        base.mosaic,
        template_contract=TemplateContractConfig(
            enabled=contract_enabled,
            shadow_log=False,
        ),
    )
    return replace(base, mosaic=mosaic)


def _pattern_sequence(chapters: list[dict]) -> list[str]:
    seq: list[str] = []
    for ch in chapters:
        for s in ch.get("screens") or []:
            pid = s.get("patternId")
            if pid:
                seq.append(str(pid))
    return seq


def _screen_signatures(chapters: list[dict]) -> list[str]:
    sigs: list[str] = []
    for ch in chapters:
        cid = ch.get("id") or ""
        for s in ch.get("screens") or []:
            aids = tuple(sorted(str(x) for x in (s.get("assetIds") or [])))
            sigs.append(f"{cid}|{s.get('patternId')}|{aids}")
    return sigs


def _run_variant(
    trip: dict,
    *,
    label: str,
    cfg: AppConfig,
    work_dir: Path,
) -> dict[str, Any]:
    body = _prepare_trip(trip)
    trip_dir = work_dir / label
    trip_dir.mkdir(parents=True, exist_ok=True)
    run_clustering_layer(body, trip_dir=trip_dir / "cluster", cfg=cfg)
    result = run_curate(body, apply_layout=True, trip_dir=trip_dir, cfg=cfg)
    chapters = body.get("chapters") or []
    metrics = compute_layout_metrics(chapters, body.get("assets") or [])
    curation = body.get("curation") or {}
    return {
        "label": label,
        "chapterCount": result.chapter_count,
        "screenCount": sum(len(ch.get("screens") or []) for ch in chapters),
        "patternSequence": _pattern_sequence(chapters),
        "screenSignatures": _screen_signatures(chapters),
        "mosaicDecisionLogCount": len(curation.get("mosaicDecisionLog") or []),
        "metrics": metrics,
        "templateContract": {
            "enabled": bool(cfg.mosaic.template_contract.enabled),
        },
        "curateSummary": result.layout_summary,
    }


def _diff_report(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    base_sigs = baseline["screenSignatures"]
    cand_sigs = candidate["screenSignatures"]
    n = max(len(base_sigs), len(cand_sigs))
    changed_indices: list[int] = []
    for i in range(n):
        if i >= len(base_sigs) or i >= len(cand_sigs) or base_sigs[i] != cand_sigs[i]:
            changed_indices.append(i)
    base_patterns = baseline["patternSequence"]
    cand_patterns = candidate["patternSequence"]
    pattern_changes = [
        {
            "index": i,
            "from": base_patterns[i] if i < len(base_patterns) else None,
            "to": cand_patterns[i] if i < len(cand_patterns) else None,
        }
        for i in changed_indices
        if i < len(base_patterns) or i < len(cand_patterns)
    ][:20]
    return {
        "screensChanged": len(changed_indices),
        "screensTotal": n,
        "screensChangedPct": round(100.0 * len(changed_indices) / n, 2) if n else 0.0,
        "patternOnlyChanges": sum(
            1
            for i in changed_indices
            if i < len(base_sigs)
            and i < len(cand_sigs)
            and base_sigs[i].split("|")[1] != cand_sigs[i].split("|")[1]
        ),
        "firstPatternChanges": pattern_changes,
    }


def _write_compare_html(work: Path, report: dict[str, Any]) -> Path:
    """Minimal side-by-side HTML for dogfood notes (reuse compare.html spirit)."""
    off = report["contractOff"]
    on = report["contractOn"]
    diff = report["diff"]
    rows = ""
    for row in diff.get("firstPatternChanges") or []:
        rows += (
            f"<tr><td>{row['index']}</td>"
            f"<td><code>{row['from']}</code></td>"
            f"<td><code>{row['to']}</code></td></tr>\n"
        )
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"/>
<title>TPC compare · {report['tripId']}</title>
<style>
body {{ font-family: ui-sans-serif, system-ui, sans-serif; margin: 24px; color: #1a1a1a; }}
h1 {{ font-size: 1.25rem; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
th, td {{ border: 1px solid #ddd; padding: 6px 8px; text-align: left; font-size: 13px; }}
th {{ background: #f5f5f3; }}
.meta {{ color: #555; font-size: 14px; }}
code {{ font-size: 12px; }}
</style></head><body>
<h1>Template Contract · on vs off</h1>
<p class="meta">trip=<strong>{report['tripId']}</strong> · {report.get('title') or ''} ·
assets={report['assetCount']}</p>
<p>屏数: {off['screenCount']} → {on['screenCount']} ·
变更屏: {diff['screensChanged']}/{diff['screensTotal']} ({diff['screensChangedPct']}%)</p>
<table>
<thead><tr><th>index</th><th>off pattern</th><th>on pattern</th></tr></thead>
<tbody>
{rows or '<tr><td colspan="3">无 pattern 差异（或仅 asset 序变化）</td></tr>'}
</tbody></table>
<p class="meta">完整 JSON：compare_report.json · 手记请另写 jsonl，勿建协议。</p>
</body></html>
"""
    path = work / "compare.html"
    path.write_text(html, encoding="utf-8")
    return path


def _compare_one_trip(trip_dir: Path, *, out_root: Path) -> int:
    trip_path = trip_dir / "trip.json"
    if not trip_path.is_file():
        print(f"trip not found: {trip_path}", file=sys.stderr)
        return 1

    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    trip_id = trip_dir.name
    title = (trip.get("meta") or {}).get("title") or trip_id
    from travelogue.config import get_config

    base_cfg = get_config(reload=True)
    work = out_root / trip_id
    work.mkdir(parents=True, exist_ok=True)

    print(f"\nTrip: {trip_id} ({title}) · assets={len(trip.get('assets') or [])} · work={work}")

    off = _run_variant(
        trip,
        label="contract_off",
        cfg=_cfg_variant(base_cfg, contract_enabled=False),
        work_dir=work,
    )
    print(f"  contract_off · screens={off['screenCount']}")

    on = _run_variant(
        trip,
        label="contract_on",
        cfg=_cfg_variant(base_cfg, contract_enabled=True),
        work_dir=work,
    )
    print(f"  contract_on · screens={on['screenCount']}")

    diff = _diff_report(off, on)
    report = {
        "tripId": trip_id,
        "title": title,
        "assetCount": len(trip.get("assets") or []),
        "contractOff": {
            k: off[k]
            for k in (
                "label",
                "screenCount",
                "chapterCount",
                "mosaicDecisionLogCount",
                "curateSummary",
                "metrics",
                "templateContract",
            )
        },
        "contractOn": {
            k: on[k]
            for k in (
                "label",
                "screenCount",
                "chapterCount",
                "mosaicDecisionLogCount",
                "curateSummary",
                "metrics",
                "templateContract",
            )
        },
        "diff": diff,
        "notesPathHint": str(work / "dogfood-notes.jsonl"),
    }

    out_json = work / "compare_report.json"
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path = _write_compare_html(work, report)

    print("\n=== TPC 对比摘要 ===")
    print(f"屏数: {off['screenCount']} → {on['screenCount']}")
    print(f"变更屏: {diff['screensChanged']}/{diff['screensTotal']} ({diff['screensChangedPct']}%)")
    print(f"其中 pattern 变化: {diff['patternOnlyChanges']}")
    bm, cm = off["metrics"], on["metrics"]
    for key in (
        "aspectPatternMatchRate",
        "subjectRunScore",
        "timeInversionRate",
        "patternDiversity",
    ):
        if key in bm or key in cm:
            print(f"  {key}: {bm.get(key)} → {cm.get(key)}")
    print(f"\n报告: {out_json}")
    print(f"HTML: {html_path}")
    if diff["firstPatternChanges"]:
        print("\n前几条 pattern 变化:")
        for row in diff["firstPatternChanges"][:8]:
            print(f"  [{row['index']}] {row['from']} → {row['to']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="TPC template_contract on vs off curate compare"
    )
    parser.add_argument("trip_id", nargs="*", help="trip folder name(s) under trips/")
    parser.add_argument("--trip-dir", type=Path, help="Single trip directory")
    parser.add_argument("--recent", type=int, default=0, help="N most recent trips")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / ".cache" / "tpc-layout-compare",
    )
    args = parser.parse_args()

    trip_dirs: list[Path] = []
    if args.trip_dir:
        trip_dirs = [args.trip_dir]
    elif args.recent > 0:
        candidates = [
            p
            for p in ROOT.joinpath("trips").iterdir()
            if p.is_dir() and (p / "trip.json").is_file()
        ]
        candidates.sort(key=lambda p: (p / "trip.json").stat().st_mtime, reverse=True)
        trip_dirs = candidates[: args.recent]
    elif args.trip_id:
        trip_dirs = [ROOT / "trips" / tid for tid in args.trip_id]
    else:
        trip_dirs = [ROOT / "trips" / "linzhi"]

    summaries: list[dict[str, Any]] = []
    for trip_dir in trip_dirs:
        code = _compare_one_trip(trip_dir, out_root=args.out)
        if code != 0:
            return code
        report_path = args.out / trip_dir.name / "compare_report.json"
        if report_path.is_file():
            summaries.append(json.loads(report_path.read_text(encoding="utf-8")))

    if len(summaries) > 1:
        batch_path = args.out / "batch_summary.json"
        batch_path.write_text(
            json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\n批量摘要: {batch_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
