"""Assemble trip-level Handlebars context from surface + chapters."""

from __future__ import annotations

from pathlib import Path

from travelogue.config import AppConfig
from travelogue.render.chapters import build_chapters_render_context
from travelogue.render.context_types import (
    CoverRenderContext,
    FeaturedGridBundleContext,
    TripIndexBundleContext,
    TripRenderContext,
)
from travelogue.render.surface import resolve_surface_context


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
    from travelogue.curation.curate import resolve_cover_asset_id
    from travelogue.render.context import (
        _longshot_bundle_version,
        alt_text,
        build_epilogue_stats,
        compile_srcset,
        format_trip_meta,
        has_share_zip,
        pick_image_sizes,
        pick_image_src,
        share_zip_filename,
    )
    from travelogue.render.engine import LONGSHOT_INDEX_NAME
    from travelogue.render.reading_profile import reading_html_attrs
    from travelogue.services.narrative_scope import resolve_cover_show_title

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

    meta = trip.get("meta", {})
    meta_title = meta.get("title", "")
    assets = surface.assets
    image_layout = surface.image_layout

    from travelogue.render.engine import RenderError

    cover_id = resolve_cover_asset_id(trip, export_layout=image_layout)
    if not cover_id or cover_id not in assets:
        cover_id = str(trip.get("coverAssetId") or "")
    cover_asset = assets.get(cover_id)
    if not cover_asset:
        for asset in assets.values():
            if asset.get("layoutEligible", True):
                cover_asset = asset
                cover_id = str(asset.get("id") or "")
                break
    if not cover_asset:
        raise RenderError(
            "E_RENDER_COVER_MISSING",
            "no layout-eligible cover asset found for render",
        )
    cover_src = pick_image_src(cover_asset, export_layout=image_layout)
    cover_srcset = compile_srcset(cover_asset, mobile=image_layout == "mobile")

    meta_line, meta_datetime = format_trip_meta(
        meta,
        intent=trip.get("intent"),
        assets=trip.get("assets") or [],
    )
    cover_show_title = resolve_cover_show_title(trip, cfg=cfg)
    hook = (meta.get("hook") or "").strip()
    epilogue = (trip.get("epilogue") or "").strip()
    if surface.strip_narrative_copy:
        hook = ""
        epilogue = ""

    chapters_bundle = build_chapters_render_context(
        trip,
        surface,
        trip_root=trip_root,
        meta_title=meta_title,
        hook=hook,
        cfg=cfg,
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

    html_attrs = [f'data-export="{surface.export_mode}"']
    if surface.export_layout and surface.export_layout != "auto":
        html_attrs.append(f'data-layout="{surface.export_layout}"')
    if surface.use_screens_global and not surface.is_longshot_surface:
        html_attrs.append(f'data-layout-engine="{surface.layout_engine}"')
    if surface.include_long_shot:
        html_attrs.append('data-longshot="on"')
    if surface.include_longshot_bridge:
        html_attrs.append('data-longshot-bridge="on"')
        html_attrs.append(f'data-longshot-mobile-url="{LONGSHOT_INDEX_NAME}"')
    if surface.include_screenplay:
        html_attrs.append('data-screenplay="on"')
    if surface.include_screenplay or surface.include_long_shot or surface.include_longshot_bridge:
        html_attrs.append('data-copy-toggle="on"')
    if surface.is_draft:
        html_attrs.append('data-inline-edit="on"')
    if surface.photos_only:
        html_attrs.append('data-copy-display="photos"')
    theme = surface.font_theme or (trip.get("export") or {}).get("fontTheme") or ""
    if theme == "magazine":
        html_attrs.append('data-font-theme="magazine"')
    html_attrs.extend(reading_html_attrs(surface.reading_payload))

    asset_version = _longshot_bundle_version(trip)
    zip_name = share_zip_filename(trip)
    zip_ready = has_share_zip(trip, trip_root)

    placeholder_script = ""
    if surface.is_draft:
        try:
            import json

            from travelogue.templating.guardrails import guardrails_for
            from travelogue.templating.resolver import resolve_effective_template

            ph = guardrails_for(resolve_effective_template(trip)).get("placeholders") or {}
            if ph:
                placeholder_script = (
                    "<script>window.TRAVELOGUE_PLACEHOLDERS="
                    + json.dumps(ph, ensure_ascii=False)
                    + ";</script>"
                )
        except Exception:
            placeholder_script = ""

    ctx: TripRenderContext = {
        "lang": "zh-CN",
        "htmlExtraAttrs": " ".join(html_attrs),
        "includeLongShot": surface.include_long_shot,
        "includeLongshotBridge": surface.include_longshot_bridge,
        "longshotMobileUrl": LONGSHOT_INDEX_NAME if surface.include_longshot_bridge else None,
        "includeScreenplay": surface.include_screenplay,
        "assetVersion": asset_version,
        "hasShareZip": zip_ready,
        "shareZipFile": zip_name if zip_ready else None,
        "exportLayout": surface.export_layout,
        "copyDisplay": surface.copy_display,
        "isPhotosOnly": surface.photos_only,
        "layoutEngine": surface.layout_engine,
        "exportMode": surface.export_mode,
        "isDraft": surface.is_draft,
        "placeholderScript": placeholder_script,
        "isShare": surface.is_share,
        "title": meta_title,
        "subtitle": (meta.get("subtitle") or "").strip(),
        "hasSubtitle": bool((meta.get("subtitle") or "").strip()),
        "coverShowTitle": cover_show_title,
        "cover": CoverRenderContext(
            src=cover_src,
            hasSrcset=bool(cover_srcset),
            srcset=cover_srcset,
            sizes=pick_image_sizes(image_layout, "cover"),
            alt=alt_text(None, cover_asset, meta_title),
        ),
        "tripMetaLine": meta_line,
        "tripMetaDatetime": meta_datetime,
        "hook": hook,
        "hasHook": bool(hook),
        "editableHook": surface.is_draft and bool(hook),
        "epilogue": epilogue,
        "hasEpilogue": bool(epilogue) or use_epilogue_stats,
        "editableEpilogue": surface.is_draft and bool(epilogue),
        "tripId": trip.get("tripId") or "",
        "chapters": chapters_bundle.chapters_out,
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
        "hasTripIndex": chapters_bundle.has_trip_index,
        "tripIndex": TripIndexBundleContext(entries=chapters_bundle.trip_index_entries),
        "hasFeaturedGrid": chapters_bundle.has_featured_grid,
        "featuredGrid": FeaturedGridBundleContext(cards=chapters_bundle.featured_grid_cards),
        "hasForewordSpread": chapters_bundle.has_foreword_spread,
        "forewordSpread": chapters_bundle.foreword_spread or {},
        "isLongshotSurface": surface.is_longshot_surface,
        "showSurfaceNav": surface.is_longshot_surface
        or surface.export_mode == "present-preview",
        "epilogueStats": epilogue_stats,
        "useEpilogueStats": use_epilogue_stats,
        "useEpilogueScreen": (surface.folio_lite and bool(epilogue)) or use_epilogue_stats,
    }
    return ctx
