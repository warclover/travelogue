"""Stamp layout arc segments onto chapter screens (PRD-PHASE4 §8.5)."""

from __future__ import annotations

from travelogue.curation.arc_patterns import (
    ARC_CLOSE,
    ARC_FALL,
    ARC_MOMENT,
    ARC_OPEN,
    ARC_PEAK,
    ARC_RISE,
)

BREATH_PATTERN = "screen-breath-pause"
MAX_PEAK_SCREENS_PER_CHAPTER = 3
PEAK_MIN_GAP = 2
HEAD_TAIL_RATIO = 0.15


def _is_content_screen(screen: dict) -> bool:
    if screen.get("patternId") == BREATH_PATTERN:
        return False
    return any(s.get("assetId") for s in screen.get("slots") or [])


def _screen_kind(screen: dict) -> str:
    slots = screen.get("slots") or []
    aids = [s.get("assetId") for s in slots if s.get("assetId")]
    return "hero" if len(aids) <= 1 else "grid"


def _content_screen_score(index: int, screen: dict) -> float:
    score = 1.0
    if index < 2:
        score += 2.0
    if _screen_kind(screen) == "hero":
        score += 0.5
    return score


def _hero_content_index(content: list[dict], chapter: dict) -> int | None:
    hero_id = (chapter.get("curation") or {}).get("heroAssetId")
    if hero_id:
        for i, screen in enumerate(content):
            for slot in screen.get("slots") or []:
                if slot.get("assetId") == hero_id:
                    return i
    if not content:
        return None
    return max(range(len(content)), key=lambda i: _content_screen_score(i, content[i]))


def _pick_peak_indices(
    n: int,
    content: list[dict],
    chapter: dict,
) -> set[int]:
    if n <= 0:
        return set()

    head = max(1, int(n * HEAD_TAIL_RATIO))
    tail = max(1, int(n * HEAD_TAIL_RATIO))
    mid_start = head
    mid_end = n - tail
    if mid_end <= mid_start:
        mid_start, mid_end = 0, n

    hero = _hero_content_index(content, chapter)
    peaks: list[int] = []
    if hero is not None:
        peaks.append(hero)

    max_peaks = 1 if n <= 12 else min(MAX_PEAK_SCREENS_PER_CHAPTER, 3)
    scored = sorted(
        range(mid_start, mid_end),
        key=lambda i: (-_content_screen_score(i, content[i]), i),
    )
    for i in scored:
        if len(peaks) >= max_peaks:
            break
        if i in peaks:
            continue
        if all(abs(i - p) >= PEAK_MIN_GAP for p in peaks):
            peaks.append(i)

    if not peaks:
        peaks = [mid_start + (mid_end - mid_start) // 2]
    return set(peaks)


def _segments_for_peak_chapter(content: list[dict], chapter: dict) -> list[str]:
    n = len(content)
    if n <= 3:
        hero = _hero_content_index(content, chapter)
        out = [ARC_MOMENT] * n
        peak_idx = hero if hero is not None else n // 2
        out[peak_idx] = ARC_PEAK
        return out

    head = max(1, int(n * HEAD_TAIL_RATIO))
    tail = max(1, int(n * HEAD_TAIL_RATIO))
    peak_indices = _pick_peak_indices(n, content, chapter)
    out: list[str] = []
    for i in range(n):
        if i < head:
            out.append(ARC_RISE)
        elif i >= n - tail:
            out.append(ARC_FALL)
        elif i in peak_indices:
            out.append(ARC_PEAK)
        else:
            out.append(ARC_MOMENT)
    return out


def _segments_for_transitional_chapter(content: list[dict], chapter_segment: str) -> list[str]:
    n = len(content)
    if n <= 3:
        return [chapter_segment] * n
    third = max(1, n // 3)
    out: list[str] = []
    for i in range(n):
        if i < third:
            out.append(chapter_segment)
        elif i < 2 * third:
            out.append(ARC_MOMENT)
        else:
            out.append(chapter_segment)
    return out


def _segments_with_intent_hero_peak(
    content: list[dict],
    chapter: dict,
    chapter_segment: str,
) -> list[str]:
    out = [chapter_segment] * len(content)
    hero = _hero_content_index(content, chapter)
    if hero is not None:
        out[hero] = ARC_PEAK
    return out


def screen_arc_segments_for_chapter(
    chapter: dict,
    chapter_segment: str,
    *,
    intent_peak_chapter: bool = False,
) -> list[str]:
    """Return arcSegment per content screen (photo screens only, document order)."""
    content = [sc for sc in chapter.get("screens") or [] if _is_content_screen(sc)]
    if not content:
        return []

    if intent_peak_chapter and chapter_segment != ARC_PEAK:
        return _segments_with_intent_hero_peak(content, chapter, chapter_segment)

    if chapter_segment == ARC_PEAK:
        return _segments_for_peak_chapter(content, chapter)

    if chapter_segment in (ARC_RISE, ARC_FALL):
        return _segments_for_transitional_chapter(content, chapter_segment)

    return [chapter_segment] * len(content)


def _assign_screen_arc_segments(
    chapter: dict,
    chapter_segment: str,
    *,
    intent_peak_chapter: bool,
) -> None:
    segments = screen_arc_segments_for_chapter(
        chapter,
        chapter_segment,
        intent_peak_chapter=intent_peak_chapter,
    )
    if not segments:
        return

    seg_iter = iter(segments)
    for screen in chapter.get("screens") or []:
        if not isinstance(screen, dict):
            continue
        if not _is_content_screen(screen):
            screen.pop("arcSegment", None)
            continue
        screen["arcSegment"] = next(seg_iter)


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
        intent_peak = bool(peak_chapters and index in peak_chapters)
        curation = chapter.setdefault("curation", {})
        if intent_peak:
            curation["intentPeakChapter"] = True
        else:
            curation.pop("intentPeakChapter", None)
        _assign_screen_arc_segments(
            chapter,
            segment,
            intent_peak_chapter=intent_peak,
        )
