"""Assemble Agent 2 briefs from trip.json (metadata only, no image bytes)."""

from __future__ import annotations

import datetime as _dt
import re
from typing import Any

from travelogue.config import AppConfig
from travelogue.curation.asset_caption import (
    asset_skips_caption,
    chapter_caption_asset_ids,
    resolve_caption,
)
from travelogue.services.narrate import _manifest_limits
from travelogue.services.narrative_scope import captions_allowed, chapter_lead_allowed

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _asset_brief(asset: dict, *, include_geo_city: bool = True) -> dict[str, Any]:
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
    if include_geo_city:
        city = place.get("city")
        if city:
            out["city"] = city
    if excerpt:
        out["voiceExcerpt"] = excerpt[:120]
        out["hasVoice"] = True
    return out


def resolve_user_notes(trip: dict) -> str | None:
    """Unified userNotes source (PRD-PHASE4 §8.4): trip.userNotes ?? intent.userNotes."""
    notes = trip.get("userNotes")
    if not notes:
        notes = (trip.get("intent") or {}).get("userNotes")
    text = str(notes or "").strip()
    return text or None


def resolve_plan_summary(trip: dict) -> str | None:
    """intent.travelPlan.summary for brief injection (PRD-PHASE4 §8.4)."""
    plan = (trip.get("intent") or {}).get("travelPlan") or {}
    text = str(plan.get("summary") or "").strip()
    return text or None


def resolve_travel_notes(trip: dict) -> str | None:
    """intent.travelNotes for prompt grounding (Phase 14)."""
    notes = (trip.get("intent") or {}).get("travelNotes")
    text = str(notes or "").strip()
    if not text:
        return None
    return text[:500]


def resolve_date_range(trip: dict) -> dict[str, str] | None:
    """Best-effort user date range from intent; invalid payloads are ignored."""
    raw = (trip.get("intent") or {}).get("dateRange")
    if not isinstance(raw, dict):
        return None
    start = str(raw.get("start") or "").strip()
    end = str(raw.get("end") or "").strip()
    out: dict[str, str] = {}
    if start and _ISO_DATE_RE.match(start):
        try:
            _dt.date.fromisoformat(start)
            out["start"] = start
        except ValueError:
            pass
    if end and _ISO_DATE_RE.match(end):
        try:
            _dt.date.fromisoformat(end)
            out["end"] = end
        except ValueError:
            pass
    source = str(raw.get("source") or "").strip().lower()
    if source in ("user", "exif", "mixed"):
        out["source"] = source
    # fail-open: if both dates exist but reversed, drop range.
    if out.get("start") and out.get("end") and out["start"] > out["end"]:
        return None
    return out or None


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


_DATEISH_LABEL_PART = re.compile(
    r"^(?:\d{4}年?)?\d{1,2}月(?:\d{1,2}日)?(?:\s*[–—\-~～]\s*(?:\d{4}年?)?\d{1,2}月?(?:\d{1,2}日)?)?$"
)
_DAYPART_LABEL_PARTS = frozenset({"上午", "下午", "傍晚", "晚上"})


def _safe_segment_labels_for_brief(
    segments: list[Any],
    *,
    allowed_places: list[str],
) -> list[str]:
    """Date/daypart (+ authorized place) labels only — never feed polluted scene tails to LLM."""
    from travelogue.services.narrative_validate import unauthorized_place_mentions

    allowed = {str(p).strip() for p in allowed_places if str(p).strip()}
    out: list[str] = []
    for seg in segments[:5]:
        if not isinstance(seg, dict):
            continue
        label = str(seg.get("label") or "").strip()
        if not label:
            continue
        parts = [p.strip() for p in re.split(r"[·•]", label) if p and p.strip()]
        kept: list[str] = []
        for part in parts:
            if _DATEISH_LABEL_PART.match(part) or part in _DAYPART_LABEL_PARTS:
                kept.append(part)
                continue
            if any(ap and (ap == part or ap in part or part in ap) for ap in allowed):
                if not unauthorized_place_mentions(part, allowed):
                    kept.append(part)
                continue
            # Drop unauthorized scene/place tails (e.g. 「京都雨季漫游」 on a 斯里兰卡 trip).
        if kept:
            out.append("·".join(kept)[:24])
        else:
            # Keep a date-only head when possible so segmentCount still has grounding.
            head = parts[0] if parts else label
            if _DATEISH_LABEL_PART.match(head):
                out.append(head[:24])
    return out


def build_meta_brief(trip: dict, *, tone: str, regenerate: bool = False) -> dict[str, Any]:
    from travelogue.services.copy_subject import (
        effective_meta_places,
        narrative_copy_subject,
        places_user_set,
    )

    meta = trip.get("meta") or {}
    intent = trip.get("intent")
    assets = trip.get("assets") or []
    curation = trip.get("curation") or {}
    segments = curation.get("segments") or []
    places = effective_meta_places(meta, intent=intent, assets=assets)
    trip_brief: dict[str, Any] = {
        "tripId": trip.get("tripId"),
        "title": meta.get("title"),
        "dateStart": meta.get("dateStart"),
        "dateEnd": meta.get("dateEnd"),
        "places": places,
        "editorialSubject": narrative_copy_subject(meta, intent=intent, assets=assets),
        "placesUserSet": places_user_set(intent),
        "tone": tone,
        "userNotes": resolve_user_notes(trip),
        "segmentCount": len(segments),
        # Authority is meta.places; labels are date scaffolding only (never invent places).
        "segmentLabels": _safe_segment_labels_for_brief(
            list(segments) if isinstance(segments, list) else [],
            allowed_places=list(places),
        ),
    }
    travel_notes = resolve_travel_notes(trip)
    if travel_notes:
        trip_brief["travelNotes"] = travel_notes
    date_range = resolve_date_range(trip)
    if date_range:
        trip_brief["dateRange"] = date_range
    plan_summary = resolve_plan_summary(trip)
    if plan_summary:
        trip_brief["travelPlanSummary"] = plan_summary
    return {
        "task": "fill_trip_meta",
        "trip": trip_brief,
        "limits": manifest_limits_brief(),
        "fieldsRequested": ["meta.hook", "epilogue"],
        "existing": {
            "hook": "" if regenerate else (meta.get("hook") or ""),
            "epilogue": "" if regenerate else (trip.get("epilogue") or ""),
        },
    }


