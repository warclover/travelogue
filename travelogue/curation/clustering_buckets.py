"""Curate bucket planning from curation.clustering segments (Phase 3 §8.1)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from travelogue.config import AppConfig
from travelogue.curation.bucket_planning import (
    group_assets_by_day,
    group_assets_by_segments,
    normalize_bucket_counts,
)
from travelogue.curation.cluster_run_sort import sort_bucket_asset_ids_for_clustering
from travelogue.curation.time_segments import TimeSegment, parse_asset_date


def should_use_clustering_buckets(trip: dict, cfg: AppConfig) -> bool:
    if cfg.clustering.enabled == "false":
        return False
    if cfg.clustering.segment_curate_mode == "date_fallback":
        return False
    clustering = (trip.get("curation") or {}).get("clustering") or {}
    if clustering.get("segmentMode") != "geo_event":
        return False
    segments = clustering.get("segments") or []
    return bool(segments)


def _parse_segment_dates(seg: dict[str, Any]) -> tuple[date, date]:
    start = date.fromisoformat(str(seg["startDate"]))
    end = date.fromisoformat(str(seg["endDate"]))
    return start, end


def _segment_time_gap_hours(a: dict[str, Any], b: dict[str, Any]) -> float:
    end = datetime.fromisoformat(str(a["endDate"]) + "T23:59:59")
    start = datetime.fromisoformat(str(b["startDate"]) + "T00:00:00")
    return max(0.0, (start - end).total_seconds() / 3600.0)


def merge_small_geo_events(
    segments: list[dict[str, Any]],
    *,
    min_photos: int = 15,
    max_gap_hours: float = 4.0,
) -> list[dict[str, Any]]:
    """PRD §8.1 step 2: merge adjacent small events."""
    if len(segments) <= 1:
        return [dict(s) for s in segments]
    out = [dict(segments[0])]
    for seg in segments[1:]:
        prev = out[-1]
        prev_count = len(prev.get("assetIds") or [])
        cur_count = len(seg.get("assetIds") or [])
        gap = _segment_time_gap_hours(prev, seg)
        if prev_count < min_photos and cur_count < min_photos and gap < max_gap_hours:
            merged_ids = list(dict.fromkeys((prev.get("assetIds") or []) + (seg.get("assetIds") or [])))
            prev["assetIds"] = merged_ids
            _, prev_end = _parse_segment_dates(prev)
            cur_start, cur_end = _parse_segment_dates(seg)
            prev["startDate"] = min(prev_end, cur_start).isoformat()
            prev["endDate"] = max(prev_end, cur_end).isoformat()
            if seg.get("location") and not prev.get("location"):
                prev["location"] = seg["location"]
        else:
            out.append(dict(seg))
    return out


def cap_geo_segments(
    segments: list[dict[str, Any]],
    *,
    min_chapters: int = 3,
    max_chapters: int = 5,
) -> list[dict[str, Any]]:
    """PRD §8.1 step 3–4: cap to 3–5 segments; merge smallest adjacent pairs."""
    segs = [dict(s) for s in segments]
    while len(segs) > max_chapters:
        best_i = 0
        best_size = float("inf")
        for i in range(len(segs) - 1):
            size = len(segs[i].get("assetIds") or []) + len(segs[i + 1].get("assetIds") or [])
            if size < best_size:
                best_size = size
                best_i = i
        left, right = segs[best_i], segs[best_i + 1]
        left["assetIds"] = list(
            dict.fromkeys((left.get("assetIds") or []) + (right.get("assetIds") or []))
        )
        l0, l1 = _parse_segment_dates(left)
        r0, r1 = _parse_segment_dates(right)
        left["startDate"] = min(l0, r0).isoformat()
        left["endDate"] = max(l1, r1).isoformat()
        del segs[best_i + 1]

    if len(segs) >= min_chapters:
        for i, seg in enumerate(segs, start=1):
            seg["id"] = seg.get("id") or f"evt-{i:02d}"
        return segs

    # Fewer than min_chapters: split largest segment by day buckets.
    flat_assets: list[str] = []
    for seg in segs:
        flat_assets.extend(seg.get("assetIds") or [])
    if not flat_assets:
        return segs
    return _split_segments_by_day(segs, min_chapters=min_chapters, max_chapters=max_chapters)


def _split_segments_by_day(
    segments: list[dict[str, Any]],
    *,
    min_chapters: int,
    max_chapters: int,
) -> list[dict[str, Any]]:
    assets: list[dict] = []
    location = segments[0].get("location") if segments else None
    for seg in segments:
        start, _ = _parse_segment_dates(seg)
        for aid in seg.get("assetIds") or []:
            assets.append({"id": aid, "takenAt": f"{start.isoformat()}T12:00:00Z"})

    day_buckets = group_assets_by_day(assets, cover_id="")
    out: list[dict[str, Any]] = []
    for i, bucket in enumerate(day_buckets, start=1):
        if not bucket:
            continue
        by_id = {a["id"]: a for a in assets}
        dates = sorted(
            d
            for aid in bucket
            if (d := parse_asset_date(by_id.get(aid, {})))
        )
        d0 = dates[0] if dates else date.today()
        d1 = dates[-1] if dates else d0
        out.append(
            {
                "id": f"evt-{i:02d}",
                "name": f"段{i}",
                "startDate": d0.isoformat(),
                "endDate": d1.isoformat(),
                "location": location,
                "assetIds": bucket,
            }
        )

    while len(out) > max_chapters and len(out) > 1:
        out[0]["assetIds"] = list(dict.fromkeys(out[0]["assetIds"] + out[1]["assetIds"]))
        d0, d1 = _parse_segment_dates(out[0])
        r0, r1 = _parse_segment_dates(out[1])
        out[0]["startDate"] = min(d0, r0).isoformat()
        out[0]["endDate"] = max(d1, r1).isoformat()
        del out[1]

    if len(out) < min_chapters and len(out) == 1 and len(out[0].get("assetIds") or []) >= min_chapters:
        bucket = out[0]["assetIds"]
        chunk = max(1, len(bucket) // min_chapters)
        split: list[dict[str, Any]] = []
        for i in range(0, len(bucket), chunk):
            part = bucket[i : i + chunk]
            if not part:
                continue
            split.append(
                {
                    "id": f"evt-{len(split) + 1:02d}",
                    "name": f"段{len(split) + 1}",
                    "startDate": out[0]["startDate"],
                    "endDate": out[0]["endDate"],
                    "location": location,
                    "assetIds": part,
                }
            )
        if len(split) > max_chapters:
            # Floor-division can leave a remainder bucket; merge any overflow
            # into the last surviving segment so assets are never dropped.
            tail_ids: list[str] = []
            for extra in split[max_chapters:]:
                tail_ids.extend(extra.get("assetIds") or [])
            split = split[:max_chapters]
            if tail_ids and split:
                merged_ids = list(
                    dict.fromkeys((split[-1].get("assetIds") or []) + tail_ids)
                )
                split[-1]["assetIds"] = merged_ids
        out = split

    return out if out else segments


def _date_distance_to_segment(asset_date: date, seg: dict[str, Any]) -> int:
    start, end = _parse_segment_dates(seg)
    if start <= asset_date <= end:
        return 0
    if asset_date < start:
        return (start - asset_date).days
    return (asset_date - end).days


def recover_uncovered_geo_bucket_assets(
    segments: list[dict[str, Any]],
    buckets: list[list[str]],
    bucket_segment_ids: list[str],
    layout_assets: list[dict],
    cover_id: str,
) -> tuple[list[dict[str, Any]], list[list[str]], list[str], list[str]]:
    """Assign layout assets missing from geo buckets to the nearest segment by date."""
    if not buckets:
        return segments, buckets, bucket_segment_ids, []

    by_id = {a["id"]: a for a in layout_assets}
    planned = {aid for bucket in buckets for aid in bucket}
    uncovered = [
        a
        for a in layout_assets
        if a.get("id")
        and a["id"] != cover_id
        and a["id"] not in planned
        and a.get("layoutEligible", True) is not False
    ]
    if not uncovered:
        return segments, buckets, bucket_segment_ids, []

    seg_by_id = {str(seg.get("id") or ""): seg for seg in segments}
    recovered: list[str] = []

    for asset in sorted(uncovered, key=lambda a: a.get("takenAt") or ""):
        aid = str(asset["id"])
        asset_date = parse_asset_date(asset)
        best_bucket = 0
        if asset_date is not None and bucket_segment_ids:
            best_dist: int | None = None
            for i, seg_id in enumerate(bucket_segment_ids):
                seg = seg_by_id.get(seg_id)
                if not seg:
                    continue
                dist = _date_distance_to_segment(asset_date, seg)
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best_bucket = i
        else:
            best_bucket = len(buckets) - 1

        buckets[best_bucket].append(aid)
        buckets[best_bucket].sort(key=lambda x: by_id[x].get("takenAt") or "")
        recovered.append(aid)

        seg_id = bucket_segment_ids[best_bucket]
        seg = seg_by_id.get(seg_id)
        if seg is not None:
            seg["assetIds"] = list(dict.fromkeys((seg.get("assetIds") or []) + [aid]))
            if asset_date is not None:
                start, end = _parse_segment_dates(seg)
                seg["startDate"] = min(start, asset_date).isoformat()
                seg["endDate"] = max(end, asset_date).isoformat()

    return segments, buckets, bucket_segment_ids, recovered


def segments_to_buckets(
    segments: list[dict[str, Any]],
    assets: list[dict],
    cover_id: str,
) -> tuple[list[list[str]], list[str]]:
    by_id = {a["id"]: a for a in assets}
    buckets: list[list[str]] = []
    seg_ids: list[str] = []
    for seg in segments:
        ids = [aid for aid in (seg.get("assetIds") or []) if aid in by_id and aid != cover_id]
        if not ids:
            continue
        ids.sort(key=lambda x: by_id[x].get("takenAt") or "")
        buckets.append(ids)
        seg_ids.append(str(seg.get("id") or ""))
    return buckets, seg_ids


def build_buckets_from_clustering(
    trip: dict,
    layout_assets: list[dict],
    cover_id: str,
    meta: dict,
    *,
    cfg: AppConfig,
    min_bucket_size: int = 3,
) -> tuple[list[list[str]], list[str], list[list[str]], list[TimeSegment]]:
    clustering = (trip.get("curation") or {}).get("clustering") or {}
    raw_segments = [dict(s) for s in (clustering.get("segments") or [])]
    segments = merge_small_geo_events(raw_segments)
    segments = cap_geo_segments(segments)
    buckets, bucket_segment_ids = segments_to_buckets(segments, layout_assets, cover_id)
    segments, buckets, bucket_segment_ids, recovered = recover_uncovered_geo_bucket_assets(
        segments,
        buckets,
        bucket_segment_ids,
        layout_assets,
        cover_id,
    )
    if recovered:
        meta.setdefault("geoBucketRecovery", {})["recoveredAssetIds"] = recovered

    if not buckets:
        return group_assets_by_segments(
            layout_assets,
            cover_id,
            meta,
            intent=trip.get("intent"),
            segment_gap_days=cfg.curate.segment_gap_days,
            city_gap_days=cfg.curate.city_gap_days,
            min_bucket_size=min_bucket_size,
        )

    by_id = {a["id"]: a for a in layout_assets}
    norm = normalize_bucket_counts(
        buckets,
        bucket_segment_ids,
        min_bucket_size=min_bucket_size,
    )
    run_aware = cfg.clustering.scene_cluster_mode == "run_aware"
    for i, bucket in enumerate(norm.buckets):
        norm.buckets[i] = sort_bucket_asset_ids_for_clustering(
            bucket, by_id, run_aware=run_aware
        )

    time_segments: list[TimeSegment] = []
    for seg in segments:
        start, end = _parse_segment_dates(seg)
        ids = [aid for aid in (seg.get("assetIds") or []) if aid in by_id]
        if not ids:
            continue
        time_segments.append(
            TimeSegment(
                id=str(seg.get("id") or ""),
                label=str(seg.get("name") or "")[:24],
                date_start=start,
                date_end=end,
                asset_ids=ids,
                places=[seg["location"]] if seg.get("location") else [],
            )
        )

    return norm.buckets, norm.primary_segment_ids, norm.segment_ids_per_bucket, time_segments
