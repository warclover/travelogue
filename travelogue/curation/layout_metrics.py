"""Layout metrics for offline evaluation (V2 PRD §8)."""

from __future__ import annotations

from typing import Any


def _screen_pattern_ids(chapters: list[dict]) -> list[str]:
    ids: list[str] = []
    for ch in chapters:
        for s in ch.get("screens") or []:
            pid = s.get("patternId")
            if pid:
                ids.append(pid)
    return ids


def pattern_diversity(chapters: list[dict]) -> float:
    """Unique patterns / total screens; 1.0 = all different."""
    pids = _screen_pattern_ids(chapters)
    if not pids:
        return 0.0
    return len(set(pids)) / len(pids)


def screens_per_chapter(chapters: list[dict]) -> dict[str, int]:
    return {ch.get("id", ""): len(ch.get("screens") or []) for ch in chapters}


def compute_layout_metrics(chapters: list[dict]) -> dict[str, Any]:
    pids = _screen_pattern_ids(chapters)
    return {
        "screenCount": len(pids),
        "chapterCount": len(chapters),
        "patternDiversity": round(pattern_diversity(chapters), 4),
        "patternIds": pids,
        "screensPerChapter": screens_per_chapter(chapters),
    }
