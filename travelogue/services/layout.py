"""Agent 1.5 · Layout Composer — apply layout rules to trip.json."""

from __future__ import annotations

from dataclasses import dataclass

from travelogue.config import AppConfig
from travelogue.util.datetime_ import utc_now_iso as _utc_now_iso
from travelogue.curation.layout_planner import build_chapters_from_plan, summarize_orientations
from travelogue.curation.layout_planner import aspect_kind_for_asset as _aspect_kind_for_asset
from travelogue.layout_contract import (
    LAYOUT_PLAN_VERSION,
    VALID_EXPORT_LAYOUTS,
    format_layout_summary,
)
from travelogue.services.pipeline_state import set_layout_status


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
