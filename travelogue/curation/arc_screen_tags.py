"""Stamp layout arc segments onto chapter screens (PRD-PHASE4 §8.5)."""

from __future__ import annotations


def stamp_screen_arc_segments(trip: dict, *, arc_profile: str = "dynamic") -> None:
    from travelogue.curation.intent_hints import (
        arc_segment_for_chapter_with_intent,
        peak_chapter_hints_for_trip,
    )

    chapters = trip.get("chapters") or []
    total = len(chapters)
    if total == 0:
        return
    peak_chapters = peak_chapter_hints_for_trip(trip, total)
    for index, chapter in enumerate(chapters, start=1):
        segment = arc_segment_for_chapter_with_intent(
            index,
            total,
            profile=arc_profile,
            peak_chapters=peak_chapters,
        )
        for screen in chapter.get("screens") or []:
            if isinstance(screen, dict):
                screen["arcSegment"] = segment
