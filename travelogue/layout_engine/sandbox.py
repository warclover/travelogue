"""LSE trip layout sandbox replay + diff (W2 · AC-P17-09 prep).

PRD §5.2.3 / R-15: **实验路径** — 内嵌 clustering+curate 全管线，仅供 sandbox/dogfood；
禁止作为第四套生产编排扩散（生产入口 = curate → adapter → planner）。
"""

from __future__ import annotations

import copy
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any

from travelogue.config import AppConfig
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.curate import run_curate


def _pattern_distribution(chapters: list[dict]) -> dict[str, float]:
    counts: Counter[str] = Counter()
    total = 0
    for ch in chapters:
        for scr in ch.get("screens") or []:
            pid = str(scr.get("patternId") or "unknown")
            counts[pid] += 1
            total += 1
    if total == 0:
        return {}
    return {pid: round(n / total, 4) for pid, n in counts.items()}


def layout_screen_rows(chapters: list[dict]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ch in chapters:
        ch_id = str(ch.get("id") or "")
        for scr in ch.get("screens") or []:
            rows.append(
                {
                    "chapterId": ch_id,
                    "patternId": scr.get("patternId"),
                    "slotAssetIds": [
                        slot.get("assetId")
                        for slot in (scr.get("slots") or [])
                        if slot.get("assetId")
                    ],
                }
            )
    return rows


def diff_layout_snapshots(baseline: dict, candidate: dict) -> dict[str, Any]:
    base_rows = layout_screen_rows(baseline.get("chapters") or [])
    cand_rows = layout_screen_rows(candidate.get("chapters") or [])
    changed: list[dict[str, Any]] = []
    limit = max(len(base_rows), len(cand_rows))
    for i in range(limit):
        b = base_rows[i] if i < len(base_rows) else None
        c = cand_rows[i] if i < len(cand_rows) else None
        if b != c:
            changed.append({"index": i, "baseline": b, "candidate": c})
    return {
        "changedScreens": changed,
        "changedCount": len(changed),
        "baselineScreenCount": len(base_rows),
        "candidateScreenCount": len(cand_rows),
        "unchanged": len(changed) == 0,
    }


def _prepare_trip(trip: dict) -> dict:
    body = copy.deepcopy(trip)
    body.setdefault("pipeline", {})["status"] = "structure_draft"
    body.pop("chapters", None)
    body.setdefault("curation", {}).pop("clustering", None)
    for asset in body.get("assets") or []:
        asset.pop("sceneClusterId", None)
        asset.pop("clusterSource", None)
    return body


def _layout_snapshot(chapters: list[dict]) -> dict[str, Any]:
    return {
        "chapters": [
            {
                "id": ch.get("id"),
                "patternId": ch.get("patternId"),
                "screens": [
                    {
                        "patternId": s.get("patternId"),
                        "slotAssetIds": [
                            slot.get("assetId")
                            for slot in (s.get("slots") or [])
                            if slot.get("assetId")
                        ],
                    }
                    for s in (ch.get("screens") or [])
                ],
            }
            for ch in chapters
        ]
    }


def _run_curate_snapshot(
    trip: dict,
    *,
    work_dir: Path,
    cfg: AppConfig,
) -> dict[str, Any]:
    body = _prepare_trip(trip)
    run_clustering_layer(body, trip_dir=work_dir / "cluster", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=work_dir, cfg=cfg)
    chapters = body.get("chapters") or []
    return {
        "snapshot": _layout_snapshot(chapters),
        "patternDistribution": _pattern_distribution(chapters),
        "screenCount": sum(len(ch.get("screens") or []) for ch in chapters),
    }


def sandbox_replay_trip(
    trip: dict,
    *,
    baseline_cfg: AppConfig,
    candidate_cfg: AppConfig,
    work_dir: Path,
) -> dict[str, Any]:
    """Replay curate twice and return layout diff summary."""
    base = _run_curate_snapshot(trip, work_dir=work_dir / "baseline", cfg=baseline_cfg)
    cand = _run_curate_snapshot(trip, work_dir=work_dir / "candidate", cfg=candidate_cfg)
    diff = diff_layout_snapshots(base["snapshot"], cand["snapshot"])
    base_total = base["screenCount"] or 1
    diff_rate = round(diff["changedCount"] / base_total, 4)
    return {
        "baseline": {
            "patternDistribution": base["patternDistribution"],
            "screenCount": base["screenCount"],
        },
        "candidate": {
            "patternDistribution": cand["patternDistribution"],
            "screenCount": cand["screenCount"],
        },
        "diff": diff,
        "diffRate": diff_rate,
    }


def enrich_changed_screen_previews(
    trip: dict,
    trip_id: str,
    trip_dir: Path,
    diff: dict[str, Any],
) -> list[dict[str, Any]]:
    """Attach first-slot preview URLs for changed screens (Studio sandbox UI)."""
    from travelogue.render.context import pick_image_src
    from travelogue.web.studio_bento_preview import _trip_static_url

    assets = {
        str(a.get("id")): a for a in (trip.get("assets") or []) if a.get("id")
    }
    enriched: list[dict[str, Any]] = []
    for ch in diff.get("changedScreens") or []:
        row = dict(ch)
        for side in ("baseline", "candidate"):
            scr = ch.get(side)
            if not isinstance(scr, dict):
                continue
            aids = scr.get("slotAssetIds") or []
            aid = aids[0] if aids else None
            asset = assets.get(str(aid)) if aid else None
            if not asset:
                continue
            rel = pick_image_src(asset)
            if rel and (trip_dir / rel).is_file():
                row[f"{side}Preview"] = _trip_static_url(trip_id, rel)
        enriched.append(row)
    return enriched


def cfg_lse_sandbox_pair(base: AppConfig) -> tuple[AppConfig, AppConfig]:
    """Baseline = LSE off; candidate = LSE on (pure convergence default pack)."""
    se_off = replace(base.layout.strategy_engine, enabled=False)
    se_on = replace(base.layout.strategy_engine, enabled=True)
    scoring_off = replace(base.layout.scoring, enabled=False)
    layout_off = replace(base.layout, strategy_engine=se_off, scoring=scoring_off)
    layout_on = replace(base.layout, strategy_engine=se_on, scoring=scoring_off)
    return (
        replace(base, layout=layout_off),
        replace(base, layout=layout_on),
    )
