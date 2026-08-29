"""Journal chapter screen loop: tone, mobile expand, 4mix, row fit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from travelogue.config import AppConfig
from travelogue.render.surface import SurfaceContext


def build_chapter_screens(
    ch: dict,
    *,
    chapter_loop_index: int,
    idx: object,
    trip: dict,
    surface: SurfaceContext,
    trip_root: Path | None,
    meta_title: str,
    featured_ids: frozenset[str],
    grid_exclude: frozenset[str],
    global_screen_index: int,
    moment_exif_pool_ids: frozenset[str],
    moment_signature_id: str,
    show_moment_exif: bool,
    show_signature_label: bool,
    moment_screen_label: str,
    trip_primary_year: Any,
    cfg: AppConfig | None,
) -> tuple[list, list[dict], int]:
    from travelogue.config import get_config
    from travelogue.curation.screen_tone import enrich_screen_tones
    from travelogue.render.context import build_layout_screen, folio_plate_rewrite_eligible

    screens_out = []
    raw_screens_for_spread: list[dict] = []
    if not (
        surface.use_screens_global and bool(ch.get("screens")) and not surface.is_longshot_surface
    ):
        return screens_out, raw_screens_for_spread, global_screen_index

    raw_screens = enrich_screen_tones(
        ch.get("screens", []),
        surface.assets,
        trip_root=trip_root,
        chapter_index=idx,
    )
    from travelogue.render.mobile_screens import (
        expand_screens_for_mobile,
        should_expand_screens_for_mobile,
    )

    render_screens = raw_screens
    if should_expand_screens_for_mobile(
        surface.image_layout, is_longshot=surface.is_longshot_surface
    ):
        render_screens = expand_screens_for_mobile(raw_screens)
    from travelogue.layout_engine.editorial.four_mix import apply_editorial_4mix_slot_fits
    from travelogue.layout_engine.editorial.portrait_row import (
        apply_editorial_row_slot_fits,
    )

    raw_screens_for_spread.extend(raw_screens)
    chapter_screen_seq = 0
    render_cfg = cfg or get_config()
    i = chapter_loop_index
    for sc in render_screens:
        sc = apply_editorial_row_slot_fits(dict(sc), surface.assets, trip=trip)
        sc = apply_editorial_4mix_slot_fits(
            sc, surface.assets, trip=trip, cfg=render_cfg
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
                surface.assets,
                meta_title=meta_title,
                export_layout=surface.image_layout,
                eager=i == 0 and chapter_screen_seq == 1,
                screen_index=global_screen_index,
                chapter_index=f"{idx:02d}",
                chapter_id=str(ch.get("id") or ""),
                is_draft=surface.is_draft,
                strip_narrative_copy=surface.strip_narrative_copy,
                folio_lite=surface.folio_lite,
                is_plate=chapter_screen_seq == 1
                and folio_plate_rewrite_eligible(sc),
                featured_asset_ids=featured_ids,
                moment_exif_pool_ids=moment_exif_pool_ids,
                moment_signature_id=moment_signature_id,
                show_moment_exif=show_moment_exif,
                show_signature_label=show_signature_label,
                moment_screen_label=moment_screen_label,
                peak_collage_exif=bool(
                    cfg is not None
                    and getattr(
                        cfg.curate.moment, "pool_portrait_collage_exif", False
                    )
                ),
                chapter_day_span=list(
                    (ch.get("curation") or {}).get("daySpan") or []
                )
                or None,
                trip_primary_year=trip_primary_year,
            )
        )
    return screens_out, raw_screens_for_spread, global_screen_index
