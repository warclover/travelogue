"""Cluster assets into travel time segments (multi-visit same trip)."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from travelogue.services.copy_subject import is_generic_place

DEFAULT_SEGMENT_GAP_DAYS = 14
DEFAULT_CITY_GAP_DAYS = 3


@dataclass
class TimeSegment:
    id: str
    label: str
    date_start: date
    date_end: date
    asset_ids: list[str]
    places: list[str] = field(default_factory=list)

    def to_dict(self, *, places: list[str] | None = None) -> dict[str, Any]:
        seg_places = self.places if places is None else places
        out: dict[str, Any] = {
            "id": self.id,
            "label": self.label[:24],
            "dateStart": self.date_start.isoformat(),
            "dateEnd": self.date_end.isoformat(),
            "assetIds": list(self.asset_ids),
        }
        if seg_places:
            out["places"] = seg_places[:3]
        return out


def parse_asset_date(asset: dict) -> date | None:
    raw = asset.get("takenAt")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).date()
    except ValueError:
        return None


def asset_city(asset: dict) -> str | None:
    place = asset.get("place") or {}
    city = place.get("city")
    if isinstance(city, str) and city.strip() and city.strip() not in ("未知", "旅途"):
        return city.strip()[:32]
    return None


def _segment_places(group: list[tuple[date, str, dict]]) -> list[str]:
    cities = [c for _, _, a in group if (c := asset_city(a))]
    if not cities:
        return []
    ranked = Counter(cities).most_common(3)
    return [name for name, _ in ranked]


def _should_split_segment(
    prev: tuple[date, str, dict],
    cur: tuple[date, str, dict],
    *,
    gap_days: int,
    city_gap_days: int,
) -> bool:
    prev_d, _, prev_a = prev
    cur_d, _, cur_a = cur
    gap = (cur_d - prev_d).days
    if gap > gap_days:
        return True
    prev_city = asset_city(prev_a)
    cur_city = asset_city(cur_a)
    if gap > city_gap_days and prev_city and cur_city and prev_city != cur_city:
        low_conf = prev_a.get("dateConfidence") == "low" or cur_a.get("dateConfidence") == "low"
        if low_conf and gap <= gap_days:
            return False
        return True
    return False


def cluster_time_segments(
    assets: list[dict],
    *,
    gap_days: int = DEFAULT_SEGMENT_GAP_DAYS,
    city_gap_days: int = DEFAULT_CITY_GAP_DAYS,
    place: str = "旅途",
    explicit_place: str | None = None,
) -> list[TimeSegment]:
    """Split assets when consecutive takenAt gap exceeds gap_days or city changes."""
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
                label="未标注日期"[:12],
                date_start=date.today(),
                date_end=date.today(),
                asset_ids=undated,
            )
        ]

    dated.sort(key=lambda x: x[0])
    groups: list[list[tuple[date, str, dict]]] = [[dated[0]]]
    for i in range(1, len(dated)):
        if _should_split_segment(
            dated[i - 1], dated[i], gap_days=gap_days, city_gap_days=city_gap_days
        ):
            groups.append([dated[i]])
        else:
            groups[-1].append(dated[i])

    segments: list[TimeSegment] = []
    for idx, group in enumerate(groups, start=1):
        ids = [gid for _, gid, _ in group]
        d0 = group[0][0]
        d1 = group[-1][0]
        seg_places = _segment_places(group)
        if seg_places and explicit_place and not is_generic_place(explicit_place):
            label_place = seg_places[0]
        elif seg_places:
            label_place = place
        else:
            label_place = place
        label = _segment_label(d0, d1, label_place, seg_index=idx, total=len(groups))
        segments.append(
            TimeSegment(
                id=f"seg-{idx:02d}",
                label=label,
                date_start=d0,
                date_end=d1,
                asset_ids=ids,
                places=seg_places,
            )
        )

    if undated:
        if segments:
            undated_seg = TimeSegment(
                id=f"seg-{len(segments) + 1:02d}",
                label="未标注日期"[:12],
                date_start=segments[-1].date_end,
                date_end=segments[-1].date_end,
                asset_ids=undated,
            )
            segments.append(undated_seg)
        else:
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
    return base[:24]


def segment_ids_for_assets(segments: list[TimeSegment]) -> dict[str, str]:
    out: dict[str, str] = {}
    for seg in segments:
        for aid in seg.asset_ids:
            out[aid] = seg.id
    return out
