"""Preview entry deep-link payload (Phase 4 M16 · F-P4-PRV-06).

GET /__travelogue/trips/{tripId}/entry returns a small, read-only payload that
lets the success overlay open the preview at a "peak" screen instead of the
cover. Pure functions over trip.json; never mutates the trip.
"""

from __future__ import annotations

from typing import Any

from travelogue.cover_engine import resolve_cover_opening_style, studio_style_options
from travelogue.cover_engine.registry import get_style
from travelogue.cover_engine.resolve import legacy_map
from travelogue.services.decor_line import chapter_has_voice
from travelogue.templating.summary import build_template_summary
from travelogue.web.studio_aesthetic import build_aesthetic_entry_summary
from travelogue.web.studio_constants import STUDIO_USER_NOTES_MAX_LEN
from travelogue.web.studio_telemetry import build_pipeline_telemetry_summary


def _ordered_screens(trip: dict) -> list[tuple[str, list[str], str | None]]:
    """All (screenId, assetIds, arcSegment) across chapters in document order."""
    screens: list[tuple[str, list[str], str | None]] = []
    for chapter in trip.get("chapters") or []:
        for screen in chapter.get("screens") or []:
            sid = screen.get("screenId")
            if not sid:
                continue
            aids = [
                slot.get("assetId")
                for slot in (screen.get("slots") or [])
                if slot.get("assetId")
            ]
            arc = screen.get("arcSegment")
            arc_str = str(arc) if arc else None
            screens.append((str(sid), aids, arc_str))
    return screens


def _peak_screen_score(screen: dict) -> float:
    slots = screen.get("slots") or []
    aids = [s.get("assetId") for s in slots if s.get("assetId")]
    score = 1.0
    if len(aids) <= 1:
        score += 0.5
    return score


def resolve_peak_screen_id(trip: dict) -> str | None:
    """Peak screen for the preview deep link (PRD-PHASE4 §8.5 fallback chain).

    Guaranteed non-None when any screen exists:
      1. best-scored screen with arcSegment == \"peak\" and assets
      2. first screen with arcSegment == \"peak\"
      3. largest scene cluster -> first matching screen
      4. first content screen (has >=1 asset slot)
      5. first screen
    """
    screens = _ordered_screens(trip)
    if not screens:
        return None

    best_sid: str | None = None
    best_score = float("-inf")
    screen_by_id: dict[str, dict] = {}
    for chapter in trip.get("chapters") or []:
        for screen in chapter.get("screens") or []:
            sid = screen.get("screenId")
            if sid:
                screen_by_id[str(sid)] = screen

    for sid, aids, arc in screens:
        if arc == "peak" and aids:
            score = _peak_screen_score(screen_by_id.get(sid, {}))
            if score > best_score:
                best_score = score
                best_sid = sid
            elif score == best_score and best_sid is not None:
                best_sid = sid
    if best_sid:
        return best_sid

    for sid, _aids, arc in screens:
        if arc == "peak":
            return sid

    clustering = (trip.get("curation") or {}).get("clustering") or {}
    clusters = clustering.get("clusters") or []
    if clusters:
        largest = max(clusters, key=lambda c: len(c.get("assetIds") or []))
        cluster_aids = {str(a) for a in (largest.get("assetIds") or [])}
        if cluster_aids:
            for sid, aids, _arc in screens:
                if any(str(a) in cluster_aids for a in aids):
                    return sid

    for sid, aids, _arc in screens:
        if aids:
            return sid

    return screens[0][0]


