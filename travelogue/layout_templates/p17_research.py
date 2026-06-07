"""Phase 17 layout generation research (PRD §15.3 · W4 spike)."""

from __future__ import annotations

import itertools
from typing import Sequence


def _ar_distance(asset_ar: float, slot_ar: float) -> float:
    if slot_ar <= 0 or asset_ar <= 0:
        return 1.0
    return abs(asset_ar - slot_ar) / max(asset_ar, slot_ar, 1e-6)


def hungarian_slot_assignment(
    asset_ars: Sequence[float],
    slot_ars: Sequence[float],
) -> list[int]:
    """Minimum-cost assignment: return asset index per slot (offline eval spike).

    Uses scipy when available; falls back to brute force for n ≤ 8.
    """
    n = len(slot_ars)
    if len(asset_ars) != n:
        raise ValueError("asset_ars and slot_ars must have equal length")
    if n == 0:
        return []
    if n == 1:
        return [0]

    cost = [[_ar_distance(float(asset_ars[i]), float(slot_ars[j])) for j in range(n)] for i in range(n)]

    try:
        from scipy.optimize import linear_sum_assignment

        row_ind, col_ind = linear_sum_assignment(cost)
        assignment = [0] * n
        for r, c in zip(row_ind, col_ind, strict=True):
            assignment[int(c)] = int(r)
        return assignment
    except ImportError:
        pass

    if n > 8:
        raise NotImplementedError("Hungarian spike requires scipy for n>8")

    best_perm: tuple[int, ...] | None = None
    best_cost = float("inf")
    for perm in itertools.permutations(range(n)):
        total = sum(cost[perm[j]][j] for j in range(n))
        if total < best_cost:
            best_cost = total
            best_perm = perm
    assert best_perm is not None
    assignment = [0] * n
    for slot_idx, asset_idx in enumerate(best_perm):
        assignment[slot_idx] = asset_idx
    return assignment


def generative_composite_stage(*_args, **_kwargs):
    raise NotImplementedError("P17 pre-research: generative composite topology")
