"""Chapter title generation from day buckets and segment labels."""

from __future__ import annotations

from datetime import date, datetime

from travelogue.curation.bucket_planning import bucket_day_span
from travelogue.curation.time_segments import parse_asset_date
from travelogue.domain.copy_subject import narrative_copy_subject


def title_for_bucket_span(span: list[str]) -> str | None:
    if len(span) < 2:
        return None
    d0 = date.fromisoformat(span[0])
    d1 = date.fromisoformat(span[-1])
    if d0.year != d1.year:
        return f"{d0.year}–{d1.year}"[:12]
    if d0.month == d1.month and d0.day == d1.day:
        return f"{d0.month}月{d0.day}日"[:12]
    return f"{d0.month}月{d0.day}–{d1.month}月{d1.day}日"[:12]


def _prd_daypart_label(taken_at: str | None) -> str | None:
    """Map hour → PRD 四档：上午 / 下午 / 傍晚 / 晚上（OQ-FST-01）。"""
    if not taken_at:
        return None
    try:
        dt = datetime.fromisoformat(str(taken_at).replace("Z", "+00:00"))
    except ValueError:
        return None
    hour = dt.hour
    if 5 <= hour < 12:
        return "上午"
    if 12 <= hour < 17:
        return "下午"
    if 17 <= hour < 20:
        return "傍晚"
    return "晚上"


def _bucket_daypart(bucket: list[str], assets_by_id: dict[str, dict]) -> str | None:
    for aid in bucket:
        raw = (assets_by_id.get(aid) or {}).get("takenAt") or ""
        label = _prd_daypart_label(str(raw) if raw else None)
        if label:
            return label
    return None


def chapter_titles(
    buckets: list[list[str]],
    assets: list[dict],
    meta: dict,
    *,
    intent: dict | None = None,
    bucket_segment_ids: list[str] | None = None,
    bucket_segment_ids_all: list[list[str]] | None = None,
    segment_labels: dict[str, str] | None = None,
    plan_cities: list[str] | None = None,
) -> list[str]:
    place = narrative_copy_subject(meta, intent=intent, assets=assets)
    assets_by_id = {a["id"]: a for a in assets}
    titles: list[str] = []
    day_seen: dict[str, int] = {}
    seg_day_seen: dict[str, int] = {}
    bucket_segment_ids = bucket_segment_ids or []
    bucket_segment_ids_all = bucket_segment_ids_all or []
    segment_labels = segment_labels or {}
    plan_cities = [c for c in (plan_cities or []) if c][:10]
    plan_idx = 0

    for i, bucket in enumerate(buckets):
        if not bucket:
            titles.append(f"片段{i + 1}")
            continue

        span = bucket_day_span(bucket, assets_by_id)
        if len(span) > 1:
            d0 = date.fromisoformat(span[0])
            d1 = date.fromisoformat(span[-1])
            if d0.year != d1.year:
                titles.append(f"{d0.year}–{d1.year}"[:12])
                continue

        all_seg = (
            bucket_segment_ids_all[i]
            if i < len(bucket_segment_ids_all)
            else []
        )
        if len(all_seg) > 1:
            labels = [segment_labels[s][:8] for s in all_seg if segment_labels.get(s)]
            if labels:
                titles.append("·".join(labels[:2])[:12])
                continue

        if plan_idx < len(plan_cities):
            titles.append(plan_cities[plan_idx][:12])
            plan_idx += 1
            continue

        seg_id = bucket_segment_ids[i] if i < len(bucket_segment_ids) else ""
        if seg_id and segment_labels.get(seg_id):
            n = seg_day_seen.get(seg_id, 0)
            seg_day_seen[seg_id] = n + 1
            if n == 0:
                titles.append(segment_labels[seg_id][:12])
                continue

        if len(span) > 1:
            span_title = title_for_bucket_span(span)
            if span_title:
                titles.append(span_title)
                continue
        d = parse_asset_date(assets_by_id.get(bucket[0], {}))
        if d:
            key = d.isoformat()
            n = day_seen.get(key, 0)
            day_seen[key] = n + 1
            base = f"{d.month}月{d.day}日"
            if n == 0:
                titles.append(base[:12])
            else:
                # BE-FST-05 / OQ-FST-01 · 禁「日期续」；优先时段，否则（n）
                daypart = _bucket_daypart(bucket, assets_by_id)
                if daypart:
                    candidate = f"{base} · {daypart}"
                    if candidate not in titles:
                        titles.append(candidate[:12])
                        continue
                titles.append(f"{base}（{n + 1}）"[:12])
        elif i == 0:
            titles.append("抵达"[:12])
        elif i == len(buckets) - 1:
            titles.append("尾声"[:12])
        else:
            titles.append(f"{place}·{i}"[:12])
    return titles
