"""Cluster assets into travel time segments (multi-visit same trip)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any


DEFAULT_SEGMENT_GAP_DAYS = 14


@dataclass
class TimeSegment:
    id: str
    label: str
    date_start: date
    date_end: date
    asset_ids: list[str]

    def to_dict(self, *, places: list[str] | None = None) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": self.id,
            "label": self.label[:24],
            "dateStart": self.date_start.isoformat(),
            "dateEnd": self.date_end.isoformat(),
            "assetIds": list(self.asset_ids),
        }
        if places:
            out["places"] = places[:3]
        return out


def parse_asset_date(asset: dict) -> date | None:
    raw = asset.get("takenAt")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).date()
    except ValueError:
        return None


def cluster_time_segments(
    assets: list[dict],
    *,
    gap_days: int = DEFAULT_SEGMENT_GAP_DAYS,
    place: str = "旅途",
) -> list[TimeSegment]:
    """Split assets when consecutive takenAt gap exceeds gap_days."""
    dated: list[tuple[date, str, dict]] = []
    undated: list[str] = []
    for a in assets:
        d = parse_asset_date(a)
        if d:
            dated.append((d, a["id"], a))
        else:
            undated.append(a["id"])

    if not dated and undated:
        return [
            TimeSegment(
                id="seg-01",
                label=place[:12],
                date_start=date.today(),
                date_end=date.today(),
                asset_ids=undated,
            )
        ]

    dated.sort(key=lambda x: x[0])
    groups: list[list[tuple[date, str, dict]]] = [[dated[0]]]
    for i in range(1, len(dated)):
        prev_d = dated[i - 1][0]
        cur_d, cur_id, cur_a = dated[i]
        if (cur_d - prev_d).days > gap_days:
            groups.append([(cur_d, cur_id, cur_a)])
        else:
            groups[-1].append((cur_d, cur_id, cur_a))

    segments: list[TimeSegment] = []
    for idx, group in enumerate(groups, start=1):
        ids = [gid for _, gid, _ in group]
        d0 = group[0][0]
        d1 = group[-1][0]
        label = _segment_label(d0, d1, place, seg_index=idx, total=len(groups))
        segments.append(
            TimeSegment(
                id=f"seg-{idx:02d}",
                label=label,
                date_start=d0,
                date_end=d1,
                asset_ids=ids,
            )
        )

    if undated and segments:
        segments[-1].asset_ids.extend(undated)
    elif undated:
        segments.append(
            TimeSegment(
                id="seg-01",
                label="未标注日期"[:12],
                date_start=date.today(),
                date_end=date.today(),
                asset_ids=undated,
            )
        )

    return segments


def _segment_label(
    d0: date,
    d1: date,
    place: str,
    *,
    seg_index: int,
    total: int,
) -> str:
    if d0.year != d1.year:
        base = f"{d0.year}–{d1.year}·{place}"
    elif d0.month != d1.month:
        base = f"{d0.month}月–{d1.month}月·{place}"
    elif d0 != d1:
        base = f"{d0.month}月{d0.day}–{d1.day}日"
    else:
        base = f"{d0.month}月{d0.day}日·{place}"
    if total > 1 and len(base) <= 8:
        base = f"{base}·{seg_index}"
    return base[:12]


def segment_ids_for_assets(segments: list[TimeSegment]) -> dict[str, str]:
    out: dict[str, str] = {}
    for seg in segments:
        for aid in seg.asset_ids:
            out[aid] = seg.id
    return out
