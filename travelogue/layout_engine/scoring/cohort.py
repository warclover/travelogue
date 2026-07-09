"""Cohort coherence scoring (layout kernel)."""

from __future__ import annotations

from collections.abc import Mapping


def asset_cohort_duo(asset: dict | None) -> bool:
    if not asset:
        return False
    cohort = (asset.get("curation") or {}).get("cohort") or {}
    return bool(cohort.get("duo"))


def score_cohort_coherence(
    asset_ids: list[str],
    assets_by_id: Mapping[str, dict],
) -> float:
    """Reward adjacent duo-tagged shots (soft narrative run)."""
    if len(asset_ids) < 2:
        return 1.0
    flags = [asset_cohort_duo(assets_by_id.get(aid)) for aid in asset_ids]
    scores: list[float] = []
    for i in range(len(flags) - 1):
        if flags[i] and flags[i + 1]:
            scores.append(1.0)
        elif flags[i] or flags[i + 1]:
            scores.append(0.55)
        else:
            scores.append(0.35)
    return sum(scores) / len(scores) if scores else 0.5
