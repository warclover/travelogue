"""Decision log explain projection from mosaic scorer penalties (PRD §4.3)."""

from __future__ import annotations

from typing import Any


def build_explain(
    penalties: dict[str, float] | None,
    *,
    weights: dict[str, float] | None = None,
    penalty_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Map multiplicative penalty terms → topFactors / contributions."""
    if not penalties:
        return {"topFactors": [], "penalties": [], "contributions": []}

    pw = penalty_weights or {}
    contributions: list[dict[str, Any]] = []
    for key, pen in sorted(penalties.items()):
        if pen <= 0:
            continue
        w = float(pw.get(key, weights.get(key, 0.15) if weights else 0.15))
        contributions.append(
            {
                "factor": key,
                "penalty": round(float(pen), 4),
                "weight": round(w, 4),
                "contribution": round(-w * float(pen), 4),
            }
        )
    contributions.sort(key=lambda x: x["contribution"])

    penalty_rows = [
        {"factor": k, "value": round(float(v), 4)}
        for k, v in sorted(penalties.items())
        if v > 0
    ]
    return {
        "topFactors": contributions[:3],
        "penalties": penalty_rows,
        "contributions": contributions,
    }
