"""Journal chapter builder. Stages: inputs → folio → moment/longshot → list → extras."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from travelogue.config import AppConfig
from travelogue.render.context_types import (
    BreathPauseItemContext,
    ChapterRenderContext,
    FeaturedGridCardContext,
    ForewordSpreadContext,
    ScreenSpreadContext,
    TripIndexEntryContext,
)
from travelogue.render.journal_folio import (
    JournalFolioState,
    build_journal_folio_extras,
    resolve_journal_folio_plan,
)
from travelogue.render.journal_screens import build_chapter_screens
from travelogue.render.screen_tone import build_chapter_separator_ticket, chapter_separator_style
from travelogue.render.surface import SurfaceContext
from travelogue.types.trip_hot import TripHot


@dataclass
class ChaptersRenderBundle:
    """Chapter list and folio extras (enrich phase)."""

    chapters_out: list[ChapterRenderContext]
    foreword_spread: ForewordSpreadContext | None
    has_foreword_spread: bool
    trip_index_entries: list[TripIndexEntryContext]
    has_trip_index: bool
    featured_grid_cards: list[FeaturedGridCardContext]
    has_featured_grid: bool


@dataclass(frozen=True)
class JournalChapterInputs:
    aspects_map: dict
    layout_eligible_count: int
    featured_ids: frozenset[str]
    moment_screen_label: str
    trip_primary_year: Any
    exif_pool: frozenset[str]
    pool_ids: list[str]


def prepare_journal_chapter_inputs(
    trip: dict,
    *,
    moment_pool_ids: list[str] | None,
    moment_exif_pool_ids: frozenset[str] | None,
    show_signature_label: bool,
) -> JournalChapterInputs:
    from travelogue.curation.layout_planner import aspect_kind_for_asset
    from travelogue.render.moment_screen import moment_label_for_trip
    from travelogue.render.reading_profile import featured_asset_ids as collect_featured_ids

    aspects_map = {a["id"]: aspect_kind_for_asset(a) for a in trip.get("assets", []) if a.get("id")}
    layout_eligible_count = sum(
        1 for a in trip.get("assets", []) if a.get("layoutEligible", True)
    )
    try:
        from travelogue.domain.narrative_posture import trip_primary_year as _resolve_trip_year

        trip_primary_year = _resolve_trip_year(trip)
    except Exception:
        trip_primary_year = None
    return JournalChapterInputs(
        aspects_map=aspects_map,
        layout_eligible_count=layout_eligible_count,
        featured_ids=frozenset(collect_featured_ids(trip)),
        moment_screen_label=moment_label_for_trip(trip) if show_signature_label else "",
        trip_primary_year=trip_primary_year,
        exif_pool=moment_exif_pool_ids or frozenset(),
        pool_ids=list(moment_pool_ids or []),
    )


def apply_journal_moment_and_longshot(
    trip: dict,
    surface: SurfaceContext,
    *,
    cfg: AppConfig | None,
    moment_signature_id: str,
    pool_ids: list[str],
    pool_solo: bool,
) -> list:
    assets = surface.assets
    raw_chapters = trip.get("chapters") or []
    if moment_signature_id and pool_ids and pool_solo:
        from travelogue.curation.moment_scoring import ensure_pool_assets_solo_screens

        ensure_pool_assets_solo_screens(
            raw_chapters,
            pool_ids,
            moment_signature_id,
            assets_by_id=assets,
            cfg=(cfg.curate.moment if cfg is not None else None),
        )
    elif moment_signature_id:
        from travelogue.curation.moment_scoring import ensure_moment_asset_in_chapters

        ensure_moment_asset_in_chapters(
            raw_chapters,
            moment_signature_id,
            assets_by_id=assets,
        )
    if surface.is_longshot_surface:
        from travelogue.config import get_config
        from travelogue.curation.longshot_filter import chapters_for_longshot_render
        from travelogue.curation.phase6_rollout import resolve_app_config_for_trip

        base_cfg = cfg or get_config()
        trip_id = str(trip.get("tripId") or "").strip()
        effective_cfg = (
            resolve_app_config_for_trip(base_cfg, trip_id) if trip_id else base_cfg
        )
        assets_by_id = {a["id"]: a for a in (trip.get("assets") or []) if a.get("id")}
        raw_chapters = chapters_for_longshot_render(
            raw_chapters,
            max_screens=effective_cfg.layout.scoring.max_screens_per_chapter,
            assets_by_id=assets_by_id,
            enable_mmr=effective_cfg.curate.enable_mmr_diversity,
            mmr_lambda=effective_cfg.curate.longshot_mmr_lambda,
            max_consecutive_same_pattern=effective_cfg.curate.max_consecutive_same_pattern,
        )
    return raw_chapters


def build_journal_chapter_list(
    trip: dict,
    surface: SurfaceContext,
    raw_chapters: list,
    inputs: JournalChapterInputs,
    folio: JournalFolioState,
    *,
    trip_root: Path | None,
    meta_title: str,
    hook: str,
    cfg: AppConfig | None,
    moment_signature_id: str,
    show_moment_exif: bool,
    show_signature_label: bool,
) -> list[ChapterRenderContext]:
    """Chapter loop: screens, items, copy, separator. Screen loop is in journal_screens."""
    from travelogue.curation.chapter_items import resolve_chapter_items_for_render
    from travelogue.render.context import (
        build_media_card,
        build_media_row,
        build_media_scroll,
        build_screen_spread,
        chapter_divider,
    )

    assets = surface.assets
    strip_narrative_copy = surface.strip_narrative_copy
    is_draft = surface.is_draft
    folio_full = surface.folio_full
    use_screens_global = surface.use_screens_global
    is_longshot_surface = surface.is_longshot_surface
    layout_engine = surface.layout_engine
    image_layout = surface.image_layout
    chapters_out: list[ChapterRenderContext] = []
    global_screen_index = 0
    chapter_total = len(raw_chapters)

    for i, ch in enumerate(raw_chapters):
        idx = ch.get("index", i + 1)
        curation = ch.get("curation") or {}
        anchors = curation.get("memoryAnchors") or []
        use_screens = (
            use_screens_global and not is_longshot_surface and bool(ch.get("screens"))
        )
        screens_out, raw_screens_for_spread, global_screen_index = build_chapter_screens(
            ch,
            chapter_loop_index=i,
            idx=idx,
            trip=trip,
            surface=surface,
            trip_root=trip_root,
            meta_title=meta_title,
            featured_ids=inputs.featured_ids,
            grid_exclude=folio.grid_exclude,
            global_screen_index=global_screen_index,
            moment_exif_pool_ids=inputs.exif_pool,
            moment_signature_id=moment_signature_id,
            show_moment_exif=show_moment_exif,
            show_signature_label=show_signature_label,
            moment_screen_label=inputs.moment_screen_label,
            trip_primary_year=inputs.trip_primary_year,
            cfg=cfg,
        )

        screen_spread: ScreenSpreadContext | None = None
        has_screen_spread = False
        if folio_full and use_screens and raw_screens_for_spread:
            spread_src = raw_screens_for_spread[-1]
            screen_spread = build_screen_spread(
                ch,
                spread_src,
                assets,
                meta_title=meta_title,
                export_layout=image_layout,
                trip_hook=hook,
            )
            has_screen_spread = screen_spread is not None

        items_out: list = []
        from travelogue.domain.longshot_density import is_compact_longshot

        compact_ls = is_longshot_surface and is_compact_longshot(trip)
        chapter_items = resolve_chapter_items_for_render(
            ch,
            export_layout=image_layout,
            layout_engine=layout_engine,
            is_longshot=is_longshot_surface,
            aspects=inputs.aspects_map,
            assets_map=assets,
            trip_photo_total=inputs.layout_eligible_count,
            compact_longshot=compact_ls,
        )
        if is_longshot_surface and not compact_ls:
            from travelogue.curation.breath_pauses import interleave_breath_items

            chapter_items = interleave_breath_items(chapter_items)
        caption_on_asset = is_longshot_surface and bool(ch.get("screens"))
        for j, it in enumerate(chapter_items):
            itype = it.get("type")
            eager = i == 0 and j == 0
            if itype == "breath-pause" and compact_ls:
                continue
            if itype == "media-card":
                aid = it.get("assetId", "")
                asset = assets.get(aid)
                if not asset:
                    continue
                items_out.append(
                    build_media_card(
                        it,
                        asset,
                        meta_title=meta_title,
                        export_layout=image_layout,
                        is_draft=is_draft,
                        eager=eager,
                        photos_only=strip_narrative_copy,
                        chapter_id=ch["id"],
                        item_index=j,
                        caption_on_asset=caption_on_asset,
                    )
                )
            elif itype == "media-row":
                items_out.append(
                    build_media_row(
                        it,
                        assets,
                        meta_title=meta_title,
                        export_layout=image_layout,
                        is_draft=is_draft,
                        chapter_id=ch["id"],
                        item_index=j,
                        photos_only=strip_narrative_copy,
                    )
                )
            elif itype == "media-scroll":
                items_out.append(
                    build_media_scroll(
                        it,
                        assets,
                        meta_title=meta_title,
                        export_layout=image_layout,
                        is_draft=is_draft,
                        chapter_id=ch["id"],
                        item_index=j,
                        photos_only=strip_narrative_copy,
                    )
                )
            elif itype == "breath-pause":
                tone = (ch.get("curation") or {}).get("tone") or {}
                r = int(tone.get("r", 26)) if isinstance(tone, dict) else 26
                g = int(tone.get("g", 32)) if isinstance(tone, dict) else 32
                b = int(tone.get("b", 38)) if isinstance(tone, dict) else 38
                breath_ctx: BreathPauseItemContext = {
                    "isBreathPause": True,
                    "breathLabel": it.get("label") or "···",
                    "breathStyle": f"--breath-tone: rgb({r}, {g}, {b});",
                }
                items_out.append(breath_ctx)

        use_chapter_separator = (
            use_screens_global
            and not is_longshot_surface
            and surface.include_breath
            and int(idx) > 1
        )
        divider_ctx = chapter_divider(
            ch,
            idx,
            meta=trip.get("meta") or {},
            intent=trip.get("intent"),
            assets=trip.get("assets") or [],
        )
        curation = ch.get("curation") or {}

        from travelogue.domain.share_face_copy import (
            record_stub_hit,
            sanitize_share_copy_tracked,
        )

        ch_edited = bool(ch.get("edited"))
        surface_name = "longshot" if is_longshot_surface else ("draft" if is_draft else "share")
        trip_id = str(trip.get("tripId") or "").strip() or None
        pattern_id = str(ch.get("patternId") or "") or None

        lead = (ch.get("lead") or "").strip()
        if strip_narrative_copy:
            lead = ""
        if i == 0 and folio.has_foreword_spread:
            lead = ""
        elif lead:
            lead, blanked = sanitize_share_copy_tracked(
                lead, title=meta_title, kind="lead", edited=ch_edited
            )
            if blanked:
                record_stub_hit(
                    surface=surface_name, field="lead", pattern_id=pattern_id, trip_id=trip_id
                )
        if not lead and not strip_narrative_copy and not (i == 0 and folio.has_foreword_spread):
            from travelogue.services.narrate import stub_face_lead

            assets_by_id = {
                str(a.get("id")): a
                for a in (trip.get("assets") or [])
                if isinstance(a, dict) and a.get("id")
            }
            lead = stub_face_lead(
                ch,
                assets=assets_by_id,
                chapter_index=int(ch.get("index") or i + 1),
                chapter_total=len(raw_chapters) if raw_chapters else 1,
            )

        decor_line = (ch.get("decorLine") or "").strip()
        if strip_narrative_copy:
            decor_line = ""
        elif decor_line:
            decor_line, blanked = sanitize_share_copy_tracked(
                decor_line, title=meta_title, kind="decorLine", edited=ch_edited
            )
            if blanked:
                record_stub_hit(
                    surface=surface_name,
                    field="decorLine",
                    pattern_id=pattern_id,
                    trip_id=trip_id,
                )

        ch_title = str(ch.get("title") or "").strip()
        if ch_title:
            cleaned_title, blanked = sanitize_share_copy_tracked(
                ch_title, title=meta_title, kind="title", edited=ch_edited
            )
            if blanked:
                record_stub_hit(
                    surface=surface_name, field="title", pattern_id=pattern_id, trip_id=trip_id
                )
                day_span = curation.get("daySpan") or []
                if day_span:
                    try:
                        from datetime import date as _date

                        ch_title = _date.fromisoformat(str(day_span[0])).strftime("%m月%d日")
                    except ValueError:
                        ch_title = str(day_span[0])
                else:
                    ch_title = cleaned_title
            else:
                ch_title = cleaned_title

        if compact_ls and divider_ctx.get("showDivider") and ch_title:
            day_span = curation.get("daySpan") or []
            if day_span:
                try:
                    from datetime import date as _date

                    d0 = _date.fromisoformat(str(day_span[0])[:10])
                    syn = f"{d0.month}月{d0.day}日"
                    if syn in str(ch_title).replace(" ", ""):
                        divider_ctx = {"showDivider": False}
                except ValueError:
                    pass

        is_appendix = bool(curation.get("isAppendix") or ch.get("isAppendix"))
        ch_ctx: ChapterRenderContext = {
            "id": ch["id"],
            "patternId": ch.get("patternId", ""),
            "index": f"{idx:02d}",
            "title": ch_title,
            "isAppendix": is_appendix,
            "lead": lead,
            "hasLead": bool(lead) and not is_appendix,
            "decorLine": decor_line,
            "hasDecorLine": bool(decor_line) and not is_appendix,
            "editableLead": is_draft and bool((ch.get("lead") or "").strip()),
            "editLeadPath": f"chapters.{ch['id']}.lead" if is_draft else None,
            "editableDecorLine": is_draft and bool((ch.get("decorLine") or "").strip()),
            "editDecorLinePath": (
                f"chapters.{ch['id']}.decorLine"
                if is_draft and (ch.get("decorLine") or "").strip()
                else None
            ),
            "hasMemoryAnchors": bool(anchors),
            "memoryAnchors": ",".join(anchors) if anchors else None,
            "useScreensEngine": use_screens,
            "screens": screens_out,
            "hasScreenSpread": has_screen_spread,
            "screenSpread": screen_spread or {},
            "items": items_out,
            "useChapterSeparator": use_chapter_separator,
            "chapterSeparatorStyle": (
                chapter_separator_style(
                    (raw_screens_for_spread[0] or {}).get("tone")
                    if raw_screens_for_spread
                    else None
                )
                if use_chapter_separator
                else ""
            ),
            **divider_ctx,
            **(
                build_chapter_separator_ticket(
                    ch,
                    int(idx),
                    chapter_total,
                    meta=trip.get("meta") or {},
                    divider=divider_ctx,
                )
                if use_chapter_separator
                else {}
            ),
        }
        chapters_out.append(ch_ctx)
    return chapters_out


def build_journal_chapters(
    trip: TripHot | dict,
    surface: SurfaceContext,
    *,
    trip_root: Path | None,
    meta_title: str,
    hook: str,
    cfg: AppConfig | None = None,
    moment_signature_id: str = "",
    moment_pool_ids: list[str] | None = None,
    moment_exif_pool_ids: frozenset[str] | None = None,
    show_moment_exif: bool = True,
    pool_solo: bool = True,
    show_signature_label: bool = True,
) -> ChaptersRenderBundle:
    inputs = prepare_journal_chapter_inputs(
        trip,
        moment_pool_ids=moment_pool_ids,
        moment_exif_pool_ids=moment_exif_pool_ids,
        show_signature_label=show_signature_label,
    )
    folio = resolve_journal_folio_plan(trip, surface, hook=hook)
    raw_chapters = apply_journal_moment_and_longshot(
        trip,
        surface,
        cfg=cfg,
        moment_signature_id=moment_signature_id,
        pool_ids=inputs.pool_ids,
        pool_solo=pool_solo,
    )
    chapters_out = build_journal_chapter_list(
        trip,
        surface,
        raw_chapters,
        inputs,
        folio,
        trip_root=trip_root,
        meta_title=meta_title,
        hook=hook,
        cfg=cfg,
        moment_signature_id=moment_signature_id,
        show_moment_exif=show_moment_exif,
        show_signature_label=show_signature_label,
    )
    return build_journal_folio_extras(
        trip,
        surface,
        folio,
        chapters_out,
        meta_title=meta_title,
    )
