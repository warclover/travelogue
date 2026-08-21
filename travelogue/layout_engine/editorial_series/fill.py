"""Portfolio fill groups (D-MSP-09 / D-MSP-13). Journal never imports this."""

from __future__ import annotations

from datetime import datetime, timezone
from statistics import median
from typing import Any, Mapping, Sequence

from travelogue.layout_engine.editorial_series.match import groups_from_assets

ADJACENCY_SECONDS = 10 * 60
SPAN_SECONDS = 45 * 60
SPARSE_MEDIAN_SECONDS = 60 * 60
FULFILL_MIN = 0.8


def parse_taken_at(raw: Any) -> datetime | None:
    if not raw:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def segment_id_for(asset_id: str, trip: Mapping[str, Any] | None) -> str:
    if not isinstance(trip, Mapping):
        return f"_own:{asset_id}"
    cur = trip.get("curation")
    if not isinstance(cur, Mapping):
        return f"_own:{asset_id}"
    for seg in cur.get("segments") or []:
        if not isinstance(seg, Mapping):
            continue
        ids = {str(x) for x in (seg.get("assetIds") or [])}
        if asset_id in ids:
            return str(seg.get("id") or "_seg")
    return f"_own:{asset_id}"


def adjacent_gaps_seconds(assets: Sequence[Mapping[str, Any]]) -> list[float]:
    stamps: list[datetime] = []
    for raw in assets:
        ts = parse_taken_at(raw.get("takenAt") or raw.get("taken_at"))
        if ts is not None:
            stamps.append(ts)
    stamps.sort()
    return [
        (b - a).total_seconds()
        for a, b in zip(stamps, stamps[1:])
        if (b - a).total_seconds() >= 0
    ]


def is_sparse_collection(assets: Sequence[Mapping[str, Any]] | None) -> bool:
    """OQ-MSP-14 · median adjacent gap > 60 min → preset sequence will not fill."""
    gaps = adjacent_gaps_seconds(assets or [])
    if not gaps:
        return False
    return float(median(gaps)) > SPARSE_MEDIAN_SECONDS


def fill_groups_from_assets(
    assets: Sequence[Mapping[str, Any]] | None,
    *,
    trip: Mapping[str, Any] | None = None,
    buckets: Sequence[Sequence[str]] | None = None,
) -> list[dict[str, Any]]:
    """Keep existing shot groups; merge adjacent solos under the triple guard."""
    if not assets:
        return groups_from_assets(None, buckets=buckets)

    ordered = sorted(
        [a for a in assets if str(a.get("id") or a.get("assetId") or "").strip()],
        key=lambda a: (
            parse_taken_at(a.get("takenAt") or a.get("taken_at"))
            or datetime.min.replace(tzinfo=timezone.utc),
            str(a.get("id") or a.get("assetId") or ""),
        ),
    )
    runs: list[dict[str, Any]] = []
    for raw in ordered:
        aid = str(raw.get("id") or raw.get("assetId") or "").strip()
        shot = str(raw.get("shotGroupId") or "").strip()
        solo = not shot
        gid = shot or f"solo-{aid}"
        kind = str(raw.get("shotGroupKind") or "scene").strip() or "scene"
        ts = parse_taken_at(raw.get("takenAt") or raw.get("taken_at"))
        seg = segment_id_for(aid, trip)
        if runs and not solo and runs[-1]["id"] == gid:
            runs[-1]["asset_ids"].append(aid)
            if ts is not None:
                runs[-1]["ts"].append(ts)
            continue
        if (
            solo
            and runs
            and runs[-1].get("solo")
            and _can_absorb(runs[-1], seg, ts)
        ):
            runs[-1]["asset_ids"].append(aid)
            if ts is not None:
                runs[-1]["ts"].append(ts)
            continue
        runs.append(
            {
                "id": gid if not solo else f"fill-{aid}",
                "kind": kind,
                "asset_ids": [aid],
                "solo": solo,
                "seg": seg,
                "ts": [ts] if ts is not None else [],
            }
        )
    return [
        {"id": r["id"], "kind": r["kind"], "asset_ids": list(r["asset_ids"])}
        for r in runs
    ]


def _can_absorb(run: Mapping[str, Any], seg: str, ts: datetime | None) -> bool:
    if run.get("seg") != seg:
        return False
    stamps = [t for t in (run.get("ts") or []) if t is not None]
    if ts is None or not stamps:
        return False
    if (ts - stamps[-1]).total_seconds() > ADJACENCY_SECONDS:
        return False
    if (ts - stamps[0]).total_seconds() > SPAN_SECONDS:
        return False
    return True


def fulfillment_ratio(*, fulfilled_pages: int, planned_pages: int) -> float:
    if planned_pages <= 0:
        return 0.0
    return fulfilled_pages / planned_pages