def build_intent_summary(trip: dict) -> dict[str, Any]:
    """Compact intent summary for the entry payload."""
    intent = trip.get("intent") or {}
    meta = trip.get("meta") or {}
    title = str(intent.get("title") or meta.get("title") or "我的旅途").strip()[:20]
    # PMX D3 · 展示名与编辑 SSOT 分列；封面 DOM 只绑 displayTitle
    from travelogue.domain.title_humanize import resolve_display_title
    display_title = resolve_display_title(meta if isinstance(meta, dict) else {})
    assets = trip.get("assets") or []
    featured = sum(1 for a in assets if a.get("userTier") == "featured")
    clustering = (trip.get("curation") or {}).get("clustering") or {}
    segments = clustering.get("segments") or []
    user_notes = str(intent.get("userNotes") or trip.get("userNotes") or "").strip()
    subjects = intent.get("featuredSubjects") or []
    cohort = (trip.get("curation") or {}).get("cohort") or {}
    return {
        "title": title or "我的旅途",
        "displayTitle": display_title or title or "我的旅途",
        "featuredCount": featured,
        "segmentCount": len(segments),
        "hasUserNotes": bool(user_notes),
        "userNotes": user_notes[:STUDIO_USER_NOTES_MAX_LEN] if user_notes else "",
        "featuredSubjectCount": len(subjects) if isinstance(subjects, list) else 0,
        "cohortDuoCount": int(cohort.get("duoCount") or 0) if cohort else 0,
    }


def build_chapter_summaries(trip: dict) -> list[dict[str, Any]]:
    """Chapter id/title/anchors for preview edit drawer."""
    rows: list[dict[str, Any]] = []
    for ch in trip.get("chapters") or []:
        ch_id = ch.get("id")
        if not ch_id:
            continue
        curation = ch.get("curation") or {}
        title_cap = 16 if curation.get("isAppendix") else 12
        appendix_ids = [str(a) for a in (curation.get("appendixAssetIds") or []) if a]
        rows.append(
            {
                "id": str(ch_id),
                "title": str(ch.get("title") or ch_id)[:title_cap],
                "memoryAnchors": list(curation.get("memoryAnchors") or [])[:3],
                "copyIntent": dict(curation.get("copyIntent") or {}),
                "hasVoice": chapter_has_voice(ch, trip),
                "isAppendix": bool(curation.get("isAppendix")),
                "appendixReason": str(curation.get("appendixReason") or ""),
                "appendixCount": len(appendix_ids),
                "appendixAssetIds": appendix_ids,
            }
        )
    return rows


def build_asset_media_index(trip: dict) -> dict[str, str]:
    """assetId → mediaClass for Studio collage override (PRD §3.4)."""
    out: dict[str, str] = {}
    for asset in trip.get("assets") or []:
        aid = asset.get("id")
        if aid:
            out[str(aid)] = str(asset.get("mediaClass") or "photo")
    return out


def build_entry(
    trip: dict,
    trip_id: str,
    *,
    aesthetic_enabled: bool = True,
    trip_dir: Any = None,
) -> dict[str, Any]:
    """Assemble the entry payload (previewUrl, peakScreenId, intentSummary)."""
    peak = resolve_peak_screen_id(trip)
    preview_url = f"/{trip_id}/index.html"
    scroll_share_url = f"{preview_url}?share=1"
    if peak:
        preview_url = f"{preview_url}#screen-{peak}"
        scroll_share_url = f"{scroll_share_url}#screen-{peak}"
    pipeline = trip.get("pipeline") or {}
    telemetry = build_pipeline_telemetry_summary(trip)
    curation = trip.get("curation") or {}
    raw_style = str((trip.get("meta") or {}).get("coverOpeningStyle") or "").strip()
    resolved = resolve_cover_opening_style(trip)
    style_rec = get_style(resolved)
    explain = curation.get("coverStyleExplain") if isinstance(curation, dict) else None
    return {
        "previewUrl": preview_url,
        "scrollShareUrl": scroll_share_url,
        "peakScreenId": peak,
        "intentSummary": build_intent_summary(trip),
        "pipelineStatus": pipeline.get("status"),
        "g1Pending": pipeline.get("status") == "structure_draft",
        "derivativesStatus": str(pipeline.get("derivativesStatus") or "") or None,
        "derivativesReady": pipeline.get("derivativesStatus") == "ready",
        "derivativesPreparing": int(pipeline.get("derivativesPreparing") or 0),
        "coverAssetId": str(trip.get("coverAssetId") or "") or None,
        "chapters": build_chapter_summaries(trip),
        "telemetry": telemetry,
        "aesthetic": build_aesthetic_entry_summary(
            trip,
            enabled=aesthetic_enabled,
            trip_dir=trip_dir,
        ),
        "template": build_template_summary(trip),
        "assetMediaById": build_asset_media_index(trip),
        "coverOpeningStyle": resolved,
        "coverOpeningStyleRaw": raw_style or None,
        "coverStyleOptions": studio_style_options(),
        "coverJointLocked": bool(curation.get("coverJointLocked")) if isinstance(curation, dict) else False,
        "coverStyleExplain": explain if isinstance(explain, dict) else None,
        "coverStyleLabel": (style_rec.studio_label or style_rec.label) if style_rec else resolved,
        "coverLegacyMapped": legacy_map(raw_style) is not None,
        "coverIsPlaceholder": (
            not bool(curation.get("coverJointLocked"))
            if isinstance(curation, dict)
            else True
        ),
        "layoutVibe": _layout_vibe_entry(trip),
        "layoutVibeOptions": _layout_vibe_options(),
        "bookends": _bookends_entry_summary(trip, curation if isinstance(curation, dict) else {}),
        "appendixOutlierCount": len(
            (curation.get("excludedTimeOutlierAssetIds") or [])
            if isinstance(curation, dict)
            else []
        ),
        "worksBrand": _works_brand_entry(trip),
        "longshotDensity": _longshot_density_entry(trip),
        "shareCopyPack": _share_copy_pack_entry(trip),
    }


