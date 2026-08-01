"""Chapter title generation from day buckets and segment labels."""

from __future__ import annotations

import re
from datetime import date, datetime

from travelogue.curation.bucket_planning import bucket_day_span
from travelogue.curation.time_segments import parse_asset_date
from travelogue.domain.copy_subject import narrative_copy_subject

_CHAPTER_TITLE_MAX = 14
_DATE_HEAD_RE = re.compile(r"^\d{1,2}月\d{1,2}")
_DAYPART_TAILS = frozenset({"上午", "下午", "傍晚", "晚上"})


def _clip_title(text: str, max_len: int = _CHAPTER_TITLE_MAX) -> str:
    """Truncate without leaving a dangling · / • separator."""
    text = (text or "").strip().strip("·• ")
    if len(text) <= max_len:
        return text
    cut = text[:max_len].rstrip("·• ")
    return cut or text[:max_len]


def _clean_segment_label(label: str, *, max_len: int = _CHAPTER_TITLE_MAX) -> str:
    """Normalize segment labels;「日期·主题」只留日期，「日期·时段」保留时段。"""
    text = (label or "").strip().strip("·• ")
    if not text:
        return ""
    if "·" in text or "•" in text:
        parts = re.split(r"[·•]", text, maxsplit=1)
        head = parts[0].strip()
        tail = parts[1].strip() if len(parts) > 1 else ""
        if head and _DATE_HEAD_RE.match(head):
            if tail in _DAYPART_TAILS:
                return _clip_title(f"{head} · {tail}", max_len)
            if tail:
                return _clip_title(head, max_len)
    return _clip_title(text, max_len)


def _day_title(d: date, *, with_year: bool) -> str:
    """D-SFP-08② · 跨年混拍册章名带年份，避免「八月后接一月」无年号。"""
    if with_year:
        return f"{d.year}年{d.month}月{d.day}日"
    return f"{d.month}月{d.day}日"


def title_for_bucket_span(span: list[str], *, with_year: bool = False) -> str | None:
    if len(span) < 2:
        return None
    d0 = date.fromisoformat(span[0])
    d1 = date.fromisoformat(span[-1])
    if d0.year != d1.year:
        return _clip_title(f"{d0.year}–{d1.year}")
    if d0.month == d1.month and d0.day == d1.day:
        return _clip_title(_day_title(d0, with_year=with_year))
    if d0.month == d1.month:
        if with_year:
            return _clip_title(f"{d0.year}年{d0.month}月{d0.day}–{d1.day}日")
        return _clip_title(f"{d0.month}月{d0.day}–{d1.day}日")
    if with_year:
        return _clip_title(f"{d0.year}年{d0.month}月{d0.day}–{d1.month}月{d1.day}日")
    return _clip_title(f"{d0.month}月{d0.day}–{d1.month}月{d1.day}日")


def _trip_needs_year_in_chapter_titles(
    meta: dict,
    assets_by_id: dict[str, dict],
    buckets: list[list[str]],
) -> bool:
    """True when meta span or bucket assets cross calendar years (D-SFP-08)."""
    start = str(meta.get("dateStart") or "").strip()[:10]
    end = str(meta.get("dateEnd") or "").strip()[:10]
    try:
        if start and end and date.fromisoformat(start).year != date.fromisoformat(end).year:
            return True
    except ValueError:
        pass
    years: set[int] = set()
    for bucket in buckets:
        for aid in bucket:
            d = parse_asset_date(assets_by_id.get(aid) or {})
            if d:
                years.add(d.year)
            if len(years) > 1:
                return True
    return False


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


# SFP D-SFP-01 · 同日后续章：时段 → segment → 同名日期（禁止「·二/·三」与「（N）」上读者面）
_ORDINAL_FACE_RE = re.compile(
    r"·\s*(?:[二三四五六七八九十]|\d+)\s*$"
)


def _same_day_followup_title(
    base: str,
    n: int,
    *,
    daypart: str | None,
    segment_label: str | None,
    used: list[str],
) -> str:
    """``n`` is 0-based count of prior same-day chapters (follow-ups have n >= 1).

    D-SFP-01/02 · OQ-SFP-01：无时段/segment 时允许与首章同名日期，靠章号区分。
    """
    del n  # retained for call-site compatibility; ordinals are no longer used
    if daypart:
        candidate = f"{base} · {daypart}"
        if candidate not in used:
            return _clip_title(candidate)
    seg = (segment_label or "").strip()
    if seg and seg != base:
        candidate = f"{base} · {seg}"
        if candidate not in used:
            return _clip_title(candidate)
    return _clip_title(base)


