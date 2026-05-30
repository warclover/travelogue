"""Resolve export surface flags and reading profile (render resolve phase)."""

from __future__ import annotations

from dataclasses import dataclass

from travelogue.config import AppConfig, get_config, reading_profile_defaults
from travelogue.curation.screen_planner import resolve_layout_engine, screens_layout_active
from travelogue.render.copy_display import (
    is_photos_only,
    resolve_copy_display,
    should_strip_narrative_copy,
)
from travelogue.render.reading_profile import reading_json_for_html, resolve_reading_payload
from travelogue.services.validate import asset_map


@dataclass
class SurfaceContext:
    """Resolved export surface flags and reading profile (resolve phase)."""

    export_mode: str
    is_draft: bool
    is_share: bool
    copy_display: str
    photos_only: bool
    export_layout: str
    is_longshot_surface: bool
    image_layout: str
    layout_engine: str
    use_screens_global: bool
    include_screenplay: bool
    strip_narrative_copy: bool
    assets: dict[str, dict]
    reading_payload: dict
    reading_json: str
    folio_lite: bool
    folio_full: bool
    include_breath: bool
    include_breath_flow: bool
    include_breath_scrub: bool
    include_breath_gsap_runtime: bool
    include_scroll_keyboard_nav: bool
    has_featured_assets: bool
    include_long_shot: bool
    include_longshot_bridge: bool
    present_preview_url: str | None
    index_name: str
    font_theme: str | None
    layout_engine_override: str | None
    export_layout_override: str | None


def resolve_surface_context(
    trip: dict,
    *,
    export_mode: str = "draft",
    layout_engine_override: str | None = None,
    export_layout_override: str | None = None,
    font_theme: str | None = None,
    copy_display_override: str | None = None,
    index_name: str = "index.html",
    reading_profile_override: str | None = None,
    cfg: AppConfig | None = None,
) -> SurfaceContext:
    from travelogue.render.engine import (
        should_include_long_shot,
        should_include_longshot_bridge,
        should_include_screenplay,
        web_screens_surface_active,
    )

    is_draft = export_mode == "draft"
    is_share = export_mode == "share"
    copy_display = resolve_copy_display(trip, override=copy_display_override)
    photos_only = is_photos_only(copy_display)
    export_layout = export_layout_override or trip.get("exportLayout", "auto")
    is_longshot_surface = export_layout == "longshot"
    image_layout = "mobile" if is_longshot_surface else export_layout
    layout_engine = resolve_layout_engine(trip, override=layout_engine_override)
    use_screens_global = screens_layout_active(trip, override=layout_engine_override)
    include_screenplay = should_include_screenplay(
        trip,
        export_mode=export_mode,
        layout_engine_override=layout_engine_override,
        export_layout_override=export_layout_override,
    )
    strip_narrative_copy = should_strip_narrative_copy(
        photos_only=photos_only,
        include_screenplay=include_screenplay,
        is_draft=is_draft,
    )
    assets = asset_map(trip)

    app_cfg = cfg or get_config()
    reading_defaults = reading_profile_defaults(app_cfg)
    reading_payload = resolve_reading_payload(
        trip,
        export_mode=export_mode,
        export_layout_override=export_layout_override,
        index_name=index_name,
        reading_profile_override=reading_profile_override,
        config_defaults=reading_defaults,
    )
    scroll_reading = reading_payload.get("scroll") or {}
    folio_mode = scroll_reading.get("folio", "off")
    folio_lite = folio_mode in ("lite", "full")
    folio_full = folio_mode == "full" and not is_longshot_surface
    include_breath = scroll_reading.get("breath", "off") not in ("off", "")
    include_breath_flow = scroll_reading.get("breath") == "flow"
    include_breath_scrub = scroll_reading.get("breath") in ("cinematic", "gallery")
    include_breath_gsap_runtime = (
        include_breath_scrub and scroll_reading.get("breathEngine") == "gsap"
    )
    include_scroll_keyboard_nav = scroll_reading.get("keyboardNav") is True
    has_featured_assets = bool(reading_payload.get("featuredAssetIds"))
    reading_json = reading_json_for_html(reading_payload)

    include_long_shot = should_include_long_shot(
        trip,
        export_mode=export_mode,
        layout_engine_override=layout_engine_override,
        export_layout_override=export_layout_override,
    )
    include_longshot_bridge = (
        is_draft
        and index_name == "index.html"
        and should_include_longshot_bridge(
            trip,
            layout_engine_override=layout_engine_override,
            export_layout_override=export_layout_override,
        )
    )
    present_preview_url = (
        "index-present.html"
        if is_draft
        and index_name == "index.html"
        and web_screens_surface_active(
            trip,
            layout_engine_override=layout_engine_override,
            export_layout_override=export_layout_override,
        )
        else None
    )

    return SurfaceContext(
        export_mode=export_mode,
        is_draft=is_draft,
        is_share=is_share,
        copy_display=copy_display,
        photos_only=photos_only,
        export_layout=export_layout,
        is_longshot_surface=is_longshot_surface,
        image_layout=image_layout,
        layout_engine=layout_engine,
        use_screens_global=use_screens_global,
        include_screenplay=include_screenplay,
        strip_narrative_copy=strip_narrative_copy,
        assets=assets,
        reading_payload=reading_payload,
        reading_json=reading_json,
        folio_lite=folio_lite,
        folio_full=folio_full,
        include_breath=include_breath,
        include_breath_flow=include_breath_flow,
        include_breath_scrub=include_breath_scrub,
        include_breath_gsap_runtime=include_breath_gsap_runtime,
        include_scroll_keyboard_nav=include_scroll_keyboard_nav,
        has_featured_assets=has_featured_assets,
        include_long_shot=include_long_shot,
        include_longshot_bridge=include_longshot_bridge,
        present_preview_url=present_preview_url,
        index_name=index_name,
        font_theme=font_theme,
        layout_engine_override=layout_engine_override,
        export_layout_override=export_layout_override,
    )
