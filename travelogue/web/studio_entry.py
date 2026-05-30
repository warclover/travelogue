"""Preview entry deep-link payload (Phase 4 M16 · F-P4-PRV-06).

GET /__travelogue/trips/{tripId}/entry returns a small, read-only payload that
lets the success overlay open the preview at a "peak" screen instead of the
cover. Pure functions over trip.json; never mutates the trip.
"""

from __future__ import annotations

from typing import Any

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


def resolve_peak_screen_id(trip: dict) -> str | None:
    """Peak screen for the preview deep link (PRD-PHASE4 §8.5 fallback chain).

    Guaranteed non-None when any screen exists:
      1. first screen with arcSegment == \"peak\" and assets
      2. first screen with arcSegment == \"peak\"
      3. largest scene cluster -> first matching screen
      4. first content screen (has >=1 asset slot)
      5. first screen
    """
    screens = _ordered_screens(trip)
    if not screens:
        return None

    for sid, aids, arc in screens:
        if arc == "peak" and aids:
            return sid
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
    assets = trip.get("assets") or []
    featured = sum(1 for a in assets if a.get("userTier") == "featured")
    clustering = (trip.get("curation") or {}).get("clustering") or {}
    segments = clustering.get("segments") or []
    user_notes = str(intent.get("userNotes") or trip.get("userNotes") or "").strip()
    return {
        "title": title or "我的旅途",
        "featuredCount": featured,
        "segmentCount": len(segments),
        "hasUserNotes": bool(user_notes),
        "userNotes": user_notes[:STUDIO_USER_NOTES_MAX_LEN] if user_notes else "",
    }


def build_chapter_summaries(trip: dict) -> list[dict[str, Any]]:
    """Chapter id/title/anchors for preview edit drawer."""
    rows: list[dict[str, Any]] = []
    for ch in trip.get("chapters") or []:
        ch_id = ch.get("id")
        if not ch_id:
            continue
        curation = ch.get("curation") or {}
        rows.append(
            {
                "id": str(ch_id),
                "title": str(ch.get("title") or ch_id)[:12],
                "memoryAnchors": list(curation.get("memoryAnchors") or [])[:3],
            }
        )
    return rows


def build_entry(trip: dict, trip_id: str) -> dict[str, Any]:
    """Assemble the entry payload (previewUrl, peakScreenId, intentSummary)."""
    peak = resolve_peak_screen_id(trip)
    preview_url = f"/{trip_id}/index.html"
    scroll_share_url = f"{preview_url}?share=1"
    if peak:
        preview_url = f"{preview_url}#screen-{peak}"
        scroll_share_url = f"{scroll_share_url}#screen-{peak}"
    pipeline = trip.get("pipeline") or {}
    telemetry = build_pipeline_telemetry_summary(trip)
    return {
        "previewUrl": preview_url,
        "scrollShareUrl": scroll_share_url,
        "peakScreenId": peak,
        "intentSummary": build_intent_summary(trip),
        "pipelineStatus": pipeline.get("status"),
        "g1Pending": pipeline.get("status") == "structure_draft",
        "chapters": build_chapter_summaries(trip),
        "telemetry": telemetry,
    }
