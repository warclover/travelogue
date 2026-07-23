"""SSG · fake-slice window metrics (AC-SSG-05)."""

from __future__ import annotations

from collections.abc import Sequence

from travelogue.layout_engine.mosaic.shot_group_gate import (
    hard_reject_same_shot_group_anti_slice,
)


def count_fake_slice_windows(
    windows: Sequence[tuple[str, list[str]]],
    assets_by_id: dict[str, dict],
    *,
    ssg_on: bool,
) -> int:
    """Count slice-pattern windows that are same-group tight「假切条」risks.

    Baseline (``ssg_on=False``): any window with ≥3 assets and a tight time span
    on a slice pattern counts (legacy risk surface).

    SSG on: only windows that still pass (i.e. are NOT hard-rejected by
    ``sameGroupAntiSlice``) count as residual fake-slice risk — typically 0
    when groups are assigned.
    """
    from travelogue.layout_contract.burst import parse_taken_ts
    from travelogue.layout_engine.mosaic.shot_group_gate import is_slice_pattern

    n = 0
    for pattern_id, asset_ids in windows:
        if not is_slice_pattern(pattern_id) or len(asset_ids) < 3:
            continue
        stamps = [parse_taken_ts(assets_by_id.get(aid) or {}) for aid in asset_ids]
        valid = [t for t in stamps if t is not None]
        if len(valid) < 2 or (max(valid) - min(valid)) > 90:
            continue
        if not ssg_on:
            n += 1
            continue
        # Residual = would still be admitted (not anti-slice rejected)
        if not hard_reject_same_shot_group_anti_slice(
            pattern_id, asset_ids, assets_by_id
        ):
            n += 1
    return n


def fake_slice_reduction_rate(
    windows: Sequence[tuple[str, list[str]]],
    assets_by_id: dict[str, dict],
) -> float:
    """Relative reduction of fake-slice windows (baseline → SSG)."""
    base = count_fake_slice_windows(windows, assets_by_id, ssg_on=False)
    if base <= 0:
        return 1.0
    residual = count_fake_slice_windows(windows, assets_by_id, ssg_on=True)
    return max(0.0, (base - residual) / float(base))
