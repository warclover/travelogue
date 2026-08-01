"""Layout-debt aggregation for TPC W1 (G-TPC-01 / AC-TPC-08)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import Any

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


def _percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 6)
    k = max(0, min(len(ordered) - 1, int(round(p * (len(ordered) - 1)))))
    return round(ordered[k], 6)


def raw_geometry_percentiles(mosaic_logs: list[dict[str, Any]]) -> dict[str, Any]:
    """P50/P95 for AC-TPC-10 raw geometry fields present on mosaicDecisionLog."""
    keys = ("heroProminenceRatio", "heroCoverageRatio", "cellAreaCv")
    out: dict[str, Any] = {"sampleCount": 0}
    samples: dict[str, list[float]] = {k: [] for k in keys}
    for e in mosaic_logs:
        hit = False
        for k in keys:
            raw = e.get(k)
            if isinstance(raw, (int, float)):
                samples[k].append(float(raw))
                hit = True
        if hit:
            out["sampleCount"] = int(out["sampleCount"]) + 1
    for k in keys:
        vals = samples[k]
        out[k] = {
            "n": len(vals),
            "p50": _percentile(vals, 0.50),
            "p95": _percentile(vals, 0.95),
        }
    return out


def caption_coverage(
    mosaic_logs: list[dict[str, Any]],
    templates: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Caption-active windows vs templates declaring captionAreas (TPC §6.1).

    V1 captionAreas SKUs are deferred — rates may stay 0 until MSR ships.
    """
    caption_active = 0
    for e in mosaic_logs:
        if e.get("captionActive") or e.get("hasCaption") or e.get("captionTiebreakApplied"):
            caption_active += 1
            continue
        if e.get("captionSlots") or e.get("captionAreas"):
            caption_active += 1

    with_areas = 0
    if templates:
        for t in templates.values():
            constraints = getattr(t, "constraints", None)
            if isinstance(constraints, dict) and constraints.get("captionAreas"):
                with_areas += 1
            elif isinstance(t, Mapping) and (t.get("constraints") or {}).get("captionAreas"):
                with_areas += 1

    return {
        "captionActiveWindows": caption_active,
        "templatesWithCaptionAreas": with_areas,
        "coverageRate": (
            round(min(1.0, with_areas / caption_active), 4) if caption_active else None
        ),
    }


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
        "captionCoverage": caption_coverage(mosaic_logs, templates),
        "rawGeometryPercentiles": raw_geometry_percentiles(mosaic_logs),
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
    caption_active_total = 0
    caption_templates_max = 0
    _GEO_KEYS = ("heroProminenceRatio", "heroCoverageRatio", "cellAreaCv")
    # Percentiles do not average: we CANNOT rebuild a corpus p95 from per-trip p50
    # (the old p50×n expansion was mathematically misleading). Keep the per-trip
    # p50/p95 lists and only report honest roll-ups (median of p50s, max of p95s).
    geo_trip_p50s: dict[str, list[float]] = {k: [] for k in _GEO_KEYS}
    geo_trip_p95s: dict[str, list[float]] = {k: [] for k in _GEO_KEYS}
    geo_total_n: dict[str, int] = {k: 0 for k in _GEO_KEYS}

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
        cap = rep.get("captionCoverage") or {}
        caption_active_total += int(cap.get("captionActiveWindows") or 0)
        caption_templates_max = max(
            caption_templates_max, int(cap.get("templatesWithCaptionAreas") or 0)
        )
        geo = rep.get("rawGeometryPercentiles") or {}
        for key in _GEO_KEYS:
            bucket = geo.get(key) or {}
            n = int(bucket.get("n") or 0)
            if n <= 0:
                continue
            geo_total_n[key] += n
            p50 = bucket.get("p50")
            if isinstance(p50, (int, float)):
                geo_trip_p50s[key].append(float(p50))
            p95 = bucket.get("p95")
            if isinstance(p95, (int, float)):
                geo_trip_p95s[key].append(float(p95))

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
        "captionCoverage": {
            "captionActiveWindows": caption_active_total,
            "templatesWithCaptionAreas": caption_templates_max,
            "coverageRate": (
                round(min(1.0, caption_templates_max / caption_active_total), 4)
                if caption_active_total
                else None
            ),
        },
        "rawGeometryPercentiles": {
            "note": (
                "per-trip percentiles only; corpus p95 not reconstructed from p50"
            ),
            **{
                k: {
                    "n": geo_total_n[k],
                    "tripCount": len(geo_trip_p50s[k]),
                    # Honest roll-up: median of per-trip p50s (no p50 copying).
                    "p50": _percentile(geo_trip_p50s[k], 0.50),
                    # p95 cannot be re-derived; expose the worst per-trip p95.
                    "tripP95Max": (max(geo_trip_p95s[k]) if geo_trip_p95s[k] else None),
                    "tripP95Median": _percentile(geo_trip_p95s[k], 0.50),
                }
                for k in _GEO_KEYS
            },
        },
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