def build_chapter_brief(
    trip: dict,
    chapter: dict,
    *,
    tone: str,
    regenerate: bool = False,
    scope: str = "frame",
) -> dict[str, Any]:
    from travelogue.services.copy_subject import (
        effective_meta_places,
        filter_chapter_places_for_copy,
        narrative_copy_subject,
        places_user_set,
        suppress_chapter_geo_places,
    )

    meta = trip.get("meta") or {}
    intent = trip.get("intent")
    assets_list = trip.get("assets") or []
    include_geo_city = not suppress_chapter_geo_places(meta, intent=intent, assets=assets_list)
    chapters = trip.get("chapters") or []
    assets = {a["id"]: a for a in assets_list}
    ch_cur = chapter.get("curation") or {}
    items_out: list[dict[str, Any]] = []
    item_by_asset = {
        it.get("assetId"): it
        for it in chapter.get("items") or []
        if it.get("type") == "media-card" and it.get("assetId")
    }
    if captions_allowed(scope):
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
                    "asset": _asset_brief(asset, include_geo_city=include_geo_city),
                }
            )
    fields_requested: list[str] = []
    if chapter_lead_allowed(chapter, chapters, scope):
        fields_requested.append("lead")
    if captions_allowed(scope):
        fields_requested.append("items[].caption")
    trip_brief: dict[str, Any] = {
        "tripId": trip.get("tripId"),
        "places": effective_meta_places(meta, intent=intent, assets=assets_list),
        "editorialSubject": narrative_copy_subject(meta, intent=intent, assets=assets_list),
        "placesUserSet": places_user_set(intent),
        "tone": tone,
    }
    user_notes = resolve_user_notes(trip)
    if user_notes:
        trip_brief["userNotes"] = user_notes
    travel_notes = resolve_travel_notes(trip)
    if travel_notes:
        trip_brief["travelNotes"] = travel_notes
    date_range = resolve_date_range(trip)
    if date_range:
        trip_brief["dateRange"] = date_range
    return {
        "task": "fill_chapter_copy",
        "trip": trip_brief,
        "limits": manifest_limits_brief(),
        "chapter": {
            "id": chapter.get("id") or f"ch-{chapter.get('index', 0):02d}",
            "index": chapter.get("index"),
            "patternId": chapter.get("patternId"),
            "title": chapter.get("title"),
            "places": filter_chapter_places_for_copy(
                ch_cur.get("places"),
                meta,
                intent=intent,
                assets=assets_list,
            ),
            "memoryAnchors": ch_cur.get("memoryAnchors") or [],
            "daySpan": ch_cur.get("daySpan") or [],
            "segmentId": ch_cur.get("segmentId"),
            "existingLead": "" if regenerate else (chapter.get("lead") or ""),
            "items": items_out,
        },
        "fieldsRequested": fields_requested,
    }


def build_chapter_decor_brief(
    trip: dict,
    chapter: dict,
    *,
    regenerate: bool = False,
    cfg: AppConfig | None = None,
) -> dict[str, Any]:
    from travelogue.config import get_config
    from travelogue.services.decor_line import (
        _chapter_voice_excerpts,
        _copy_intent,
        extract_chapter_facts,
    )

    app_cfg = cfg or get_config()
    ch_cur = chapter.get("curation") or {}
    facts = extract_chapter_facts(chapter, trip, cfg=app_cfg)
    voice_excerpts = _chapter_voice_excerpts(chapter, trip)
    visual_facts: list[str] = []
    if app_cfg.narrative.decor_line_visual_facts_enabled:
        from travelogue.services.visual_facts import extract_visual_facts

        visual_facts = extract_visual_facts(chapter, trip)
    intent = _copy_intent(chapter) if app_cfg.narrative.decor_line_intent_enabled else {}
    limits = manifest_limits_brief()
    limits["decorLineMaxChars"] = app_cfg.narrative.decor_line_max_chars
    return {
        "task": "fill_chapter_decor_line",
        "limits": limits,
        "chapter": {
            "id": chapter.get("id"),
            "index": chapter.get("index"),
            "title": chapter.get("title"),
            "facts": facts[:8],
            "voiceExcerpts": voice_excerpts[:3],
            "visualFacts": visual_facts[:4],
            "memoryAnchors": ch_cur.get("memoryAnchors") or [],
            "copyIntent": intent,
            "existingDecorLine": "" if regenerate else (chapter.get("decorLine") or ""),
        },
        "fieldsRequested": ["decorLine"],
    }