def is_ordinal_face_title(title: str) -> bool:
    """True when reader-facing title ends with ·二/·三/·N (SFP-01)."""
    return bool(_ORDINAL_FACE_RE.search((title or "").strip()))


def strip_ordinal_face_title(title: str) -> str:
    """Sequence Pass · drop reader-facing ·二/·三/·N suffixes."""
    from travelogue.domain.share_face_purity import (
        strip_ordinal_face_title as _strip,
    )

    return _strip(title)


def _sequence_pass_titles(titles: list[str]) -> list[str]:
    return [strip_ordinal_face_title(t) for t in titles]


_YEARLESS_DATE_FACE_RE = re.compile(r"^\d{1,2}月")


def migrate_cross_year_chapter_titles(trip: dict) -> list[str]:
    """D-SFP-08② / D-SFP-12 · prefix year onto yearless date chapter titles (idempotent)."""
    from travelogue.domain.copy_origin import is_user_protected

    trip = trip if isinstance(trip, dict) else {}
    chapters = [c for c in (trip.get("chapters") or []) if isinstance(c, dict)]
    if not chapters:
        return []
    assets = [a for a in (trip.get("assets") or []) if isinstance(a, dict) and a.get("id")]
    assets_by_id = {str(a["id"]): a for a in assets}
    buckets = [_chapter_asset_ids(ch) for ch in chapters]
    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    if not _trip_needs_year_in_chapter_titles(meta, assets_by_id, buckets):
        return []

    updated: list[str] = []
    for ch, bucket in zip(chapters, buckets, strict=False):
        if (ch.get("curation") or {}).get("isAppendix"):
            continue
        if is_user_protected(ch, "titleOrigin"):
            continue
        raw = str(ch.get("title") or "").strip()
        if not raw or "年" in raw or not _YEARLESS_DATE_FACE_RE.match(raw):
            continue
        year: int | None = None
        for aid in bucket:
            d = parse_asset_date(assets_by_id.get(str(aid)) or {})
            if d:
                year = d.year if year is None else min(year, d.year)
        if year is None:
            continue
        cleaned = _clip_title(f"{year}年{raw}")
        if cleaned and cleaned != raw:
            ch["title"] = cleaned
            updated.append(str(ch.get("id") or ""))
    return updated


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
    with_year = _trip_needs_year_in_chapter_titles(meta, assets_by_id, buckets)

    for i, bucket in enumerate(buckets):
        if not bucket:
            titles.append(f"片段{i + 1}")
            continue

        span = bucket_day_span(bucket, assets_by_id)
        # Travel-plan cities win over calendar day titles when still available.
        if plan_idx < len(plan_cities):
            titles.append(_clip_title(plan_cities[plan_idx]))
            plan_idx += 1
            continue

        # 多日章节优先日期跨度，避免多段 label 硬截断出「2月9–12日··4月4」
        if len(span) > 1:
            span_title = title_for_bucket_span(span, with_year=with_year)
            if span_title:
                titles.append(span_title)
                continue

        # D-SFI-05 · 离群排除后若只剩单日，禁止再用多段 label 把离群日期拼回章名
        # （否则会出现「6月30日·11月30日」/「2018–2020」）
        if len(span) == 1:
            d = date.fromisoformat(span[0])
            key = d.isoformat()
            n = day_seen.get(key, 0)
            day_seen[key] = n + 1
            base = _day_title(d, with_year=with_year)
            if n == 0:
                titles.append(_clip_title(base))
            else:
                daypart = _bucket_daypart(
                    [
                        aid
                        for aid in bucket
                        if not (assets_by_id.get(aid) or {}).get("timeOutlier")
                    ]
                    or bucket,
                    assets_by_id,
                )
                seg_id = bucket_segment_ids[i] if i < len(bucket_segment_ids) else ""
                seg_label = (
                    _clean_segment_label(segment_labels.get(seg_id, ""), max_len=8)
                    if seg_id and segment_labels.get(seg_id)
                    else ""
                )
                titles.append(
                    _same_day_followup_title(
                        base,
                        n,
                        daypart=daypart,
                        segment_label=seg_label or None,
                        used=titles,
                    )
                )
            continue

        all_seg = (
            bucket_segment_ids_all[i]
            if i < len(bucket_segment_ids_all)
            else []
        )
        if len(all_seg) > 1:
            labels = [
                _clean_segment_label(segment_labels[s], max_len=8)
                for s in all_seg
                if segment_labels.get(s)
            ]
            labels = [lb for lb in labels if lb]
            if labels:
                titles.append(_clip_title("·".join(labels[:2])))
                continue

        seg_id = bucket_segment_ids[i] if i < len(bucket_segment_ids) else ""
        if seg_id and segment_labels.get(seg_id):
            n = seg_day_seen.get(seg_id, 0)
            seg_day_seen[seg_id] = n + 1
            if n == 0:
                titles.append(_clean_segment_label(segment_labels[seg_id]))
                continue

        d = parse_asset_date(assets_by_id.get(bucket[0], {}))
        if d:
            key = d.isoformat()
            n = day_seen.get(key, 0)
            day_seen[key] = n + 1
            base = _day_title(d, with_year=with_year)
            if n == 0:
                titles.append(_clip_title(base))
            else:
                # SFP D-SFP-01 · 禁「日期续」与「（N）」；时段 → segment → 同名日期
                daypart = _bucket_daypart(bucket, assets_by_id)
                seg_id = bucket_segment_ids[i] if i < len(bucket_segment_ids) else ""
                seg_label = (
                    _clean_segment_label(segment_labels.get(seg_id, ""), max_len=8)
                    if seg_id and segment_labels.get(seg_id)
                    else ""
                )
                titles.append(
                    _same_day_followup_title(
                        base,
                        n,
                        daypart=daypart,
                        segment_label=seg_label or None,
                        used=titles,
                    )
                )
        elif i == 0:
            titles.append("抵达")
        elif i == len(buckets) - 1:
            titles.append("尾声")
        else:
            titles.append(_clip_title(f"{place}·{i}"))
    return _sequence_pass_titles(titles)


