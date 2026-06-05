"""Mosaic observability metrics (PRD §7.1)."""

from __future__ import annotations

from typing import Any

from travelogue.curation.chapter_items import summarize_screen_patterns
from travelogue.curation.longshot_filter import BREATH_PATTERN
from travelogue.curation.mosaic.constants import MOSAIC_UNIFIED_PATTERN_IDS
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


def compute_mosaic_metrics(
    chapters: list[dict],
    *,
    mosaic_logs: list[dict] | None = None,
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
    if not logs:
        return out
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
    return out
