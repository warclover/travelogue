"""Trip-level date range and ingest warnings (multi-segment safe)."""

from __future__ import annotations

from datetime import date, datetime

from travelogue.media.image_ops import filter_trip_dates


def _parse_asset_date(raw: object) -> date | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).date()
    except ValueError:
        return None


def trip_meta_date_range(
    assets: list[dict],
) -> tuple[date | None, date | None]:
    """
    Full-book display range: min/max of takenAt after light outlier trim.

    Unlike legacy meta logic, does not collapse multi-year albums to a single day.
    """
    dated: list[date] = []
    sources: list[str] = []
    for a in assets:
        d = _parse_asset_date(a.get("takenAt"))
        if d:
            dated.append(d)
            sources.append(a.get("dateSource") or "mtime")

    if not dated:
        return None, None
    if len(dated) <= 2:
        return min(dated), max(dated)

    trimmed = filter_trip_dates(dated, sources=sources)
    if len(trimmed) >= 2:
        return min(trimmed), max(trimmed)
    return min(dated), max(dated)


def apply_meta_dates_from_assets(trip: dict) -> list[str]:
    """Set meta.dateStart/dateEnd from assets; return ingest warnings."""
    assets = trip.get("assets") or []
    warnings: list[str] = []
    d0, d1 = trip_meta_date_range(assets)
    if d0 and d1:
        meta = trip.setdefault("meta", {})
        meta["dateStart"] = d0.isoformat()
        meta["dateEnd"] = d1.isoformat()
        if d0 == d1:
            low = sum(1 for a in assets if a.get("dateConfidence") == "low")
            if low > len(assets) * 0.4:
                warnings.append(
                    "多数照片无 EXIF 日期，meta 显示为单日估算；分章仍以各图 takenAt 为准"
                )
    warn = ingest_date_source_warning(assets)
    if warn:
        warnings.append(warn)
    return warnings


def ingest_date_source_warning(assets: list[dict]) -> str | None:
    if len(assets) < 4:
        return None
    low = sum(1 for a in assets if a.get("dateConfidence") == "low")
    if low <= len(assets) * 0.5:
        return None
    return (
        f"日期来源：{low}/{len(assets)} 张为文件时间(mtime)，"
        "建议在相册中保留 EXIF 或使用带日期的文件名"
    )
