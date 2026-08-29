"""Portfolio chapter builder (DPI W2). page-* screens, no journal chrome."""

from __future__ import annotations

from pathlib import Path

from travelogue.config import AppConfig, get_config
from travelogue.curation.screen_tone import enrich_screen_tones
from travelogue.render.context import build_layout_screen
from travelogue.render.context_types import ChapterRenderContext
from travelogue.render.journal_chapters import ChaptersRenderBundle
from travelogue.render.surface import SurfaceContext
from travelogue.types.trip_hot import TripHot


def overlay_portfolio_epilogue_stats(trip: dict, stats: dict) -> dict:
    """PIS BLK-03 · 作品集辑封默认只写「P 张照片」，不写天数。"""
    photo = 0
    studio = trip.get("studio") if isinstance(trip.get("studio"), dict) else {}
    folio = studio.get("portfolio") if isinstance(studio.get("portfolio"), dict) else {}
    try:
        photo = int(folio.get("photosPlaced") or 0)
    except (TypeError, ValueError):
        photo = 0
    if photo <= 0:
        try:
            photo = int((stats or {}).get("photoCount") or 0)
        except (TypeError, ValueError):
            photo = 0
    out = dict(stats or {})
    out["photoCount"] = photo
    out["summaryLine"] = f"{photo} 张照片" if photo else "照片"
    return out


def build_portfolio_chapters(
    trip: TripHot | dict,
    surface: SurfaceContext,
    *,
    trip_root: Path | None,
    meta_title: str,
    hook: str = "",
    cfg: AppConfig | None = None,
) -> ChaptersRenderBundle:
    """Pure-image magazine body: skip empty chapters, strip narrative, no trip-index."""
    del hook  # portfolio_body never surfaces chapter/foreword copy
    assets = surface.assets
    is_draft = surface.is_draft
    image_layout = surface.image_layout
    render_cfg = cfg or get_config()
    raw_chapters = trip.get("chapters") or []
    chapters_out: list[ChapterRenderContext] = []
    global_screen_index = 0

    for i, ch in enumerate(raw_chapters):
        idx = ch.get("index", i + 1)
        raw_screens = list(ch.get("screens") or [])
        if not raw_screens:
            continue
        raw_screens = enrich_screen_tones(
            raw_screens,
            assets,
            trip_root=trip_root,
            chapter_index=idx,
        )
        from travelogue.layout_engine.editorial.four_mix import apply_editorial_4mix_slot_fits
        from travelogue.layout_engine.editorial.portrait_row import apply_editorial_row_slot_fits

        screens_out = []
        for seq, sc in enumerate(raw_screens, start=1):
            sc = apply_editorial_row_slot_fits(dict(sc), assets, trip=trip)
            sc = apply_editorial_4mix_slot_fits(sc, assets, trip=trip, cfg=render_cfg)
            if not (sc.get("slots") or []):
                continue
            global_screen_index += 1
            screens_out.append(
                build_layout_screen(
                    sc,
                    assets,
                    meta_title=meta_title,
                    export_layout=image_layout,
                    eager=i == 0 and seq == 1,
                    screen_index=global_screen_index,
                    chapter_index=f"{idx:02d}",
                    chapter_id=str(ch.get("id") or ""),
                    is_draft=is_draft,
                    strip_narrative_copy=True,
                    folio_lite=False,
                    stage_aspect="16:9",
                )
            )
        if not screens_out:
            continue
        chapters_out.append(
            {
                "id": ch["id"],
                "patternId": ch.get("patternId", ""),
                "index": f"{idx:02d}",
                "title": str(ch.get("title") or "").strip(),
                "isAppendix": False,
                "lead": "",
                "hasLead": False,
                "decorLine": "",
                "hasDecorLine": False,
                "editableLead": False,
                "editLeadPath": None,
                "editableDecorLine": False,
                "editDecorLinePath": None,
                "hasMemoryAnchors": False,
                "memoryAnchors": None,
                "useScreensEngine": True,
                "screens": screens_out,
                "hasScreenSpread": False,
                "screenSpread": {},
                "items": [],
                "useChapterSeparator": False,
                "chapterSeparatorStyle": "",
                "showDivider": False,
            }
        )

    return ChaptersRenderBundle(
        chapters_out=chapters_out,
        foreword_spread=None,
        has_foreword_spread=False,
        trip_index_entries=[],
        has_trip_index=False,
        featured_grid_cards=[],
        has_featured_grid=False,
    )
