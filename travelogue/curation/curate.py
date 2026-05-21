"""Agent 1 · Curator — day-based chapters, cover, then layout."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

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


def _date_span_warning(assets: list[dict], *, max_span_days: int = 365) -> str | None:
    """Warn when takenAt spans multiple years (mixed archive + trip photos)."""
    dates = [d for a in assets if (d := _parse_asset_date(a))]
    if len(dates) < 2:
        return None
    lo, hi = min(dates), max(dates)
    span = (hi - lo).days
    if span > max_span_days:
        return (
            f"素材拍摄日跨度 {span} 天（{lo.isoformat()} – {hi.isoformat()}），"
            "分章可能混杂多段旅行，建议核对相册或过滤旧图"
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
        return score

    score = h / w
    if kind == "tall":
        score *= 1.1
    if kind == "panorama":
        score *= 0.85
    return score


def layout_eligible_assets(trip: dict) -> list[dict]:
    """Assets usable for cover, chapters, and screens (excludes low-res curation drops)."""
    excluded = set((trip.get("curation") or {}).get("excludedLowResAssetIds") or [])
    return [
        a
        for a in trip.get("assets") or []
        if a["id"] not in excluded and a.get("type", "image") != "video"
    ]


def apply_low_resolution_exclusion(trip: dict) -> str | None:
    """Mark明显偏低分辨率 assets; returns warning message if any dropped."""
    from travelogue.config import get_config
    from travelogue.curation.asset_quality import partition_low_resolution_assets

    cfg = get_config().ingest
    all_assets = trip.get("assets") or []
    _, dropped, warn = partition_low_resolution_assets(
        all_assets,
        min_long_edge_px=cfg.min_long_edge_layout_px,
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

    n = len(buckets)
    if n > 5:
        merged: list[list[str]] = []
        chunk = 0
        target = 5
        per = (n + target - 1) // target
        for i in range(0, n, per):
            group: list[str] = []
            for b in buckets[i : i + per]:
                group.extend(b)
            merged.append(group)
        buckets = merged
    buckets = _merge_small_buckets(buckets, min_size=3)
    if len(buckets) < 3:
        flat_count = sum(len(b) for b in buckets)
        target = 3 if flat_count < 9 else min(5, max(3, len(buckets) or 3))
        while len(buckets) < target:
            largest_i = max(range(len(buckets)), key=lambda i: len(buckets[i]))
            bucket = buckets[largest_i]
            if len(bucket) < 2:
                break
            mid = len(bucket) // 2
            buckets[largest_i] = bucket[:mid]
            buckets.insert(largest_i + 1, bucket[mid:])
    return buckets


def _merge_small_buckets(buckets: list[list[str]], *, min_size: int = 3) -> list[list[str]]:
    """Merge chapters with fewer than min_size photos into neighbors (preserve day order)."""
    out = [list(b) for b in buckets if b]
    if not out:
        return out
    while True:
        small = [i for i, b in enumerate(out) if len(b) < min_size]
        if not small or len(out) <= 1:
            break
        idx = min(small, key=lambda i: len(out[i]))
        if idx > 0:
            out[idx - 1].extend(out[idx])
            del out[idx]
        else:
            out[0].extend(out[1])
            del out[1]
    return out


def _bucket_day_span(bucket: list[str], assets_by_id: dict[str, dict]) -> list[str]:
    dates = sorted(
        {
            d
            for aid in bucket
            if (d := _parse_asset_date(assets_by_id.get(aid, {})))
        }
    )
    return [d.isoformat() for d in dates]


def _chapter_titles(buckets: list[list[str]], assets: list[dict], meta: dict) -> list[str]:
    place = (meta.get("places") or ["旅途"])[0]
    assets_by_id = {a["id"]: a for a in assets}
    titles: list[str] = []
    day_seen: dict[str, int] = {}
    for i, bucket in enumerate(buckets):
        if not bucket:
            titles.append(f"片段{i + 1}")
            continue
        span = _bucket_day_span(bucket, assets_by_id)
        if len(span) > 1:
            d0 = date.fromisoformat(span[0])
            d1 = date.fromisoformat(span[-1])
            base = f"{d0.month}月{d0.day}–{d1.month}月{d1.day}日"
            titles.append(base[:12])
            continue
        d = _parse_asset_date(next((a for a in assets if a["id"] == bucket[0]), {}))
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


def run_curate(
    trip: dict,
    *,
    export_layout: str | None = None,
    layout_engine: str | None = None,
    apply_layout: bool = True,
) -> CurateResult:
    if len(trip.get("assets") or []) < 4:
        raise CurateError("E_CURATE_TOO_FEW", "need at least 4 assets to curate")

    res_warn = apply_low_resolution_exclusion(trip)
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

    buckets = _group_assets_by_day(layout_assets, cover_id)
    aspects = {a["id"]: aspect_kind_for_asset(a) for a in layout_assets}
    titles = _chapter_titles(buckets, layout_assets, trip.get("meta", {}))
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
    )
    assets_by_id = {a["id"]: a for a in layout_assets}
    for ch, bucket in zip(chapters, [b for b in buckets if b]):
        span = _bucket_day_span(bucket, assets_by_id)
        if span:
            ch.setdefault("curation", {})["daySpan"] = span
    trip["chapters"] = chapters
    trip["exportLayout"] = layout
    trip["layoutEngine"] = engine
    if engine == LAYOUT_ENGINE_SCREENS:
        trip["layoutEngineVersion"] = LAYOUT_ENGINE_VERSION_SCREENS
    curation = trip.setdefault("curation", {})
    curation["orientationSummary"] = summary_dict
    curation["layoutPlanVersion"] = LAYOUT_PLAN_VERSION
    warnings: list[str] = []
    span_warn = _date_span_warning(layout_assets)
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
