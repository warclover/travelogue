"""Geo×Scene sub-segmentation (Phase 6 · P6-F1 / ART-A1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from travelogue.curation.geo_events import GeoSegment, _dominant_location, _segment_name
from travelogue.curation.time_segments import parse_asset_date

NOISE_CLUSTER_ID = -1


@dataclass
class SceneSplitExplain:
    parent_event_id: str
    scene_cluster_id: int
    asset_count: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "parentEventId": self.parent_event_id,
            "sceneClusterId": self.scene_cluster_id,
            "assetCount": self.asset_count,
            "reason": self.reason,
        }


def _scene_cluster_for_asset(asset: dict) -> int | None:
    raw = asset.get("sceneClusterId")
    if raw is None:
        return None
    try:
        cid = int(raw)
    except (TypeError, ValueError):
        return None
    if cid == NOISE_CLUSTER_ID:
        return None
    return cid


def _group_assets_by_scene_run(
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
) -> list[tuple[int | None, list[str]]]:
    groups: list[tuple[int | None, list[str]]] = []
    current_cluster: int | None = None
    current_ids: list[str] = []
    for aid in asset_ids:
        cluster = _scene_cluster_for_asset(assets_by_id.get(aid) or {})
        if cluster != current_cluster and current_ids:
            groups.append((current_cluster, current_ids))
            current_ids = [aid]
            current_cluster = cluster
        else:
            current_ids.append(aid)
            current_cluster = cluster
    if current_ids:
        groups.append((current_cluster, current_ids))
    return groups


def _segment_dates(asset_ids: list[str], assets_by_id: dict[str, dict]) -> tuple[date, date]:
    dates: list[date] = []
    for aid in asset_ids:
        asset = assets_by_id.get(aid) or {}
        d = parse_asset_date(asset)
        if d:
            dates.append(d)
    if not dates:
        today = date.today()
        return today, today
    return min(dates), max(dates)


def split_geo_segment_by_scene(
    segment: GeoSegment,
    assets_by_id: dict[str, dict],
    *,
    min_photos_per_sub: int = 3,
) -> tuple[list[GeoSegment], list[SceneSplitExplain]]:
    """Split one geo segment when scene clusters change along the timeline."""
    groups = _group_assets_by_scene_run(segment.asset_ids, assets_by_id)
    valid_groups = [(cid, ids) for cid, ids in groups if len(ids) >= min_photos_per_sub]
    if len(valid_groups) <= 1:
        return [segment], []

    explains: list[SceneSplitExplain] = []
    out: list[GeoSegment] = []
    total = len(valid_groups)
    for idx, (cluster_id, ids) in enumerate(valid_groups, start=1):
        start, end = _segment_dates(ids, assets_by_id)
        location = _dominant_location([assets_by_id.get(aid) or {} for aid in ids]) or segment.location
        sub = GeoSegment(
            id=f"{segment.id}-sc{idx:02d}",
            name=_segment_name(start, end, location, index=idx, total=total),
            start_date=start,
            end_date=end,
            location=location,
            asset_ids=list(ids),
        )
        out.append(sub)
        if cluster_id is not None:
            explains.append(
                SceneSplitExplain(
                    parent_event_id=segment.id,
                    scene_cluster_id=cluster_id,
                    asset_count=len(ids),
                    reason="场景变化",
                )
            )
    return out, explains


def apply_scene_subsegments(
    segments: list[GeoSegment],
    assets_by_id: dict[str, dict],
    *,
    min_photos_per_sub: int = 3,
) -> tuple[list[GeoSegment], dict[str, Any]]:
    """Return refined segments and metadata for trip.curation.clustering."""
    refined: list[GeoSegment] = []
    explains: list[dict[str, Any]] = []
    split_parents = 0
    for segment in segments:
        subs, split_explain = split_geo_segment_by_scene(
            segment,
            assets_by_id,
            min_photos_per_sub=min_photos_per_sub,
        )
        if len(subs) == 1 and subs[0].id == segment.id:
            refined.append(segment)
            continue
        split_parents += 1
        refined.extend(subs)
        explains.extend(item.to_dict() for item in split_explain)

    for i, seg in enumerate(refined, start=1):
        seg.id = f"evt-{i:02d}"
        seg.name = _segment_name(
            seg.start_date,
            seg.end_date,
            seg.location,
            index=i,
            total=len(refined),
        )

    meta = {
        "enabled": True,
        "parentSplitCount": split_parents,
        "segmentCount": len(refined),
        "breakpoints": explains,
    }
    return refined, meta
