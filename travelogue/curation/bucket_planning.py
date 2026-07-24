"""Day/segment bucket planning for curate (chapter count caps via manifest)."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import NamedTuple

from travelogue.curation.curate_scoring import sort_bucket_asset_ids
from travelogue.curation.time_segments import cluster_time_segments, parse_asset_date
from travelogue.domain.copy_subject import narrative_copy_subject, user_place_explicit


class NormalizedBuckets(NamedTuple):
    buckets: list[list[str]]
    primary_segment_ids: list[str]
    segment_ids_per_bucket: list[list[str]]


def bucket_day_span(bucket: list[str], assets_by_id: dict[str, dict]) -> list[str]:
    """Day span for titles; excludes timeOutlier assets (D-SFI-05)."""
    dates = sorted(
        {
            d
            for aid in bucket
            if not (assets_by_id.get(aid) or {}).get("timeOutlier")
            and (d := parse_asset_date(assets_by_id.get(aid, {})))
        }
    )
    return [d.isoformat() for d in dates]


def group_assets_by_day(assets: list[dict], cover_id: str) -> list[list[str]]:
    body = [a for a in assets if a["id"] != cover_id]
    if len(body) < 4:
        body = list(assets)

    by_day: dict[date, list[str]] = defaultdict(list)
    no_date: list[str] = []
    for a in sorted(body, key=lambda x: x.get("takenAt") or ""):
        d = parse_asset_date(a)
        if d:
            by_day[d].append(a["id"])
        else:
            no_date.append(a["id"])

    buckets: list[list[str]] = []
    if no_date:
        buckets.append(no_date)
    buckets.extend([by_day[k] for k in sorted(by_day)])

    if not buckets:
        return [[a["id"] for a in body]]

    merged = merge_small_buckets(buckets, min_size=3)
    return _sort_all_buckets(merged, {a["id"]: a for a in assets})


def _sort_all_buckets(buckets: list[list[str]], assets_by_id: dict[str, dict]) -> list[list[str]]:
    return [sort_bucket_asset_ids(b, assets_by_id) for b in buckets]


def _merge_adjacent_to_chapter_limit(
    out: list[list[str]],
    seg: list[str],
    seg_all: list[list[str]],
    max_c: int,
) -> tuple[list[list[str]], list[str], list[list[str]]]:
    """Merge adjacent buckets until count <= max_c; prefer same-segment pairs."""
    while len(out) > max_c:
        best_i = -1
        best_cost = float("inf")
        for i in range(len(out) - 1):
            same_seg = bool(seg[i]) and seg[i] == seg[i + 1]
            cost = (0 if same_seg else 1000) + len(out[i]) + len(out[i + 1])
            if cost < best_cost:
                best_cost = cost
                best_i = i
        if best_i < 0:
            break
        i = best_i
        right_n = len(out[i + 1])
        left_n = len(out[i])
        out[i].extend(out[i + 1])
        seg_all[i] = _merge_segment_lists(seg_all[i], seg_all[i + 1])
        if right_n > left_n and seg[i + 1]:
            seg[i] = seg[i + 1]
        del out[i + 1]
        del seg[i + 1]
        del seg_all[i + 1]
    return out, seg, seg_all


def _align_segment_ids(segment_ids: list[str] | None, count: int) -> list[str]:
    seg = list(segment_ids or [])
    if len(seg) < count:
        seg.extend([""] * (count - len(seg)))
    return seg[:count]


def _primary_segment_in_chunk(
    out: list[list[str]],
    seg: list[str],
    start: int,
    end: int,
) -> str:
    weights: dict[str, int] = defaultdict(int)
    for j in range(start, end):
        sid = seg[j] if j < len(seg) else ""
        if sid:
            weights[sid] += len(out[j])
    if not weights:
        return seg[start] if start < len(seg) else ""
    return max(weights, key=weights.get)


def _segments_in_chunk(seg: list[str], start: int, end: int) -> list[str]:
    seen: list[str] = []
    for j in range(start, end):
        sid = seg[j] if j < len(seg) else ""
        if sid and sid not in seen:
            seen.append(sid)
    return seen


def effective_balance_min_size(
    buckets: list[list[str]],
    *,
    min_bucket_size: int,
    balance_ratio: float,
) -> int:
    """Adaptive floor: merge day buckets below max(min_size, ratio × average)."""
    if not buckets:
        return min_bucket_size
    total = sum(len(b) for b in buckets)
    avg = total / len(buckets)
    return max(min_bucket_size, int(avg * balance_ratio))


def normalize_bucket_counts(
    buckets: list[list[str]],
    segment_ids: list[str] | None = None,
    *,
    min_chapters: int | None = None,
    max_chapters: int | None = None,
    min_bucket_size: int = 3,
    chapter_balance_enabled: bool = True,
    chapter_balance_ratio: float = 0.55,
    assets_by_id: dict[str, dict] | None = None,
    gap_days: int = 14,
) -> NormalizedBuckets:
    """Merge day buckets to fit manifest chapter limits; preserve segment metadata."""
    from travelogue.manifest_limits import chapter_limits

    min_c, max_c = chapter_limits()
    if min_chapters is not None:
        min_c = min_chapters
    if max_chapters is not None:
        max_c = max_chapters

    out = [list(b) for b in buckets if b]
    if not out:
        return NormalizedBuckets([], [], [])

    seg = _align_segment_ids(segment_ids, len(out))
    seg_all: list[list[str]] = [[s] if s else [] for s in seg]

    n = len(out)
    if n > max_c:
        out, seg, seg_all = _merge_adjacent_to_chapter_limit(out, seg, seg_all, max_c)

    merge_min = (
        effective_balance_min_size(
            out,
            min_bucket_size=min_bucket_size,
            balance_ratio=chapter_balance_ratio,
        )
        if chapter_balance_enabled
        else min_bucket_size
    )
    out, seg, seg_all = merge_small_buckets_with_segments(
        out,
        seg,
        seg_all,
        min_size=merge_min,
        assets_by_id=assets_by_id,
        gap_days=gap_days,
    )

    if len(out) < min_c:
        flat_count = sum(len(b) for b in out)
        target = (
            min_c
            if flat_count < 9
            else min(max_c, max(min_c, len(out) or min_c))
        )
        while len(out) < target:
            largest_i = max(range(len(out)), key=lambda i: len(out[i]))
            bucket = out[largest_i]
            if len(bucket) < 2:
                break
            mid = len(bucket) // 2
            out[largest_i] = bucket[:mid]
            out.insert(largest_i + 1, bucket[mid:])
            split_seg = seg[largest_i]
            seg.insert(largest_i + 1, split_seg)
            split_all = list(seg_all[largest_i])
            seg_all.insert(largest_i + 1, split_all)

    # SFP D-SFP-02④ · 弱桶合并：同日后续桶 len≤2 且无 daypart/segment → 并入前桶
    if assets_by_id:
        out, seg, seg_all = merge_weak_same_day_followups(
            out, seg, seg_all, assets_by_id=assets_by_id
        )

    return NormalizedBuckets(out, seg, seg_all)


def merge_weak_same_day_followups(
    buckets: list[list[str]],
    segment_ids: list[str],
    segment_ids_all: list[list[str]],
    *,
    assets_by_id: dict[str, dict],
) -> tuple[list[list[str]], list[str], list[list[str]]]:
    """OQ-SFP-01 · merge tiny same-day follow-ups that lack daypart/segment labels."""
    from travelogue.curation.chapter_titles import _bucket_daypart

    out = [list(b) for b in buckets if b]
    seg = _align_segment_ids(segment_ids, len(out))
    seg_all = list(segment_ids_all or [])
    while len(seg_all) < len(out):
        seg_all.append([])
    seg_all = [list(seg_all[i]) if i < len(seg_all) else [] for i in range(len(out))]

    i = 1
    while i < len(out):
        cur = out[i]
        if len(cur) > 2:
            i += 1
            continue
        prev = out[i - 1]
        span_prev = bucket_day_span(prev, assets_by_id)
        span_cur = bucket_day_span(cur, assets_by_id)
        if not span_prev or not span_cur or span_prev[-1] != span_cur[0]:
            i += 1
            continue
        # OQ-SFP-01 · 有独立 segment，或 daypart 能消歧（与前桶不同）→ 不合并
        cur_segs = [s for s in (seg_all[i] or ([seg[i]] if seg[i] else [])) if s]
        prev_segs = [s for s in (seg_all[i - 1] or ([seg[i - 1]] if seg[i - 1] else [])) if s]
        if cur_segs and (not prev_segs or set(cur_segs) - set(prev_segs)):
            i += 1
            continue
        cur_dp = _bucket_daypart(cur, assets_by_id)
        prev_dp = _bucket_daypart(prev, assets_by_id)
        if cur_dp and cur_dp != prev_dp:
            i += 1
            continue
        out[i - 1].extend(out[i])
        seg_all[i - 1] = _merge_segment_lists(seg_all[i - 1], seg_all[i])
        if not seg[i - 1] and seg[i]:
            seg[i - 1] = seg[i]
        del out[i]
        del seg[i]
        del seg_all[i]
        # stay at i to re-check next follow-up against merged prev
    return out, seg, seg_all

def sort_buckets_in_place(buckets: list[list[str]], assets_by_id: dict[str, dict]) -> None:
    for i, bucket in enumerate(buckets):
        buckets[i] = sort_bucket_asset_ids(bucket, assets_by_id)


def cap_book_buckets(
    buckets: list[list[str]],
    bucket_segment_ids: list[str] | None = None,
    *,
    min_chapters: int | None = None,
    max_chapters: int | None = None,
) -> tuple[list[list[str]], list[str]]:
    """Backward-compatible wrapper (primary segment ids only)."""
    norm = normalize_bucket_counts(
        buckets,
        bucket_segment_ids,
        min_chapters=min_chapters,
        max_chapters=max_chapters,
    )
    return norm.buckets, norm.primary_segment_ids


def _merge_segment_lists(a: list[str], b: list[str]) -> list[str]:
    out = list(a)
    for sid in b:
        if sid and sid not in out:
            out.append(sid)
    return out


def merge_small_buckets(buckets: list[list[str]], *, min_size: int = 3) -> list[list[str]]:
    """Merge chapters with fewer than min_size photos into neighbors (preserve day order)."""
    merged, _, _ = merge_small_buckets_with_segments(
        buckets,
        [""] * len(buckets),
        [[""]] * len(buckets),
        min_size=min_size,
    )
    return merged


def merge_small_buckets_with_segments(
    buckets: list[list[str]],
    segment_ids: list[str],
    segment_ids_all: list[list[str]] | None = None,
    *,
    min_size: int = 3,
    assets_by_id: dict[str, dict] | None = None,
    gap_days: int = 14,
) -> tuple[list[list[str]], list[str], list[list[str]]]:
    """Like merge_small_buckets; keeps primary and full segment lists per bucket.

    BE-SFI-07 · 禁止把跨大 gap 的离群小桶并回邻章（仙本那根因）。
    """
    from travelogue.curation.time_outlier import bucket_gap_days

    out = [list(b) for b in buckets if b]
    seg = _align_segment_ids(segment_ids, len(out))
    seg_all = list(segment_ids_all or [])
    if len(seg_all) < len(out):
        seg_all.extend([[] for _ in range(len(out) - len(seg_all))])
    seg_all = [
        list(seg_all[i]) if i < len(seg_all) and seg_all[i] else ([seg[i]] if seg[i] else [])
        for i in range(len(out))
    ]
    if not out:
        return out, seg, seg_all

    def _can_merge(a: int, b: int) -> bool:
        if not assets_by_id:
            return True
        gap = bucket_gap_days(out[a], out[b], assets_by_id)
        if gap is None:
            return True
        return gap <= gap_days

    blocked: set[int] = set()
    while True:
        small = [i for i, b in enumerate(out) if len(b) < min_size and i not in blocked]
        if not small or len(out) <= 1:
            break
        idx = min(small, key=lambda i: len(out[i]))
        if idx > 0 and _can_merge(idx - 1, idx):
            left_n, right_n = len(out[idx - 1]), len(out[idx])
            out[idx - 1].extend(out[idx])
            seg_all[idx - 1] = _merge_segment_lists(seg_all[idx - 1], seg_all[idx])
            if right_n > left_n and seg[idx]:
                seg[idx - 1] = seg[idx]
            del out[idx]
            del seg[idx]
            del seg_all[idx]
            blocked = {i if i < idx else i - 1 for i in blocked if i != idx}
        elif idx == 0 and len(out) > 1 and _can_merge(0, 1):
            left_n, right_n = len(out[0]), len(out[1])
            out[0].extend(out[1])
            seg_all[0] = _merge_segment_lists(seg_all[0], seg_all[1])
            if right_n > left_n and seg[1]:
                seg[0] = seg[1]
            del out[1]
            del seg[1]
            del seg_all[1]
            blocked = {i if i < 1 else i - 1 for i in blocked if i != 1}
        else:
            # Hard assert: leave outlier small bucket alone
            blocked.add(idx)
            if len(blocked) >= len(out):
                break
    for i, sid in enumerate(seg):
        if sid and sid not in seg_all[i]:
            seg_all[i].insert(0, sid)
    return out, seg, seg_all


def group_assets_by_segments(
    layout_assets: list[dict],
    cover_id: str,
    meta: dict,
    *,
    intent: dict | None = None,
    segment_gap_days: int = 14,
    city_gap_days: int = 3,
    min_bucket_size: int = 3,
    chapter_balance_enabled: bool = True,
    chapter_balance_ratio: float = 0.55,
) -> tuple[list[list[str]], list[str], list[list[str]], list]:
    """Segment cluster → per-segment day buckets → flat chapter bucket list."""
    places = meta.get("places") or []
    explicit_place = str(places[0]).strip() if places else None
    place = narrative_copy_subject(meta, intent=intent, assets=layout_assets)
    by_id = {a["id"]: a for a in layout_assets}
    segments = cluster_time_segments(
        layout_assets,
        gap_days=segment_gap_days,
        city_gap_days=city_gap_days,
        place=place,
        explicit_place=explicit_place if user_place_explicit(meta, intent=intent) else None,
    )

    all_buckets: list[list[str]] = []
    bucket_segment_ids: list[str] = []

    for seg in segments:
        seg_assets = [by_id[aid] for aid in seg.asset_ids if aid in by_id]
        if not seg_assets:
            continue
        local_cover = cover_id if cover_id in {a["id"] for a in seg_assets} else ""
        seg_buckets = group_assets_by_day(seg_assets, local_cover)
        for b in seg_buckets:
            all_buckets.append(b)
            bucket_segment_ids.append(seg.id)

    if not all_buckets:
        all_buckets = group_assets_by_day(layout_assets, cover_id)
        bucket_segment_ids = [""] * len(all_buckets)
        segments = []

    norm = normalize_bucket_counts(
        all_buckets,
        bucket_segment_ids,
        min_bucket_size=min_bucket_size,
        chapter_balance_enabled=chapter_balance_enabled,
        chapter_balance_ratio=chapter_balance_ratio,
        assets_by_id=by_id,
        gap_days=segment_gap_days,
    )
    sort_buckets_in_place(norm.buckets, by_id)
    return norm.buckets, norm.primary_segment_ids, norm.segment_ids_per_bucket, segments