def _layout_vibe_entry(trip: dict) -> str:
    from travelogue.config.layout_vibe import resolve_layout_vibe

    return resolve_layout_vibe(trip)


def _layout_vibe_options() -> list[dict[str, str]]:
    from travelogue.web.studio_handlers.layout_vibe_handlers import layout_vibe_options

    return layout_vibe_options()


def _works_brand_entry(trip: dict) -> dict:
    from travelogue.domain.works_brand import resolve_works_brand

    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    resolved = resolve_works_brand(meta)
    return {
        "mode": resolved["worksBrandMode"],
        "text": str(meta.get("worksBrandText") or "").strip()[:14],
        "line": resolved["worksBrandLine"],
        "show": resolved["showWorksBrand"],
    }


def _longshot_density_entry(trip: dict) -> str:
    from travelogue.domain.longshot_density import resolve_longshot_density

    return resolve_longshot_density(trip)


def _share_copy_pack_entry(trip: dict) -> dict:
    """Xiaohongshu copy pack fields (D-SFI-14 / OQ-2)."""
    from travelogue.domain.share_copy_pack import build_share_copy_pack
    from travelogue.web.studio_narrate import studio_llm_status

    status = studio_llm_status()
    pack = build_share_copy_pack(
        trip, llm_available=bool(status.get("llmAvailable"))
    )
    return {
        "title": pack["title"],
        "body": pack["body"],
        "topics": pack["topics"],
        "llmAvailable": bool(status.get("llmAvailable")),
    }


def _bookends_entry_summary(trip: dict, curation: dict) -> dict:
    """Compact bookends snapshot for Studio entry (B2b)."""
    try:
        from travelogue.cover_engine.api import build_bookends_studio_payload

        payload = build_bookends_studio_payload(trip)
        return {
            "panelTitle": payload.get("panelTitle"),
            "panelSubtitle": payload.get("panelSubtitle"),
            "userOneLiner": payload.get("userOneLiner"),
            "closingAssetId": payload.get("closingAssetId"),
            "closingPending": payload.get("closingPending"),
            "degraded": payload.get("degraded"),
            "lock": payload.get("lock"),
            "closingUserPicked": payload.get("closingUserPicked"),
            "mobileClosingEnabled": payload.get("mobileClosingEnabled"),
            "hasScreens": payload.get("hasScreens"),
        }
    except Exception:
        lock = curation.get("bookendsLock") if isinstance(curation.get("bookendsLock"), dict) else {}
        return {
            "panelTitle": "封面与封底",
            "panelSubtitle": "画册的第一眼与最后一眼",
            "userOneLiner": "",
            "closingAssetId": curation.get("closingAssetId") if "closingAssetId" in curation else None,
            "closingPending": "closingAssetId" not in curation,
            "degraded": bool(curation.get("bookendsDegraded")),
            "lock": {"opening": bool(lock.get("opening")), "closing": bool(lock.get("closing"))},
            "closingUserPicked": bool(curation.get("closingUserPicked")),
            "mobileClosingEnabled": False,
            "hasScreens": False,
        }
