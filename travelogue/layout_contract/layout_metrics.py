"""Layout metrics pure helpers (layout kernel)."""

from __future__ import annotations


def _screen_pattern_ids(chapters: list[dict]) -> list[str]:
    ids: list[str] = []
    for ch in chapters:
        for s in ch.get("screens") or []:
            pid = s.get("patternId")
            if pid:
                ids.append(pid)
    return ids


def pattern_diversity(chapters: list[dict]) -> float:
    pids = _screen_pattern_ids(chapters)
    if not pids:
        return 0.0
    return len(set(pids)) / len(pids)


def chapter_distinct_pattern_counts(chapters: list[dict]) -> list[int]:
    counts: list[int] = []
    for ch in chapters:
        pids = {
            str(s.get("patternId"))
            for s in ch.get("screens") or []
            if s.get("patternId")
        }
        if pids:
            counts.append(len(pids))
    return counts


def pattern_diversity_p50(chapters: list[dict]) -> float:
    counts = chapter_distinct_pattern_counts(chapters)
    if not counts:
        return 0.0
    counts.sort()
    mid = len(counts) // 2
    if len(counts) % 2:
        return float(counts[mid])
    return (counts[mid - 1] + counts[mid]) / 2.0
