"""Build Handlebars context from trip.json."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from travelogue.config import AppConfig

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
        label = f"{date.fromisoformat(start).strftime('%Y.%m.%d')} – {fmt_short(end)}"
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
) -> dict:
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
    if photos_only:
        caption = ""
    voice = item.get("voice")
    edit_caption = f"chapters.{chapter_id}.items.{item_index}.caption" if is_draft else None
    ctx: dict = {
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


def build_epilogue_stats(trip: dict) -> dict:
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
) -> dict:
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

    featured_ids = featured_asset_ids or frozenset()
    slot_aids = [sl.get("assetId", "") for sl in screen.get("slots") or []]
    is_featured = any(aid in featured_ids for aid in slot_aids if aid)

    out: dict = {
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


def _trip_index_desc(lead: str, *, max_len: int = 48) -> str:
    text = lead.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def build_trip_index_entries(chapters: list[dict]) -> list[dict]:
    entries: list[dict] = []
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
) -> list[dict]:
    cards: list[dict] = []
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


def build_foreword_spread(first_chapter: dict, *, trip_hook: str = "") -> dict | None:
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
) -> dict | None:
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


@dataclass
class ChaptersRenderBundle:
    """Chapter list and folio extras (enrich phase)."""

    chapters_out: list[dict]
    foreword_spread: dict | None
    has_foreword_spread: bool
    trip_index_entries: list[dict]
    has_trip_index: bool
    featured_grid_cards: list[dict]
    has_featured_grid: bool


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
    from travelogue.config import get_config, reading_profile_defaults
    from travelogue.curation.screen_planner import resolve_layout_engine, screens_layout_active
    from travelogue.render.copy_display import is_photos_only, resolve_copy_display, should_strip_narrative_copy
    from travelogue.render.engine import (
        should_include_long_shot,
        should_include_longshot_bridge,
        should_include_screenplay,
        web_screens_surface_active,
    )
    from travelogue.render.reading_profile import (
        reading_json_for_html,
        resolve_reading_payload,
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


def build_chapters_render_context(
    trip: dict,
    surface: SurfaceContext,
    *,
    trip_root: Path | None,
    meta_title: str,
    hook: str,
) -> ChaptersRenderBundle:
    from travelogue.curation.chapter_items import resolve_chapter_items_for_render
    from travelogue.curation.layout_planner import aspect_kind_for_asset
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

    chapters_out: list[dict] = []
    aspects_map = {a["id"]: aspect_kind_for_asset(a) for a in trip.get("assets", []) if a.get("id")}
    layout_eligible_count = sum(
        1 for a in trip.get("assets", []) if a.get("layoutEligible", True)
    )
    featured_ids = frozenset(collect_featured_ids(trip))
    global_screen_index = 0

    folio_plan: dict = {}
    grid_exclude: frozenset[str] = frozenset()
    if folio_full:
        from travelogue.curation.folio_plan import resolve_folio_plan

        layout_eligible = [a for a in trip.get("assets", []) if a.get("layoutEligible", True)]
        folio_plan = resolve_folio_plan(trip, trip.get("chapters") or [], layout_eligible)
        if folio_plan.get("featuredGrid"):
            grid_exclude = frozenset(folio_plan.get("featuredGridAssetIds") or [])

    foreword_spread: dict | None = None
    has_foreword_spread = False
    if folio_full and folio_plan.get("foreword"):
        chapters_raw = trip.get("chapters") or []
        if chapters_raw:
            first_lead = (chapters_raw[0].get("lead") or "").strip()
            if first_lead and not strip_narrative_copy:
                foreword_spread = build_foreword_spread(chapters_raw[0], trip_hook=hook)
                has_foreword_spread = foreword_spread is not None

    raw_chapters = trip.get("chapters") or []
    if is_longshot_surface:
        from travelogue.curation.longshot_filter import chapters_for_longshot_render

        raw_chapters = chapters_for_longshot_render(raw_chapters)

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
            chapter_screen_seq = 0
            for sc in raw_screens:
                slots = sc.get("slots") or []
                if grid_exclude:
                    slots = [s for s in slots if s.get("assetId") not in grid_exclude]
                    if not slots:
                        continue
                    if len(slots) != len(sc.get("slots") or []):
                        sc = dict(sc)
                        sc["slots"] = slots
                raw_screens_for_spread.append(sc)
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
                        folio_lite=folio_lite,
                        is_plate=chapter_screen_seq == 1,
                        featured_asset_ids=featured_ids,
                    )
                )

        screen_spread: dict | None = None
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

        items_out = []
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
                aid = it["assetId"]
                items_out.append(
                    build_media_card(
                        it,
                        assets[aid],
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
                items_out.append(
                    {
                        "isBreathPause": True,
                        "breathLabel": it.get("label") or "···",
                        "breathStyle": f"--breath-tone: rgb({r}, {g}, {b});",
                    }
                )

        use_chapter_separator = (
            use_screens_global
            and not is_longshot_surface
            and surface.include_breath
            and int(idx) > 1
        )
        chapter_tone = None
        if use_chapter_separator and raw_screens_for_spread:
            chapter_tone = _screen_tone_css((raw_screens_for_spread[0] or {}).get("tone"))

        lead = (ch.get("lead") or "").strip()
        if strip_narrative_copy:
            lead = ""
        if i == 0 and has_foreword_spread:
            lead = ""
        ch_ctx = {
            "id": ch["id"],
            "patternId": ch.get("patternId", ""),
            "index": f"{idx:02d}",
            "title": ch.get("title", ""),
            "lead": lead,
            "hasLead": bool(lead),
            "editableLead": is_draft and bool(lead),
            "editLeadPath": f"chapters.{ch['id']}.lead" if is_draft else None,
            "hasMemoryAnchors": bool(anchors),
            "memoryAnchors": ",".join(anchors) if anchors else None,
            "useScreensEngine": use_screens,
            "screens": screens_out,
            "hasScreenSpread": has_screen_spread,
            "screenSpread": screen_spread or {},
            "items": items_out,
            "useChapterSeparator": use_chapter_separator,
            "chapterSeparatorStyle": (
                f"background: {chapter_tone or _DEFAULT_SCREEN_TONE};" if use_chapter_separator else ""
            ),
            **chapter_divider(ch, idx),
        }
        chapters_out.append(ch_ctx)

    trip_index_entries: list[dict] = []
    featured_grid_cards: list[dict] = []
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
) -> dict:
    """export_mode: draft | share | present-preview"""
    from travelogue.curation.curate import resolve_cover_asset_id
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

    cover_id = resolve_cover_asset_id(trip, export_layout=image_layout)
    if not cover_id or cover_id not in assets:
        cover_id = trip.get("coverAssetId") or ""
    cover_asset = assets[cover_id]
    cover_src = pick_image_src(cover_asset, export_layout=image_layout)
    cover_srcset = compile_srcset(cover_asset, mobile=image_layout == "mobile")

    meta_line, meta_datetime = format_trip_meta(meta)
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

    return {
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
        "isShare": surface.is_share,
        "title": meta_title,
        "subtitle": (meta.get("subtitle") or "").strip(),
        "hasSubtitle": bool((meta.get("subtitle") or "").strip()),
        "coverShowTitle": cover_show_title,
        "cover": {
            "src": cover_src,
            "hasSrcset": bool(cover_srcset),
            "srcset": cover_srcset,
            "sizes": pick_image_sizes(image_layout, "cover"),
            "alt": alt_text(None, cover_asset, meta_title),
        },
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
        "tripIndex": {"entries": chapters_bundle.trip_index_entries},
        "hasFeaturedGrid": chapters_bundle.has_featured_grid,
        "featuredGrid": {"cards": chapters_bundle.featured_grid_cards},
        "hasForewordSpread": chapters_bundle.has_foreword_spread,
        "forewordSpread": chapters_bundle.foreword_spread or {},
        "isLongshotSurface": surface.is_longshot_surface,
        "epilogueStats": epilogue_stats,
        "useEpilogueStats": use_epilogue_stats,
        "useEpilogueScreen": (surface.folio_lite and bool(epilogue)) or use_epilogue_stats,
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
