"""LSE-CAP-01 Hungarian slot assignment · deterministic fail-open (§4.5.1)."""

from __future__ import annotations

import itertools
from typing import Any

from travelogue.curation.layout_constraints import FOCAL_EDGE_MARGIN
from travelogue.layout_engine.features import (
    _asset_aspect,
    _slot_display_aspect,
    salient_retention_for_slot,
)
from travelogue.layout_engine.quality_features import QualityPool


def _ar_distance(asset_ar: float, slot_ar: float) -> float:
    if slot_ar <= 0 or asset_ar <= 0:
        return 1.0
    return abs(asset_ar - slot_ar) / max(asset_ar, slot_ar, 1e-6)


def _focal_near_edge(asset: dict, margin: float = FOCAL_EDGE_MARGIN) -> bool:
    fp = asset.get("focalPoint") or {}
    x, y = fp.get("x"), fp.get("y")
    if x is None or y is None:
        return False
    try:
        xf, yf = float(x), float(y)
    except (TypeError, ValueError):
        return False
    return bool(xf < margin or xf > 1.0 - margin or yf < margin or yf > 1.0 - margin)


def _has_person(asset: dict) -> bool:
    tags = asset.get("tags") or []
    return any(str(t).lower() in ("person", "people", "face") for t in tags)


def pair_assignment_cost(
    asset: dict,
    slot_ar: float,
    *,
    slot_index: int,
    quality: QualityPool | None = None,
) -> float:
    """Decomposable per-pair cost for Hungarian (lower is better)."""
    ar_cost = _ar_distance(_asset_aspect(asset), slot_ar)
    slot_stub = {"displayAspect": slot_ar, "fit": "cover"}
    salient_loss = 1.0 - salient_retention_for_slot(slot_stub, asset)
    face_pen = 0.12 if _has_person(asset) and _focal_near_edge(asset) else 0.0
    quality_adj = 0.0
    if quality is not None:
        aid = str(asset.get("id") or "")
        q = quality.for_asset(aid)
        quality_adj = -0.04 * (q.sharp_pct + q.aesthetic_pct)
    aid = str(asset.get("id") or "")
    tie = (hash((aid, slot_index)) % 10_000) * 1e-10
    return ar_cost * 0.5 + salient_loss * 0.35 + face_pen + quality_adj + tie


def _solve_hungarian(cost: list[list[float]], n: int) -> list[int] | None:
    """Return asset index assigned to each slot (length n)."""
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
        return None

    best_perm: tuple[int, ...] | None = None
    best_cost = float("inf")
    for perm in itertools.permutations(range(n)):
        total = sum(cost[perm[j]][j] for j in range(n))
        if total < best_cost - 1e-12:
            best_cost = total
            best_perm = perm
        elif abs(total - best_cost) <= 1e-12 and best_perm is not None:
            if perm < best_perm:
                best_perm = perm
                best_cost = total
    if best_perm is None:
        return None
    assignment = [0] * n
    for slot_idx, asset_idx in enumerate(best_perm):
        assignment[slot_idx] = asset_idx
    return assignment


def refine_asset_order_hungarian(
    ordered_ids: list[str],
    screen: dict,
    assets_map: dict[str, dict],
    *,
    max_matrix_n: int = 16,
    quality: QualityPool | None = None,
) -> tuple[list[str] | None, str | None]:
    """Re-order assets to slots via Hungarian; fail-open returns (None, reason)."""
    slots = screen.get("slots") or []
    n = len(ordered_ids)
    if n == 0 or n != len(slots):
        return None, "slot_count_mismatch"
    if n > max_matrix_n:
        return None, "matrix_too_large"

    slot_ars = [_slot_display_aspect(sl) for sl in slots]
    assets = [assets_map.get(aid, {"id": aid}) for aid in ordered_ids]
    cost = [
        [
            pair_assignment_cost(
                assets[i],
                slot_ars[j],
                slot_index=j,
                quality=quality,
            )
            for j in range(n)
        ]
        for i in range(n)
    ]
    assignment = _solve_hungarian(cost, n)
    if assignment is None:
        return None, "solver_unavailable"
    return [ordered_ids[assignment[j]] for j in range(n)], None


def hungarian_metrics(
    greedy_ids: list[str],
    refined_ids: list[str],
    screen: dict,
    assets_map: dict[str, dict],
    *,
    quality: QualityPool | None = None,
) -> dict[str, Any]:
    """Probe metrics for AC-P17-19 style evaluation."""
    slots = screen.get("slots") or []
    if len(greedy_ids) != len(refined_ids) or not slots:
        return {"changed": False}

    def _avg_retention(ids: list[str]) -> float:
        vals: list[float] = []
        for aid, sl in zip(ids, slots):
            asset = assets_map.get(aid, {})
            vals.append(salient_retention_for_slot(sl, asset))
        return sum(vals) / len(vals) if vals else 0.0

    greedy_ret = _avg_retention(greedy_ids)
    refined_ret = _avg_retention(refined_ids)
    return {
        "changed": greedy_ids != refined_ids,
        "salientRetentionGreedy": round(greedy_ret, 4),
        "salientRetentionHungarian": round(refined_ret, 4),
        "salientRetentionDelta": round(refined_ret - greedy_ret, 4),
    }
