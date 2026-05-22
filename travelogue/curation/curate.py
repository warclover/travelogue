"""Agent 1 · Curator — day-based chapters, cover, then layout."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import NamedTuple

from travelogue.curation.layout_planner import (
    aspect_kind_for_asset,
    build_chapters_from_buckets,
    summarize_orientations,
)
from travelogue.services.layout import LAYOUT_PLAN_VERSION, format_layout_summary
from travelogue.services.pipeline_state import set_layout_status


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class CurateError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass
class CurateResult:
    chapter_count: int
    cover_asset_id: str
    layout_summary: str
    day_groups: int
    warnings: list[str]


def _date_span_warning(
    assets: list[dict],
    segments: list | None = None,
    *,
    max_span_days: int = 365,
) -> str | None:
    """Warn when multiple time segments or a very wide date span is detected."""
    from travelogue.curation.time_segments import TimeSegment

    if segments and len(segments) >= 2:
        labels = []
        for s in segments:
            if isinstance(s, TimeSegment):
                labels.append(s.label)
            else:
                labels.append(str(s.get("label", s.get("id", ""))))
        preview = "、".join(labels[:4])
        if len(segments) > 4:
            preview += f" 等{len(segments)}段"
        return (
            f"检测到 {len(segments)} 个时间段（{preview}），已合成一本并按段编排；"
            "可在 G1 合并段，或拆成多本游记"
        )

    dates = [d for a in assets if (d := _parse_asset_date(a))]
    if len(dates) < 2:
        return None
    lo, hi = min(dates), max(dates)
    span = (hi - lo).days
    if span > max_span_days:
        return (
            f"素材拍摄日跨度 {span} 天（{lo.isoformat()} – {hi.isoformat()}），"
            "已合成一本并按日期编排；可在 G1 合并时间段或拆成多本"
        )
    return None


def _parse_asset_date(asset: dict) -> date | None:
    raw = asset.get("takenAt")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _cover_score(asset: dict, export_layout: str) -> float:
    """Mobile: prefer tall/portrait. Web: prefer landscape / panorama for 16:9 displays."""
    from travelogue.curation.media_classify import cover_class_weight

    kind = aspect_kind_for_asset(asset)
    if kind == "square":
        return 0.0
    w = int(asset.get("width") or 1)
    h = int(asset.get("height") or 1)
    if w <= 0 or h <= 0:
        return 0.0

    if export_layout == "web":
        if kind in ("portrait", "tall"):
            return 0.0
        ratio = w / h
        score = ratio
        if kind == "panorama":
            score *= 1.2
        elif kind == "landscape":
            target = 16 / 9
            score *= 1.0 + 0.35 / (1.0 + abs(ratio - target))
        return score * cover_class_weight(asset.get("mediaClass"))

    score = h / w
    if kind == "tall":
        score *= 1.1
    if kind == "panorama":
        score *= 0.85
    return score * cover_class_weight(asset.get("mediaClass"))


def layout_eligible_assets(trip: dict) -> list[dict]:
    """Assets usable for cover, chapters, and screens (excludes low-res curation drops)."""
    excluded = set((trip.get("curation") or {}).get("excludedLowResAssetIds") or [])
    return [
        a
        for a in trip.get("assets") or []
        if a["id"] not in excluded and a.get("type", "image") != "video"
    ]


def apply_low_resolution_exclusion(
    trip: dict,
    *,
    trip_dir: Path | None = None,
) -> str | None:
    """Mark明显偏低分辨率 assets; returns warning message if any dropped."""
    from travelogue.config import get_config
    from travelogue.curation.asset_quality import (
        backfill_native_dimensions,
        partition_low_resolution_assets,
    )

    if trip_dir is not None:
        backfill_native_dimensions(trip, Path(trip_dir))

    cfg = get_config().ingest
    all_assets = trip.get("assets") or []
    _, dropped, warn = partition_low_resolution_assets(
        all_assets,
        min_long_edge_px=cfg.min_long_edge_layout_px,
        min_short_edge_px=cfg.min_short_edge_layout_px,
        median_ratio=cfg.low_res_median_ratio,
        peak_ratio=cfg.low_res_peak_ratio,
    )
    curation = trip.setdefault("curation", {})
    if dropped:
        curation["excludedLowResAssetIds"] = [a["id"] for a in dropped]
    else:
        curation.pop("excludedLowResAssetIds", None)
    return warn


def resolve_cover_asset_id(
    trip: dict,
    *,
    export_layout: str,
) -> str:
    """Pick cover for render/curate profile (mobile | web | auto→mobile)."""
    assets = layout_eligible_assets(trip)
    if not assets:
        return ""
    profile = export_layout
    if profile == "auto":
        profile = "mobile"
    by_layout = (trip.get("curation") or {}).get("coverByLayout") or {}
    if isinstance(by_layout, dict) and profile in by_layout:
        cid = by_layout[profile]
        if cid and any(a.get("id") == cid for a in assets):
            return cid
    return _pick_cover_asset_id(assets, export_layout=profile)


def sync_trip_covers(
    trip: dict,
    *,
    export_layout: str | None = None,
    assets: list[dict] | None = None,
) -> str:
    """Write coverAssetId (+ coverByLayout when exportLayout=auto). Returns primary cover id."""
    assets = assets if assets is not None else layout_eligible_assets(trip)
    layout = export_layout or trip.get("exportLayout") or "auto"
    curation = trip.setdefault("curation", {})

    if layout == "auto":
        mobile_id = _pick_cover_asset_id(assets, export_layout="mobile")
        web_id = _pick_cover_asset_id(assets, export_layout="web")
        curation["coverByLayout"] = {"mobile": mobile_id, "web": web_id}
        trip["coverAssetId"] = mobile_id
        trip["coverCandidates"] = _cover_candidates(assets, mobile_id, export_layout="mobile")
        curation["coverCandidatesByLayout"] = {
            "mobile": _cover_candidates(assets, mobile_id, export_layout="mobile"),
            "web": _cover_candidates(assets, web_id, export_layout="web"),
        }
        return mobile_id

    cover_id = _pick_cover_asset_id(assets, export_layout=layout)
    trip["coverAssetId"] = cover_id
    trip["coverCandidates"] = _cover_candidates(assets, cover_id, export_layout=layout)
    curation.pop("coverByLayout", None)
    curation.pop("coverCandidatesByLayout", None)
    return cover_id


def _pick_cover_asset_id(
    assets: list[dict],
    *,
    export_layout: str = "mobile",
    exclude: set[str] | None = None,
) -> str:
    exclude = exclude or set()
    best_id = ""
    best_score = 0.0
    for a in assets:
        if a["id"] in exclude or a.get("type") == "video":
            continue
        score = _cover_score(a, export_layout)
        if score > best_score:
            best_score = score
            best_id = a["id"]
    if best_id:
        return best_id
    for a in assets:
        if a["id"] not in exclude and a.get("type") != "video":
            return a["id"]
    return assets[0]["id"]


def _cover_candidates(
    assets: list[dict],
    cover_id: str,
    *,
    export_layout: str = "mobile",
    limit: int = 5,
) -> list[str]:
    scored: list[tuple[float, str]] = []
    for a in assets:
        if a["id"] == cover_id or a.get("type") == "video":
            continue
        score = _cover_score(a, export_layout)
        if score > 0:
            scored.append((score, a["id"]))
    scored.sort(reverse=True)
    out = [cover_id] + [aid for _, aid in scored[: limit - 1]]
    return out[:limit]


_MAX_CHAPTER_ITEMS = 8
_DEFAULT_CARD_LAYOUT = {"fill": True, "bleed": True, "overlay": True}


def _item_asset_ids(item: dict) -> list[str]:
    if item.get("type") == "media-card":
        aid = item.get("assetId")
        return [aid] if aid else []
    if item.get("type") in ("media-row", "media-scroll"):
        return list(item.get("assetIds") or [])
    return []


def _filter_item_excluded(item: dict, excluded: set[str]) -> dict | None:
    itype = item.get("type")
    if itype == "media-card":
        aid = item.get("assetId")
        if not aid or aid in excluded:
            return None
        return item
    if itype in ("media-row", "media-scroll"):
        aids = [a for a in item.get("assetIds") or [] if a not in excluded]
        if not aids:
            return None
        out = dict(item)
        out["assetIds"] = aids
        return out
    return item


def _items_from_screen_asset_ids(asset_ids: list[str]) -> list[dict]:
    """Rebuild a compact items[] from screens (schema max 8)."""
    items: list[dict] = []
    i = 0
    while i < len(asset_ids) and len(items) < _MAX_CHAPTER_ITEMS:
        chunk = asset_ids[i : i + 3]
        if len(chunk) == 1:
            items.append(
                {
                    "type": "media-card",
                    "assetId": chunk[0],
                    "layout": dict(_DEFAULT_CARD_LAYOUT),
                }
            )
            i += 1
        else:
            layout = "landscape-triple" if len(chunk) >= 3 else "landscape-pair"
            items.append(
                {"type": "media-row", "assetIds": chunk[:3], "rowLayout": layout}
            )
            i += len(chunk[:3])
    return items[:_MAX_CHAPTER_ITEMS]


def _sanitize_chapters_after_exclusion(chapters: list[dict], excluded: set[str]) -> None:
    """Drop excluded assets from items[] and keep within schema maxItems."""
    for ch in chapters:
        items = []
        for it in ch.get("items", []):
            kept = _filter_item_excluded(it, excluded)
            if kept is not None:
                items.append(kept)
        if len(items) > _MAX_CHAPTER_ITEMS:
            aids: list[str] = []
            for sc in ch.get("screens") or []:
                for sl in sc.get("slots") or []:
                    aid = sl.get("assetId")
                    if aid and aid not in excluded and aid not in aids:
                        aids.append(aid)
            if aids:
                items = _items_from_screen_asset_ids(aids)
            else:
                flat: list[str] = []
                for it in items:
                    flat.extend(_item_asset_ids(it))
                items = _items_from_screen_asset_ids(flat)
        ch["items"] = items


def _group_assets_by_day(assets: list[dict], cover_id: str) -> list[list[str]]:
    body = [a for a in assets if a["id"] != cover_id]
    if len(body) < 4:
        body = list(assets)

    by_day: dict[date, list[str]] = defaultdict(list)
    no_date: list[str] = []
    for a in sorted(body, key=lambda x: x.get("takenAt") or ""):
        d = _parse_asset_date(a)
        if d:
            by_day[d].append(a["id"])
        else:
            no_date.append(a["id"])

    buckets: list[list[str]] = [by_day[k] for k in sorted(by_day)]
    if no_date:
        buckets.append(no_date)

    if not buckets:
        return [[a["id"] for a in body]]

    return _merge_small_buckets(buckets, min_size=3)


class NormalizedBuckets(NamedTuple):
    buckets: list[list[str]]
    primary_segment_ids: list[str]
    segment_ids_per_bucket: list[list[str]]


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


def _normalize_bucket_counts(
    buckets: list[list[str]],
    segment_ids: list[str] | None = None,
    *,
    min_chapters: int | None = None,
    max_chapters: int | None = None,
    min_bucket_size: int = 3,
) -> NormalizedBuckets:
    """Merge day buckets to fit manifest chapter limits; preserve segment metadata."""
    from travelogue.services.manifest_limits import chapter_limits

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
        merged: list[list[str]] = []
        merged_primary: list[str] = []
        merged_all: list[list[str]] = []
        per = (n + max_c - 1) // max_c
        for i in range(0, n, per):
            end = min(i + per, n)
            group: list[str] = []
            for j in range(i, end):
                group.extend(out[j])
            merged.append(group)
            merged_primary.append(_primary_segment_in_chunk(out, seg, i, end))
            merged_all.append(_segments_in_chunk(seg, i, end))
        out, seg, seg_all = merged, merged_primary, merged_all

    out, seg, seg_all = _merge_small_buckets_with_segments(
        out, seg, seg_all, min_size=min_bucket_size
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

    return NormalizedBuckets(out, seg, seg_all)


def _cap_book_buckets(
    buckets: list[list[str]],
    bucket_segment_ids: list[str] | None = None,
    *,
    min_chapters: int | None = None,
    max_chapters: int | None = None,
) -> tuple[list[list[str]], list[str]]:
    """Backward-compatible wrapper (primary segment ids only)."""
    norm = _normalize_bucket_counts(
        buckets,
        bucket_segment_ids,
        min_chapters=min_chapters,
        max_chapters=max_chapters,
    )
    return norm.buckets, norm.primary_segment_ids


def _merge_small_buckets(buckets: list[list[str]], *, min_size: int = 3) -> list[list[str]]:
    """Merge chapters with fewer than min_size photos into neighbors (preserve day order)."""
    merged, _, _ = _merge_small_buckets_with_segments(
        buckets,
        [""] * len(buckets),
        [[""]] * len(buckets),
        min_size=min_size,
    )
    return merged


def _merge_segment_lists(a: list[str], b: list[str]) -> list[str]:
    out = list(a)
    for sid in b:
        if sid and sid not in out:
            out.append(sid)
    return out


def _merge_small_buckets_with_segments(
    buckets: list[list[str]],
    segment_ids: list[str],
    segment_ids_all: list[list[str]] | None = None,
    *,
    min_size: int = 3,
) -> tuple[list[list[str]], list[str], list[list[str]]]:
    """Like _merge_small_buckets; keeps primary and full segment lists per bucket."""
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
    while True:
        small = [i for i, b in enumerate(out) if len(b) < min_size]
        if not small or len(out) <= 1:
            break
        idx = min(small, key=lambda i: len(out[i]))
        if idx > 0:
            left_n, right_n = len(out[idx - 1]), len(out[idx])
            out[idx - 1].extend(out[idx])
            seg_all[idx - 1] = _merge_segment_lists(seg_all[idx - 1], seg_all[idx])
            if right_n > left_n and seg[idx]:
                seg[idx - 1] = seg[idx]
            del out[idx]
            del seg[idx]
            del seg_all[idx]
        else:
            left_n, right_n = len(out[0]), len(out[1])
            out[0].extend(out[1])
            seg_all[0] = _merge_segment_lists(seg_all[0], seg_all[1])
            if right_n > left_n and seg[1]:
                seg[0] = seg[1]
            del out[1]
            del seg[1]
            del seg_all[1]
    for i, sid in enumerate(seg):
        if sid and sid not in seg_all[i]:
            seg_all[i].insert(0, sid)
    return out, seg, seg_all


def _bucket_day_span(bucket: list[str], assets_by_id: dict[str, dict]) -> list[str]:
    dates = sorted(
        {
            d
            for aid in bucket
            if (d := _parse_asset_date(assets_by_id.get(aid, {})))
        }
    )
    return [d.isoformat() for d in dates]


def _title_for_bucket_span(span: list[str]) -> str | None:
    if len(span) < 2:
        return None
    d0 = date.fromisoformat(span[0])
    d1 = date.fromisoformat(span[-1])
    if d0.year != d1.year:
        return f"{d0.year}–{d1.year}"[:12]
    if d0.month == d1.month and d0.day == d1.day:
        return f"{d0.month}月{d0.day}日"[:12]
    return f"{d0.month}月{d0.day}–{d1.month}月{d1.day}日"[:12]


def _chapter_titles(
    buckets: list[list[str]],
    assets: list[dict],
    meta: dict,
    *,
    bucket_segment_ids: list[str] | None = None,
    bucket_segment_ids_all: list[list[str]] | None = None,
    segment_labels: dict[str, str] | None = None,
) -> list[str]:
    place = (meta.get("places") or ["旅途"])[0]
    assets_by_id = {a["id"]: a for a in assets}
    titles: list[str] = []
    day_seen: dict[str, int] = {}
    seg_day_seen: dict[str, int] = {}
    bucket_segment_ids = bucket_segment_ids or []
    bucket_segment_ids_all = bucket_segment_ids_all or []
    segment_labels = segment_labels or {}

    for i, bucket in enumerate(buckets):
        if not bucket:
            titles.append(f"片段{i + 1}")
            continue

        span = _bucket_day_span(bucket, assets_by_id)
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

        seg_id = bucket_segment_ids[i] if i < len(bucket_segment_ids) else ""
        if seg_id and segment_labels.get(seg_id):
            n = seg_day_seen.get(seg_id, 0)
            seg_day_seen[seg_id] = n + 1
            if n == 0:
                titles.append(segment_labels[seg_id][:12])
                continue

        if len(span) > 1:
            span_title = _title_for_bucket_span(span)
            if span_title:
                titles.append(span_title)
                continue
        d = _parse_asset_date(assets_by_id.get(bucket[0], {}))
        if d:
            key = d.isoformat()
            n = day_seen.get(key, 0)
            day_seen[key] = n + 1
            base = f"{d.month}月{d.day}日"
            if n == 0:
                titles.append(base[:12])
            elif n == 1:
                titles.append(f"{base}·二"[:12])
            else:
                titles.append(f"{base}·{n + 1}"[:12])
        elif i == 0:
            titles.append("抵达"[:12])
        elif i == len(buckets) - 1:
            titles.append("尾声"[:12])
        else:
            titles.append(f"{place}·{i}"[:12])
    return titles


def _group_assets_by_segments(
    layout_assets: list[dict],
    cover_id: str,
    meta: dict,
) -> tuple[list[list[str]], list[str], list[list[str]], list]:
    """Segment cluster → per-segment day buckets → flat chapter bucket list."""
    from travelogue.curation.time_segments import TimeSegment, cluster_time_segments

    place = (meta.get("places") or ["旅途"])[0]
    by_id = {a["id"]: a for a in layout_assets}
    segments = cluster_time_segments(layout_assets, place=place)

    all_buckets: list[list[str]] = []
    bucket_segment_ids: list[str] = []

    for seg in segments:
        seg_assets = [by_id[aid] for aid in seg.asset_ids if aid in by_id]
        if not seg_assets:
            continue
        local_cover = cover_id if cover_id in {a["id"] for a in seg_assets} else ""
        seg_buckets = _group_assets_by_day(seg_assets, local_cover)
        for b in seg_buckets:
            all_buckets.append(b)
            bucket_segment_ids.append(seg.id)

    if not all_buckets:
        all_buckets = _group_assets_by_day(layout_assets, cover_id)
        bucket_segment_ids = [""] * len(all_buckets)
        segments = []

    norm = _normalize_bucket_counts(all_buckets, bucket_segment_ids)
    return norm.buckets, norm.primary_segment_ids, norm.segment_ids_per_bucket, segments


def run_curate(
    trip: dict,
    *,
    export_layout: str | None = None,
    layout_engine: str | None = None,
    apply_layout: bool = True,
    trip_dir: Path | None = None,
) -> CurateResult:
    if len(trip.get("assets") or []) < 4:
        raise CurateError("E_CURATE_TOO_FEW", "need at least 4 assets to curate")

    res_warn = apply_low_resolution_exclusion(trip, trip_dir=trip_dir)
    layout_assets = layout_eligible_assets(trip)
    if len(layout_assets) < 4:
        raise CurateError(
            "E_CURATE_TOO_FEW",
            "need at least 4 layout-eligible assets after resolution filter",
        )

    from travelogue.curation.screen_planner import (
        LAYOUT_ENGINE_LEGACY,
        LAYOUT_ENGINE_SCREENS,
        LAYOUT_ENGINE_VERSION_SCREENS,
    )

    from travelogue.config import default_web_layout_engine

    layout = export_layout or trip.get("exportLayout") or "auto"
    engine = (
        layout_engine
        or trip.get("layoutEngine")
        or default_web_layout_engine(layout)
    )
    if engine not in (LAYOUT_ENGINE_LEGACY, LAYOUT_ENGINE_SCREENS):
        engine = LAYOUT_ENGINE_LEGACY
    cover_id = sync_trip_covers(trip, export_layout=layout, assets=layout_assets)
    curation = trip.get("curation") or {}
    by_layout = curation.get("coverByLayout") or {}
    skip_screen_ids: set[str] = set()
    if layout in ("auto", "web") and isinstance(by_layout, dict):
        web_cover = by_layout.get("web") or ""
        if web_cover:
            skip_screen_ids.add(web_cover)

    meta = trip.get("meta", {})
    buckets, bucket_segment_ids, bucket_segment_ids_all, segments = _group_assets_by_segments(
        layout_assets, cover_id, meta
    )
    places = meta.get("places") or []
    segment_labels = {s.id: s.label for s in segments}
    curation_segments = [s.to_dict(places=places) for s in segments]

    aspects = {a["id"]: aspect_kind_for_asset(a) for a in layout_assets}
    titles = _chapter_titles(
        buckets,
        layout_assets,
        meta,
        bucket_segment_ids=bucket_segment_ids,
        bucket_segment_ids_all=bucket_segment_ids_all,
        segment_labels=segment_labels,
    )
    summary = summarize_orientations(layout_assets, export_layout=layout)  # type: ignore[arg-type]
    summary_dict = summary.to_dict()
    chapters = build_chapters_from_buckets(
        buckets,
        aspects,
        export_layout=layout,  # type: ignore[arg-type]
        titles=titles,
        layout_engine=engine,
        assets=layout_assets,
        orientation_summary=summary_dict,
        skip_screen_asset_ids=skip_screen_ids,
        trip_photo_total=len(layout_assets),
    )
    assets_by_id = {a["id"]: a for a in layout_assets}
    for ch, bucket, seg_id, seg_ids in zip(
        chapters,
        [b for b in buckets if b],
        bucket_segment_ids,
        bucket_segment_ids_all,
    ):
        ch_cur = ch.setdefault("curation", {})
        span = _bucket_day_span(bucket, assets_by_id)
        if span:
            ch_cur["daySpan"] = span
        if seg_id:
            ch_cur["segmentId"] = seg_id
        if len(seg_ids) > 1:
            ch_cur["segmentIds"] = seg_ids
    excluded_ids = set(curation.get("excludedLowResAssetIds") or [])
    if excluded_ids:
        _sanitize_chapters_after_exclusion(chapters, excluded_ids)
    trip["chapters"] = chapters
    trip["exportLayout"] = layout
    trip["layoutEngine"] = engine
    if engine == LAYOUT_ENGINE_SCREENS:
        trip["layoutEngineVersion"] = LAYOUT_ENGINE_VERSION_SCREENS
    curation = trip.setdefault("curation", {})
    curation["orientationSummary"] = summary_dict
    curation["layoutPlanVersion"] = LAYOUT_PLAN_VERSION
    if curation_segments:
        curation["segments"] = curation_segments
        if len(curation_segments) == 1:
            curation["primarySegmentId"] = curation_segments[0]["id"]
        else:
            best = max(curation_segments, key=lambda s: len(s.get("assetIds") or []))
            curation["primarySegmentId"] = best["id"]
    from travelogue.curation.media_classify import summarize_media_classes

    mc = summarize_media_classes(trip.get("assets") or [])
    if mc:
        curation["mediaClassSummary"] = mc
    warnings: list[str] = []
    span_warn = _date_span_warning(layout_assets, segments)
    if span_warn:
        warnings.append(span_warn)
    if res_warn:
        warnings.append(res_warn)
    if warnings:
        curation["warnings"] = warnings

    layout_summary = format_layout_summary(summary_dict, chapters)
    pipe = trip.setdefault("pipeline", {})
    now = _utc_now_iso()
    if apply_layout:
        set_layout_status(trip, "layout_draft")
        pipe.setdefault("runs", []).append(
            {
                "runId": f"layout-{trip.get('tripId', 'trip')}",
                "agent": "layout",
                "startedAt": now,
                "finishedAt": now,
                "model": None,
            }
        )
    else:
        set_layout_status(trip, "pending")

    pipe["status"] = "structure_draft"
    pipe["pendingAssets"] = []
    trip["updatedAt"] = now
    pipe.setdefault("runs", []).append(
        {
            "runId": f"curate-{trip.get('tripId', 'trip')}",
            "agent": "curator",
            "startedAt": now,
            "finishedAt": now,
            "model": None,
        }
    )

    return CurateResult(
        chapter_count=len(trip.get("chapters", [])),
        cover_asset_id=cover_id,
        layout_summary=layout_summary,
        day_groups=len(buckets),
        warnings=warnings,
    )
