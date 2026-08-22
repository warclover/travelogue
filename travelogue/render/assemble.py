"""Assemble trip-level Handlebars context from surface + chapters."""

from __future__ import annotations

from pathlib import Path

from travelogue.config import AppConfig
from travelogue.render.journal_chapters import build_journal_chapters
from travelogue.render.portfolio_chapters import build_portfolio_chapters
from travelogue.render.context_types import (
    CoverRenderContext,
    FeaturedGridBundleContext,
    TripIndexBundleContext,
    TripRenderContext,
)
from travelogue.render.surface import resolve_surface_context

#: §6.2 兜底位置（whitelist rect 的近似几何中心），仅在 ``titleArt.position``
#: 缺失时使用——正常路径下这两个百分比来自 placement_score 的实际算出坐标。
_TITLE_ART_FALLBACK_X = "50%"
_TITLE_ART_FALLBACK_Y = "25%"

#: 装帧身份线前封回声（D-CAL-26 / D-SFI-13 扩容，2026-08-09）：署名三态原仅
#: 驱动 cover-closing__brand + longshot-boundary-footer__brand 两处；这里新增
#: 第三处渲染位。**全部 10 款**封面风格已用真实渲染截图逐个核对后默认开启
#: （首批 4 款见决策记录 §5；扩展 6 款见 §8），不再保留「风格外不显示」的
#: 过渡白名单语义——元组即全量 catalog 风格 id。
_COVER_OPENING_BRAND_STYLES: tuple[str, ...] = (
    "band-cut",
    "veil-footer",
    "contact-stamp",
    "folio-overlap",
    "cameo-aperture",
    "type-monument",
    "scroll-head",
    "portal-arch",
    "horizon-split",
    "diptych-seam",
)


def _resolve_title_art_src(
    trip: dict, opening_style_id: str
) -> tuple[str | None, bool, str, str, str]:
    """PRD-COVER-CALLIGRAPHY-TITLE-V1 §7：白名单内 + 非 stale + enabled 才叠加。

    ``titleArt.assetPath`` 是相对 trip 根目录的路径（index.html 同级），可直接
    作为 ``<img src>`` 使用，不做磁盘存在性校验（信任 trip.json 状态，与其余
    computed 字段一致）。

    同时回传 §6.2 ``position.x``/``position.y``（0~1 归一化，相对整个
    ``cover-opening`` 画布，非某个文案面板）供模板转成 CSS 百分比——此前这两个
    字段只落库、未接进渲染表面，模板用的是写死的 ``50%/28%``，恰好与
    ``.cover-opening__title-art`` 当时误嵌在 ``.cover-opening__panel``
    （雾带底部文案面板，随内容自适应矮高度）内部的 bug 绑在一起：面板高度只由
    hook 文案撑起，写死的 28% 几乎总是与 hook 文案重叠。§7 修复：贴纸挪到
    ``.cover-opening`` 直接子层，百分比改用这里回传的真实定位。

    第五返回值是 §10 归因文案（无贴纸时为空串）。
    """
    from travelogue.cover_engine.title_art.attribution import title_art_attribution_line
    from travelogue.cover_engine.title_art.whitelist import is_whitelisted

    empty = (None, False, _TITLE_ART_FALLBACK_X, _TITLE_ART_FALLBACK_Y, "")
    if not is_whitelisted(opening_style_id):
        return empty
    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    title_art = meta.get("titleArt") if isinstance(meta.get("titleArt"), dict) else None
    if not isinstance(title_art, dict):
        return empty
    if not title_art.get("enabled") or title_art.get("stale"):
        return empty
    if str(title_art.get("openingStyleId") or "") != opening_style_id:
        return empty
    # 换封面后旧贴纸的定位/墨色按旧照片算——有指纹且不一致则不叠加。
    # 缺 coverAssetId 的旧数据兼容放行（生成时未落库的历史结果）。
    cached_cover = str(title_art.get("coverAssetId") or "")
    current_cover = str(trip.get("coverAssetId") or "")
    if cached_cover and cached_cover != current_cover:
        return empty
    asset_path = str(title_art.get("assetPath") or "").strip()
    if not asset_path:
        return empty
    position = title_art.get("position") if isinstance(title_art.get("position"), dict) else {}
    x_pct = _title_art_pct(position.get("x"), _TITLE_ART_FALLBACK_X)
    y_pct = _title_art_pct(position.get("y"), _TITLE_ART_FALLBACK_Y)
    attribution = title_art_attribution_line(str(title_art.get("engine") or ""))
    return asset_path, True, x_pct, y_pct, attribution

