"""Layout metrics for offline evaluation (V2 PRD §8)."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

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


def chapter_distinct_pattern_counts(chapters: list[dict]) -> list[int]:
    """Distinct patternId count per chapter (screens with a pattern only)."""
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
    """PRD P16 · median distinct patternId count per chapter."""
    counts = chapter_distinct_pattern_counts(chapters)
    if not counts:
        return 0.0
    counts.sort()
    mid = len(counts) // 2
    if len(counts) % 2:
        return float(counts[mid])
    return (counts[mid - 1] + counts[mid]) / 2.0


def pattern_repeat_rate(chapters: list[dict]) -> float:
    """PRD §7.1 · share of screens in repeated-pattern runs (1 − diversity)."""
    return round(1.0 - pattern_diversity(chapters), 6)


def max_pattern_repeat_streak(chapters: list[dict]) -> int:
    """Longest run of identical patternId across reading order (P6-D3 metric)."""
    streak = 0
    best = 0
    prev: str | None = None
    for ch in chapters:
        for screen in ch.get("screens") or []:
            pid = screen.get("patternId")
            if not pid:
                streak = 0
                prev = None
                continue
            if pid == prev:
                streak += 1
            else:
                streak = 1
                prev = pid
            best = max(best, streak)
    return best


def longshot_visual_variety(chapters: list[dict], assets_by_id: Mapping[str, dict]) -> float:
    """0–100 variety score from pattern/tone/kind diversity (P6-D2 metric)."""
    from travelogue.curation.longshot_filter import _screen_diversity_key

    keys: list[tuple] = []
    for ch in chapters:
        for screen in ch.get("screens") or []:
            if not any(s.get("assetId") for s in (screen.get("slots") or [])):
                continue
            keys.append(_screen_diversity_key(screen, assets_by_id))
    if not keys:
        return 0.0
    unique = len(set(keys))
    return round(unique / len(keys) * 100.0, 2)


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
            # Skip image-less transition screens (e.g. breath-pause); they have no
            # slots to match and would otherwise drag the rate toward 0.
            if not (screen.get("slots") or []):
                continue
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
        from travelogue.curation.layout_planner import aspect_kind_for_asset

        aspects = {a["id"]: aspect_kind_for_asset(a) for a in assets if a.get("id")}
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


def _all_screens(chapters: list[dict]) -> list[dict]:
    screens: list[dict] = []
    for ch in chapters:
        screens.extend(ch.get("screens") or [])
    return screens


def compute_layout_metrics(
    chapters: list[dict],
    assets: list[dict] | None = None,
    *,
    subject_run_tolerance: int = 1,
    mosaic_logs: list[dict] | None = None,
) -> dict[str, Any]:
    pids = _screen_pattern_ids(chapters)
    assets_by_id = {a["id"]: a for a in (assets or []) if a.get("id")}
    repeat_rate = pattern_repeat_rate(chapters)
    out: dict[str, Any] = {
        "screenCount": len(pids),
        "chapterCount": len(chapters),
        "patternDiversity": round(pattern_diversity(chapters), 4),
        "patternRepeatRate": repeat_rate,
        "layout.pattern.repeat_rate": repeat_rate,
        "layoutRepeatStreak": max_pattern_repeat_streak(chapters),
        "patternIds": pids,
        "screensPerChapter": screens_per_chapter(chapters),
    }
    if assets_by_id:
        from travelogue.curation.layout_scoring import score_gravity_balance

        out["gravityBalance"] = round(
            score_gravity_balance(_all_screens(chapters), assets_by_id), 4
        )
        out["longshotVisualVariety"] = longshot_visual_variety(chapters, assets_by_id)
    if assets:
        out.update(
            compute_layout_quality_metrics(
                chapters,
                assets,
                subject_run_tolerance=subject_run_tolerance,
            )
        )
    from travelogue.curation.mosaic.constants import MOSAIC_UNIFIED_PATTERN_IDS
    from travelogue.curation.mosaic.metrics import compute_mosaic_metrics

    if mosaic_logs is not None or any("mosaic-5" in pid for pid in pids):
        out.update(compute_mosaic_metrics(chapters, mosaic_logs=mosaic_logs))
    elif any(p in MOSAIC_UNIFIED_PATTERN_IDS for p in pids):
        out.update(compute_mosaic_metrics(chapters, mosaic_logs=None))
    if assets:
        from travelogue.config import get_config
        from travelogue.curation.usage_rules.metrics import compute_usage_rules_metrics

        ur_cfg = get_config().layout.usage_rules
        out.update(
            compute_usage_rules_metrics(
                chapters,
                assets,
                mosaic_logs=mosaic_logs,
                usage_rules_enabled=ur_cfg.enabled,
                hero_gap_threshold=ur_cfg.hero_gap_threshold,
            )
        )
    return out


def template_exposure_shares_from_trips(trips_root: Path | None = None) -> dict[str, float]:
    """Share of screens per patternId across dogfood trips (AC-P16-14)."""
    from travelogue.config import get_config

    root = trips_root or get_config().trips_dir
    counts: dict[str, int] = {}
    if not root.is_dir():
        return {}
    for trip_json in root.glob("*/trip.json"):
        try:
            import json

            data = json.loads(trip_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for ch in data.get("chapters") or []:
            for screen in ch.get("screens") or []:
                pid = str(screen.get("patternId") or "").strip()
                if pid:
                    counts[pid] = counts.get(pid, 0) + 1
    total = sum(counts.values())
    if not total:
        return {}
    return {pid: round(n / total, 4) for pid, n in sorted(counts.items())}
