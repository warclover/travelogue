"""Chapter-level render context (enrich phase)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from travelogue.config import AppConfig
from travelogue.curation.screen_tone import enrich_screen_tones
from travelogue.render.context_types import (
    BreathPauseItemContext,
    ChapterRenderContext,
    FeaturedGridCardContext,
    ForewordSpreadContext,
    ScreenSpreadContext,
    TripIndexEntryContext,
)
from travelogue.render.screen_tone import build_chapter_separator_ticket, chapter_separator_style
from travelogue.render.surface import SurfaceContext


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


def build_chapters_render_context(
    trip: dict,
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
    from travelogue.curation.chapter_items import resolve_chapter_items_for_render
    from travelogue.curation.layout_planner import aspect_kind_for_asset
    from travelogue.render.context import (
        build_featured_grid_cards,
        build_foreword_spread,
        build_layout_screen,
        build_media_card,
        build_media_row,
        build_media_scroll,
        build_screen_spread,
        build_trip_index_entries,
        chapter_divider,
        folio_plate_rewrite_eligible,
    )
    from travelogue.render.reading_profile import featured_asset_ids as collect_featured_ids

    assets = surface.assets
    strip_narrative_copy = surface.strip_narrative_copy
    is_draft = surface.is_draft
    folio_lite = surface.folio_lite
    folio_full = surface.folio_full
    use_screens_global = surface.use_screens_global
    is_longshot_surface = surface.is_longshot_surface
    layout_engine = surface.layout_engine
    image_layout = surface.image_layout

    chapters_out: list[ChapterRenderContext] = []
    aspects_map = {a["id"]: aspect_kind_for_asset(a) for a in trip.get("assets", []) if a.get("id")}
    layout_eligible_count = sum(
        1 for a in trip.get("assets", []) if a.get("layoutEligible", True)
    )
    featured_ids = frozenset(collect_featured_ids(trip))
    global_screen_index = 0
    exif_pool = moment_exif_pool_ids or frozenset()
    pool_ids = list(moment_pool_ids or [])
    from travelogue.render.moment_screen import moment_label_for_trip

    moment_screen_label = moment_label_for_trip(trip) if show_signature_label else ""

    folio_plan: dict = {}
    grid_exclude: frozenset[str] = frozenset()
    if folio_full:
        from travelogue.curation.folio_plan import resolve_folio_plan

        layout_eligible = [a for a in trip.get("assets", []) if a.get("layoutEligible", True)]
        folio_plan = resolve_folio_plan(trip, trip.get("chapters") or [], layout_eligible)
        if folio_plan.get("featuredGrid"):
            grid_exclude = frozenset(folio_plan.get("featuredGridAssetIds") or [])

    foreword_spread: ForewordSpreadContext | None = None
    has_foreword_spread = False
    if folio_full and folio_plan.get("foreword"):
        chapters_raw = trip.get("chapters") or []
        if chapters_raw:
            first_lead = (chapters_raw[0].get("lead") or "").strip()
            if first_lead and not strip_narrative_copy:
                foreword_spread = build_foreword_spread(chapters_raw[0], trip_hook=hook)
                has_foreword_spread = foreword_spread is not None

    raw_chapters = trip.get("chapters") or []
    if moment_signature_id and pool_ids and pool_solo:
        from travelogue.curation.moment_scoring import ensure_pool_assets_solo_screens

        ensure_pool_assets_solo_screens(
            raw_chapters,
            pool_ids,
            moment_signature_id,
            assets_by_id=assets,
        )
    elif moment_signature_id:
        from travelogue.curation.moment_scoring import ensure_moment_asset_in_chapters

        ensure_moment_asset_in_chapters(
            raw_chapters,
            moment_signature_id,
            assets_by_id=assets,
        )
    if is_longshot_surface:
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

    from travelogue.config import get_config

    render_cfg = cfg or get_config()
    chapter_total = len(raw_chapters)

    for i, ch in enumerate(raw_chapters):
        idx = ch.get("index", i + 1)
        curation = ch.get("curation") or {}
        anchors = curation.get("memoryAnchors") or []
        use_screens = use_screens_global and bool(ch.get("screens")) and not is_longshot_surface
        raw_screens_for_spread: list[dict] = []
        screens_out = []
        if use_screens_global and bool(ch.get("screens")) and not is_longshot_surface:
            raw_screens = enrich_screen_tones(
                ch.get("screens", []),
                assets,
                trip_root=trip_root,
                chapter_index=idx,
            )
            from travelogue.render.mobile_screens import (
                expand_screens_for_mobile,
                should_expand_screens_for_mobile,
            )

            render_screens = raw_screens
            if should_expand_screens_for_mobile(
                image_layout, is_longshot=is_longshot_surface
            ):
                render_screens = expand_screens_for_mobile(raw_screens)
            from travelogue.layout_engine.editorial.four_mix import apply_editorial_4mix_slot_fits
            from travelogue.layout_engine.editorial.portrait_row import (
                apply_editorial_row_slot_fits,
            )

            raw_screens_for_spread.extend(raw_screens)
            chapter_screen_seq = 0
            for sc in render_screens:
                sc = apply_editorial_row_slot_fits(dict(sc), assets, trip=trip)
                sc = apply_editorial_4mix_slot_fits(
                    sc, assets, trip=trip, cfg=render_cfg
                )
                slots = sc.get("slots") or []
                if grid_exclude:
                    slots = [s for s in slots if s.get("assetId") not in grid_exclude]
                    if not slots:
                        continue
                    if len(slots) != len(sc.get("slots") or []):
                        sc = dict(sc)
                        sc["slots"] = slots
                chapter_screen_seq += 1
                global_screen_index += 1
                screens_out.append(
                    build_layout_screen(
                        sc,
                        assets,
                        meta_title=meta_title,
                        export_layout=image_layout,
                        eager=i == 0 and chapter_screen_seq == 1,
                        screen_index=global_screen_index,
                        chapter_index=f"{idx:02d}",
                        chapter_id=str(ch.get("id") or ""),
                        is_draft=is_draft,
                        strip_narrative_copy=strip_narrative_copy,
                        folio_lite=folio_lite,
                        is_plate=chapter_screen_seq == 1
                        and folio_plate_rewrite_eligible(sc),
                        featured_asset_ids=featured_ids,
                        moment_exif_pool_ids=exif_pool,
                        moment_signature_id=moment_signature_id,
                        show_moment_exif=show_moment_exif,
                        show_signature_label=show_signature_label,
                        moment_screen_label=moment_screen_label,
                    )
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
        chapter_items = resolve_chapter_items_for_render(
            ch,
            export_layout=image_layout,
            layout_engine=layout_engine,
            is_longshot=is_longshot_surface,
            aspects=aspects_map,
            assets_map=assets,
            trip_photo_total=layout_eligible_count,
        )
        if is_longshot_surface:
            from travelogue.curation.breath_pauses import interleave_breath_items

            chapter_items = interleave_breath_items(chapter_items)
        caption_on_asset = is_longshot_surface and bool(ch.get("screens"))
        for j, it in enumerate(chapter_items):
            itype = it.get("type")
            eager = i == 0 and j == 0
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

        # BE-SFI-01 · 读者面收口 share_face_copy（含 decorLine 旁路）
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
        if i == 0 and has_foreword_spread:
            lead = ""
        elif lead:
            lead, blanked = sanitize_share_copy_tracked(
                lead, title=meta_title, kind="lead", edited=ch_edited
            )
            if blanked:
                record_stub_hit(
                    surface=surface_name, field="lead", pattern_id=pattern_id, trip_id=trip_id
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
                # 示例泄漏等：回退日期章名（D-SFI-01）
                curation = ch.get("curation") or {}
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

        ch_ctx: ChapterRenderContext = {
            "id": ch["id"],
            "patternId": ch.get("patternId", ""),
            "index": f"{idx:02d}",
            "title": ch_title,
            "lead": lead,
            "hasLead": bool(lead),
            "decorLine": decor_line,
            "hasDecorLine": bool(decor_line),
            # 编辑面保留 trip.json 原文入口；读者面已过滤。edited 豁免时两边一致。
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

    trip_index_entries: list[TripIndexEntryContext] = []
    featured_grid_cards: list[FeaturedGridCardContext] = []
    has_trip_index = False
    has_featured_grid = False
    if folio_full and folio_plan.get("index"):
        trip_index_entries = build_trip_index_entries(trip.get("chapters") or [])
        has_trip_index = bool(trip_index_entries)
    if folio_full and folio_plan.get("featuredGrid"):
        featured_grid_cards = build_featured_grid_cards(
            list(folio_plan.get("featuredGridAssetIds") or []),
            assets,
            meta_title=meta_title,
            export_layout=image_layout,
        )
        has_featured_grid = len(featured_grid_cards) >= 4

    return ChaptersRenderBundle(
        chapters_out=chapters_out,
        foreword_spread=foreword_spread,
        has_foreword_spread=has_foreword_spread,
        trip_index_entries=trip_index_entries,
        has_trip_index=has_trip_index,
        featured_grid_cards=featured_grid_cards,
        has_featured_grid=has_featured_grid,
    )
