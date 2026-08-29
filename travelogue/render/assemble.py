"""Assemble trip-level Handlebars context. S-04 stays here; no identity if in stages."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from travelogue.config import AppConfig
from travelogue.render.assemble_copy import apply_share_face_copy
from travelogue.render.assemble_cover import (  # noqa: F401
    _COVER_OPENING_BRAND_STYLES,
    _resolve_title_art_src,
    _title_art_pct,
    build_cover_closing_bundle,
    build_cover_opening_bundle,
)
from travelogue.render.context_types import (
    FeaturedGridBundleContext,
    TripIndexBundleContext,
    TripRenderContext,
)
from travelogue.render.journal_chapters import ChaptersRenderBundle, build_journal_chapters
from travelogue.render.portfolio_chapters import (
    build_portfolio_chapters,
    overlay_portfolio_epilogue_stats,
)
from travelogue.render.surface import SurfaceContext, resolve_surface_context


def _moment_render_state(
    trip: dict,
    surface: SurfaceContext,
    *,
    app_cfg: AppConfig,
    reading_payload: dict,
    use_cover_closing: bool,
) -> dict[str, Any]:
    moment_cfg = app_cfg.curate.moment
    omit_moment_exif = (
        str(reading_payload.get("profile") or "") == "performance"
        and surface.export_mode not in ("draft", "present-preview")
    )
    moment_signature_id = ""
    moment_pool_ids: list[str] = []
    moment_exif_pool_ids: frozenset[str] = frozenset()
    moment_exclude: set[str] = set()
    moment_active = (
        moment_cfg.enabled
        and surface.use_screens_global
        and not surface.is_longshot_surface
    )
    if moment_active:
        curation = trip.get("curation") or {}
        moment_id = str(trip.get("momentAssetId") or "").strip()
        if moment_id and not curation.get("momentSkipped"):
            moment_signature_id = moment_id
            moment_pool_ids = list(curation.get("momentPoolIds") or [])
            if (
                not omit_moment_exif
                and moment_cfg.show_exif
                and moment_cfg.pool_exif
                and moment_pool_ids
            ):
                moment_exif_pool_ids = frozenset(
                    str(x).strip() for x in moment_pool_ids if str(x).strip()
                )
            elif not omit_moment_exif and moment_cfg.show_exif:
                moment_exif_pool_ids = frozenset([moment_id])
            if use_cover_closing:
                moment_exclude.add(moment_id)
    return {
        "moment_cfg": moment_cfg,
        "moment_active": moment_active,
        "moment_signature_id": moment_signature_id,
        "moment_pool_ids": moment_pool_ids,
        "moment_exif_pool_ids": moment_exif_pool_ids,
        "moment_exclude": moment_exclude,
        "show_moment_exif": moment_cfg.show_exif and not omit_moment_exif,
    }


def attach_folio_extras(chapters_bundle: ChaptersRenderBundle) -> dict[str, Any]:
    """Copy folio fields off the chapter bundle. Portfolio extras are already empty."""
    return {
        "hasTripIndex": chapters_bundle.has_trip_index,
        "tripIndex": TripIndexBundleContext(entries=chapters_bundle.trip_index_entries),
        "hasFeaturedGrid": chapters_bundle.has_featured_grid,
        "featuredGrid": FeaturedGridBundleContext(cards=chapters_bundle.featured_grid_cards),
        "hasForewordSpread": chapters_bundle.has_foreword_spread,
        "forewordSpread": chapters_bundle.foreword_spread or {},
        "hasMomentScreen": False,
        "momentScreen": {},
    }


def _html_extra_attrs(trip: dict, surface: SurfaceContext, *, is_portfolio: bool) -> str:
    from travelogue.domain.longshot_density import resolve_longshot_density
    from travelogue.render.engine import LONGSHOT_INDEX_NAME
    from travelogue.render.reading_profile import reading_html_attrs

    html_attrs = [f'data-export="{surface.export_mode}"']
    if surface.export_layout:
        layout_attr = "auto" if surface.export_layout == "auto" else surface.export_layout
        html_attrs.append(f'data-layout="{layout_attr}"')
    if surface.use_screens_global and not surface.is_longshot_surface:
        html_attrs.append(f'data-layout-engine="{surface.layout_engine}"')
    if surface.include_long_shot:
        html_attrs.append('data-longshot="on"')
    if surface.include_longshot_bridge:
        html_attrs.append('data-longshot-bridge="on"')
        html_attrs.append(f'data-longshot-mobile-url="{LONGSHOT_INDEX_NAME}"')
    if surface.include_screenplay:
        html_attrs.append('data-screenplay="on"')
    if surface.present_preview_url:
        html_attrs.append(f'data-present-preview-url="{surface.present_preview_url}"')
    if surface.include_screenplay or surface.include_long_shot or surface.include_longshot_bridge:
        html_attrs.append('data-copy-toggle="on"')
    if surface.is_draft:
        html_attrs.append('data-inline-edit="on"')
    trip_id = str(trip.get("tripId") or "").strip()
    if surface.is_draft and trip_id:
        html_attrs.append(f'data-trip-id="{trip_id}"')
    if is_portfolio:
        html_attrs.append('data-edition="portfolio"')
    try:
        from travelogue.cover_engine.craft import craft_attr_value

        craft_v = craft_attr_value()
        if craft_v:
            html_attrs.append(f'data-cover-craft="{craft_v}"')
    except Exception:
        pass
    if surface.photos_only:
        html_attrs.append('data-copy-display="photos"')
    theme = surface.font_theme or (trip.get("export") or {}).get("fontTheme") or ""
    if theme == "magazine":
        html_attrs.append('data-font-theme="magazine"')
    if surface.is_longshot_surface:
        html_attrs.append(f'data-longshot-density="{resolve_longshot_density(trip)}"')
    html_attrs.extend(reading_html_attrs(surface.reading_payload))
    return " ".join(html_attrs)


def _placeholder_script(trip: dict, surface: SurfaceContext) -> str:
    if not surface.is_draft:
        return ""
    try:
        import json

        from travelogue.templating.guardrails import guardrails_for
        from travelogue.templating.resolver import resolve_effective_template

        ph = guardrails_for(resolve_effective_template(trip)).get("placeholders") or {}
        if ph:
            return (
                "<script>window.TRAVELOGUE_PLACEHOLDERS="
                + json.dumps(ph, ensure_ascii=False)
                + ";</script>"
            )
    except Exception:
        return ""
    return ""


def _merge_render_context(
    trip: dict,
    surface: SurfaceContext,
    cover_ctx: dict[str, Any],
    closing_ctx: dict[str, Any],
    chapters_bundle: ChaptersRenderBundle,
    *,
    hook: str,
    epilogue: str,
    is_portfolio: bool,
    trip_root: Path | None,
    has_epilogue: bool,
    use_epilogue_stats: bool,
    use_cover_closing: bool,
    epilogue_stats: Any,
) -> dict[str, Any]:
    from travelogue.domain.longshot_density import resolve_longshot_density
    from travelogue.domain.works_brand import resolve_works_brand
    from travelogue.export.longshot import EXPORT_OUTPUT_DIRNAME
    from travelogue.render.context import (
        _longshot_bundle_version,
        has_share_zip,
        share_zip_filename,
    )
    from travelogue.render.engine import LONGSHOT_INDEX_NAME

    meta = trip.get("meta", {}) if isinstance(trip.get("meta"), dict) else {}
    works_brand = resolve_works_brand(meta)
    density = resolve_longshot_density(trip)
    zip_name = f"{EXPORT_OUTPUT_DIRNAME}/{share_zip_filename(trip)}"
    zip_ready = has_share_zip(trip, trip_root)
    style = cover_ctx["coverOpeningStyle"]
    return {
        "lang": "zh-CN",
        "htmlExtraAttrs": _html_extra_attrs(trip, surface, is_portfolio=is_portfolio),
        "includeLongShot": surface.include_long_shot,
        "includeLongshotBridge": surface.include_longshot_bridge,
        "longshotMobileUrl": LONGSHOT_INDEX_NAME if surface.include_longshot_bridge else None,
        "includeScreenplay": surface.include_screenplay,
        "assetVersion": _longshot_bundle_version(trip),
        "hasShareZip": zip_ready,
        "shareZipFile": zip_name if zip_ready else None,
        "exportLayout": surface.export_layout,
        "copyDisplay": surface.copy_display,
        "isPhotosOnly": surface.photos_only,
        "layoutEngine": surface.layout_engine,
        "exportMode": surface.export_mode,
        "isDraft": surface.is_draft,
        "placeholderScript": _placeholder_script(trip, surface),
        "isShare": surface.is_share,
        "hook": hook,
        "hasHook": bool(hook),
        "editableHook": surface.is_draft and bool(hook),
        "epilogue": epilogue,
        "hasEpilogue": has_epilogue,
        "editableEpilogue": surface.is_draft and bool(epilogue),
        "tripId": trip.get("tripId") or "",
        "chapters": chapters_bundle.chapters_out,
        "chapterPartial": "chapter-portfolio" if is_portfolio else "chapter",
        "tripRoot": str(trip_root) if trip_root else None,
        "readingJson": surface.reading_json,
        "includeBreath": surface.include_breath,
        "includeBreathFlow": surface.include_breath_flow,
        "includeBreathScrub": surface.include_breath_scrub,
        "includeBreathGsapRuntime": surface.include_breath_gsap_runtime,
        "includeScrollKeyboardNav": surface.include_scroll_keyboard_nav,
        "presentPreviewUrl": surface.present_preview_url,
        "hasFeaturedAssets": surface.has_featured_assets,
        "folioLite": surface.folio_lite,
        "folioFull": surface.folio_full,
        "isLongshotSurface": surface.is_longshot_surface,
        "showSurfaceNav": surface.is_longshot_surface or surface.export_mode == "present-preview",
        "epilogueStats": epilogue_stats,
        "useEpilogueStats": use_epilogue_stats,
        "useEpilogueScreen": (surface.folio_lite and bool(epilogue)) or use_epilogue_stats,
        "useCoverClosing": use_cover_closing,
        "showWorksBrand": works_brand["showWorksBrand"],
        "worksBrandLine": works_brand["worksBrandLine"],
        "worksBrandCustom": works_brand["worksBrandCustom"],
        "showCoverOpeningBrand": (
            bool(works_brand["showWorksBrand"]) and style in _COVER_OPENING_BRAND_STYLES
        ),
        "longshotDensity": density,
        "compactLongshot": density == "compact" and surface.is_longshot_surface,
        **cover_ctx,
        **attach_folio_extras(chapters_bundle),
        **closing_ctx,
    }


def build_render_context(
    trip: dict,
    *,
    export_mode: str = "draft",
    trip_root: Path | None = None,
    layout_engine_override: str | None = None,
    export_layout_override: str | None = None,
    font_theme: str | None = None,
    copy_display_override: str | None = None,
    index_name: str = "index.html",
    reading_profile_override: str | None = None,
    cfg: AppConfig | None = None,
) -> TripRenderContext:
    """export_mode: draft | share | present-preview"""
    from travelogue.config import get_config, reading_profile_defaults
    from travelogue.config.edition import is_portfolio_trip
    from travelogue.domain.title_humanize import resolve_display_title
    from travelogue.render.context import build_epilogue_stats
    from travelogue.render.cover_opening import show_hook_on_cover
    from travelogue.render.reading_profile import resolve_reading_payload

    surface = resolve_surface_context(
        trip,
        export_mode=export_mode,
        layout_engine_override=layout_engine_override,
        export_layout_override=export_layout_override,
        font_theme=font_theme,
        copy_display_override=copy_display_override,
        index_name=index_name,
        reading_profile_override=reading_profile_override,
        cfg=cfg,
    )
    app_cfg = cfg or get_config()
    meta = trip.get("meta", {})
    meta_title = resolve_display_title(meta)
    is_portfolio = is_portfolio_trip(trip)
    hook = (meta.get("hook") or "").strip()
    epilogue = (trip.get("epilogue") or "").strip()
    if surface.strip_narrative_copy or is_portfolio:
        hook = ""
        epilogue = ""
    else:
        hook, epilogue = apply_share_face_copy(
            hook=hook,
            epilogue=epilogue,
            meta_title=meta_title,
            meta_edited=bool(meta.get("edited")),
            is_draft=surface.is_draft,
            trip_id=str(trip.get("tripId") or ""),
        )
    show_cover_hook = show_hook_on_cover(hook)
    cover = build_cover_opening_bundle(
        trip,
        surface,
        meta_title=meta_title,
        show_cover_hook=show_cover_hook,
        cfg=app_cfg,
    )
    use_epilogue_stats = (
        surface.use_screens_global
        and not surface.is_longshot_surface
        and surface.include_breath
    )
    epilogue_stats = (
        build_epilogue_stats(trip)
        if (use_epilogue_stats or surface.is_longshot_surface)
        else None
    )
    if is_portfolio and epilogue_stats:
        epilogue_stats = overlay_portfolio_epilogue_stats(trip, epilogue_stats)
    has_epilogue = bool(epilogue) or use_epilogue_stats
    use_cover_closing = (
        surface.use_screens_global
        and not surface.is_longshot_surface
        and cover.image_layout in ("web", "auto")
        and has_epilogue
    )
    reading_payload = resolve_reading_payload(
        trip,
        export_mode=surface.export_mode,
        export_layout_override=cover.image_layout,
        index_name=index_name,
        reading_profile_override=reading_profile_override,
        config_defaults=reading_profile_defaults(app_cfg),
    )
    moment = _moment_render_state(
        trip,
        surface,
        app_cfg=app_cfg,
        reading_payload=reading_payload,
        use_cover_closing=use_cover_closing,
    )
    if is_portfolio:
        chapters_bundle = build_portfolio_chapters(
            trip,
            surface,
            trip_root=trip_root,
            meta_title=meta_title,
            hook=hook,
            cfg=app_cfg,
        )
    else:
        chapters_bundle = build_journal_chapters(
            trip,
            surface,
            trip_root=trip_root,
            meta_title=meta_title,
            hook=hook,
            cfg=app_cfg,
            moment_signature_id=moment["moment_signature_id"],
            moment_pool_ids=moment["moment_pool_ids"],
            moment_exif_pool_ids=moment["moment_exif_pool_ids"],
            show_moment_exif=moment["show_moment_exif"],
            pool_solo=moment["moment_cfg"].pool_solo and moment["moment_active"],
            show_signature_label=moment["moment_cfg"].signature_label,
        )
    closing = build_cover_closing_bundle(
        trip,
        assets=cover.assets,
        image_layout=cover.image_layout,
        meta_title=meta_title,
        use_cover_closing=use_cover_closing,
        moment_exclude=moment["moment_exclude"],
    )
    return TripRenderContext(
        **_merge_render_context(
            trip,
            surface,
            cover.context,
            closing,
            chapters_bundle,
            hook=hook,
            epilogue=epilogue,
            is_portfolio=is_portfolio,
            trip_root=trip_root,
            has_epilogue=has_epilogue,
            use_epilogue_stats=use_epilogue_stats,
            use_cover_closing=use_cover_closing,
            epilogue_stats=epilogue_stats,
        )
    )
