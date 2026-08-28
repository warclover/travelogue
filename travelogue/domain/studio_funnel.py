"""Journal vertical-slice funnel (MET-01 · Sprint 0).

Four stages only. Does not invent a parallel telemetry store: existing
homepage jsonl is the source, plus one new event for inspectable preview.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final

HOME_ENTER: Final = "home_enter"
IMPORT_SUCCESS: Final = "import_success"
FIRST_PREVIEW: Final = "first_preview"
FIRST_EXPORT: Final = "first_export"

FUNNEL_FIRST_PREVIEW_EVENT: Final = "funnel_first_preview"

# Wizard folder thumbs — never treat as inspectable preview.
WIZARD_PREVIEW_EVENT: Final = "preview_loaded"

FUNNEL_META_ALLOW: Final = frozenset(
    {
        "tripId",
        "trip_id",
        "edition",
        "source",
        "proxy",
        "state",
        "layout",
        "variant",
    }
)

FUNNEL_META_DENY: Final = frozenset(
    {
        "path",
        "filename",
        "fileName",
        "displayTitle",
        "title",
        "caption",
        "copy",
        "prompt",
        "photoPath",
        "folder",
    }
)


@dataclass(frozen=True)
class FunnelStage:
    id: str
    label: str
    events: tuple[str, ...]
    historical_proxy: tuple[str, ...] = ()
    identity: str = "trip"  # "event" | "trip"


FUNNEL_STAGES: Final = (
    FunnelStage(HOME_ENTER, "进入首页", ("homepage_view",), identity="event"),
    FunnelStage(IMPORT_SUCCESS, "导入成功", ("import_success",)),
    FunnelStage(
        FIRST_PREVIEW,
        "首次预览",
        (FUNNEL_FIRST_PREVIEW_EVENT,),
        historical_proxy=("cover_opening_style_render", "preview_open_from_success"),
    ),
    FunnelStage(FIRST_EXPORT, "首次成功导出", ("longshot_export_success",)),
)

FUNNEL_STAGE_IDS: Final = tuple(stage.id for stage in FUNNEL_STAGES)


def trip_id_of(record: dict[str, Any]) -> str | None:
    meta = record.get("meta")
    if not isinstance(meta, dict):
        return None
    raw = meta.get("tripId")
    if raw is None:
        raw = meta.get("trip_id")
    text = str(raw or "").strip()
    return text or None


def _ts_of(record: dict[str, Any]) -> datetime | None:
    raw = str(record.get("ts") or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def sanitize_funnel_meta(meta: dict[str, Any] | None) -> dict[str, Any]:
    """Keep only funnel-safe keys. Reject path / filename / copy / photo fields."""
    if not isinstance(meta, dict):
        return {}
    out: dict[str, Any] = {}
    for key, value in meta.items():
        if key in FUNNEL_META_DENY:
            continue
        if key not in FUNNEL_META_ALLOW:
            continue
        if value is None or value == "":
            continue
        out[key] = value
    return out


def is_journal_or_unknown(record: dict[str, Any]) -> bool:
    meta = record.get("meta")
    if not isinstance(meta, dict):
        return True
    edition = str(meta.get("edition") or "").strip().lower()
    return edition != "portfolio"


def records_for_stage(
    stage: FunnelStage, events: Sequence[dict[str, Any]]
) -> list[dict[str, Any]]:
    pool = events if stage.identity == "event" else [rec for rec in events if is_journal_or_unknown(rec)]
    canonical = [rec for rec in pool if rec.get("event") in stage.events]
    if canonical:
        return canonical
    if not stage.historical_proxy:
        return []
    return [rec for rec in pool if rec.get("event") in stage.historical_proxy]


def first_per_trip(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    ordered = sorted(records, key=lambda rec: (_ts_of(rec) or datetime.min, rec.get("event") or ""))
    for rec in ordered:
        trip_id = trip_id_of(rec)
        if not trip_id or trip_id in seen:
            continue
        seen.add(trip_id)
        out.append(rec)
    return out


@dataclass(frozen=True)
class FunnelStageStat:
    id: str
    label: str
    event_count: int
    unique_trips: int | None
    conversion_from_prev: float | None
    median_seconds_from_prev: float | None
    source: str


@dataclass(frozen=True)
class FunnelBaseline:
    total_events: int
    first_ts: str | None
    last_ts: str | None
    stages: tuple[FunnelStageStat, ...]


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _source_label(stage: FunnelStage, used: Sequence[dict[str, Any]]) -> str:
    if not used:
        return "none"
    names = {str(rec.get("event") or "") for rec in used}
    if names <= set(stage.events):
        return "canonical"
    return "historical_proxy"


def build_funnel_baseline(events: Iterable[dict[str, Any]]) -> FunnelBaseline:
    rows = [rec for rec in events if isinstance(rec, dict) and rec.get("event")]
    timestamps = [ts for rec in rows if (ts := _ts_of(rec)) is not None]
    prev_trip_times: dict[str, datetime] = {}
    prev_unique: int | None = None
    prev_event_count: int | None = None
    stats: list[FunnelStageStat] = []

    for stage in FUNNEL_STAGES:
        used = records_for_stage(stage, rows)
        if stage.identity == "event":
            event_count = len(used)
            unique = None
            conversion = None
        else:
            firsts = first_per_trip(used)
            event_count = len(used)
            unique = len(firsts)
            if prev_unique:
                conversion = unique / prev_unique
            elif prev_event_count:
                conversion = unique / prev_event_count
            else:
                conversion = None

            deltas: list[float] = []
            for rec in firsts:
                trip_id = trip_id_of(rec)
                ts = _ts_of(rec)
                if not trip_id or ts is None:
                    continue
                prev_ts = prev_trip_times.get(trip_id)
                if prev_ts is not None:
                    deltas.append((ts - prev_ts).total_seconds())
                prev_trip_times[trip_id] = ts
            median = _median(deltas)
            stats.append(
                FunnelStageStat(
                    id=stage.id,
                    label=stage.label,
                    event_count=event_count,
                    unique_trips=unique,
                    conversion_from_prev=conversion,
                    median_seconds_from_prev=median,
                    source=_source_label(stage, used),
                )
            )
            prev_unique = unique
            prev_event_count = event_count
            continue

        stats.append(
            FunnelStageStat(
                id=stage.id,
                label=stage.label,
                event_count=event_count,
                unique_trips=unique,
                conversion_from_prev=conversion,
                median_seconds_from_prev=None,
                source=_source_label(stage, used),
            )
        )
        prev_event_count = event_count
        prev_unique = None

    first_ts = min(timestamps).isoformat() if timestamps else None
    last_ts = max(timestamps).isoformat() if timestamps else None
    return FunnelBaseline(
        total_events=len(rows),
        first_ts=first_ts,
        last_ts=last_ts,
        stages=tuple(stats),
    )


def format_funnel_baseline(baseline: FunnelBaseline, *, source_path: str) -> str:
    lines = [
        "Travelogue journal 竖切漏斗 · 本机基线",
        f"Source: {source_path}",
        f"Events: {baseline.total_events}",
    ]
    if baseline.first_ts and baseline.last_ts:
        lines.append(f"Range: {baseline.first_ts} .. {baseline.last_ts}")
    lines.append("Privacy: stage / duration / error class only; no path, filename, title, or photo.")
    lines.append("")
    lines.append(
        f"{'stage':<16} {'events':>7} {'trips':>7} {'from_prev':>10} {'median':>10}  source"
    )
    for stage in baseline.stages:
        trips = "-" if stage.unique_trips is None else str(stage.unique_trips)
        conv = "-" if stage.conversion_from_prev is None else f"{stage.conversion_from_prev * 100:.1f}%"
        if stage.median_seconds_from_prev is None:
            median = "-"
        else:
            seconds = stage.median_seconds_from_prev
            median = f"{seconds / 60:.1f}m" if seconds >= 60 else f"{seconds:.0f}s"
        lines.append(
            f"{stage.id:<16} {stage.event_count:>7} {trips:>7} {conv:>10} {median:>10}  {stage.source}"
        )
    lines.append("")
    lines.append("home_enter → import 用事件比（同一安装会多次打开首页）。")
    lines.append("import 之后按 trip 首次到达计；preview_loaded 是向导缩略图，不计入首次预览。")
    return "\n".join(lines) + "\n"
