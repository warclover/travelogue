"""LTN E4 · asymmetric dense quota (hard max, soft opportunity min).

Rules:
- ``dense_collage_max`` remains the hard ceiling (P21 + track cap).
- ``dense_opportunity_min`` is aspirational / observable only.
- Never force-emit dense/mosaic when no legal window exists.
"""

from __future__ import annotations

import math
from typing import Any, Literal

MosaicTrackLike = Literal["curated", "archive", "quick_share"] | str | None


def dense_opportunity_min_for(
    *,
    dense_max: int,
    track: MosaicTrackLike = None,
) -> int:
    """Soft aspirational floor for dense/mosaic emits (never a force gate)."""
    hi = max(0, int(dense_max))
    if hi <= 0:
        return 0
    mode = str(track or "curated").strip().lower().replace("-", "_")
    if mode in ("quick_share", "quickshare", "quick"):
        return 0
    if mode == "archive":
        # Soft band lower edge ≈0.4 of max (PRD utilization health), at least 1.
        return min(hi, max(1, int(math.ceil(hi * 0.4))))
    # curated / default · expect ~1 legal hero when max allows
    return min(1, hi)


def dense_opportunity_fill_rate(
    *,
    used: int,
    opportunity_min: int,
) -> float | None:
    """used / soft-min; None when soft-min is 0 (nothing to aspire to)."""
    lo = max(0, int(opportunity_min))
    if lo <= 0:
        return None
    return round(min(1.0, max(0, int(used)) / lo), 6)


def asymmetric_dense_snapshot(
    *,
    dense_max: int,
    dense_used: int,
    opportunity_min: int,
    opportunity_seen: int = 0,
) -> dict[str, Any]:
    """One row for layoutMetrics / weekly board."""
    hi = max(0, int(dense_max))
    used = max(0, int(dense_used))
    opp_min = max(0, int(opportunity_min))
    util = round(min(1.0, used / hi), 6) if hi > 0 else None
    return {
        "denseCollageMax": hi,
        "denseCollageUsed": used,
        "denseOpportunityMin": opp_min,
        "denseOpportunitySeen": max(0, int(opportunity_seen)),
        "denseQuotaUtilization": util,
        "denseOpportunityFillRate": dense_opportunity_fill_rate(
            used=used, opportunity_min=opp_min
        ),
        # E4 invariant — planners must never set this true.
        "denseForcedEmit": False,
        "asymmetricQuota": True,
    }
