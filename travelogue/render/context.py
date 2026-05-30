"""Build Handlebars context from trip.json."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from travelogue.render.context_types import (
    BreathPauseItemContext,
    ChapterDividerContext,
    ChapterRenderContext,
    EpilogueStatsContext,
    FeaturedGridCardContext,
    ForewordSpreadContext,
    LayoutScreenContext,
    MediaCardContext,
    MediaRowContext,
    MediaScrollContext,
    ScreenSpreadContext,
    TripIndexEntryContext,
)

from travelogue.curation.asset_caption import asset_caption, resolve_caption
from travelogue.media.image_ops import classify_aspect, detect_orientation
from travelogue.paths import (
    BREATH_CSS,
    BREATH_JS,
    COPY_DISPLAY_CSS,
    COPY_TOGGLE_JS,
    INLINE_EDIT_CSS,
    INLINE_EDIT_JS,
    JOURNAL_CSS,
    JOURNAL_SCREENS_CSS,
    LONGSHOT_BRIDGE_JS,
    LONGSHOT_JS,
    SCREENPLAY_CSS,
    SCREENPLAY_HASH_JS,
    SCREENPLAY_BOOKMARKS_JS,
    SCREENPLAY_JS,
    SHARE_JS,
)
from travelogue.services.validate import asset_map


def _asset_lookup(assets: dict[str, dict], aid: str) -> dict | None:
    if not aid:
        return None
    return assets.get(aid)


def _longshot_bundle_version(trip: dict) -> str:
    """Pin asset cache-busting to bundle mtimes so template changes invalidate
    even when trip.json is unchanged."""
    stamps: list[int] = []
    for path in (
        JOURNAL_CSS,
        JOURNAL_SCREENS_CSS,
        BREATH_JS,
        BREATH_CSS,
        LONGSHOT_JS,
        SHARE_JS,
        SCREENPLAY_JS,
        SCREENPLAY_CSS,
        SCREENPLAY_HASH_JS,
        SCREENPLAY_BOOKMARKS_JS,
        COPY_TOGGLE_JS,
        COPY_DISPLAY_CSS,
        LONGSHOT_BRIDGE_JS,
        INLINE_EDIT_JS,
        INLINE_EDIT_CSS,
    ):
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
    if export_layout in ("mobile", "longshot"):
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
        try:
            label = f"{date.fromisoformat(start).strftime('%Y.%m.%d')} – {fmt_short(end)}"
            dt_attr = f"{start}/{end}"
        except ValueError:
            label = f"{fmt_short(start)} – {fmt_short(end)}"
            dt_attr = f"{start}/{end}"
    else:
        label = ""
        dt_attr = ""
    line = f"{label} · {place} · {days} 天" if label else f"{place} · {days} 天"
    return line, dt_attr


def build_voice(
    voice: dict,
    *,
    label: str,
    is_draft: bool,
    edit_path_transcript: str | None = None,
) -> dict:
    return {
        "hasVoice": True,
        "audioFile": voice.get("audioFile", ""),
        "duration": format_duration(voice.get("durationSec")),
        "ariaLabel": f"语音：{label}",
        "transcript": voice.get("transcript") or voice.get("transcriptPreview") or "",
        "transcriptOpen": is_draft and voice.get("showTranscript", True),
        "editableTranscript": is_draft and bool(edit_path_transcript),
        "editPathTranscript": edit_path_transcript if is_draft else None,
    }


def build_media_card(
    item: dict,
    asset: dict,
    *,
    meta_title: str,
    export_layout: str,
    is_draft: bool,
    eager: bool = False,
    photos_only: bool = False,
    chapter_id: str | None = None,
    item_index: int | None = None,
    caption_on_asset: bool = False,
) -> MediaCardContext:
    layout = item.get("layout") or {}
    src = pick_image_src(asset, export_layout=export_layout)
    srcset = compile_srcset(asset, mobile=export_layout == "mobile")
    alt = alt_text(item, asset, meta_title)
    title = (item.get("title") or "").strip()
    caption = resolve_caption(item, asset)
    if photos_only:
        title = ""
        caption = ""
    tags = asset.get("tags") or []
    voice = asset.get("voice")
    is_video = asset.get("type") == "video"

    if is_draft:
        if caption_on_asset:
            edit_caption = f"assets.{asset['id']}.caption"
        elif chapter_id is not None and item_index is not None:
            edit_caption = f"chapters.{chapter_id}.items.{item_index}.caption"
        else:
            edit_caption = f"items.{asset['id']}.caption"
    else:
        edit_caption = None

    ctx: MediaCardContext = {
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
        "editPathTitle": f"items.{asset['id']}.title" if is_draft else None,
        "editPathCaption": edit_caption,
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
                label=title or alt,
                is_draft=is_draft,
                edit_path_transcript=f"assets.{asset['id']}.voice.transcript" if is_draft else None,
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
    chapter_id: str,
    item_index: int,
    photos_only: bool = False,
) -> MediaRowContext:
    cells = []
    for aid in item.get("assetIds", []):
        asset = _asset_lookup(assets, aid)
        if not asset:
            continue
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
    if photos_only:
        caption = ""
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
    edit_caption = f"chapters.{chapter_id}.items.{item_index}.caption" if is_draft else None
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
        "editPathCaption": edit_caption,
    }


def build_media_scroll(
    item: dict,
    assets: dict[str, dict],
    *,
    meta_title: str,
    export_layout: str,
    is_draft: bool,
    chapter_id: str,
    item_index: int,
    photos_only: bool = False,
) -> MediaScrollContext:
    slides = []
    for aid in item.get("assetIds", []):
        asset = _asset_lookup(assets, aid)
        if not asset:
            continue
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
    if photos_only:
        caption = ""
    voice = item.get("voice")
    edit_caption = f"chapters.{chapter_id}.items.{item_index}.caption" if is_draft else None
    ctx: MediaScrollContext = {
        "isMediaCard": False,
        "isMediaRow": False,
        "isMediaScroll": True,
        "slides": slides,
        "caption": caption,
        "hasCaption": bool(caption),
        "hasVoice": False,
        "editable": is_draft,
        "editPathCaption": edit_caption,
    }
    if voice:
        ctx.update(
            build_voice(
                voice,
                label=caption or meta_title,
                is_draft=is_draft,
                edit_path_transcript=(
                    f"chapters.{chapter_id}.items.{item_index}.voice.transcript" if is_draft else None
                ),
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


def build_epilogue_stats(trip: dict) -> EpilogueStatsContext:
    """P5-S4 · trip summary for epilogue stats screen."""
    assets = [
        a
        for a in trip.get("assets") or []
        if a.get("layoutEligible", True) and a.get("type") != "video"
    ]
    days: set[str] = set()
    places: set[str] = set()
    for ch in trip.get("chapters") or []:
        cur = ch.get("curation") or {}
        for d in cur.get("daySpan") or []:
            key = str(d)[:10]
            if key:
                days.add(key)
        for p in cur.get("places") or []:
            text = str(p).strip()
            if text:
                places.add(text)
    meta = trip.get("meta") or {}
    if isinstance(meta.get("place"), str) and meta["place"].strip():
        places.add(meta["place"].strip())
    photo_count = len(assets)
    day_count = max(len(days), 1) if photo_count else 0
    place_count = max(len(places), 1) if photo_count else 0
    summary = f"{day_count} 天 · {place_count} 个地方 · {photo_count} 张照片"
    return {
        "dayCount": day_count,
        "placeCount": place_count,
        "photoCount": photo_count,
        "summaryLine": summary,
    }


def build_layout_screen(
    screen: dict,
    assets: dict[str, dict],
    *,
    meta_title: str,
    export_layout: str,
    eager: bool = False,
    screen_index: int | None = None,
    chapter_index: str | None = None,
    folio_lite: bool = False,
    is_plate: bool = False,
    featured_asset_ids: frozenset[str] | None = None,
) -> LayoutScreenContext:
    pattern_id = screen.get("patternId", "screen-landscape-1")
    if pattern_id == "screen-breath-pause":
        from travelogue.curation.breath_pauses import build_breath_pause_render_ctx

        return build_breath_pause_render_ctx(
            screen,
            screen_index=screen_index,
            chapter_index=chapter_index,
        )
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
        asset = _asset_lookup(assets, aid)
        if not asset:
            continue
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

    featured_ids = featured_asset_ids or frozenset()
    slot_aids = [sl.get("assetId", "") for sl in screen.get("slots") or []]
    is_featured = any(aid in featured_ids for aid in slot_aids if aid)

    out: LayoutScreenContext = {
        "patternId": pattern_id,
        "gridClass": grid_class,
        "screenTone": tone,
        "screenStyle": screen_style,
        "layoutHint": layout_hint,
        "hasLayoutHint": bool(layout_hint),
        "slots": slots_out,
        "isFeatured": is_featured,
    }
    if screen_index is not None:
        out["screenIndex"] = screen_index
        out["hasScreenIndex"] = True
    if chapter_index:
        out["chapterIndex"] = chapter_index
        out["hasChapterIndex"] = True
    joined_aids = ",".join(aid for aid in slot_aids if aid)
    if joined_aids:
        out["assetIds"] = joined_aids
        out["hasAssetIds"] = True
    if folio_lite:
        out["folioLite"] = True
        if is_plate:
            out["isPlate"] = True
            out["patternId"] = "screen-plate"
            first_aid = slot_aids[0] if slot_aids else ""
            if first_aid and first_aid in assets:
                cap = asset_caption(assets[first_aid])
                if cap:
                    out["plateCaption"] = cap
                    out["hasPlateCaption"] = True
        if screen_index is not None:
            out["folioPageLabel"] = f"Plate · {screen_index:02d}"
    return out


def chapter_divider(ch: dict, index: int) -> ChapterDividerContext:
    if index <= 1:
        return {"showDivider": False}
    curation = ch.get("curation") or {}
    day_span = curation.get("daySpan") or []
    places = curation.get("places") or []
    if not day_span and not places:
        return {"showDivider": False}
    divider: ChapterDividerContext = {"showDivider": True}
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


def _trip_index_desc(lead: str, *, max_len: int = 48) -> str:
    text = lead.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def build_trip_index_entries(chapters: list[dict]) -> list[TripIndexEntryContext]:
    entries: list[TripIndexEntryContext] = []
    for ch in chapters:
        idx = ch.get("index", len(entries) + 1)
        lead = str(ch.get("lead") or "")
        desc = _trip_index_desc(lead)
        entries.append(
            {
                "id": ch.get("id", f"ch-{idx:02d}"),
                "index": f"{int(idx):02d}",
                "title": ch.get("title", ""),
                "desc": desc,
                "hasDesc": bool(desc),
            }
        )
    return entries


def build_featured_grid_cards(
    asset_ids: list[str],
    assets: dict[str, dict],
    *,
    meta_title: str,
    export_layout: str,
) -> list[FeaturedGridCardContext]:
    cards: list[FeaturedGridCardContext] = []
    for aid in asset_ids:
        asset = assets.get(aid)
        if not asset:
            continue
        srcset = compile_srcset(asset, mobile=export_layout == "mobile")
        cards.append(
            {
                "assetId": aid,
                "src": pick_image_src(asset, export_layout=export_layout),
                "hasSrcset": bool(srcset),
                "srcset": srcset,
                "sizes": pick_image_sizes(export_layout, "row_third"),
                "alt": alt_text(None, asset, meta_title),
            }
        )
    return cards


def _extract_pull_quote(text: str, *, max_len: int = 40) -> str:
    text = text.strip()
    if not text:
        return ""
    for sep in ("。", "！", "？", "，", ",", "；", ";", "·"):
        if sep in text:
            chunk = text.split(sep, 1)[0].strip()
            if chunk:
                text = chunk
                break
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def build_foreword_spread(first_chapter: dict, *, trip_hook: str = "") -> ForewordSpreadContext | None:
    lead = str(first_chapter.get("lead") or "").strip()
    if not lead:
        return None
    title = str(first_chapter.get("title") or "").strip()
    pull = _extract_pull_quote(lead)
    if not pull or pull == lead:
        pull = (trip_hook or "").strip()
    return {
        "chapterTitle": title,
        "hasChapterTitle": bool(title),
        "lead": lead,
        "pullQuote": pull,
        "hasPullQuote": bool(pull and pull != lead),
    }


def build_screen_spread(
    chapter: dict,
    screen: dict,
    assets: dict[str, dict],
    *,
    meta_title: str,
    export_layout: str,
    trip_hook: str = "",
) -> ScreenSpreadContext | None:
    slots = screen.get("slots") or []
    if not slots:
        return None
    aid = slots[0].get("assetId", "")
    asset = assets.get(aid)
    if not asset:
        return None
    lead = str(chapter.get("lead") or "").strip()
    anchors = (chapter.get("curation") or {}).get("memoryAnchors") or []
    body = lead
    if not body and anchors:
        body = " · ".join(str(a) for a in anchors[:3])
    if not body:
        return None
    pull = _extract_pull_quote(body)
    if not pull or pull == body:
        hook = (trip_hook or "").strip()
        pull = hook if hook and hook != body else ""
    srcset = compile_srcset(asset, mobile=export_layout == "mobile")
    return {
        "src": pick_image_src(asset, export_layout=export_layout),
        "hasSrcset": bool(srcset),
        "srcset": srcset,
        "sizes": pick_image_sizes(export_layout, "row_half"),
        "alt": alt_text(None, asset, meta_title),
        "body": body,
        "pullQuote": pull,
        "hasPullQuote": bool(pull),
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
                    a = _asset_lookup(assets, aid)
                    if not a:
                        continue
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


from travelogue.render.assemble import build_render_context  # noqa: E402
from travelogue.render.chapters import ChaptersRenderBundle, build_chapters_render_context  # noqa: E402

__all__ = [
    "ChaptersRenderBundle",
    "build_chapters_render_context",
    "build_render_context",
]
