"""Moment-screen render context (Phase 23)."""

from __future__ import annotations

from travelogue.curation.asset_subject import full_frame_fit_for_asset, portrait_fit_for_asset
from travelogue.curation.layout_planner import aspect_kind_for_asset
from travelogue.render.context import (
    _asset_aspect_ratio_float,
    _presentation_tier,
    _screen_weight_for_tier,
    alt_text,
    compile_srcset,
    pick_image_sizes,
    pick_image_src,
)
from travelogue.render.cover_opening import cover_focal_point
from travelogue.render.moment_exif import format_moment_exif_line


def _moment_screen_weight_for_tier(tier: str) -> float:
    """Slightly larger than chapter viewport-fit so the signature screen reads at full weight."""
    return min(0.82, _screen_weight_for_tier(tier) + 0.12)


def moment_label_for_trip(trip: dict) -> str:
    locale = str((trip.get("meta") or {}).get("locale") or "").strip().lower()
    if locale.startswith("en"):
        return "Moment"
    return "决定性瞬间"


def moment_enabled_for_trip(trip: dict, *, cfg_moment_enabled: bool = True) -> bool:
    if not cfg_moment_enabled:
        return False
    moment_id = str(trip.get("momentAssetId") or "").strip()
    if not moment_id:
        return False
    skipped = (trip.get("curation") or {}).get("momentSkipped")
    return not skipped


def _day_span_for_asset(trip: dict, asset_id: str) -> list[str] | None:
    """PMX · 供 moment EXIF 与章 daySpan 对齐（抑制矛盾绝对年）。"""
    aid = str(asset_id or "").strip()
    if not aid:
        return None
    for ch in trip.get("chapters") or []:
        curation = ch.get("curation") if isinstance(ch.get("curation"), dict) else {}
        span = [str(d) for d in (curation.get("daySpan") or []) if d]
        for item in ch.get("items") or []:
            ids = item.get("assetIds") or []
            if aid in {str(x) for x in ids if x}:
                return span or None
        for screen in ch.get("screens") or []:
            for item in screen.get("items") or []:
                ids = item.get("assetIds") or []
                if aid in {str(x) for x in ids if x}:
                    return span or None
            sid = str(screen.get("assetId") or "").strip()
            if sid and sid == aid:
                return span or None
    return None


def build_moment_screen_context(
    trip: dict,
    assets: dict[str, dict],
    *,
    export_layout: str,
    meta_title: str,
    cfg_moment_enabled: bool = True,
    show_exif: bool = True,
) -> dict | None:
    if not moment_enabled_for_trip(trip, cfg_moment_enabled=cfg_moment_enabled):
        return None

    moment_id = str(trip.get("momentAssetId") or "").strip()
    asset = assets.get(moment_id)
    if not asset:
        return None

    kind = aspect_kind_for_asset(asset)
    is_portrait = kind in ("portrait", "tall", "square")
    if is_portrait:
        fit = portrait_fit_for_asset(asset)
    else:
        fit = full_frame_fit_for_asset(asset)

    fx, fy = cover_focal_point(asset)
    src = pick_image_src(asset, export_layout=export_layout)
    srcset = compile_srcset(asset, mobile=export_layout == "mobile")
    day_span = _day_span_for_asset(trip, moment_id)
    try:
        from travelogue.domain.narrative_posture import trip_primary_year

        primary_year = trip_primary_year(trip)
    except Exception:
        primary_year = None
    exif_line = (
        format_moment_exif_line(
            asset, day_span=day_span, trip_primary_year=primary_year
        )
        if show_exif
        else None
    )

    ar = _asset_aspect_ratio_float(asset)
    tier = _presentation_tier(ar)
    screen_style = (
        f"--screen-fit-ar: {ar:.6f}; --screen-weight: {_moment_screen_weight_for_tier(tier):.3f}"
    )

    return {
        "assetId": moment_id,
        "src": src,
        "hasSrc": bool(src),
        "hasSrcset": bool(srcset),
        "srcset": srcset,
        "sizes": pick_image_sizes(export_layout, "cover"),
        "alt": alt_text(None, asset, meta_title),
        "fit": fit,
        "focalX": fx,
        "focalY": fy,
        "isPortrait": is_portrait,
        "hasExifLine": bool(exif_line),
        "exifLine": exif_line or "",
        "label": moment_label_for_trip(trip),
        "hasViewportFit": True,
        "hasScreenStyle": True,
        "screenStyle": screen_style,
        "hasTierUltra": tier == "ultra",
    }
