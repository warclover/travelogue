"""Shared burst detection (layout kernel).: prefer ingest burstGroupId, fallback to takenAt."""

from __future__ import annotations

from datetime import datetime

from travelogue.media.image_ops import AspectKind
from travelogue.media.quality import asset_sharpness


def parse_taken_ts(asset: dict) -> float | None:
    raw = asset.get("takenAt")
    if not raw:
        return None
    try:
        text = str(raw).replace("Z", "+00:00")
        return datetime.fromisoformat(text).timestamp()
    except (TypeError, ValueError):
        return None


def ingest_burst_group_id(asset: dict) -> str | None:
    bg = asset.get("burstGroupId")
    if isinstance(bg, str) and bg.strip():
        return bg.strip()
    return None


def shared_ingest_burst_group(
    asset_ids: list[str],
    assets_map: dict[str, dict],
) -> str | None:
    """Return burstGroupId when all ids share the same non-empty ingest group."""
    groups: set[str] = set()
    for aid in asset_ids:
        gid = ingest_burst_group_id(assets_map.get(aid) or {})
        if gid:
            groups.add(gid)
    if len(groups) == 1:
        return groups.pop()
    return None


def family_kind(kind: AspectKind | str) -> str:
    if kind in ("portrait", "tall"):
        return "portrait"
    if kind in ("landscape", "panorama"):
        return "landscape"
    return "square"


def time_near_chain(
    asset_ids: list[str],
    assets_map: dict[str, dict],
    *,
    burst_seconds: float,
) -> bool:
    if shared_ingest_burst_group(asset_ids, assets_map):
        return True
    stamps = [parse_taken_ts(assets_map.get(aid) or {}) for aid in asset_ids]
    valid = [t for t in stamps if t is not None]
    if len(valid) < 2:
        return True
    return max(valid) - min(valid) <= burst_seconds


def time_near_sequential(
    asset_ids: list[str],
    assets_map: dict[str, dict],
    *,
    burst_seconds: float,
) -> bool:
    if shared_ingest_burst_group(asset_ids, assets_map):
        return True
    stamps = [parse_taken_ts(assets_map.get(aid) or {}) for aid in asset_ids]
    known = [(i, t) for i, t in enumerate(stamps) if t is not None]
    if len(known) < 2:
        return True
    for (_, t0), (_, t1) in zip(known, known[1:]):
        if abs(t1 - t0) > burst_seconds:
            return False
    return True


def burst_group_map(
    asset_ids: list[str],
    assets_map: dict[str, dict],
    aspects: dict[str, AspectKind],
    *,
    burst_seconds: float = 3.0,
) -> dict[str, int]:
    """
    Map asset id → numeric burst group.

    Uses ingest burstGroupId when present; otherwise takenAt + aspect family.
    """
    ingest_to_gid: dict[str, int] = {}
    groups: dict[str, int] = {}
    gid = 0
    last_ts: float | None = None
    last_family: str | None = None

    for aid in asset_ids:
        asset = assets_map.get(aid) or {}
        ibg = ingest_burst_group_id(asset)
        if ibg:
            if ibg not in ingest_to_gid:
                gid += 1
                ingest_to_gid[ibg] = gid
            groups[aid] = ingest_to_gid[ibg]
            ts = parse_taken_ts(asset)
            if ts is not None:
                last_ts = ts
            last_family = family_kind(aspects.get(aid, "square"))
            continue

        fam = family_kind(aspects.get(aid, "square"))
        ts = parse_taken_ts(asset)
        if (
            last_ts is not None
            and ts is not None
            and last_family == fam
            and abs(ts - last_ts) <= burst_seconds
        ):
            groups[aid] = gid
        else:
            gid += 1
            groups[aid] = gid
        if ts is not None:
            last_ts = ts
        last_family = fam
    return groups


def same_burst_group(
    asset_ids: list[str],
    burst_groups: dict[str, int],
) -> bool:
    if len(asset_ids) < 2:
        return False
    g0 = burst_groups.get(asset_ids[0])
    return g0 is not None and all(burst_groups.get(a) == g0 for a in asset_ids)


def sort_ids_by_sharpness(
    asset_ids: list[str],
    assets_map: dict[str, dict],
) -> list[str]:
    return sorted(
        asset_ids,
        key=lambda aid: -asset_sharpness(assets_map.get(aid) or {}),
    )
