"""Layout metrics for offline evaluation (V2 PRD §8)."""

from __future__ import annotations

from typing import Any, Mapping

from travelogue.curation.burst_utils import ingest_burst_group_id, parse_taken_ts
from travelogue.curation.layout_planner import AspectKind


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


def asset_order_from_chapters(chapters: list[dict]) -> list[str]:
    """Global reading order of asset ids across all screens."""
    order: list[str] = []
    seen: set[str] = set()
    for ch in chapters:
        for screen in ch.get("screens") or []:
            for slot in screen.get("slots") or []:
                aid = slot.get("assetId")
                if aid and aid not in seen:
                    order.append(aid)
                    seen.add(aid)
    return order


def time_inversion_rate(
    chapters: list[dict],
    assets_by_id: Mapping[str, dict],
) -> float:
    """Fraction of ordered pairs where layout order inverts takenAt (I-G1)."""
    order = asset_order_from_chapters(chapters)
    times: list[float] = []
    for aid in order:
        ts = parse_taken_ts(assets_by_id.get(aid) or {})
        if ts is not None:
            times.append(ts)
    if len(times) < 2:
        return 0.0
    inversions = 0
    pairs = 0
    for i in range(len(times)):
        for j in range(i + 1, len(times)):
            pairs += 1
            if times[i] > times[j]:
                inversions += 1
    return inversions / pairs if pairs else 0.0


def burst_integrity_violations(
    chapters: list[dict],
    assets_by_id: Mapping[str, dict],
) -> int:
    """Count ingest burst groups split across more than one screen (AC-P3-C09)."""
    group_screens: dict[str, set[int]] = {}
    screen_idx = 0
    for ch in chapters:
        for screen in ch.get("screens") or []:
            for slot in screen.get("slots") or []:
                aid = slot.get("assetId")
                if not aid:
                    continue
                gid = ingest_burst_group_id(assets_by_id.get(aid) or {})
                if gid:
                    group_screens.setdefault(gid, set()).add(screen_idx)
            screen_idx += 1
    return sum(1 for screens in group_screens.values() if len(screens) > 1)


def aspect_pattern_match_rate(
    chapters: list[dict],
    aspects: Mapping[str, AspectKind],
) -> float:
    from travelogue.curation.layout_scoring import score_aspect_match

    hits = 0.0
    total = 0
    for ch in chapters:
        for screen in ch.get("screens") or []:
            hits += score_aspect_match(screen, aspects)
            total += 1
    return hits / total if total else 0.0


def subject_run_score(
    chapters: list[dict],
    assets_by_id: Mapping[str, dict],
    *,
    subject_run_tolerance: int = 1,
) -> float:
    """Average soft subject-run score per chapter (I-G2)."""
    from travelogue.curation.layout_scoring import score_subject_run_soft

    scores: list[float] = []
    for ch in chapters:
        order = asset_order_from_chapters([ch])
        if len(order) >= 2:
            scores.append(
                score_subject_run_soft(
                    order,
                    assets_by_id,
                    tolerance=subject_run_tolerance,
                )
            )
    return sum(scores) / len(scores) if scores else 1.0


def compute_layout_quality_metrics(
    chapters: list[dict],
    assets: list[dict],
    *,
    aspects: Mapping[str, AspectKind] | None = None,
    subject_run_tolerance: int = 1,
) -> dict[str, Any]:
    assets_by_id = {a["id"]: a for a in assets if a.get("id")}
    if aspects is None:
        aspects = {
            a["id"]: a.get("aspectKind") or "landscape"  # type: ignore[misc]
            for a in assets
            if a.get("id")
        }
    return {
        "timeInversionRate": round(time_inversion_rate(chapters, assets_by_id), 6),
        "subjectRunScore": round(
            subject_run_score(
                chapters,
                assets_by_id,
                subject_run_tolerance=subject_run_tolerance,
            ),
            4,
        ),
        "aspectPatternMatchRate": round(aspect_pattern_match_rate(chapters, aspects), 4),
        "burstIntegrityViolations": burst_integrity_violations(chapters, assets_by_id),
    }


def compute_layout_metrics(
    chapters: list[dict],
    assets: list[dict] | None = None,
    *,
    subject_run_tolerance: int = 1,
) -> dict[str, Any]:
    pids = _screen_pattern_ids(chapters)
    out: dict[str, Any] = {
        "screenCount": len(pids),
        "chapterCount": len(chapters),
        "patternDiversity": round(pattern_diversity(chapters), 4),
        "patternIds": pids,
        "screensPerChapter": screens_per_chapter(chapters),
    }
    if assets:
        out.update(
            compute_layout_quality_metrics(
                chapters,
                assets,
                subject_run_tolerance=subject_run_tolerance,
            )
        )
    return out