def _chapter_asset_ids(chapter: dict) -> list[str]:
    from travelogue.layout_contract.chapter_items import collect_screen_asset_ids

    if chapter.get("screens"):
        return list(collect_screen_asset_ids(chapter))
    ids: list[str] = []
    for item in chapter.get("items") or []:
        if item.get("type") == "media-card" and item.get("assetId"):
            ids.append(str(item["assetId"]))
        elif item.get("type") in ("media-row", "media-scroll"):
            ids.extend(str(a) for a in (item.get("assetIds") or []) if a)
    return ids


def refresh_chapter_titles_on_trip(trip: dict) -> list[str]:
    """BE-SFI-06 · regenerate chapter titles via CN rules; never overwrite titleOrigin=user."""
    from travelogue.domain.copy_origin import is_user_protected

    chapters = trip.get("chapters") or []
    if not chapters:
        return []
    assets = trip.get("assets") or []
    meta = trip.get("meta") or {}
    buckets = [_chapter_asset_ids(ch) for ch in chapters]
    # Preserve segment labels from curation when present
    bucket_segment_ids: list[str] = []
    segment_labels: dict[str, str] = {}
    for ch in chapters:
        curation = ch.get("curation") or {}
        sid = str(curation.get("segmentId") or "").strip()
        bucket_segment_ids.append(sid)
        for seg in (trip.get("curation") or {}).get("segments") or []:
            if isinstance(seg, dict) and seg.get("id") and seg.get("label"):
                segment_labels[str(seg["id"])] = str(seg["label"])

    titles = chapter_titles(
        buckets,
        assets,
        meta,
        intent=trip.get("intent"),
        bucket_segment_ids=bucket_segment_ids,
        segment_labels=segment_labels or None,
    )
    updated: list[str] = []
    for ch, title in zip(chapters, titles, strict=False):
        if (ch.get("curation") or {}).get("isAppendix"):
            continue
        if is_user_protected(ch, "titleOrigin"):
            continue
        new_title = (title or "").strip()
        if not new_title or new_title == str(ch.get("title") or "").strip():
            continue
        ch["title"] = new_title[:12]
        # Rule-based CN · not LLM invent; clear non-user origin so later refresh can update
        if str(ch.get("titleOrigin") or "") != "user":
            ch.pop("titleOrigin", None)
        updated.append(f"chapters[{ch.get('index')}].title")
    return updated
