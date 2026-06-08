#!/usr/bin/env python3
"""Compare curate output: LSE off vs capabilities on (dogfood / real trip).

Usage:
  python scripts/lse_flags_curate_compare.py linzhi
  python scripts/lse_flags_curate_compare.py demo-2025 demo-80301df45c
  python scripts/lse_flags_curate_compare.py --recent 5
  python scripts/lse_flags_curate_compare.py --trip-dir trips/linzhi
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

from travelogue.config import AppConfig
from travelogue.config.layout import LayoutStrategyCapabilitiesConfig, LayoutStrategyEngineConfig
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.curate import run_curate
from travelogue.curation.layout_metrics import compute_layout_metrics
from travelogue.layout_engine.registry import get_strategy_pack

import travelogue.curation.screen_planner  # noqa: F401


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


def _cfg_variant(
    base: AppConfig,
    *,
    enabled: bool,
    caps: LayoutStrategyCapabilitiesConfig | None = None,
) -> AppConfig:
    se0 = base.layout.strategy_engine
    caps_eff = caps or LayoutStrategyCapabilitiesConfig()
    se = LayoutStrategyEngineConfig(
        enabled=enabled,
        default_strategy_id=se0.default_strategy_id,
        policy_path=se0.policy_path,
        runtime_store=se0.runtime_store,
        overrides=se0.overrides,
        telemetry=se0.telemetry,
        feedback=se0.feedback,
        capabilities=caps_eff,
    )
    scoring = replace(base.layout.scoring, enabled=True)
    return replace(
        base,
        layout=replace(base.layout, strategy_engine=se, scoring=scoring),
        clustering=replace(base.clustering, enabled="true", scene_cluster_mode="run_aware"),
        vision=replace(base.vision, enabled="true"),
    )


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
    ls = curation.get("layoutStrategy") or {}
    pack = get_strategy_pack(cfg.layout.strategy_engine.default_strategy_id) if cfg.layout.strategy_engine.enabled else None
    from travelogue.layout_engine.adapter import mosaic_config_from_pack

    mosaic_cfg = mosaic_config_from_pack(cfg, pack) if pack else None
    return {
        "label": label,
        "chapterCount": result.chapter_count,
        "screenCount": sum(len(ch.get("screens") or []) for ch in chapters),
        "patternSequence": _pattern_sequence(chapters),
        "screenSignatures": _screen_signatures(chapters),
        "layoutStrategy": ls,
        "capabilityFlags": ls.get("capabilityFlags"),
        "mosaicDecisionLogCount": len(curation.get("mosaicDecisionLog") or []),
        "layoutDecisionLogCount": len(curation.get("layoutDecisionLog") or []),
        "metrics": metrics,
        "mosaicRuntime": {
            "lse_saliency_scoring": getattr(mosaic_cfg, "lse_saliency_scoring", False),
            "lse_tone_harmony": getattr(mosaic_cfg, "lse_tone_harmony", False),
            "lse_beat_profile": getattr(mosaic_cfg, "lse_beat_profile", "flat"),
            "lse_hungarian_assignment": getattr(mosaic_cfg, "lse_hungarian_assignment", False),
            "toneContinuityWeight": float((mosaic_cfg.weights or {}).get("tone_continuity") or 0.0)
            if mosaic_cfg
            else 0.0,
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
        {"index": i, "from": base_patterns[i] if i < len(base_patterns) else None, "to": cand_patterns[i] if i < len(cand_patterns) else None}
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


def main() -> int:
    parser = argparse.ArgumentParser(description="LSE capabilities curate A/B on real trip")
    parser.add_argument("trip_id", nargs="*", help="trip folder name(s) under trips/")
    parser.add_argument("--trip-dir", type=Path, help="Single trip directory (overrides trip_id)")
    parser.add_argument(
        "--recent",
        type=int,
        default=0,
        help="Compare N most recently modified trips under trips/",
    )
    parser.add_argument("--out", type=Path, default=ROOT / ".cache" / "lse-flags-compare")
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
        _print_batch_table(summaries)
    return 0


def _print_batch_table(summaries: list[dict[str, Any]]) -> None:
    print("\n| trip | 标题 | 资产 | 屏差 | 变更% | pattern变 | diversity Δ |")
    print("|------|------|------|------|-------|-----------|-------------|")
    for s in summaries:
        tid = s["tripId"]
        title = s.get("title") or "—"
        assets = s["assetCount"]
        d = s["diff"]
        bd = s["baseline"]["metrics"]
        cd = s["capsFull"]["metrics"]
        div_delta = round(float(cd.get("patternDiversity", 0)) - float(bd.get("patternDiversity", 0)), 4)
        print(
            f"| {tid} | {title} | {assets} | {d['screensChanged']}/{d['screensTotal']} "
            f"| {d['screensChangedPct']}% | {d['patternOnlyChanges']} | {div_delta:+.4f} |"
        )


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

    caps_on = LayoutStrategyCapabilitiesConfig(
        saliency_scoring=True,
        tone_harmony=True,
        hungarian_assignment=True,
        quality_unified=True,
        segment_order_optimizer=True,
        highlight_windows=True,
        editorial_hints=True,
        beat_profile="classic_magazine",
    )

    work = out_root / trip_id
    work.mkdir(parents=True, exist_ok=True)

    print(f"\nTrip: {trip_id} ({title}) · assets={len(trip.get('assets') or [])} · work={work}")

    baseline = _run_variant(
        trip,
        label="baseline_lse_off",
        cfg=_cfg_variant(base_cfg, enabled=False),
        work_dir=work,
    )
    print(f"  baseline done · screens={baseline['screenCount']}")

    caps = _run_variant(
        trip,
        label="caps_full_lse_on",
        cfg=_cfg_variant(base_cfg, enabled=True, caps=caps_on),
        work_dir=work,
    )
    print(f"  caps_full done · screens={caps['screenCount']}")

    diff = _diff_report(baseline, caps)
    report = {
        "tripId": trip_id,
        "title": title,
        "assetCount": len(trip.get("assets") or []),
        "baseline": {
            k: baseline[k]
            for k in (
                "label",
                "screenCount",
                "chapterCount",
                "capabilityFlags",
                "mosaicDecisionLogCount",
                "curateSummary",
                "metrics",
                "mosaicRuntime",
            )
        },
        "capsFull": {
            k: caps[k]
            for k in (
                "label",
                "screenCount",
                "chapterCount",
                "capabilityFlags",
                "mosaicDecisionLogCount",
                "curateSummary",
                "metrics",
                "mosaicRuntime",
            )
        },
        "diff": diff,
    }

    out_json = work / "compare_report.json"
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== 对比摘要 ===")
    print(f"屏数: {baseline['screenCount']} → {caps['screenCount']}")
    print(f"变更屏: {diff['screensChanged']}/{diff['screensTotal']} ({diff['screensChangedPct']}%)")
    print(f"其中 pattern 变化: {diff['patternOnlyChanges']}")
    print(f"Mosaic 决策日志: {baseline['mosaicDecisionLogCount']} → {caps['mosaicDecisionLogCount']}")
    bm = baseline["metrics"]
    cm = caps["metrics"]
    for key in ("aspectPatternMatchRate", "subjectRunScore", "timeInversionRate", "patternDiversity"):
        if key in bm or key in cm:
            print(f"  {key}: {bm.get(key)} → {cm.get(key)}")
    print(f"capabilityFlags (caps): {caps.get('capabilityFlags')}")
    print(f"\n完整报告: {out_json}")
    if diff["firstPatternChanges"]:
        print("\n前几条 pattern 变化:")
        for row in diff["firstPatternChanges"][:8]:
            print(f"  [{row['index']}] {row['from']} → {row['to']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
