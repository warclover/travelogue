"""Geo/time stay detection for Phase 3 Curate clustering (P3-Lite)."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from travelogue.config import GeoClusterConfig
from travelogue.curation.time_segments import asset_city, parse_asset_date


@dataclass
class GeoSegment:
    id: str
    name: str
    start_date: date
    end_date: date
    location: str | None
    asset_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": self.id,
            "name": self.name[:48],
            "startDate": self.start_date.isoformat(),
            "endDate": self.end_date.isoformat(),
            "assetIds": list(self.asset_ids),
        }
        if self.location:
            out["location"] = self.location[:32]
        return out


def _parse_asset_datetime(asset: dict) -> datetime | None:
    raw = asset.get("takenAt")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _asset_geo(asset: dict) -> tuple[float, float] | None:
    geo = asset.get("geo")
    if not isinstance(geo, dict):
        return None
    try:
        lat = float(geo["lat"])
        lon = float(geo["lon"])
    except (KeyError, TypeError, ValueError):
        return None
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return None
    if abs(lat) < 1e-6 and abs(lon) < 1e-6:
        return None
    return lat, lon


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlamb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlamb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def gps_coverage_ratio(assets: list[dict]) -> float:
    if not assets:
        return 0.0
    with_gps = sum(1 for a in assets if _asset_geo(a) is not None)
    return with_gps / len(assets)


def _segment_name(
    start: date,
    end: date,
    location: str | None,
    *,
    index: int,
    total: int,
    suppress_geo: bool = False,
    label_place: str | None = None,
) -> str:
    if suppress_geo:
        place = (label_place or "").strip()[:16]
    else:
        place = (location or "旅途").strip()[:16]

    if suppress_geo and not place:
        if start.year != end.year:
            base = f"{start.year}–{end.year}"
        elif start.month != end.month:
            base = f"{start.month}月–{end.month}月"
        elif start != end:
            base = f"{start.month}月{start.day}–{end.day}日"
        else:
            base = f"{start.month}月{start.day}日"
    elif start.year != end.year:
        base = f"{start.year}–{end.year}·{place}"
    elif start.month != end.month:
        base = f"{start.month}月–{end.month}月·{place}"
    elif start != end:
        base = f"{start.month}月{start.day}–{end.day}日·{place}"
    else:
        base = f"{start.month}月{start.day}日·{place}"
    if total > 1 and len(base) <= 10:
        base = f"{base}·{index}"
    return base[:48]


def _dominant_location(assets: list[dict]) -> str | None:
    cities = [c for a in assets if (c := asset_city(a))]
    if not cities:
        return None
    return Counter(cities).most_common(1)[0][0]


def _adaptive_gap_threshold_hours(
    timestamps: list[datetime],
    *,
    fallback_hours: float,
) -> float:
    """Pick a split threshold from the gap distribution (Phase 6 P6-B1)."""
    if len(timestamps) < 4:
        return fallback_hours

    gaps = sorted(
        (timestamps[i + 1] - timestamps[i]).total_seconds() / 3600.0
        for i in range(len(timestamps) - 1)
    )
    if not gaps:
        return fallback_hours

    n = len(gaps)
    p75 = gaps[int(n * 0.75)]
    p90 = gaps[int(n * 0.90)]

    if p90 > max(p75 * 3, 1e-6):
        # Bimodal gap distribution: prefer the upper mode (inter-session / lunch
        # breaks) rather than the dense within-session gaps near p75.
        upper = [g for g in gaps if g >= p90 * 0.85]
        if upper:
            return upper[len(upper) // 2]
        candidates = [g for g in gaps if p75 <= g <= p90]
        if candidates:
            return candidates[-1]

    return fallback_hours


def _resolve_gap_hours(
    gps_rows: list[tuple[datetime, str, dict, tuple[float, float]]],
    *,
    cfg: GeoClusterConfig,
    event_time_gap_hours: float | None,
) -> tuple[float, str]:
    """Return (gap_hours, gap_mode) with fail-open to fixed fallback."""
    fallback = (
        event_time_gap_hours
        if event_time_gap_hours is not None
        else cfg.event_time_gap_hours
    )
    mode = cfg.event_gap_mode
    if mode != "auto":
        return fallback, "fixed"

    try:
        timestamps = [row[0] for row in gps_rows]
        adaptive = _adaptive_gap_threshold_hours(timestamps, fallback_hours=fallback)
        if adaptive <= 0 or adaptive > 168:
            return fallback, "fixed"
        return adaptive, "auto"
    except Exception:
        return fallback, "fixed"


def _time_split_groups(
    rows: list[tuple[datetime, str, dict, tuple[float, float]]],
    *,
    gap_hours: float,
) -> list[list[tuple[datetime, str, dict, tuple[float, float]]]]:
    if not rows:
        return []
    groups: list[list[tuple[datetime, str, dict, tuple[float, float]]]] = [[rows[0]]]
    gap = timedelta(hours=gap_hours)
    for row in rows[1:]:
        prev_dt = groups[-1][-1][0]
        if row[0] - prev_dt > gap:
            groups.append([row])
        else:
            groups[-1].append(row)
    return groups


def _geo_split_group(
    group: list[tuple[datetime, str, dict, tuple[float, float]]],
    *,
    proximity_km: float,
) -> list[list[tuple[datetime, str, dict, tuple[float, float]]]]:
    if len(group) <= 1:
        return [group]
    chunks: list[list[tuple[datetime, str, dict, tuple[float, float]]]] = [[group[0]]]
    for row in group[1:]:
        prev = chunks[-1][-1]
        dist = haversine_km(prev[3][0], prev[3][1], row[3][0], row[3][1])
        if dist > proximity_km:
            chunks.append([row])
        else:
            chunks[-1].append(row)
    return chunks


def _merge_event_chunks(
    chunks: list[list[tuple[datetime, str, dict, tuple[float, float]]]],
    *,
    merge_time_gap_hours: float,
    merge_location_km: float,
    max_event_days: int,
) -> list[list[tuple[datetime, str, dict, tuple[float, float]]]]:
    if len(chunks) <= 1:
        return chunks
    merged: list[list[tuple[datetime, str, dict, tuple[float, float]]]] = [list(chunks[0])]
    merge_gap = timedelta(hours=merge_time_gap_hours)
    for chunk in chunks[1:]:
        prev = merged[-1]
        time_gap = chunk[0][0] - prev[-1][0]
        dist = haversine_km(prev[-1][3][0], prev[-1][3][1], chunk[0][3][0], chunk[0][3][1])
        span_days = (chunk[-1][0].date() - prev[0][0].date()).days + 1
        if time_gap <= merge_gap and dist <= merge_location_km and span_days <= max_event_days:
            prev.extend(chunk)
        else:
            merged.append(list(chunk))
    return merged


def _rows_to_segment(
    rows: list[tuple[datetime, str, dict, tuple[float, float] | None]],
    *,
    index: int,
    total: int,
    suppress_geo: bool = False,
    label_place: str | None = None,
) -> GeoSegment | None:
    if not rows:
        return None
    assets = [r[2] for r in rows]
    start = rows[0][0].date()
    end = rows[-1][0].date()
    location = _dominant_location(assets)
    return GeoSegment(
        id=f"evt-{index:02d}",
        name=_segment_name(
            start,
            end,
            location,
            index=index,
            total=total,
            suppress_geo=suppress_geo,
            label_place=label_place,
        ),
        start_date=start,
        end_date=end,
        location=location,
        asset_ids=[r[1] for r in rows],
    )


def detect_geo_events(
    assets: list[dict],
    *,
    cfg: GeoClusterConfig | None = None,
    event_time_gap_hours: float | None = None,
    min_photos_per_event: int | None = None,
    location_proximity_km: float | None = None,
    merge_time_gap_hours: float | None = None,
    merge_location_km: float | None = None,
    max_event_days: int | None = None,
    meta: dict | None = None,
    intent: dict | None = None,
) -> tuple[list[GeoSegment], dict[str, Any]]:
    """Detect stay/event segments from GPS + takenAt (Recasa-inspired rules).

    Returns (segments, segmentation_meta) where meta includes gapMode/thresholdHours.
    """
    from travelogue.services.copy_subject import (
        narrative_copy_subject,
        suppress_chapter_geo_places,
    )

    suppress_geo = False
    label_place: str | None = None
    if meta is not None:
        suppress_geo = suppress_chapter_geo_places(meta, intent=intent, assets=assets)
        if suppress_geo:
            label_place = narrative_copy_subject(meta, intent=intent, assets=assets)

    geo_cfg = cfg or GeoClusterConfig()
    gap_meta: dict[str, Any] = {"gapMode": geo_cfg.event_gap_mode, "thresholdHours": geo_cfg.event_time_gap_hours}
    min_photos = (
        min_photos_per_event if min_photos_per_event is not None else geo_cfg.min_photos_per_event
    )
    prox_km = (
        location_proximity_km if location_proximity_km is not None else geo_cfg.location_proximity_km
    )
    merge_h = (
        merge_time_gap_hours if merge_time_gap_hours is not None else geo_cfg.merge_time_gap_hours
    )
    merge_km = merge_location_km if merge_location_km is not None else geo_cfg.merge_location_km
    max_days = max_event_days if max_event_days is not None else geo_cfg.max_event_days

    gps_rows: list[tuple[datetime, str, dict, tuple[float, float]]] = []
    for asset in assets:
        dt = _parse_asset_datetime(asset)
        geo = _asset_geo(asset)
        if dt is None or geo is None:
            continue
        gps_rows.append((dt, asset["id"], asset, geo))
    if not gps_rows:
        return [], gap_meta

    gps_rows.sort(key=lambda r: r[0])
    gap_h, gap_mode_used = _resolve_gap_hours(
        gps_rows,
        cfg=geo_cfg,
        event_time_gap_hours=event_time_gap_hours,
    )
    gap_meta = {"gapMode": gap_mode_used, "thresholdHours": round(gap_h, 3)}
    time_groups = _time_split_groups(gps_rows, gap_hours=gap_h)
    raw_chunks: list[list[tuple[datetime, str, dict, tuple[float, float]]]] = []
    for tg in time_groups:
        raw_chunks.extend(_geo_split_group(tg, proximity_km=prox_km))
    merged_chunks = _merge_event_chunks(
        raw_chunks,
        merge_time_gap_hours=merge_h,
        merge_location_km=merge_km,
        max_event_days=max_days,
    )

    segments: list[GeoSegment] = []
    orphan_rows: list[tuple[datetime, str, dict, tuple[float, float] | None]] = []
    for chunk in merged_chunks:
        if len(chunk) >= min_photos:
            seg = _rows_to_segment(
                chunk,
                index=len(segments) + 1,
                total=max(1, len(merged_chunks)),
                suppress_geo=suppress_geo,
                label_place=label_place,
            )
            if seg is not None:
                segments.append(seg)
        else:
            orphan_rows.extend(chunk)

    if orphan_rows and segments:
        for row in orphan_rows:
            dt, aid, asset, _ = row
            d = dt.date()

            def _date_segment_distance(seg: GeoSegment) -> int:
                if seg.start_date <= d <= seg.end_date:
                    return 0
                return min(
                    abs((d - seg.start_date).days),
                    abs((d - seg.end_date).days),
                )

            best_i = min(
                range(len(segments)),
                key=lambda i: _date_segment_distance(segments[i]),
            )
            segments[best_i].asset_ids.append(aid)
            if dt.date() < segments[best_i].start_date:
                segments[best_i].start_date = dt.date()
            if dt.date() > segments[best_i].end_date:
                segments[best_i].end_date = dt.date()
    elif orphan_rows and not segments:
        orphan_seg = _rows_to_segment(
            orphan_rows,  # type: ignore[arg-type]
            index=1,
            total=1,
            suppress_geo=suppress_geo,
            label_place=label_place,
        )
        if orphan_seg is not None:
            segments.append(orphan_seg)

    # Assign no-GPS assets by takenAt falling inside a segment span.
    assigned: set[str] = {aid for seg in segments for aid in seg.asset_ids}
    for asset in assets:
        aid = asset["id"]
        if aid in assigned:
            continue
        dt = _parse_asset_datetime(asset)
        d = parse_asset_date(asset)
        if dt is None and d is None:
            continue
        check = dt.date() if dt else d
        for seg in segments:
            if seg.start_date <= check <= seg.end_date:
                seg.asset_ids.append(aid)
                assigned.add(aid)
                break

    # Preserve chronological order while deduplicating; downstream bucket
    # builders rely on takenAt-ordered ids.
    asset_taken_at: dict[str, str] = {
        str(a["id"]): str(a.get("takenAt") or "")
        for a in assets
        if a.get("id")
    }
    for i, seg in enumerate(segments, start=1):
        seg.id = f"evt-{i:02d}"
        seg.name = _segment_name(
            seg.start_date,
            seg.end_date,
            seg.location,
            index=i,
            total=len(segments),
            suppress_geo=suppress_geo,
            label_place=label_place,
        )
        seg.asset_ids = sorted(
            dict.fromkeys(seg.asset_ids),
            key=lambda aid: (asset_taken_at.get(aid, ""), aid),
        )

    return [s for s in segments if s.asset_ids], gap_meta