def _title_art_pct(value: object, fallback: str) -> str:
    try:
        ratio = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return fallback
    if not (0.0 <= ratio <= 1.0):
        return fallback
    return f"{ratio * 100:.2f}%"


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
    from travelogue.domain.cover_view import resolve_cover_asset_id, resolve_cover_render_profile
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
    from travelogue.render.cover_closing import (
        closing_focal_point,
        closing_use_contain_fit,
        show_closing_title,
    )
    from travelogue.render.cover_opening import (
        build_cover_archive_strip,
        cover_focal_point,
        cover_use_contain_fit,
        resolve_cover_subtitle,
        resolve_monument_title_layout,
        resolve_show_cover_place,
        resolve_split_mat_title_layout,
        show_hook_on_cover,
    )
    from travelogue.render.engine import LONGSHOT_INDEX_NAME
    from travelogue.render.reading_profile import reading_html_attrs
    from travelogue.services.cover_opening_style import resolve_cover_opening_style
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
    from travelogue.domain.title_humanize import resolve_display_title

    # BE-FST-06 · 封面主标题用展示名（噪音目录名回退）
    meta_title = resolve_display_title(meta)
    assets = surface.assets
    image_layout = surface.image_layout

    from travelogue.render.engine import RenderError

    cover_profile = resolve_cover_render_profile(
        image_layout,
        index_name=surface.index_name,
        layout_engine=surface.layout_engine,
    )
    cover_id = resolve_cover_asset_id(
        trip,
        export_layout=image_layout,
        index_name=surface.index_name,
        layout_engine=surface.layout_engine,
    )
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
    cover_src = pick_image_src(cover_asset, export_layout=cover_profile)
    cover_srcset = compile_srcset(cover_asset, mobile=cover_profile == "mobile")

    meta_line, meta_datetime, cover_place, meta_subline = format_trip_meta(
        meta,
        intent=trip.get("intent"),
        assets=trip.get("assets") or [],
    )
    cover_subtitle = resolve_cover_subtitle(trip, meta)
    cover_show_title = resolve_cover_show_title(trip, cfg=cfg)
    hook = (meta.get("hook") or "").strip()
    epilogue = (trip.get("epilogue") or "").strip()
    from travelogue.config.edition import is_portfolio_trip

    is_portfolio = is_portfolio_trip(trip)
    if surface.strip_narrative_copy or is_portfolio:
        hook = ""
        epilogue = ""
    else:
        # BE-SFI-01 · 封面 hook 再过分享面护栏（与章级同一漏斗）
        from travelogue.domain.share_face_copy import (
            record_stub_hit,
            sanitize_share_copy_tracked,
        )

        meta_edited = bool(meta.get("edited"))
        hook, hook_blanked = sanitize_share_copy_tracked(
            hook, title=meta_title, kind="lead", edited=meta_edited
        )
        if hook_blanked:
            record_stub_hit(
                surface="draft" if surface.is_draft else "share",
                field="hook",
                trip_id=str(trip.get("tripId") or "") or None,
            )
        epilogue, epi_blanked = sanitize_share_copy_tracked(
            epilogue, title=meta_title, kind="lead", edited=meta_edited
        )
        if epi_blanked:
            record_stub_hit(
                surface="draft" if surface.is_draft else "share",
                field="epilogue",
                trip_id=str(trip.get("tripId") or "") or None,
            )
    # T-M4-01：封面 hook 一律经 show_hook_on_cover（系统 stub 句默认不上封面；
    # 真人短 hook 仍可显示。draft/精修不再旁路放行「碎片拼成」类句子）。
    show_cover_hook = show_hook_on_cover(hook)
    raw_meta_title = str(meta.get("title") or "").strip()
    show_cover_place = resolve_show_cover_place(
        cover_place=cover_place, meta_title=meta_title, raw_meta_title=raw_meta_title
    )
    fx, fy = cover_focal_point(cover_asset)
    cover_contain = cover_use_contain_fit(cover_asset)

    # Craft attrs for CSS packs (seal / archive stamp) — first title glyph + short date.
    cover_seal_char = "行"
    for ch in meta_title:
        if ch.strip():
            cover_seal_char = ch
            break
    cover_stamp_label = "旅行\n档案"
    stamp_src = str(meta_datetime or meta_line or "").strip()
    if stamp_src:
        # Prefer compact 2-line stamp: YYYY / MM·DD
        compact = stamp_src.replace("—", "-").replace("/", "-").replace(".", "-")
        parts = [p for p in compact.replace(" ", "-").split("-") if p]
        if len(parts) >= 3 and parts[0].isdigit() and len(parts[0]) == 4:
            cover_stamp_label = f"{parts[0]}\n{parts[1]}·{parts[2][:2]}"
        else:
            cover_stamp_label = stamp_src[:18].replace(" ", "\n")

    # Archive strip for contact-stamp (trip meta only — no camera EXIF on reader face).
    cover_archive_strip = build_cover_archive_strip(
        meta_subline=meta_subline, cover_place=cover_place, cover_asset=cover_asset
    )

    cover_secondary_ctx: CoverRenderContext = CoverRenderContext(
        src="", hasSrcset=False, srcset="", sizes="", alt=""
    )
    has_cover_secondary = False
    if resolve_cover_opening_style(trip) == "diptych-seam":
        sec_id = str(meta.get("coverSecondaryAssetId") or "").strip()
        sec_asset = assets.get(sec_id) if sec_id else None
        if sec_asset and sec_id != cover_id:
            sfx, sfy = cover_focal_point(sec_asset)
            cover_secondary_ctx = CoverRenderContext(
                src=pick_image_src(sec_asset, export_layout=cover_profile),
                hasSrcset=bool(compile_srcset(sec_asset, mobile=cover_profile == "mobile")),
                srcset=compile_srcset(sec_asset, mobile=cover_profile == "mobile"),
                sizes=pick_image_sizes(image_layout, "cover"),
                alt=alt_text(None, sec_asset, meta_title),
                useContainFit=cover_use_contain_fit(sec_asset),
                focalX=sfx,
                focalY=sfy,
                hasFocal=True,
            )
            has_cover_secondary = bool(cover_secondary_ctx.get("src"))

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

    has_epilogue = bool(epilogue) or use_epilogue_stats
    use_cover_closing = (
        surface.use_screens_global
        and not surface.is_longshot_surface
        and image_layout in ("web", "auto")
        and has_epilogue
    )
    app_cfg = cfg or get_config()
    moment_cfg = app_cfg.curate.moment
    from travelogue.render.reading_profile import resolve_reading_payload

    reading_payload = resolve_reading_payload(
        trip,
        export_mode=surface.export_mode,
        export_layout_override=image_layout,
        index_name=index_name,
        reading_profile_override=reading_profile_override,
        config_defaults=reading_profile_defaults(app_cfg),
    )
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
            moment_signature_id=moment_signature_id,
            moment_pool_ids=moment_pool_ids,
            moment_exif_pool_ids=moment_exif_pool_ids,
            show_moment_exif=moment_cfg.show_exif and not omit_moment_exif,
            pool_solo=moment_cfg.pool_solo and moment_active,
            show_signature_label=moment_cfg.signature_label,
        )

    closing_asset = None
    closing_id = ""
    closing_has_hero = False
    if use_cover_closing:
        curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
        if "closingAssetId" in curation:
            # Explicit null → no hero, do not recompute (ADR-017)
            raw = curation.get("closingAssetId")
            closing_id = str(raw).strip() if raw else ""
        else:
            from travelogue.cover_engine.api import maybe_resolve_closing_after_layout
            from travelogue.cover_engine.lock import is_closing_locked

            if not is_closing_locked(trip):
                maybe_resolve_closing_after_layout(trip, layout=image_layout)
                curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
            raw = curation.get("closingAssetId") if "closingAssetId" in curation else None
            if raw is None and "closingAssetId" not in curation:
                # fail-open ephemeral pick without cover reuse
                from travelogue.domain.closing_view import resolve_closing_asset_id

                ephemeral = resolve_closing_asset_id(
                    trip,
                    assets,
                    prefer_landscape=image_layout in ("web", "auto"),
                    exclude_ids=moment_exclude,
                )
                closing_id = str(ephemeral or "").strip()
            else:
                closing_id = str(raw).strip() if raw else ""
        if closing_id and moment_exclude and closing_id in moment_exclude:
            # Prefer persisted id unless it collides with moment signature
            closing_id = ""
        closing_asset = assets.get(closing_id) if closing_id else None
        closing_has_hero = bool(closing_asset)

    closing_fx, closing_fy = (0.5, 0.45)
    closing_contain = False
    closing_src = ""
    closing_srcset = ""
    if use_cover_closing and closing_asset:
        closing_src = pick_image_src(closing_asset, export_layout=image_layout)
        closing_srcset = compile_srcset(closing_asset, mobile=image_layout == "mobile")
        closing_fx, closing_fy = closing_focal_point(closing_asset)
        closing_contain = closing_use_contain_fit(closing_asset)

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
    from travelogue.domain.longshot_density import resolve_longshot_density
    from travelogue.domain.works_brand import resolve_works_brand

    density = resolve_longshot_density(trip)
    if surface.is_longshot_surface:
        html_attrs.append(f'data-longshot-density="{density}"')
    works_brand = resolve_works_brand(meta if isinstance(meta, dict) else {})
    html_attrs.extend(reading_html_attrs(surface.reading_payload))

    asset_version = _longshot_bundle_version(trip)
    # EOI · 分享 zip 落盘在 EXPORT_OUTPUT_DIRNAME 子目录；下载链接需带上子目录前缀
    # 才能相对 index.html（trip 根）正确解析（见 share.js downloadZip）。
    from travelogue.export.longshot import EXPORT_OUTPUT_DIRNAME

    zip_name = f"{EXPORT_OUTPUT_DIRNAME}/{share_zip_filename(trip)}"
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

    resolved_opening_style = resolve_cover_opening_style(trip)
    title_art_src, has_title_art, title_art_x, title_art_y, title_art_attribution = (
        _resolve_title_art_src(trip, resolved_opening_style)
    )

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
        "subtitle": cover_subtitle,
        "hasSubtitle": bool(cover_subtitle),
        "coverShowTitle": cover_show_title,
        "cover": CoverRenderContext(
            src=cover_src,
            hasSrcset=bool(cover_srcset),
            srcset=cover_srcset,
            sizes=pick_image_sizes(image_layout, "cover"),
            alt=alt_text(None, cover_asset, meta_title),
            useContainFit=cover_contain,
            focalX=fx,
            focalY=fy,
            hasFocal=True,
        ),
        "coverSecondary": cover_secondary_ctx,
        "hasCoverSecondary": has_cover_secondary,
        "tripMetaLine": meta_line,
        "tripMetaSubline": meta_subline,
        "tripMetaDatetime": meta_datetime,
        "coverPlace": cover_place,
        "hasCoverPlace": bool(cover_place),
        "showCoverPlace": show_cover_place,
        "showCoverHook": show_cover_hook,
        "coverSealChar": cover_seal_char,
        "coverStampLabel": cover_stamp_label,
        "coverArchiveStrip": cover_archive_strip,
        "hasCoverArchiveStrip": bool(cover_archive_strip),
        "hook": hook,
        "hasHook": bool(hook),
        "coverOpeningStyle": resolved_opening_style,
        "coverTitleLayout": resolve_split_mat_title_layout(meta_title),
        "coverMonumentTitleLayout": resolve_monument_title_layout(meta_title),
        "hasTitleArt": has_title_art,
        # veil-footer / band-cut：艺术字进 panel 文档流，由原生纸签/雾带托住；
        # 其它风格仍绝对定位。
        "titleArtInPanel": bool(
            has_title_art and resolved_opening_style in ("veil-footer", "band-cut")
        ),
        "titleArtSrc": title_art_src,
        "titleArtAlt": meta_title,
        "titleArtX": title_art_x,
        "titleArtY": title_art_y,
        "titleArtAttribution": title_art_attribution,
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
        "useCoverClosing": use_cover_closing,
        "showWorksBrand": works_brand["showWorksBrand"],
        "worksBrandLine": works_brand["worksBrandLine"],
        "worksBrandCustom": works_brand["worksBrandCustom"],
        "showCoverOpeningBrand": (
            bool(works_brand["showWorksBrand"])
            and resolved_opening_style in _COVER_OPENING_BRAND_STYLES
        ),
        "longshotDensity": density,
        "compactLongshot": density == "compact" and surface.is_longshot_surface,
        "hasMomentScreen": False,
        "momentScreen": {},
        "showClosingTitle": show_closing_title(meta_title) if use_cover_closing else False,
        "hasClosingHero": closing_has_hero if use_cover_closing else False,
        "closingDegraded": bool(
            use_cover_closing
            and isinstance(trip.get("curation"), dict)
            and (trip.get("curation") or {}).get("bookendsDegraded")
        )
        or (use_cover_closing and not closing_has_hero),
        "closingQuiet": (
            use_cover_closing
            and str((trip.get("meta") or {}).get("coverClosingStyle") or "")
            == "colophon-quiet"
        ),
        "closing": CoverRenderContext(
            src=closing_src,
            hasSrcset=bool(closing_srcset),
            srcset=closing_srcset,
            sizes=pick_image_sizes(image_layout, "cover"),
            alt=alt_text(None, closing_asset, meta_title) if closing_asset else meta_title,
            useContainFit=closing_contain,
            focalX=closing_fx,
            focalY=closing_fy,
            hasFocal=True,
        )
        if use_cover_closing
        else CoverRenderContext(src="", hasSrcset=False, srcset="", sizes="", alt=""),
    }
    return ctx
