"""Mosaic observability metrics (PRD §7.1)."""

from __future__ import annotations

from typing import Any

from travelogue.curation.chapter_items import summarize_screen_patterns
from travelogue.curation.longshot_filter import BREATH_PATTERN
from travelogue.curation.mosaic.constants import (
    MOSAIC_UNIFIED_PATTERN_IDS,
    PATTERN_MOSAIC_5_2P3L_EQUAL,
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    PATTERN_PORTRAIT_1_LANDSCAPE_2,
    PATTERN_PORTRAIT_2_LANDSCAPE_2,
)
from travelogue.curation.mosaic.main_eligibility import screen_main_slot_eligible
from travelogue.curation.mosaic.render_check import compute_layout_render_error_rate


def _image_screen_pattern_counts(chapters: list[dict]) -> dict[str, int]:
    """Pattern counts excluding image-less transition screens (breath-pause),
    so exposure rates are measured against content screens only."""
    counts = summarize_screen_patterns(chapters)
    counts.pop(BREATH_PATTERN, None)
    return counts


def mosaic5_exposure_rate(chapters: list[dict]) -> float:
    counts = _image_screen_pattern_counts(chapters)
    total = sum(counts.values())
    if not total:
        return 0.0
    m5 = sum(v for pid, v in counts.items() if "mosaic-5" in pid)
    return round(m5 / total, 6)


def mcs_unified_exposure_rate(chapters: list[dict]) -> float:
    """Share of screens using any MCS-managed pattern (3/4/5/6 family)."""
    counts = _image_screen_pattern_counts(chapters)
    total = sum(counts.values())
    if not total:
        return 0.0
    unified = sum(v for pid, v in counts.items() if pid in MOSAIC_UNIFIED_PATTERN_IDS)
    return round(unified / total, 6)


_MIXED_LAYOUT_PATTERNS: frozenset[str] = frozenset(
    {
        PATTERN_PORTRAIT_1_LANDSCAPE_2,
        PATTERN_PORTRAIT_2_LANDSCAPE_2,
        PATTERN_MOSAIC_5_2P3L_EQUAL,
        "screen-mosaic-5-main-portrait-3land",
        "screen-mosaic-5-main-landscape-2portrait-2land",
        "screen-mosaic-5-2portrait-3land-balanced",
    }
)


def mixed_layout_exposure_rate(chapters: list[dict]) -> float:
    """Share of content screens using portrait+landscape composite layouts."""
    counts = _image_screen_pattern_counts(chapters)
    total = sum(counts.values())
    if not total:
        return 0.0
    mixed = sum(v for pid, v in counts.items() if pid in _MIXED_LAYOUT_PATTERNS)
    return round(mixed / total, 6)


def mosaic_win_score_percentiles(mosaic_logs: list[dict]) -> dict[str, float | None]:
    """PRD §7.1 · layout.mosaic5.win_score_p50/p90 from window decision logs."""
    scores = [
        float(lg["winnerScore"])
        for lg in mosaic_logs
        if lg.get("winnerScore") is not None and not lg.get("fallbackUsed")
    ]
    if not scores:
        return {"layout.mosaic5.win_score_p50": None, "layout.mosaic5.win_score_p90": None}
    scores.sort()
    n = len(scores)

    def _pct(p: float) -> float:
        idx = min(n - 1, max(0, int(round((n - 1) * p))))
        return round(scores[idx], 4)

    return {
        "layout.mosaic5.win_score_p50": _pct(0.5),
        "layout.mosaic5.win_score_p90": _pct(0.9),
    }


