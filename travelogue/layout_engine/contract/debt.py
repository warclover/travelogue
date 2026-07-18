"""Layout-debt aggregation for TPC W1 (G-TPC-01 / AC-TPC-08)."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from travelogue.layout_contract.orientations import AspectKind, aspect_kind_for_asset
from travelogue.layout_engine.contract.mix_index import (
    format_mix_key,
    mix_key_from_aspects,
)


def summarize_mosaic_decision_log(logs: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate planner_path / fallback / self-heal from mosaicDecisionLog."""
    total = len(logs)
    path_counts = Counter(str(e.get("plannerPath") or "unknown") for e in logs)
    fallback_counts = Counter(
        str(e.get("fallbackReason") or "none")
        for e in logs
        if e.get("fallbackUsed")
    )
    self_heal_steps = Counter(
        str(e.get("selfHealStep") or "unknown")
        for e in logs
        if e.get("selfHealApplied")
    )
    by_window_size: dict[str, dict[str, int]] = {}
    for e in logs:
        n = str(e.get("windowSize") or "?")
        bucket = by_window_size.setdefault(n, {"total": 0, "legacy": 0})
        bucket["total"] += 1
        if str(e.get("plannerPath") or "") == "legacy":
            bucket["legacy"] += 1

    legacy = int(path_counts.get("legacy", 0))
    return {
        "windowCount": total,
        "legacyCount": legacy,
        "legacyRate": round(legacy / total, 4) if total else 0.0,
        "plannerPathCounts": dict(path_counts),
        "fallbackReasonCounts": dict(fallback_counts),
        "selfHealStepCounts": dict(self_heal_steps),
        "byWindowSize": by_window_size,
    }


def window_mix_histogram(
    chapters: list[dict],
    assets_by_id: Mapping[str, dict],
    aspects: Mapping[str, AspectKind] | None = None,
) -> dict[str, int]:
    """Count emitted content screens by bag-of-mix of their slot assets."""
    counts: Counter[str] = Counter()
    for ch in chapters:
        for screen in ch.get("screens") or []:
            pid = str(screen.get("patternId") or "")
            if not pid or pid.startswith("breath"):
                continue
            aids = [
                str(sl["assetId"])
                for sl in (screen.get("slots") or [])
                if sl.get("assetId")
            ]
            if not aids:
                continue
            if aspects is None:
                local_aspects: dict[str, AspectKind] = {
                    aid: aspect_kind_for_asset(assets_by_id.get(aid) or {})
                    for aid in aids
                }
            else:
                local_aspects = {
                    aid: aspects.get(aid)
                    or aspect_kind_for_asset(assets_by_id.get(aid) or {})
                    for aid in aids
                }
            key = mix_key_from_aspects(aids, local_aspects)
            counts[format_mix_key(key)] += 1
    return dict(counts.most_common())


def library_mix_coverage(templates: Mapping[str, Any]) -> dict[str, list[str]]:
    """pattern_ids grouped by mix key (active templates only)."""
    from travelogue.layout_engine.contract.mix_index import build_mix_inverted_index

    index = build_mix_inverted_index(templates)
    return {format_mix_key(k): v for k, v in index.items()}


def mix_holes(
    window_hist: Mapping[str, int],
    library: Mapping[str, list[str]],
    *,
    min_window_freq: int = 1,
) -> list[dict[str, Any]]:
    """Window mixes seen in corpus with zero (or thin) library coverage."""
    holes: list[dict[str, Any]] = []
    for mix, freq in sorted(window_hist.items(), key=lambda kv: (-kv[1], kv[0])):
        if freq < min_window_freq:
            continue
        covered = library.get(mix) or []
        if not covered:
            holes.append({"mix": mix, "windowFreq": freq, "libraryPatterns": []})
    return holes


def build_trip_debt_report(
    *,
    trip_id: str,
    mosaic_logs: list[dict[str, Any]],
    chapters: list[dict],
    assets: list[dict],
    layout_metrics: Mapping[str, Any] | None = None,
    templates: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    assets_by_id = {str(a.get("id")): a for a in assets if a.get("id")}
    log_summary = summarize_mosaic_decision_log(mosaic_logs)
    window_hist = window_mix_histogram(chapters, assets_by_id)
    library = library_mix_coverage(templates) if templates is not None else {}
    holes = mix_holes(window_hist, library) if library else []
    metrics = dict(layout_metrics or {})
    return {
        "tripId": trip_id,
        "legacy": log_summary,
        "aspectPatternMatchRate": metrics.get("aspectPatternMatchRate"),
        "layoutMetrics": {
            k: metrics[k]
            for k in (
                "aspectPatternMatchRate",
                "patternDiversity",
                "heroLedRate",
                "denseScreenRate",
            )
            if k in metrics
        },
        "windowMixHistogram": window_hist,
        "mixHoles": holes,
        "libraryMixCount": len(library),
    }


def merge_debt_reports(trip_reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Roll up per-trip debt into a corpus summary."""
    total_windows = 0
    total_legacy = 0
    path_counts: Counter[str] = Counter()
    fallback_counts: Counter[str] = Counter()
    mix_hist: Counter[str] = Counter()
    hole_freq: Counter[str] = Counter()
    match_rates: list[float] = []

    for rep in trip_reports:
        legacy = rep.get("legacy") or {}
        total_windows += int(legacy.get("windowCount") or 0)
        total_legacy += int(legacy.get("legacyCount") or 0)
        path_counts.update(legacy.get("plannerPathCounts") or {})
        fallback_counts.update(legacy.get("fallbackReasonCounts") or {})
        mix_hist.update(rep.get("windowMixHistogram") or {})
        for hole in rep.get("mixHoles") or []:
            hole_freq[str(hole.get("mix"))] += int(hole.get("windowFreq") or 0)
        rate = rep.get("aspectPatternMatchRate")
        if isinstance(rate, (int, float)):
            match_rates.append(float(rate))

    return {
        "tripCount": len(trip_reports),
        "windowCount": total_windows,
        "legacyCount": total_legacy,
        "legacyRate": round(total_legacy / total_windows, 4) if total_windows else 0.0,
        "plannerPathCounts": dict(path_counts),
        "fallbackReasonCounts": dict(fallback_counts),
        "meanAspectPatternMatchRate": (
            round(sum(match_rates) / len(match_rates), 4) if match_rates else None
        ),
        "windowMixHistogram": dict(mix_hist.most_common()),
        "mixHoleTop": [
            {"mix": m, "windowFreq": f} for m, f in hole_freq.most_common(20)
        ],
        "trips": [
            {
                "tripId": r.get("tripId"),
                "legacyRate": (r.get("legacy") or {}).get("legacyRate"),
                "windowCount": (r.get("legacy") or {}).get("windowCount"),
                "aspectPatternMatchRate": r.get("aspectPatternMatchRate"),
            }
            for r in trip_reports
        ],
    }
