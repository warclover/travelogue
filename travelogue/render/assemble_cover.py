"""Cover opening / closing bundles for assemble. No edition branch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from travelogue.config import AppConfig
from travelogue.render.context_types import CoverRenderContext
from travelogue.render.surface import SurfaceContext

# 装帧身份线前封回声白名单。展示判定留在 assemble.py，便于现网 monkeypatch。
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

_TITLE_ART_FALLBACK_X = "50%"
_TITLE_ART_FALLBACK_Y = "25%"


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


@dataclass(frozen=True)
class CoverOpeningBundle:
    """Cover-opening context keys plus intermediates the orchestrator still needs."""

    context: dict[str, Any]
    assets: dict[str, dict]
    image_layout: str
    resolved_opening_style: str


def build_cover_opening_bundle(
    trip: dict,
    surface: SurfaceContext,
    *,
    meta_title: str,
    show_cover_hook: bool,
    cfg: AppConfig | None,
) -> CoverOpeningBundle:
    """Resolve cover hero, secondary, stamp, archive strip, and title-art overlay."""
    from travelogue.domain.cover_view import resolve_cover_asset_id, resolve_cover_render_profile
    from travelogue.render.context import (
        alt_text,
        compile_srcset,
        format_trip_meta,
        pick_image_sizes,
        pick_image_src,
    )
    from travelogue.render.cover_opening import (
        build_cover_archive_strip,
        cover_focal_point,
        cover_use_contain_fit,
        resolve_cover_subtitle,
        resolve_monument_title_layout,
        resolve_show_cover_place,
        resolve_split_mat_title_layout,
    )
    from travelogue.render.engine import RenderError
    from travelogue.services.cover_opening_style import resolve_cover_opening_style
    from travelogue.services.narrative_scope import resolve_cover_show_title

    meta = trip.get("meta", {})
    assets = surface.assets
    image_layout = surface.image_layout
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
    raw_meta_title = str(meta.get("title") or "").strip()
    show_cover_place = resolve_show_cover_place(
        cover_place=cover_place, meta_title=meta_title, raw_meta_title=raw_meta_title
    )
    fx, fy = cover_focal_point(cover_asset)
    cover_contain = cover_use_contain_fit(cover_asset)

    cover_seal_char = "行"
    for ch in meta_title:
        if ch.strip():
            cover_seal_char = ch
            break
    cover_stamp_label = "旅行\n档案"
    stamp_src = str(meta_datetime or meta_line or "").strip()
    if stamp_src:
        compact = stamp_src.replace("—", "-").replace("/", "-").replace(".", "-")
        parts = [p for p in compact.replace(" ", "-").split("-") if p]
        if len(parts) >= 3 and parts[0].isdigit() and len(parts[0]) == 4:
            cover_stamp_label = f"{parts[0]}\n{parts[1]}·{parts[2][:2]}"
        else:
            cover_stamp_label = stamp_src[:18].replace(" ", "\n")

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

    resolved_opening_style = resolve_cover_opening_style(trip)
    title_art_src, has_title_art, title_art_x, title_art_y, title_art_attribution = (
        _resolve_title_art_src(trip, resolved_opening_style)
    )
    context: dict[str, Any] = {
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
        "coverOpeningStyle": resolved_opening_style,
        "coverTitleLayout": resolve_split_mat_title_layout(meta_title),
        "coverMonumentTitleLayout": resolve_monument_title_layout(meta_title),
        "hasTitleArt": has_title_art,
        "titleArtInPanel": bool(
            has_title_art and resolved_opening_style in ("veil-footer", "band-cut")
        ),
        "titleArtSrc": title_art_src,
        "titleArtAlt": meta_title,
        "titleArtX": title_art_x,
        "titleArtY": title_art_y,
        "titleArtAttribution": title_art_attribution,
    }
    return CoverOpeningBundle(
        context=context,
        assets=assets,
        image_layout=image_layout,
        resolved_opening_style=resolved_opening_style,
    )


def build_cover_closing_bundle(
    trip: dict,
    *,
    assets: dict[str, dict],
    image_layout: str,
    meta_title: str,
    use_cover_closing: bool,
    moment_exclude: set[str],
) -> dict[str, Any]:
    """Resolve closing hero after layout. No edition branch."""
    from travelogue.render.context import (
        alt_text,
        compile_srcset,
        pick_image_sizes,
        pick_image_src,
    )
    from travelogue.render.cover_closing import (
        closing_focal_point,
        closing_use_contain_fit,
        show_closing_title,
    )

    closing_asset = None
    closing_id = ""
    closing_has_hero = False
    if use_cover_closing:
        curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
        if "closingAssetId" in curation:
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

    return {
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
