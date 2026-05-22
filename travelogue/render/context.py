"""Build Handlebars context from trip.json."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from travelogue.media.image_ops import classify_aspect, detect_orientation
from travelogue.paths import LONGSHOT_JS, SHARE_JS
from travelogue.services.validate import asset_map


def _longshot_bundle_version(trip: dict) -> str:
    """Pin asset cache-busting to bundle mtimes so template changes invalidate
    even when trip.json is unchanged."""
    stamps: list[int] = []
    for path in (LONGSHOT_JS, SHARE_JS):
        try:
            stamps.append(int(path.stat().st_mtime))
        except OSError:
            pass
    if stamps:
        return f"ls{max(stamps)}"
    updated = (trip.get("updatedAt") or trip.get("createdAt") or "0")
    return updated.replace(":", "").replace("-", "")[:15] or "0"


def share_zip_filename(trip: dict) -> str:
    trip_id = (trip.get("tripId") or "").strip()
    return f"trip-{trip_id}.zip" if trip_id else ""


def has_share_zip(trip: dict, trip_root: Path | None) -> bool:
    name = share_zip_filename(trip)
    if not name or trip_root is None:
        return False
    return (trip_root / name).is_file()


def format_duration(seconds: int | float | None) -> str:
    if seconds is None:
        return "0:00"
    total = max(0, int(round(seconds)))
    m, s = divmod(total, 60)
    return f"{m}:{s:02d}"


def compile_srcset(asset: dict, *, mobile: bool = False) -> str:
    if mobile and asset.get("cropMobile"):
        return ""
    parts: list[str] = []
    for entry in asset.get("srcset") or []:
        parts.append(f'{entry["file"]} {entry["width"]}w')
    return ", ".join(parts)


_MOBILE_IMAGE_SIZES: dict[str, str] = {
    "cover": "100vw",
    "card_bleed": "100vw",
    "card_page": "100vw",
    "row_third": "33vw",
    "row_half": "50vw",
    "scroll": "86vw",
}

# Align with journal.css --page-width / --bleed-width clamps (up to 1320 / 1920px).
_WEB_IMAGE_SIZES: dict[str, str] = {
    "cover": (
        "(min-width: 1920px) 2200px, (min-width: 1200px) 1800px, "
        "(min-width: 768px) 1400px, 100vw"
    ),
    "card_bleed": (
        "(min-width: 1920px) 2200px, (min-width: 1200px) 1800px, "
        "(min-width: 768px) 1400px, 100vw"
    ),
    "card_page": (
        "(min-width: 1920px) 1320px, (min-width: 1200px) 1200px, "
        "(min-width: 768px) 1100px, 100vw"
    ),
    "row_third": "(min-width: 1920px) 720px, (min-width: 1200px) 600px, 33vw",
    "row_half": "(min-width: 1920px) 1100px, (min-width: 1200px) 900px, 50vw",
    "screen_full": (
        "(min-width: 1920px) 2200px, (min-width: 1200px) 1800px, "
        "(min-width: 768px) 1400px, 100vw"
    ),
    "scroll": (
        "(min-width: 1920px) 1000px, (min-width: 1200px) 760px, "
        "(min-width: 768px) 620px, 86vw"
    ),
}


def pick_image_sizes(export_layout: str, slot: str) -> str:
    """Responsive `sizes` for srcset; web/auto use desktop tiers up to bleed 1920px."""
    if export_layout == "mobile":
        return _MOBILE_IMAGE_SIZES[slot]
    return _WEB_IMAGE_SIZES[slot]


def pick_image_src(asset: dict, *, export_layout: str = "mobile") -> str:
    """Display WebP (scaled, original aspect). Ignores legacy profile crop files."""
    return asset.get("displayFile") or asset.get("sourceFile") or ""


def pick_collage_src(asset: dict) -> str:
    """Same as pick_image_src — display assets are no longer pre-cropped."""
    return pick_image_src(asset)


def asset_aspect_kind(asset: dict) -> str:
    kind = asset.get("aspectKind")
    if kind in ("portrait", "landscape", "square", "panorama", "tall"):
        return kind
    w = int(asset.get("width") or 0)
    h = int(asset.get("height") or 0)
    if w > 0 and h > 0:
        return classify_aspect(w, h)
    return "square"


def alt_text(item: dict | None, asset: dict, meta_title: str) -> str:
    if item:
        for key in ("title", "caption"):
            v = (item.get(key) or "").strip()
            if v:
                return v
    for key in ("title", "caption"):
        v = (asset.get(key) or "").strip() if isinstance(asset.get(key), str) else ""
        if v:
            return v
    return meta_title or "旅行照片"


def media_card_classes(layout: dict | None, asset: dict) -> str:
    layout = layout or {}
    classes = ["media-card"]
    if layout.get("bleed", True):
        classes.append("media-card--bleed")
    if layout.get("fill", True):
        classes.append("media-card--fill")
    if layout.get("overlay", True):
        classes.append("media-card--overlay")
    if asset.get("type") == "video":
        classes.append("media-card--video")
    slot = (layout.get("slot") or "").strip()
    if slot == "panorama":
        classes.append("media-card--panorama")
    elif slot == "square":
        classes.append("media-card--square")
    elif slot == "tall":
        classes.append("media-card--tall")
    else:
        kind = asset.get("aspectKind")
        w = asset.get("width") or 0
        h = asset.get("height") or 0
        if not kind and w and h:
            kind = classify_aspect(int(w), int(h))
        if kind == "panorama":
            classes.append("media-card--panorama")
        elif kind == "square":
            classes.append("media-card--square")
        elif kind == "tall":
            classes.append("media-card--tall")
        elif kind == "landscape" or (w and h and detect_orientation(int(w), int(h)) == "landscape"):
            classes.append("media-card--landscape")
        elif kind == "portrait" or (w and h and detect_orientation(int(w), int(h)) == "portrait"):
            classes.append("media-card--portrait")
    return " ".join(classes)


def format_trip_meta(meta: dict) -> tuple[str, str]:
    start = meta.get("dateStart", "")
    end = meta.get("dateEnd", "")
    place = (meta.get("places") or ["—"])[0]
    days = 1
    try:
        d0 = date.fromisoformat(start)
        d1 = date.fromisoformat(end)
        days = max(1, (d1 - d0).days + 1)
    except ValueError:
        pass

    def fmt_short(d: str) -> str:
        try:
            return date.fromisoformat(d).strftime("%m.%d")
        except ValueError:
            return d

    if start and end:
        label = f"{date.fromisoformat(start).strftime('%Y.%m.%d')} – {fmt_short(end)}"
        dt_attr = f"{start}/{end}"
    else:
        label = ""
        dt_attr = ""
    line = f"{label} · {place} · {days} 天" if label else f"{place} · {days} 天"
    return line, dt_attr


def build_voice(voice: dict, *, asset_id: str, label: str, is_draft: bool) -> dict:
    return {
        "hasVoice": True,
        "audioFile": voice.get("audioFile", ""),
        "duration": format_duration(voice.get("durationSec")),
        "ariaLabel": f"语音：{label}",
        "transcript": voice.get("transcript") or voice.get("transcriptPreview") or "",
        "transcriptOpen": is_draft and voice.get("showTranscript", True),
        "editableTranscript": is_draft,
    }


def build_media_card(
    item: dict,
    asset: dict,
    *,
    meta_title: str,
    export_layout: str,
    is_draft: bool,
    eager: bool = False,
) -> dict:
    layout = item.get("layout") or {}
    src = pick_image_src(asset, export_layout=export_layout)
    srcset = compile_srcset(asset, mobile=export_layout == "mobile")
    alt = alt_text(item, asset, meta_title)
    title = (item.get("title") or "").strip()
    caption = (item.get("caption") or "").strip()
    tags = asset.get("tags") or []
    voice = asset.get("voice")
    is_video = asset.get("type") == "video"

    ctx: dict = {
        "isMediaCard": True,
        "isMediaRow": False,
        "isMediaScroll": False,
        "classes": media_card_classes(layout, asset),
        "assetId": asset["id"],
        "aspectKind": asset_aspect_kind(asset),
        "tagsAttr": ",".join(tags) if tags else None,
        "hasTags": bool(tags),
        "isVideo": is_video,
        "src": src,
        "hasSrcset": bool(srcset),
        "srcset": srcset,
        "sizes": pick_image_sizes(
            export_layout,
            "card_bleed" if layout.get("bleed", True) else "card_page",
        ),
        "alt": alt,
        "loading": "eager" if eager else "lazy",
        "title": title,
        "hasTitle": bool(title),
        "caption": caption,
        "hasCaption": bool(caption),
        "editable": is_draft,
        "hasVoice": False,
        "playBadge": None,
    }

    if is_video:
        ctx["poster"] = asset.get("posterFile") or src
        ctx["videoFile"] = asset.get("displayFile", "")
        duration = asset.get("durationSec")
        if duration:
            ctx["playBadge"] = f"{int(duration)}s · 轻触开声" if asset.get("hasAudio") else f"{int(duration)}s"
        elif asset.get("hasAudio"):
            ctx["playBadge"] = "轻触开声"

    if voice and not is_video:
        ctx.update(
            build_voice(
                voice,
                asset_id=asset["id"],
                label=title or alt,
                is_draft=is_draft,
            )
        )

    return ctx


def build_media_row(
    item: dict,
    assets: dict[str, dict],
    *,
    meta_title: str,
    export_layout: str,
    is_draft: bool,
) -> dict:
    cells = []
    for aid in item.get("assetIds", []):
        asset = assets[aid]
        kind = asset_aspect_kind(asset)
        cells.append(
            {
                "src": pick_image_src(asset, export_layout=export_layout),
                "srcset": compile_srcset(asset, mobile=export_layout == "mobile"),
                "hasSrcset": bool(compile_srcset(asset)),
                "alt": alt_text(None, asset, meta_title),
                "sizes": pick_image_sizes(export_layout, "row_half"),
                "aspectKind": kind,
            }
        )
    caption = (item.get("caption") or "").strip()
    row_layout = (item.get("rowLayout") or "").strip()
    row_class = f"media-row--{row_layout}" if row_layout and row_layout != "default" else ""
    row_slot = (
        "row_third"
        if row_layout in ("landscape-triple", "square-triple", "portrait-triple")
        else "row_half"
    )
    if row_layout in ("mobile-landscape-grid-8", "mobile-portrait-grid-4"):
        row_slot = "row_half"
    sizes = pick_image_sizes(export_layout, row_slot)
    for cell in cells:
        cell["sizes"] = sizes
    layout_hint = (item.get("layoutHint") or "").strip() or None
    return {
        "isMediaCard": False,
        "isMediaRow": True,
        "isMediaScroll": False,
        "cells": cells,
        "caption": caption,
        "hasCaption": bool(caption),
        "rowLayout": row_layout or None,
        "rowClass": row_class,
        "layoutHint": layout_hint,
        "hasLayoutHint": bool(layout_hint),
        "editable": is_draft,
    }


def build_media_scroll(
    item: dict,
    assets: dict[str, dict],
    *,
    meta_title: str,
    export_layout: str,
    is_draft: bool,
) -> dict:
    slides = []
    for aid in item.get("assetIds", []):
        asset = assets[aid]
        kind = asset_aspect_kind(asset)
        slides.append(
            {
                "src": pick_image_src(asset, export_layout=export_layout),
                "srcset": compile_srcset(asset, mobile=export_layout == "mobile"),
                "hasSrcset": bool(compile_srcset(asset)),
                "alt": alt_text(None, asset, meta_title),
                "sizes": pick_image_sizes(export_layout, "scroll"),
                "aspectKind": kind,
            }
        )
    caption = (item.get("caption") or "").strip()
    voice = item.get("voice")
    ctx: dict = {
        "isMediaCard": False,
        "isMediaRow": False,
        "isMediaScroll": True,
        "slides": slides,
        "caption": caption,
        "hasCaption": bool(caption),
        "hasVoice": False,
        "editable": is_draft,
    }
    if voice:
        ctx.update(
            build_voice(
                voice,
                asset_id="scroll",
                label=caption or meta_title,
                is_draft=is_draft,
            )
        )
    return ctx


from travelogue.curation.screen_planner import grid_class_for_pattern
from travelogue.curation.screen_tone import enrich_screen_tones

_DEFAULT_SCREEN_TONE = "#e8e4df"


def _screen_tone_css(tone: dict | None) -> str | None:
    if not tone:
        return _DEFAULT_SCREEN_TONE
    try:
        r = int(tone.get("r", 0))
        g = int(tone.get("g", 0))
        b = int(tone.get("b", 0))
    except (TypeError, ValueError):
        return _DEFAULT_SCREEN_TONE
    return f"#{r:02x}{g:02x}{b:02x}"


def _screen_aspect_ratio_css(asset: dict) -> str | None:
    """Native source ratio for single-slot screens (avoids squashed 16:9 boxes)."""
    w = int(asset.get("nativeWidth") or asset.get("width") or 0)
    h = int(asset.get("nativeHeight") or asset.get("height") or 0)
    if w > 0 and h > 0:
        return f"{w} / {h}"
    return None


def build_layout_screen(
    screen: dict,
    assets: dict[str, dict],
    *,
    meta_title: str,
    export_layout: str,
    eager: bool = False,
) -> dict:
    pattern_id = screen.get("patternId", "screen-landscape-1")
    grid_class = grid_class_for_pattern(pattern_id)
    n_slots = len(screen.get("slots") or [])
    if "1col" in grid_class and n_slots == 1:
        sizes_slot = "screen_full"
    elif "3x3" in grid_class or n_slots >= 9:
        sizes_slot = "row_third"
    elif "2x2" in grid_class or "2col" in grid_class or n_slots == 2:
        sizes_slot = "row_half"
    else:
        sizes_slot = "row_third"

    slots_out = []
    mixed_p1_l2 = pattern_id == "screen-portrait-1-landscape-2"
    for j, slot in enumerate(screen.get("slots") or []):
        aid = slot.get("assetId", "")
        asset = assets[aid]
        fit = slot.get("fit", "cover")
        role = slot.get("role")
        if mixed_p1_l2:
            slot_sizes = "row_third" if role == "portrait" or slot.get("slot") == 0 else "row_half"
        else:
            slot_sizes = sizes_slot
        srcset = compile_srcset(asset, mobile=export_layout == "mobile")
        slot_aspect = _screen_aspect_ratio_css(asset)
        style_parts_slot: list[str] = []
        if slot_aspect:
            style_parts_slot.append(f"--slot-aspect: {slot_aspect}")
        fp = asset.get("focalPoint") or {}
        try:
            fx = float(fp.get("x", 0.5))
            fy = float(fp.get("y", 0.45))
            style_parts_slot.append(f"--focal-x: {fx}")
            style_parts_slot.append(f"--focal-y: {fy}")
        except (TypeError, ValueError):
            pass
        slot_style = "; ".join(style_parts_slot)
        if slot_style:
            slot_style += ";"
        entry: dict = {
            "slotIndex": slot.get("slot", j),
            "fit": fit,
            "src": pick_image_src(asset, export_layout=export_layout),
            "hasSrcset": bool(srcset),
            "srcset": srcset,
            "sizes": pick_image_sizes(export_layout, slot_sizes),
            "alt": alt_text(None, asset, meta_title),
            "loading": "eager" if eager and j == 0 else "lazy",
            "slotStyle": slot_style,
        }
        if role:
            entry["role"] = role
        slots_out.append(entry)

    layout_hint = screen.get("layoutHint")
    screen_aspect: str | None = None
    # 人物竖屏用 layoutHint + 视口高度 CSS，勿再套整屏 --screen-aspect（否则大底色+小图）
    if layout_hint not in ("person-pair", "person-triple") and n_slots == 1 and "1col" in grid_class:
        first_aid = (screen.get("slots") or [{}])[0].get("assetId", "")
        if first_aid and first_aid in assets:
            screen_aspect = _screen_aspect_ratio_css(assets[first_aid])

    style_parts: list[str] = []
    if screen_aspect:
        style_parts.append(f"--screen-aspect: {screen_aspect}")
    tone = _screen_tone_css(screen.get("tone"))
    if tone:
        style_parts.append(f"--screen-tone: {tone}")
    screen_style = "; ".join(style_parts)
    if screen_style:
        screen_style += ";"

    return {
        "patternId": pattern_id,
        "gridClass": grid_class,
        "screenTone": tone,
        "screenStyle": screen_style,
        "layoutHint": layout_hint,
        "hasLayoutHint": bool(layout_hint),
        "slots": slots_out,
    }


def chapter_divider(ch: dict, index: int) -> dict:
    if index <= 1:
        return {"showDivider": False}
    curation = ch.get("curation") or {}
    day_span = curation.get("daySpan") or []
    places = curation.get("places") or []
    if not day_span and not places:
        return {"showDivider": False}
    divider: dict = {"showDivider": True}
    if day_span:
        d = day_span[0]
        try:
            divider["dividerDatetime"] = d
            divider["dividerDate"] = date.fromisoformat(d).strftime("%m.%d")
        except ValueError:
            divider["dividerDatetime"] = d
            divider["dividerDate"] = d
    if places:
        divider["dividerPlace"] = places[0]
    return divider


def build_render_context(
    trip: dict,
    *,
    export_mode: str = "draft",
    trip_root: Path | None = None,
    layout_engine_override: str | None = None,
    export_layout_override: str | None = None,
    font_theme: str | None = None,
) -> dict:
    """export_mode: draft | share"""
    is_draft = export_mode == "draft"
    is_share = export_mode == "share"
    assets = asset_map(trip)
    meta = trip.get("meta", {})
    export_layout = export_layout_override or trip.get("exportLayout", "auto")
    from travelogue.curation.screen_planner import resolve_layout_engine, screens_layout_active

    layout_engine = resolve_layout_engine(trip, override=layout_engine_override)
    use_screens_global = screens_layout_active(trip, override=layout_engine_override)
    meta_title = meta.get("title", "")

    from travelogue.curation.curate import resolve_cover_asset_id

    cover_id = resolve_cover_asset_id(trip, export_layout=export_layout)
    if not cover_id or cover_id not in assets:
        cover_id = trip.get("coverAssetId") or ""
    cover_asset = assets[cover_id]
    cover_src = pick_image_src(cover_asset, export_layout=export_layout)
    cover_srcset = compile_srcset(cover_asset, mobile=export_layout == "mobile")

    meta_line, meta_datetime = format_trip_meta(meta)
    hook = (meta.get("hook") or "").strip()
    epilogue = (trip.get("epilogue") or "").strip()

    chapters_out = []
    for i, ch in enumerate(trip.get("chapters", [])):
        idx = ch.get("index", i + 1)
        curation = ch.get("curation") or {}
        anchors = curation.get("memoryAnchors") or []
        use_screens = use_screens_global and bool(ch.get("screens"))
        screens_out = []
        if use_screens:
            raw_screens = enrich_screen_tones(
                ch.get("screens", []),
                assets,
                trip_root=trip_root,
                chapter_index=idx,
            )
            for j, sc in enumerate(raw_screens):
                screens_out.append(
                    build_layout_screen(
                        sc,
                        assets,
                        meta_title=meta_title,
                        export_layout=export_layout,
                        eager=i == 0 and j == 0,
                    )
                )

        items_out = []
        for j, it in enumerate(ch.get("items", [])):
            itype = it.get("type")
            eager = i == 0 and j == 0
            if itype == "media-card":
                aid = it["assetId"]
                items_out.append(
                    build_media_card(
                        it,
                        assets[aid],
                        meta_title=meta_title,
                        export_layout=export_layout,
                        is_draft=is_draft,
                        eager=eager,
                    )
                )
            elif itype == "media-row":
                items_out.append(
                    build_media_row(
                        it,
                        assets,
                        meta_title=meta_title,
                        export_layout=export_layout,
                        is_draft=is_draft,
                    )
                )
            elif itype == "media-scroll":
                items_out.append(
                    build_media_scroll(
                        it,
                        assets,
                        meta_title=meta_title,
                        export_layout=export_layout,
                        is_draft=is_draft,
                    )
                )

        lead = (ch.get("lead") or "").strip()
        ch_ctx = {
            "id": ch["id"],
            "patternId": ch.get("patternId", ""),
            "index": f"{idx:02d}",
            "title": ch.get("title", ""),
            "lead": lead,
            "hasLead": bool(lead),
            "hasMemoryAnchors": bool(anchors),
            "memoryAnchors": ",".join(anchors) if anchors else None,
            "useScreensEngine": use_screens,
            "screens": screens_out,
            "items": items_out,
            **chapter_divider(ch, idx),
        }
        chapters_out.append(ch_ctx)

    from travelogue.render.engine import should_include_long_shot

    include_long_shot = should_include_long_shot(
        trip,
        export_mode=export_mode,
        layout_engine_override=layout_engine_override,
    )

    html_attrs = [f'data-export="{export_mode}"']
    if export_layout and export_layout != "auto":
        html_attrs.append(f'data-layout="{export_layout}"')
    if use_screens_global:
        html_attrs.append(f'data-layout-engine="{layout_engine}"')
    if include_long_shot:
        html_attrs.append('data-longshot="on"')
    theme = font_theme or (trip.get("export") or {}).get("fontTheme") or ""
    if theme == "magazine":
        html_attrs.append('data-font-theme="magazine"')

    asset_version = _longshot_bundle_version(trip)
    zip_name = share_zip_filename(trip)
    zip_ready = has_share_zip(trip, trip_root)

    return {
        "lang": "zh-CN",
        "htmlExtraAttrs": " ".join(html_attrs),
        "includeLongShot": include_long_shot,
        "assetVersion": asset_version,
        "hasShareZip": zip_ready,
        "shareZipFile": zip_name if zip_ready else None,
        "exportLayout": export_layout,
        "layoutEngine": layout_engine,
        "exportMode": export_mode,
        "isDraft": is_draft,
        "isShare": is_share,
        "title": meta_title,
        "subtitle": (meta.get("subtitle") or "").strip(),
        "hasSubtitle": bool((meta.get("subtitle") or "").strip()),
        "cover": {
            "src": cover_src,
            "hasSrcset": bool(cover_srcset),
            "srcset": cover_srcset,
            "sizes": pick_image_sizes(export_layout, "cover"),
            "alt": alt_text(None, cover_asset, meta_title),
        },
        "tripMetaLine": meta_line,
        "tripMetaDatetime": meta_datetime,
        "hook": hook,
        "hasHook": bool(hook),
        "epilogue": epilogue,
        "hasEpilogue": bool(epilogue),
        "chapters": chapters_out,
        "tripRoot": str(trip_root) if trip_root else None,
    }


def collect_asset_paths(trip: dict, trip_root: Path) -> list[tuple[str, Path]]:
    """Return (display path, absolute path) for files that must exist before render."""
    assets = asset_map(trip)
    export_layout = trip.get("exportLayout", "auto")
    seen: set[str] = set()
    out: list[tuple[str, Path]] = []

    def add(rel: str | None) -> None:
        if not rel or rel in seen:
            return
        seen.add(rel)
        out.append((rel, trip_root / rel))

    for asset in assets.values():
        add(pick_image_src(asset, export_layout=export_layout))
        if asset.get("type") == "video":
            add(asset.get("posterFile"))
            add(asset.get("displayFile"))
        for entry in asset.get("srcset") or []:
            add(entry.get("file"))
        voice = asset.get("voice")
        if voice:
            add(voice.get("audioFile"))

    for ch in trip.get("chapters", []):
        for sc in ch.get("screens") or []:
            for slot in sc.get("slots") or []:
                aid = slot.get("assetId")
                if aid and aid in assets:
                    add(pick_image_src(assets[aid], export_layout=export_layout))
        for it in ch.get("items", []):
            if it.get("type") == "media-scroll":
                v = it.get("voice")
                if v:
                    add(v.get("audioFile"))
                for aid in it.get("assetIds", []):
                    a = assets[aid]
                    add(pick_image_src(a, export_layout=export_layout))

    from travelogue.curation.curate import resolve_cover_asset_id

    if export_layout == "auto":
        cover_profiles: tuple[str, ...] = ("mobile", "web")
    elif export_layout in ("mobile", "web"):
        cover_profiles = (export_layout,)
    else:
        cover_profiles = ("mobile",)
    for profile in cover_profiles:
        cid = resolve_cover_asset_id(trip, export_layout=profile)
        cover = assets.get(cid or "")
        if cover:
            add(pick_image_src(cover, export_layout=profile))

    return out
