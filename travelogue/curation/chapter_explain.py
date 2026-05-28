"""Human-readable chapter layout summary for preview (M14 · §6.4.8)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _segment_label(seg: dict[str, Any]) -> str:
    for key in ("name", "location"):
        raw = seg.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    start = seg.get("startDate")
    if isinstance(start, str) and start.strip():
        return start.strip()
    return "一段行程"


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
    }


def attach_chapter_explain(trip: dict, *, trip_dir: Path | None = None) -> dict[str, Any]:
    """Write userSummary into trip.curation.clustering (non-destructive merge)."""
    explain = build_chapter_explain(trip, trip_dir=trip_dir)
    curation = trip.setdefault("curation", {})
    clustering = dict(curation.get("clustering") or {})
    clustering["userSummary"] = explain
    curation["clustering"] = clustering
    return explain