def _rejection_entries_from_log(log: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect template rejection rows from raw or window-formatted mosaic logs."""
    entries: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def _add(entry: dict[str, Any]) -> None:
        tid = str(entry.get("templateId") or entry.get("template_id") or "")
        reason = str(entry.get("reason") or "")
        detail = str(entry.get("detail") or "")
        key = (tid, reason, detail)
        if key in seen:
            return
        seen.add(key)
        row = {"templateId": tid, "reason": reason}
        if detail:
            row["detail"] = detail
        entries.append(row)

    for key in (
        "rejectedTemplates",
        "rejected",
        "geometryRejectedTemplates",
        "mainArRejectedTemplates",
        "rhythmRejectedTemplates",
        "constraintRejectedTemplates",
    ):
        raw_list = log.get(key)
        if isinstance(raw_list, list):
            for item in raw_list:
                if isinstance(item, dict):
                    _add(item)
    return entries


def hero_main_conventional_rate(
    chapters: list[dict],
    assets_by_id: dict[str, dict],
) -> float | None:
    """Share of main-slot mosaic screens whose main passes R-MAIN-AR-01."""
    hero_patterns = {
        PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
        PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
        PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
    }
    total = 0
    ok_n = 0
    for ch in chapters:
        for screen in ch.get("screens") or []:
            pid = screen.get("patternId")
            if pid not in hero_patterns:
                continue
            total += 1
            eligible, _ = screen_main_slot_eligible(
                screen,
                assets_by_id,
                pattern_id=str(pid),
            )
            if eligible:
                ok_n += 1
    if total == 0:
        return None
    return round(ok_n / total, 6)


def main_ar_reject_rate(mosaic_logs: list[dict]) -> float | None:
    """Share of mosaic windows with at least one main_ar_ineligible rejection."""
    if not mosaic_logs:
        return None
    hits = 0
    for lg in mosaic_logs:
        if any(
            entry.get("reason") == "main_ar_ineligible"
            for entry in _rejection_entries_from_log(lg)
        ):
            hits += 1
    return round(hits / len(mosaic_logs), 6)


_HERO_MAIN_PATTERNS = frozenset(
    {
        PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
        PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
        PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
    }
)


def hero6_fallback_pattern_counts(mosaic_logs: list[dict]) -> dict[str, int] | None:
    """Winner pattern counts when a hero+tile template was rejected for main AR."""
    if not mosaic_logs:
        return None
    counts: dict[str, int] = {}
    for lg in mosaic_logs:
        rejections = _rejection_entries_from_log(lg)
        hero_rejected = any(
            entry.get("reason") == "main_ar_ineligible"
            and entry.get("templateId") in _HERO_MAIN_PATTERNS
            for entry in rejections
        )
        if not hero_rejected:
            continue
        winner = str(lg.get("winnerPatternId") or "")
        if not winner or winner in _HERO_MAIN_PATTERNS:
            continue
        counts[winner] = counts.get(winner, 0) + 1
    return counts or None


def hero6_fallback_rate(mosaic_logs: list[dict]) -> float | None:
    """Windows where hero+tile lost to another pattern after main AR rejection."""
    if not mosaic_logs:
        return None
    rejected_windows = 0
    fallback_windows = 0
    for lg in mosaic_logs:
        rejections = _rejection_entries_from_log(lg)
        hero_rejected = any(
            entry.get("reason") == "main_ar_ineligible"
            and entry.get("templateId") in _HERO_MAIN_PATTERNS
            for entry in rejections
        )
        if not hero_rejected:
            continue
        rejected_windows += 1
        winner = str(lg.get("winnerPatternId") or "")
        if winner and winner not in _HERO_MAIN_PATTERNS:
            fallback_windows += 1
    if rejected_windows == 0:
        return None
    return round(fallback_windows / rejected_windows, 6)


def compute_mosaic_metrics(
    chapters: list[dict],
    *,
    mosaic_logs: list[dict] | None = None,
    assets_by_id: dict[str, dict] | None = None,
) -> dict[str, Any]:
    rate5 = mosaic5_exposure_rate(chapters)
    rate_u = mcs_unified_exposure_rate(chapters)
    out: dict[str, Any] = {
        "mosaic5ExposureRate": rate5,
        "layout.mosaic5.exposure_rate": rate5,
        "mcsUnifiedExposureRate": rate_u,
        "layout.mosaic_v2.unified_exposure_rate": rate_u,
    }
    if rate_u > 0:
        out.update(compute_layout_render_error_rate(chapters, scope="mcs_unified"))
    logs = mosaic_logs or []
    if assets_by_id:
        conv = hero_main_conventional_rate(chapters, assets_by_id)
        if conv is not None:
            out["hero6WithConventionalMainRate"] = conv
            out["layout.mosaic.hero_main_conventional_rate"] = conv
    if logs:
        out.update(mosaic_win_score_percentiles(logs))
        fallbacks = sum(1 for lg in logs if lg.get("fallbackUsed"))
        low_score = sum(1 for lg in logs if lg.get("fallbackReason") == "low_score")
        n = len(logs) or 1
        out["mosaicWindowDecisions"] = len(logs)
        out["mosaicFallbackRate"] = round(fallbacks / n, 4)
        out["layout.mosaic_v2.fallback_rate"] = out["mosaicFallbackRate"]
        out["layout.mosaic_v2.low_score_fallback_rate"] = round(low_score / n, 4)
        winners = [lg.get("winnerPatternId") for lg in logs if lg.get("winnerPatternId")]
        if winners:
            out["mosaic5WinnerPatterns"] = winners
        reject_rate = main_ar_reject_rate(logs)
        if reject_rate is not None:
            out["mainArRejectRate"] = reject_rate
            out["layout.mosaic.main_ar_reject_rate"] = reject_rate
        fallback_rate = hero6_fallback_rate(logs)
        if fallback_rate is not None:
            out["hero6FallbackRate"] = fallback_rate
            out["layout.mosaic.hero6_fallback_rate"] = fallback_rate
        fallback_counts = hero6_fallback_pattern_counts(logs)
        if fallback_counts:
            out["hero6FallbackPatternCounts"] = fallback_counts
    return out
