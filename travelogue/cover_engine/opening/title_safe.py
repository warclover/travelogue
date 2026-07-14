"""Opening title-safe marking (B1: mark only; hard gate deferred to B2a)."""

from __future__ import annotations

from typing import Any

from travelogue.cover_engine.fit import focal_is_trusted
from travelogue.cover_engine.registry import get_profile

_DEFAULT_FOCAL_X = 0.5
_DEFAULT_FOCAL_Y = 0.45


def _focal(asset: dict[str, Any]) -> tuple[float, float]:
    fp = asset.get("focalPoint") or {}
    try:
        fx = float(fp.get("x", _DEFAULT_FOCAL_X))
    except (TypeError, ValueError):
        fx = _DEFAULT_FOCAL_X
    try:
        fy = float(fp.get("y", _DEFAULT_FOCAL_Y))
    except (TypeError, ValueError):
        fy = _DEFAULT_FOCAL_Y
    return fx, fy


def _point_in_region(fx: float, fy: float, region: dict[str, float]) -> bool:
    try:
        x = float(region.get("x", 0.0))
        y = float(region.get("y", 0.0))
        w = float(region.get("w", 0.0))
        h = float(region.get("h", 0.0))
    except (TypeError, ValueError):
        return False
    return x <= fx <= x + w and y <= fy <= y + h


def mark_title_safe(
    asset: dict[str, Any],
    style_id: str,
    *,
    hard_gate: bool = False,
) -> dict[str, Any]:
    """Annotate whether focal collides with style text-safe regions.

    B1: always returns a mark payload; never mutates ranking.
    ``hard_gate`` is accepted for API stability but ignored until B2a.
    """
    del hard_gate  # B1: mark-only; do not reorder Top1
    profile = get_profile(style_id)
    regions = list(profile.text_safe_regions or [])
    reasons: list[str] = []
    title_unsafe = False

    if regions and focal_is_trusted(asset):
        fx, fy = _focal(asset)
        for i, region in enumerate(regions):
            if isinstance(region, dict) and _point_in_region(fx, fy, region):
                title_unsafe = True
                reasons.append(f"focal_in_text_safe_region:{i}")
                break

    # High edge subject under avoid.edge_subject is also a soft mark signal.
    avoid = profile.avoid or {}
    if avoid.get("edge_subject"):
        fx, fy = _focal(asset)
        if fx < 0.18 or fx > 0.82 or fy < 0.12 or fy > 0.88:
            title_unsafe = True
            if "edge_subject" not in reasons:
                reasons.append("edge_subject")

    return {
        "titleUnsafe": title_unsafe,
        "reasons": reasons,
        "hardGateApplied": False,
    }


def annotate_title_safe_on_explain(
    explain: dict[str, Any],
    mark: dict[str, Any],
) -> dict[str, Any]:
    """Attach title-safe mark onto an explain dict without changing pick fields."""
    out = dict(explain)
    out["titleSafe"] = {
        "titleUnsafe": bool(mark.get("titleUnsafe")),
        "reasons": list(mark.get("reasons") or []),
        "hardGateApplied": False,
    }
    return out
