"""Human-readable chapter layout summary for preview (M14 · §6.4.8)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_SCORE_LABELS: dict[str, str] = {
    "aspect_match": "画幅匹配",
    "sharpness": "清晰度",
    "hero_separation": "封面图间隔",
    "temporal_coherence": "时间连贯",
    "diversity": "画面多样",
    "arc_fit": "叙事节奏",
    "burst_integrity": "连拍完整",
    "luminance_continuity": "亮度连贯",
    "subject_run": "主题连贯",
    "tone_continuity": "色调连贯",
    "layout_rhythm": "版面节奏",
}

_DEGRADATION_LABELS: dict[str, str] = {
    "structure_locked": "章节结构已锁定，屏序沿用确认版",
    "insufficient_layout_eligible": "可参与排版的照片较少",
    "insufficient_aspect_diversity": "照片横竖比例较单一",
    "scoring_disabled": "智能排版实验未开启",
    "aspect_only_preserve_legacy": "当前权重与经典排版等价",
}

_VARIANT_LABELS: dict[str, str] = {
    "legacy": "经典方案",
    "with_hero": "含大图屏",
    "no_mosaic": "标准网格",
    "no_hero": "无独立大图",
    "hero_no_pref": "大图备选",
    "no_hero_no_mosaic": "紧凑网格",
}


def _segment_label(seg: dict[str, Any]) -> str:
    for key in ("name", "location"):
        raw = seg.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    start = seg.get("startDate")
    if isinstance(start, str) and start.strip():
        return start.strip()
    return "一段行程"


def _human_degradation(reason: str) -> str:
    return _DEGRADATION_LABELS.get(reason, "已回退到经典排版")


def _aggregate_score_dims(events: list[dict[str, Any]]) -> dict[str, float]:
    totals: dict[str, float] = {k: 0.0 for k in _SCORE_LABELS}
    count = 0
    for event in events:
        score = event.get("score")
        if not isinstance(score, dict):
            continue
        count += 1
        for key in _SCORE_LABELS:
            totals[key] += float(score.get(key) or 0.0)
    if count <= 0:
        return {}
    return {k: v / count for k, v in totals.items()}


def _top_score_reasons(avg_scores: dict[str, float], *, limit: int = 3) -> list[str]:
    ranked = sorted(
        ((k, v) for k, v in avg_scores.items() if v > 0.01),
        key=lambda item: -item[1],
    )
    out: list[str] = []
    for key, value in ranked[:limit]:
        label = _SCORE_LABELS.get(key, key)
        out.append(f"评分侧重{label}（{value:.2f}）")
    return out


def build_layout_explain(curation: dict[str, Any] | None) -> dict[str, Any] | None:
    """P5-7.5 · user-facing layout engine summary from curation metadata."""
    if not curation:
        return None

    degradation = curation.get("degradationReason")
    if isinstance(degradation, str) and degradation.strip():
        reason = degradation.strip()
        details = [_human_degradation(reason)]
        budget = curation.get("layoutSearchBudget")
        if isinstance(budget, dict):
            eligible = budget.get("layoutEligibleCount")
            if isinstance(eligible, int) and eligible >= 0:
                details.append(f"当前 {eligible} 张照片参与智能排版评估")
        return {
            "mode": "degraded",
            "summary": "经典排版（实验模式已降级）",
            "details": details,
        }

    logs = curation.get("layoutDecisionLog")
    if not isinstance(logs, list) or not logs:
        return None

    beam_events: list[dict[str, Any]] = []
    changed = 0
    candidates = 0
    variants: dict[str, int] = {}
    for entry in logs:
        if not isinstance(entry, dict):
            continue
        for event in entry.get("events") or []:
            if not isinstance(event, dict) or event.get("type") != "beam_pick":
                continue
            beam_events.append(event)
            if event.get("changed"):
                changed += 1
            candidates += int(event.get("candidateCount") or 0)
            variant = str(event.get("variant") or "legacy")
            variants[variant] = variants.get(variant, 0) + 1

    if not beam_events:
        return None

    bucket_count = len(beam_events)
    if changed > 0:
        summary = f"智能排版在 {bucket_count} 个日期段中优化了 {changed} 处屏序"
    else:
        summary = f"智能排版评估了 {bucket_count} 个日期段（与经典方案一致）"

    details: list[str] = []
    if candidates > 0:
        avg_candidates = max(1, round(candidates / bucket_count))
        details.append(f"每段平均比较 {avg_candidates} 种候选方案")

    top_variant = max(variants.items(), key=lambda item: item[1])[0] if variants else "legacy"
    if top_variant != "legacy":
        details.append(f"常用方案：{_VARIANT_LABELS.get(top_variant, top_variant)}")

    details.extend(_top_score_reasons(_aggregate_score_dims(beam_events)))

    budget = curation.get("layoutSearchBudget")
    if isinstance(budget, dict):
        evals = budget.get("evaluations")
        if isinstance(evals, int) and evals > 0:
            details.append(f"共评估 {evals} 组屏序组合")

    seen: set[str] = set()
    unique: list[str] = []
    for line in details:
        if line not in seen:
            seen.add(line)
            unique.append(line)

    return {
        "mode": "beam",
        "summary": summary,
        "details": unique,
    }


def build_chapter_explain(trip: dict, *, trip_dir: Path | None = None) -> dict[str, Any]:
    """Build user-facing summary; no cluster IDs or internal codes."""
    clustering = (trip.get("curation") or {}).get("clustering") or {}
    chapters = trip.get("chapters") or []
    segment_mode = str(clustering.get("segmentMode") or "date_fallback")
    segments = clustering.get("segments") or []
    if not isinstance(segments, list):
        segments = []

    details: list[str] = []
    chapter_count = len(chapters)
    segment_count = len(segments)

    if segment_mode == "geo_event" and segment_count:
        labels = [_segment_label(seg) for seg in segments if isinstance(seg, dict)]
        if not labels:
            summary = f"本次按 {chapter_count} 章排版"
        elif len(labels) == 1:
            summary = f"本次按 1 段行程排版：{labels[0]}"
        elif len(labels) <= 5:
            summary = f"本次按 {len(labels)} 段行程排版：{'、'.join(labels)}"
        else:
            summary = (
                f"本次按 {len(labels)} 段行程排版："
                f"{'、'.join(labels[:4])} 等"
            )
        details.append("有位置信息的照片已按停留地点分段")
    else:
        summary = f"已按日期分成 {chapter_count} 章"
        if segment_mode != "geo_event":
            details.append("部分照片缺少位置信息，已按拍摄日期合并")

    clusters = clustering.get("clusters") or []
    if isinstance(clusters, list) and clusters:
        details.append("场景分析已用于段内照片排序")

    if trip_dir is not None:
        from travelogue.curation.cluster_decision_log import cluster_decision_log_path

        log_path = cluster_decision_log_path(trip_dir)
        if log_path.is_file():
            try:
                raw = json.loads(log_path.read_text(encoding="utf-8"))
                for entry in raw.get("entries") or []:
                    if not isinstance(entry, dict):
                        continue
                    kind = str(entry.get("kind") or "")
                    detail = str(entry.get("detail") or "")
                    if kind == "fallback" and "minPhotos" in detail:
                        details.append("少量停留点的照片已并入相邻段落")
                        break
            except (OSError, json.JSONDecodeError):
                pass

    intent_hints = (trip.get("curation") or {}).get("intentHints") or {}
    plan_cities = intent_hints.get("planCities") or []
    if not plan_cities:
        plan_cities = ((trip.get("intent") or {}).get("travelPlan") or {}).get("cities") or []
    if plan_cities:
        from travelogue.services.intent_plan import cities_match

        segment_labels = [
            _segment_label(seg) for seg in segments if isinstance(seg, dict)
        ]
        aligned = [
            city
            for city in plan_cities
            if any(cities_match(city, label) for label in segment_labels)
        ] if segment_labels else list(plan_cities)
        if aligned:
            route = " → ".join(aligned[:5])
            if len(aligned) > 5:
                route += " 等"
            details.append(f"章节顺序已参考您的行程单：{route}")
        else:
            route = " → ".join(plan_cities[:5])
            if len(plan_cities) > 5:
                route += " 等"
            details.append(f"章节标题已参考您的行程单：{route}")

    # De-dupe while preserving order
    seen: set[str] = set()
    unique_details: list[str] = []
    for line in details:
        if line not in seen:
            seen.add(line)
            unique_details.append(line)

    return {
        "summary": summary,
        "details": unique_details,
        "chapterCount": chapter_count,
        "segmentCount": segment_count,
        "segmentMode": segment_mode,
        "layoutExplain": build_layout_explain(trip.get("curation") or {}),
    }


def attach_chapter_explain(trip: dict, *, trip_dir: Path | None = None) -> dict[str, Any]:
    """Write userSummary into trip.curation.clustering (non-destructive merge)."""
    explain = build_chapter_explain(trip, trip_dir=trip_dir)
    curation = trip.setdefault("curation", {})
    clustering = dict(curation.get("clustering") or {})
    clustering["userSummary"] = explain
    curation["clustering"] = clustering
    return explain
