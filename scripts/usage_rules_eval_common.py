"""Shared off/on curate helpers for URO eval + blind export scripts."""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from scripts.phase3_ig2_report import load_fixture_trip
from tests._golden.helpers import layout_snapshot
from travelogue.config import AppConfig, get_config
from travelogue.config.runtime import config_override
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.curate import run_curate
from travelogue.curation.layout_metrics import compute_layout_metrics
from travelogue.curation.usage_rules.metrics import compare_usage_rules_metrics

AC_URO_BLIND_THRESHOLD = 0.55
HERO_MISMATCH_IMPROVE_TARGET = 0.30


def prepare_trip(trip: dict) -> dict:
    t = copy.deepcopy(trip)
    t.setdefault("pipeline", {})["status"] = "structure_draft"
    t.pop("chapters", None)
    cur = t.setdefault("curation", {})
    cur.pop("clustering", None)
    cur.pop("mosaicDecisionLog", None)
    cur.pop("layoutDecisionLog", None)
    cur.pop("layoutMetrics", None)
    for asset in t.get("assets") or []:
        asset.pop("sceneClusterId", None)
        asset.pop("clusterSource", None)
    return t


def ensure_trip_screen_ids(trip: dict) -> int:
    """Assign ``screenId`` on any screen missing it (render schema requires it)."""
    filled = 0
    for ch in trip.get("chapters") or []:
        ch_id = str(ch.get("id") or "ch-unknown")
        screens = ch.get("screens") or []
        max_seq = 0
        for sc in screens:
            sid = str(sc.get("screenId") or "").strip()
            prefix = f"{ch_id}-sc-"
            if sid.startswith(prefix):
                try:
                    max_seq = max(max_seq, int(sid[len(prefix) :]))
                except ValueError:
                    pass
        for sc in screens:
            if str(sc.get("screenId") or "").strip():
                continue
            max_seq += 1
            sc["screenId"] = f"{ch_id}-sc-{max_seq:02d}"
            filled += 1
    return filled


def cfg_with_usage_rules(base: AppConfig, *, enabled: bool) -> AppConfig:
    ur = replace(base.layout.usage_rules, enabled=enabled)
    layout = replace(base.layout, usage_rules=ur)
    return replace(base, layout=layout)


def load_trip(trip_id: str, *, trips_dir: Path, use_fixture: bool) -> dict | None:
    if use_fixture:
        return load_fixture_trip(trip_id)
    path = trips_dir / trip_id / "trip.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    try:
        return load_fixture_trip(trip_id)
    except (FileNotFoundError, KeyError, OSError):
        return None


def run_variant(
    trip: dict,
    *,
    usage_enabled: bool,
    work_dir: Path,
    cfg_base: AppConfig | None = None,
    return_trip: bool = False,
) -> dict[str, Any]:
    base = cfg_base or get_config(reload=True)
    cfg = cfg_with_usage_rules(base, enabled=usage_enabled)
    body = prepare_trip(trip)
    tag = "on" if usage_enabled else "off"
    run_dir = work_dir / tag
    with config_override(cfg):
        run_clustering_layer(body, trip_dir=run_dir / "cluster", cfg=cfg)
        run_curate(body, apply_layout=True, trip_dir=run_dir, cfg=cfg)
    chapters = body.get("chapters") or []
    assets = body.get("assets") or []
    curation = body.get("curation") or {}
    mosaic_logs = curation.get("mosaicDecisionLog")
    metrics = compute_layout_metrics(chapters, assets, mosaic_logs=mosaic_logs)
    usage_block = metrics.get("usageRules") or {}
    if usage_block:
        usage_block = dict(usage_block)
        usage_block["enabled"] = usage_enabled
        metrics["usageRules"] = usage_block
    snapshot = layout_snapshot(chapters)
    usage_reject_count = sum(
        len(lg.get("usageRuleRejects") or []) for lg in (mosaic_logs or [])
    )
    out: dict[str, Any] = {
        "usageRulesEnabled": usage_enabled,
        "metrics": metrics,
        "layoutSnapshot": snapshot,
        "mosaicLogCount": len(mosaic_logs or []),
        "usageRuleRejectCount": usage_reject_count,
    }
    if return_trip:
        out["trip"] = body
    return out


def evaluate_trip_off_on(
    trip_id: str,
    trip: dict,
    *,
    work_dir: Path,
) -> dict[str, Any]:
    off = run_variant(trip, usage_enabled=False, work_dir=work_dir)
    on = run_variant(trip, usage_enabled=True, work_dir=work_dir)
    snap_equal = off["layoutSnapshot"] == on["layoutSnapshot"]
    metric_cmp = compare_usage_rules_metrics(off["metrics"], on["metrics"])
    off_hmr = off["metrics"].get("heroMismatchRate")
    on_hmr = on["metrics"].get("heroMismatchRate")
    hmr_improved = False
    if off_hmr is not None and on_hmr is not None and float(off_hmr) > 0:
        hmr_improved = (
            float(off_hmr) - float(on_hmr)
        ) / float(off_hmr) >= HERO_MISMATCH_IMPROVE_TARGET
    elif off_hmr is not None and on_hmr is not None:
        hmr_improved = float(on_hmr) <= float(off_hmr)

    return {
        "tripId": trip_id,
        "assetCount": len(trip.get("assets") or []),
        "layoutSnapshotEqual": snap_equal,
        "off": {
            "screenCount": off["metrics"].get("screenCount"),
            "heroMismatchRate": off_hmr,
            "denseStreakViolationRate": off["metrics"].get("denseStreakViolationRate"),
            "patternExposureEntropy": off["metrics"].get("patternExposureEntropy"),
        },
        "on": {
            "screenCount": on["metrics"].get("screenCount"),
            "heroMismatchRate": on_hmr,
            "denseStreakViolationRate": on["metrics"].get("denseStreakViolationRate"),
            "patternExposureEntropy": on["metrics"].get("patternExposureEntropy"),
            "usageRuleRejectCount": on["usageRuleRejectCount"],
        },
        "delta": metric_cmp,
        "passesHeroMismatchTarget": hmr_improved,
        "notes": (
            "layoutSnapshotEqual=true 表示 off 基线未被意外改变；"
            "盲评胜率需人工 AC-URO-BLIND，本脚本仅输出诊断指标。"
        ),
    }


def aggregate_eval_rows(rows: list[dict]) -> dict[str, Any]:
    changed = [r for r in rows if not r.get("layoutSnapshotEqual")]
    hmr_pass = [r for r in rows if r.get("passesHeroMismatchTarget")]
    return {
        "tripCount": len(rows),
        "layoutChangedCount": len(changed),
        "heroMismatchTargetPassCount": len(hmr_pass),
        "heroMismatchTargetPassRate": round(len(hmr_pass) / len(rows), 4) if rows else None,
        "acUroBlindThreshold": AC_URO_BLIND_THRESHOLD,
        "notes": (
            "AC-URO-BLIND 需人工盲评 pairwise；"
            f"代理指标 heroMismatchRate 改善 ≥{int(HERO_MISMATCH_IMPROVE_TARGET * 100)}% 为非门禁诊断。"
        ),
    }
