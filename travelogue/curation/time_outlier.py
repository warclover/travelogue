"""Share-Face Integrity · time outlier detection (BE-SFI-08 / D-SFI-05).

Marks assets far from the dense date core so merge/pools/titles can exclude them.
Appendix chapter (≥2 outliers) is composed outside ADR-007 chapter cap.
"""

from __future__ import annotations

from datetime import date, timedelta

from travelogue.curation.time_segments import parse_asset_date

# Adaptive threshold: clamp(k × core_span_days, floor, ceil)
_K = 1.5
_FLOOR_DAYS = 14
_CEIL_DAYS = 180
_MAX_OUTLIER_RATIO = 0.20
APPENDIX_TITLE_TMPL = "往年 · 旧照 · {n} 张"
APPENDIX_REASON = "拍摄时间远离行程主时段，已归入往年旧照"


def _percentile_dates(dates: list[date], lo: float, hi: float) -> tuple[date, date] | None:
    """Dense core via median-neighborhood then P10–P90 (outlier-resistant).

    Plain calendar P10–P90 is contaminated when a few far dates sit at the
    tips; take the closest 80% to the median first, then read that cluster's
    span as the dense core.
    """
    if not dates:
        return None
    ordered = sorted(dates)
    n = len(ordered)
    if n == 1:
        return ordered[0], ordered[0]
    median = ordered[n // 2]
    keep_n = max(1, int(round(n * (hi - lo))))  # ~80% for 0.10–0.90
    keep_n = min(n, max(keep_n, n - 2 if n >= 5 else n))
    nearest = sorted(ordered, key=lambda d: abs((d - median).days))[:keep_n]
    return min(nearest), max(nearest)


def adaptive_outlier_threshold_days(core_span_days: int) -> int:
    return max(_FLOOR_DAYS, min(_CEIL_DAYS, int(_K * max(core_span_days, 1))))


def substantial_segment_count(
    segment_sizes: list[int],
    *,
    dated_total: int,
    min_size: int = 3,
) -> int:
    """Count segments large enough to mean intentional multi-trip (年度精选).

    A lone stray photo that opens its own gap segment must NOT suppress
    outlier isolation (仙本那 FX-SFI-03).
    """
    if dated_total <= 0:
        return 0
    floor = max(min_size, int(dated_total * 0.10))
    return sum(1 for n in segment_sizes if n >= floor)


def detect_time_outlier_ids(
    assets: list[dict],
    *,
    segments_count: int | None = None,
    segment_sizes: list[int] | None = None,
) -> list[str]:
    """Return asset ids to mark as timeOutlier.

    Multi-segment **substantial** trips skip auto-isolation (年度精选豁免).
    Tiny gap segments (stray photos) do not count. If outliers would exceed
    20% of dated assets, abandon isolation.
    """
    dated_preview = [
        a
        for a in assets
        if a.get("layoutEligible", True)
        and not a.get("timeOutlierExempt")
        and parse_asset_date(a)
    ]
    if segment_sizes is not None:
        if (
            substantial_segment_count(segment_sizes, dated_total=len(dated_preview))
            >= 2
        ):
            return []
    elif segments_count is not None and segments_count >= 2:
        # Legacy callers without sizes: keep old gate (tests / yearbook).
        return []

    dated: list[tuple[date, str]] = []
    for a in assets:
        if not a.get("layoutEligible", True):
            continue
        # User「移回原章」豁免：不再自动隔离
        if a.get("timeOutlierExempt"):
            continue
        d = parse_asset_date(a)
        if d:
            dated.append((d, str(a["id"])))
    if len(dated) < 4:
        return []

    dates = [d for d, _ in dated]
    core = _percentile_dates(dates, 0.10, 0.90)
    if not core:
        return []
    core_lo, core_hi = core
    core_span = max(0, (core_hi - core_lo).days)
    threshold = adaptive_outlier_threshold_days(core_span)
    window_lo = core_lo - timedelta(days=threshold)
    window_hi = core_hi + timedelta(days=threshold)

    outliers = [aid for d, aid in dated if d < window_lo or d > window_hi]
    if not outliers:
        return []
    if len(outliers) / len(dated) > _MAX_OUTLIER_RATIO:
        return []
    return outliers


def apply_time_outlier_marks(
    trip: dict,
    *,
    segments_count: int | None = None,
    segment_sizes: list[int] | None = None,
) -> list[str]:
    """Mark assets with timeOutlier; write curation.excludedTimeOutlierAssetIds."""
    assets = trip.get("assets") or []
    # Clear previous marks on layout-eligible assets
    for a in assets:
        if isinstance(a, dict):
            a.pop("timeOutlier", None)

    outlier_ids = detect_time_outlier_ids(
        assets,
        segments_count=segments_count,
        segment_sizes=segment_sizes,
    )
    for a in assets:
        if isinstance(a, dict) and a.get("id") in set(outlier_ids):
            a["timeOutlier"] = True

    curation = trip.setdefault("curation", {})
    if outlier_ids:
        curation["excludedTimeOutlierAssetIds"] = list(outlier_ids)
    else:
        curation.pop("excludedTimeOutlierAssetIds", None)
    return outlier_ids


def is_time_outlier_asset(asset: dict | None) -> bool:
    return bool(asset and asset.get("timeOutlier"))


def is_appendix_chapter(chapter: dict | None) -> bool:
    if not chapter:
        return False
    curation = chapter.get("curation") or {}
    return bool(curation.get("isAppendix") or chapter.get("isAppendix"))


def appendix_title(n: int) -> str:
    return APPENDIX_TITLE_TMPL.format(n=max(0, int(n)))


def peel_time_outliers_from_buckets(
    buckets: list[list[str]],
    assets_by_id: dict[str, dict],
) -> tuple[list[list[str]], list[str]]:
    """Remove timeOutlier ids from normal buckets; return (cleaned, outlier_ids)."""
    outlier_ids: list[str] = []
    cleaned: list[list[str]] = []
    for bucket in buckets:
        kept: list[str] = []
        for aid in bucket:
            asset = assets_by_id.get(aid)
            if is_time_outlier_asset(asset):
                outlier_ids.append(str(aid))
            else:
                kept.append(aid)
        if kept:
            cleaned.append(kept)
    # Preserve discovery order, unique
    seen: set[str] = set()
    unique: list[str] = []
    for aid in outlier_ids:
        if aid not in seen:
            seen.add(aid)
            unique.append(aid)
    return cleaned, unique


def build_appendix_chapter(
    outlier_ids: list[str],
    *,
    index: int,
    aspects: dict,
    export_layout: str,
    layout_engine: str,
    assets: list[dict],
    orientation_summary: dict | None = None,
    trip_photo_total: int | None = None,
    cfg=None,
) -> dict | None:
    """Compose a special appendix chapter (≥2). Does not go through normalize/cap."""
    if len(outlier_ids) < 2:
        return None
    from travelogue.curation.layout_planner import build_chapters_from_buckets

    chapters = build_chapters_from_buckets(
        [list(outlier_ids)],
        aspects,
        export_layout=export_layout,  # type: ignore[arg-type]
        titles=[appendix_title(len(outlier_ids))],
        layout_engine=layout_engine,
        assets=assets,
        orientation_summary=orientation_summary,
        trip_photo_total=trip_photo_total,
        pattern_hints=["gallery"],
        cfg=cfg,
    )
    if not chapters:
        return None
    ch = chapters[0]
    ch["id"] = f"ch-appendix"
    ch["index"] = int(index)
    title = appendix_title(len(outlier_ids))
    ch["title"] = title  # do not truncate; schema allows 16 for appendix titles
    ch_cur = ch.setdefault("curation", {})
    ch_cur["isAppendix"] = True
    ch_cur["appendixReason"] = APPENDIX_REASON
    ch_cur["appendixAssetIds"] = list(outlier_ids)
    return ch


def exempt_time_outlier(asset: dict) -> None:
    """User restore: keep asset on main timeline on next curate."""
    asset.pop("timeOutlier", None)
    asset["timeOutlierExempt"] = True


def bucket_gap_days(
    left: list[str],
    right: list[str],
    assets_by_id: dict[str, dict],
) -> int | None:
    """Calendar gap between two buckets (excluding timeOutlier assets). None if undated."""
    left_dates = [
        d
        for aid in left
        if not is_time_outlier_asset(assets_by_id.get(aid))
        and (d := parse_asset_date(assets_by_id.get(aid, {})))
    ]
    right_dates = [
        d
        for aid in right
        if not is_time_outlier_asset(assets_by_id.get(aid))
        and (d := parse_asset_date(assets_by_id.get(aid, {})))
    ]
    if not left_dates or not right_dates:
        return None
    lo = max(min(left_dates), min(right_dates))
    hi = min(max(left_dates), max(right_dates))
    # Overlap → 0; else distance between ranges
    if max(left_dates) < min(right_dates):
        return (min(right_dates) - max(left_dates)).days
    if max(right_dates) < min(left_dates):
        return (min(left_dates) - max(right_dates)).days
    return 0
