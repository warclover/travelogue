"""Assemble Agent 2 briefs from trip.json (metadata only, no image bytes)."""

from __future__ import annotations

from typing import Any

from travelogue.curation.asset_caption import asset_skips_caption, chapter_caption_asset_ids, resolve_caption
from travelogue.services.narrate import _manifest_limits


def _asset_brief(asset: dict) -> dict[str, Any]:
    place = asset.get("place") or {}
    voice = asset.get("voice") or {}
    excerpt = (voice.get("transcriptPreview") or voice.get("transcript") or "").strip()
    out: dict[str, Any] = {
        "id": asset.get("id"),
        "takenAt": asset.get("takenAt"),
        "tags": list(asset.get("tags") or [])[:8],
        "tagsSource": asset.get("tagsSource"),
        "aspectKind": asset.get("aspectKind"),
        "mediaClass": asset.get("mediaClass"),
    }
    city = place.get("city")
    if city:
        out["city"] = city
    if excerpt:
        out["voiceExcerpt"] = excerpt[:120]
        out["hasVoice"] = True
    return out


def manifest_limits_brief() -> dict[str, int]:
    lim = _manifest_limits()
    return {
        "tripTitleMaxChars": 20,
        "hookMaxChars": lim["hookMaxChars"],
        "chapterTitleMaxChars": 12,
        "chapterLeadMaxChars": lim["chapterLeadMaxChars"],
        "captionMaxChars": 60,
        "epilogueMaxChars": lim["epilogueMaxChars"],
    }


def build_meta_brief(trip: dict, *, tone: str, regenerate: bool = False) -> dict[str, Any]:
    meta = trip.get("meta") or {}
    curation = trip.get("curation") or {}
    segments = curation.get("segments") or []
    return {
        "task": "fill_trip_meta",
        "trip": {
            "tripId": trip.get("tripId"),
            "title": meta.get("title"),
            "dateStart": meta.get("dateStart"),
            "dateEnd": meta.get("dateEnd"),
            "places": meta.get("places") or [],
            "tone": tone,
            "userNotes": meta.get("userNotes"),
            "segmentCount": len(segments),
            "segmentLabels": [s.get("label") for s in segments[:5] if s.get("label")],
        },
        "limits": manifest_limits_brief(),
        "fieldsRequested": ["meta.hook", "epilogue"],
        "existing": {
            "hook": "" if regenerate else (meta.get("hook") or ""),
            "epilogue": "" if regenerate else (trip.get("epilogue") or ""),
        },
    }


def build_chapter_brief(
    trip: dict, chapter: dict, *, tone: str, regenerate: bool = False
) -> dict[str, Any]:
    meta = trip.get("meta") or {}
    assets = {a["id"]: a for a in trip.get("assets") or []}
    ch_cur = chapter.get("curation") or {}
    items_out: list[dict[str, Any]] = []
    item_by_asset = {
        it.get("assetId"): it
        for it in chapter.get("items") or []
        if it.get("type") == "media-card" and it.get("assetId")
    }
    for aid in chapter_caption_asset_ids(chapter):
        item = item_by_asset.get(aid)
        asset = assets.get(aid) or {}
        existing = resolve_caption(item, asset)
        items_out.append(
            {
                "assetId": aid,
                "existingTitle": (item.get("title") if item else "") or "",
                "existingCaption": "" if regenerate else existing,
                "skipCaption": bool(item and item.get("edited"))
                or asset_skips_caption(asset)
                or (bool(existing) and not regenerate),
                "asset": _asset_brief(asset),
            }
        )
    return {
        "task": "fill_chapter_copy",
        "trip": {
            "tripId": trip.get("tripId"),
            "places": meta.get("places") or [],
            "tone": tone,
        },
        "limits": manifest_limits_brief(),
        "chapter": {
            "id": chapter.get("id") or f"ch-{chapter.get('index', 0):02d}",
            "index": chapter.get("index"),
            "patternId": chapter.get("patternId"),
            "title": chapter.get("title"),
            "places": ch_cur.get("places") or [],
            "memoryAnchors": ch_cur.get("memoryAnchors") or [],
            "daySpan": ch_cur.get("daySpan") or [],
            "segmentId": ch_cur.get("segmentId"),
            "existingLead": "" if regenerate else (chapter.get("lead") or ""),
            "items": items_out,
        },
        "fieldsRequested": ["lead", "items[].caption"],
    }
