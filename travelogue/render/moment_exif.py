"""Format one-line EXIF footnote for moment-screen (Phase 23)."""

from __future__ import annotations

from datetime import date, datetime


def _month_label(taken_at: str | None) -> str | None:
    if not taken_at:
        return None
    try:
        dt = datetime.fromisoformat(str(taken_at).replace("Z", "+00:00"))
        return f"{dt.year}.{dt.month:02d}"
    except ValueError:
        return None


def _day_label(taken_at: str | None) -> str | None:
    """Month.day when place is missing — avoids identical「2025.04 · 正午」spam."""
    if not taken_at:
        return None
    try:
        dt = datetime.fromisoformat(str(taken_at).replace("Z", "+00:00"))
        return f"{dt.year}.{dt.month:02d}.{dt.day:02d}"
    except ValueError:
        return None


def _daypart_label(taken_at: str | None) -> str | None:
    if not taken_at:
        return None
    try:
        dt = datetime.fromisoformat(str(taken_at).replace("Z", "+00:00"))
        hour = dt.hour
        if 5 <= hour < 9:
            return "清晨"
        if 9 <= hour < 12:
            return "上午"
        if 12 <= hour < 14:
            return "正午"
        if 14 <= hour < 17:
            return "下午"
        if 17 <= hour < 20:
            return "黄昏"
        return "夜晚"
    except ValueError:
        return None


def _place_label(asset: dict) -> str | None:
    place = asset.get("place")
    if isinstance(place, dict):
        city = str(place.get("city") or "").strip()
        if city:
            return city
    for key in ("location", "city", "placeName"):
        val = asset.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _parse_taken_date(taken_at: str | None) -> date | None:
    if not taken_at:
        return None
    try:
        return datetime.fromisoformat(str(taken_at).replace("Z", "+00:00")).date()
    except ValueError:
        return None


def date_outside_day_span(
    taken_at: str | None, day_span: list[str] | None
) -> bool:
    """True when asset calendar day is outside chapter ``daySpan`` (inclusive).

    D-SFI-06 · 图注日期与章区间矛盾时抑制绝对年份。
    """
    taken = _parse_taken_date(taken_at)
    if taken is None or not day_span:
        return False
    days: list[date] = []
    for raw in day_span:
        try:
            days.append(date.fromisoformat(str(raw)[:10]))
        except ValueError:
            continue
    if not days:
        return False
    return taken < min(days) or taken > max(days)


def format_moment_exif_line(
    asset: dict,
    *,
    day_span: list[str] | None = None,
    trip_primary_year: int | None = None,
) -> str | None:
    """Build footnote segments; returns None when fewer than 2 valid parts.

    BE-SFI-09 · ``dateConfidence=low`` 或与章 ``daySpan`` 矛盾时抑制绝对年份，
    仅保留时段（+地点）。
    SNR D-SNR-05 · 相对行程主年离群（≥2 年）→「往年 · 时段」或省略年。
    """
    segments: list[str] = []
    taken = str(asset.get("takenAt") or "") or None
    # PMX D7 · timeOutlier 不得上读者面绝对日期
    # SNR · 行程年离群同纪律
    year_outlier = False
    try:
        from travelogue.domain.narrative_posture import photo_year_is_outlier

        year_outlier = photo_year_is_outlier(taken, trip_primary_year)
    except Exception:
        year_outlier = False
    if asset.get("timeOutlier") or year_outlier:
        daypart_only = _daypart_label(taken)
        place_only = _place_label(asset)
        if year_outlier and not asset.get("timeOutlier"):
            # COPY-SNR-T01
            try:
                from travelogue.domain.studio_events import append_studio_homepage_event

                append_studio_homepage_event(
                    "snr_outlier_year_suppressed",
                    {"count": 1, "mode": "wangnian"},
                )
            except Exception:
                pass
            if daypart_only:
                return f"往年 · {daypart_only}"
            return "往年"
        if place_only and daypart_only:
            return f"{place_only} · {daypart_only}"
        return place_only or daypart_only
    low_conf = str(asset.get("dateConfidence") or "").strip().lower() == "low"
    contradict = date_outside_day_span(taken, day_span)
    suppress_year = low_conf or contradict

    place = _place_label(asset)
    if place:
        segments.append(place)
        if not suppress_year:
            month = _month_label(taken)
            if month:
                segments.append(month)
    elif not suppress_year:
        day = _day_label(taken)
        if day:
            segments.append(day)

    daypart = _daypart_label(taken)
    if daypart:
        segments.append(daypart)

    # BE-FST-04 / D-FST-07 · 读者面禁止相机 Make/Model 与曝光串
    _ = asset.get("exif")

    if len(segments) < 2:
        if place and len(segments) == 1:
            return place
        if daypart and len(segments) == 1:
            return daypart
        return None
    return " · ".join(segments)

