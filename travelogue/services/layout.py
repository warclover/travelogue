"""Agent 1.5 · Layout Composer — apply layout rules to trip.json."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from travelogue.config import AppConfig
from travelogue.curation.layout_planner import build_chapters_from_plan, summarize_orientations
from travelogue.curation.layout_planner import aspect_kind_for_asset as _aspect_kind_for_asset
from travelogue.services.pipeline_state import set_layout_status

LAYOUT_PLAN_VERSION = "0.2.0"
VALID_EXPORT_LAYOUTS = frozenset({"auto", "mobile", "web"})


class LayoutError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass
class LayoutResult:
    summary_text: str
    orientation_summary: dict
    chapter_count: int
    item_count: int


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def extract_ordered_asset_ids(trip: dict) -> list[str]:
    """Flatten chapter items in order; dedupe while preserving first occurrence."""
    seen: set[str] = set()
    ordered: list[str] = []
    for ch in trip.get("chapters", []):
        for it in ch.get("items", []):
            aids: list[str] = []
            itype = it.get("type")
            if itype == "media-card":
                aids = [it.get("assetId", "")]
            elif itype in ("media-row", "media-scroll"):
                aids = list(it.get("assetIds") or [])
            for aid in aids:
                if aid and aid not in seen:
                    seen.add(aid)
                    ordered.append(aid)
    return ordered


def _body_asset_ids(trip: dict) -> list[str]:
    assets = trip.get("assets") or []
    cover = trip.get("coverAssetId")
    ordered = extract_ordered_asset_ids(trip)
    if ordered:
        body = [aid for aid in ordered if aid != cover]
        if len(body) >= 4:
            return body
    return [a["id"] for a in assets if a.get("id") != cover]


def _chapter_titles(trip: dict) -> list[str] | None:
    titles = [str(ch.get("title", "")).strip() for ch in trip.get("chapters", [])]
    titles = [t for t in titles if t]
    return titles if len(titles) >= 2 else None


def format_layout_summary(summary: dict, chapters: list[dict]) -> str:
    """Human-readable summary for CLI / G1."""
    parts = [
        f"共 {summary.get('total', 0)} 张",
        f"横 {summary.get('landscape', 0)}",
        f"竖 {summary.get('portrait', 0)}",
    ]
    if summary.get("square"):
        parts.append(f"方 {summary['square']}")
    if summary.get("panorama"):
        parts.append(f"全景 {summary['panorama']}")
    if summary.get("tall"):
        parts.append(f"超长 {summary['tall']}")
    engine = None
    row_counts: dict[str, int] = {}
    slots: dict[str, int] = {}
    screen_counts: dict[str, int] = {}
    screen_total = 0
    for ch in chapters:
        if ch.get("screens"):
            engine = engine or "screens"
            for sc in ch.get("screens") or []:
                screen_total += 1
                pid = sc.get("patternId") or "screen"
                screen_counts[pid] = screen_counts.get(pid, 0) + 1
        for it in ch.get("items", []):
            rl = it.get("rowLayout")
            if rl:
                row_counts[rl] = row_counts.get(rl, 0) + 1
            if it.get("type") == "media-card":
                slot = (it.get("layout") or {}).get("slot")
                if slot:
                    slots[slot] = slots.get(slot, 0) + 1

    hints: list[str] = []
    if row_counts.get("landscape-triple"):
        hints.append(f"{row_counts['landscape-triple']} 组横图三联")
    if row_counts.get("portrait-triple"):
        hints.append(f"{row_counts['portrait-triple']} 组竖图三联")
    if row_counts.get("portrait-pair"):
        hints.append(f"{row_counts['portrait-pair']} 组竖图双列")
    if row_counts.get("square-triple"):
        hints.append(f"{row_counts['square-triple']} 组方图三宫格")
    if row_counts.get("square-pair"):
        hints.append(f"{row_counts['square-pair']} 组方图双列")
    if slots.get("panorama"):
        hints.append(f"{slots['panorama']} 条全景宽条")

    if engine == "screens" and screen_total:
        parts.append("引擎 screens")
        parts.append(f"{screen_total} 屏")
        for pid, n in sorted(screen_counts.items(), key=lambda x: (-x[1], x[0])):
            short = pid.replace("screen-", "").replace("landscape", "横").replace("portrait", "竖")
            short = short.replace("square", "方").replace("panorama", "全景")
            if pid.endswith("-3"):
                hints.append(f"{n}×{short}三联")
            elif pid.endswith("-4"):
                hints.append(f"{n}×{short}四宫格")
            elif pid.endswith("-9"):
                hints.append(f"{n}×{short}九宫格")
            elif pid.endswith("-1"):
                hints.append(f"{n}×{short}单张")
            else:
                hints.append(f"{n}×{short}")

    parts.append(f"版式 {summary.get('export_layout', 'mobile')}")

    line1 = " · ".join(parts)
    if hints:
        return f"{line1}；{'、'.join(hints)}"
    return line1


def apply_layout_to_trip(
    trip: dict,
    *,
    export_layout: str | None = None,
    layout_engine: str | None = None,
    preserve_titles: bool = True,
    cfg: AppConfig | None = None,
) -> LayoutResult:
    """
    Recompute chapters[].items[] from asset aspects and exportLayout.

    Does not re-ingest pixels or change coverAssetId.
    """
    from travelogue.curation.screen_planner import (
        LAYOUT_ENGINE_LEGACY,
        LAYOUT_ENGINE_SCREENS,
        LAYOUT_ENGINE_VERSION_SCREENS,
    )

    layout = export_layout or trip.get("exportLayout") or "mobile"
    if layout not in VALID_EXPORT_LAYOUTS:
        raise LayoutError("E_LAYOUT_EXPORT", f"export_layout must be one of {sorted(VALID_EXPORT_LAYOUTS)}")

    from travelogue.config import default_web_layout_engine

    engine = (
        layout_engine
        or trip.get("layoutEngine")
        or default_web_layout_engine(layout, cfg=cfg)
    )
    if engine not in (LAYOUT_ENGINE_LEGACY, LAYOUT_ENGINE_SCREENS):
        raise LayoutError("E_LAYOUT_ENGINE", "layout_engine must be legacy or screens")

    assets = trip.get("assets") or []
    if len(assets) < 4:
        raise LayoutError("E_LAYOUT_TOO_FEW", "need at least 4 assets to layout")

    aspects = {a["id"]: _aspect_kind_for_asset(a) for a in assets if a.get("id")}
    body_ids = _body_asset_ids(trip)
    if len(body_ids) < 4:
        raise LayoutError("E_LAYOUT_TOO_FEW", "need at least 4 body assets after excluding cover")

    titles = _chapter_titles(trip) if preserve_titles else None
    chapters, _ = build_chapters_from_plan(
        body_ids,
        aspects,
        export_layout=layout,  # type: ignore[arg-type]
        titles=titles,
        layout_engine=engine,
        assets=assets,
    )

    summary = summarize_orientations(assets, export_layout=layout)  # type: ignore[arg-type]
    summary_dict = summary.to_dict()

    trip["exportLayout"] = layout
    trip["layoutEngine"] = engine
    if engine == LAYOUT_ENGINE_SCREENS:
        trip["layoutEngineVersion"] = LAYOUT_ENGINE_VERSION_SCREENS
    trip["chapters"] = chapters
    curation = trip.setdefault("curation", {})
    curation["orientationSummary"] = summary_dict
    curation["layoutPlanVersion"] = LAYOUT_PLAN_VERSION
    curation["layoutPlanRunId"] = f"layout-{_utc_now_iso()}"

    pipe = trip.setdefault("pipeline", {})
    runs = pipe.setdefault("runs", [])
    runs.append(
        {
            "runId": curation["layoutPlanRunId"],
            "agent": "layout",
            "startedAt": _utc_now_iso(),
            "finishedAt": _utc_now_iso(),
            "model": None,
        }
    )
    trip["updatedAt"] = _utc_now_iso()
    set_layout_status(trip, "layout_draft")

    item_count = sum(len(ch.get("items", [])) for ch in chapters)
    summary_text = format_layout_summary(summary_dict, chapters)
    return LayoutResult(
        summary_text=summary_text,
        orientation_summary=summary_dict,
        chapter_count=len(chapters),
        item_count=item_count,
    )


def apply_layout_from_album_build(
    body_ids: list[str],
    assets: list[dict],
    aspects: dict,
    *,
    export_layout: str = "mobile",
    titles: list[str] | None = None,
) -> tuple[list[dict], dict, str]:
    """Shared path for demo from_album (ingest + layout in one step)."""
    chapters, _ = build_chapters_from_plan(
        body_ids,
        aspects,
        export_layout=export_layout,  # type: ignore[arg-type]
        titles=titles,
    )
    summary = summarize_orientations(assets, export_layout=export_layout)  # type: ignore[arg-type]
    summary_dict = summary.to_dict()
    summary_text = format_layout_summary(summary_dict, chapters)
    return chapters, summary_dict, summary_text
