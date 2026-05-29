"""Preview entry deep-link payload (Phase 4 M16 · F-P4-PRV-06).

GET /__travelogue/trips/{tripId}/entry returns a small, read-only payload that
lets the success overlay open the preview at a "peak" screen instead of the
cover. Pure functions over trip.json; never mutates the trip.
"""

from __future__ import annotations

from typing import Any


def _ordered_screens(trip: dict) -> list[tuple[str, list[str]]]:
    """All (screenId, [assetIds]) across chapters in document order."""
    screens: list[tuple[str, list[str]]] = []
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
            screens.append((str(sid), aids))
    return screens


def resolve_peak_screen_id(trip: dict) -> str | None:
    """Peak screen for the preview deep link (PRD-PHASE4 §8.5 fallback chain).

    Phase-3-independent; guaranteed non-None when any screen exists:
      1. scene-cluster peak: largest curation.clustering cluster -> first screen
         containing one of its assets
      2. first content screen (has >=1 asset slot)
      3. first screen
    Returns None only for legacy/no-screen layouts (preview opens at top).
    """
    screens = _ordered_screens(trip)
    if not screens:
        return None

    clustering = (trip.get("curation") or {}).get("clustering") or {}
    clusters = clustering.get("clusters") or []
    if clusters:
        largest = max(clusters, key=lambda c: len(c.get("assetIds") or []))
        cluster_aids = {str(a) for a in (largest.get("assetIds") or [])}
        if cluster_aids:
            for sid, aids in screens:
                if any(str(a) in cluster_aids for a in aids):
                    return sid

    for sid, aids in screens:
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
    return {
        "title": title or "我的旅途",
        "featuredCount": featured,
        "segmentCount": len(segments),
        "hasUserNotes": bool(intent.get("userNotes") or trip.get("userNotes")),
    }


def build_entry(trip: dict, trip_id: str) -> dict[str, Any]:
    """Assemble the entry payload (previewUrl, peakScreenId, intentSummary)."""
    peak = resolve_peak_screen_id(trip)
    preview_url = f"/{trip_id}/index.html"
    if peak:
        preview_url = f"{preview_url}#screen-{peak}"
    return {
        "previewUrl": preview_url,
        "peakScreenId": peak,
        "intentSummary": build_intent_summary(trip),
    }
