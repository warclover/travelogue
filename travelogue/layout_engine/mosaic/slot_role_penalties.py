"""LTN C8 · D-03 slot-role soft penalties (window-relative)."""

from __future__ import annotations

from travelogue.layout_contract.burst import ingest_burst_group_id, parse_taken_ts
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_engine.scoring.hero import effective_hero_score

MAIN_CLONE_DT_S = 3.0
MAIN_AREA_RATIO_TARGET = 3.0


def _main_asset_id(screen: dict) -> str | None:
    for sl in screen.get("slots") or []:
        if sl.get("role") == "main" and sl.get("assetId"):
            return str(sl["assetId"])
    return None


def main_not_window_best_penalty(
    screen: dict,
    *,
    assets_by_id: dict[str, dict],
    median_sharp: float = 0.0,
) -> float:
    """1.0 when main is strictly worse than another window asset on hero score."""
    pattern_id = str(screen.get("patternId") or "")
    if not ScreenLayoutPlannerState.pattern_has_main_role(pattern_id):
        return 0.0
    main_id = _main_asset_id(screen)
    if not main_id:
        return 0.0
    ids = [str(sl["assetId"]) for sl in screen.get("slots") or [] if sl.get("assetId")]
    if len(ids) < 2:
        return 0.0
    scores = {
        aid: float(
            effective_hero_score(
                assets_by_id.get(aid, {}),
                median_sharp=median_sharp,
                pool=list(assets_by_id.values()),
            )
        )
        for aid in ids
    }
    main_score = scores.get(main_id, 0.0)
    best = max(scores.values()) if scores else 0.0
    if best > main_score + 1e-9:
        return 1.0
    return 0.0


def main_clone_in_sidebar_penalty(
    screen: dict,
    *,
    assets_by_id: dict[str, dict],
) -> float:
    """1.0 when main shares burst with a side slot and |Δt|≤3s (D-03)."""
    pattern_id = str(screen.get("patternId") or "")
    if not ScreenLayoutPlannerState.pattern_has_main_role(pattern_id):
        return 0.0
    main_id = _main_asset_id(screen)
    if not main_id:
        return 0.0
    main_a = assets_by_id.get(main_id, {}) or {}
    main_bg = ingest_burst_group_id(main_a)
    main_ts = parse_taken_ts(main_a)
    if not main_bg:
        return 0.0
    for sl in screen.get("slots") or []:
        aid = sl.get("assetId")
        if not aid or str(aid) == main_id or sl.get("role") == "main":
            continue
        side = assets_by_id.get(str(aid), {}) or {}
        if ingest_burst_group_id(side) != main_bg:
            continue
        side_ts = parse_taken_ts(side)
        if main_ts is None or side_ts is None:
            return 1.0
        if abs(side_ts - main_ts) <= MAIN_CLONE_DT_S:
            return 1.0
    return 0.0


def main_area_ratio_penalty(
    pattern_id: str, *, min_ratio: float = MAIN_AREA_RATIO_TARGET
) -> float:
    """Soft penalty when heroProminenceRatio is known and below target (D-03).

    Not a hard gate: core SKUs like main-portrait-3land sit near 2:1 by design.
    """
    if not ScreenLayoutPlannerState.pattern_has_main_role(pattern_id):
        return 0.0
    try:
        from travelogue.layout_engine.contract.geometry_features import (
            compute_raw_geometry_features,
        )

        feat = compute_raw_geometry_features(pattern_id)
    except Exception:
        return 0.0
    ratio = feat.get("heroProminenceRatio")
    if ratio is None:
        return 0.0
    r = float(ratio)
    if r >= float(min_ratio):
        return 0.0
    # Scale: at 2.0 → ~0.5; near 0 → 1.0
    return max(0.0, min(1.0, 1.0 - (r / float(min_ratio))))


def main_ar_mismatch_gate_ok(
    screen: dict,
    assets_by_id: dict[str, dict],
    *,
    max_mismatch: float = 1.4,
) -> bool | None:
    """True/False when main target AR known; None = skip."""
    pattern_id = str(screen.get("patternId") or "")
    if not ScreenLayoutPlannerState.pattern_has_main_role(pattern_id):
        return None
    main_id = _main_asset_id(screen)
    if not main_id:
        return None
    from travelogue.layout_contract.asset_geometry import asset_native_ar
    from travelogue.layout_engine.mosaic.main_eligibility import template_main_slot_policy

    policy = template_main_slot_policy(pattern_id)
    if not policy:
        return None
    target = policy.get("targetDisplayAspect") or policy.get("target_display_aspect")
    if target is None:
        return None
    try:
        target_f = float(target)
        native = float(asset_native_ar(assets_by_id.get(main_id, {}) or {}) or 0.0)
    except (TypeError, ValueError):
        return None
    if target_f <= 1e-9 or native <= 1e-9:
        return None
    mismatch = max(native / target_f, target_f / native)
    return mismatch <= float(max_mismatch)


def sidebar_min_short_side_ok(
    pattern_id: str,
    *,
    canvas_width_px: float = 428.0,
    min_short_px: float = 72.0,
) -> bool | None:
    """Conservative short-side check at longshot canvas width; None = skip."""
    if not ScreenLayoutPlannerState.pattern_has_main_role(pattern_id):
        return None
    try:
        from travelogue.layout_templates.geometry import _track_weights
        from travelogue.layout_templates.registry import get_engine

        template = get_engine().get(pattern_id)
        stage = getattr(template, "stage", None)
        if stage is None:
            return None
        cols, rows = _track_weights(stage)
        col_sum = sum(cols)
        row_sum = sum(rows)
        if col_sum <= 0 or row_sum <= 0:
            return None
        # Approximate canvas height from stage aspect if present.
        stage_ar = float(getattr(stage, "aspect", 0) or 0) or (9 / 16)
        canvas_h = canvas_width_px / stage_ar if stage_ar > 1e-9 else canvas_width_px * 16 / 9
        for slot in template.slots or []:
            role = str(getattr(slot, "role", "") or "").lower()
            if role == "main":
                continue
            rect = getattr(slot, "rect", None)
            if not rect or len(rect) != 4:
                continue
            c0, c1, r0, r1 = (int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))
            w_frac = sum(cols[c0 - 1 : c1]) / col_sum
            h_frac = sum(rows[r0 - 1 : r1]) / row_sum
            short = min(canvas_width_px * w_frac, canvas_h * h_frac)
            if short + 1e-6 < min_short_px:
                return False
        return True
    except Exception:
        return None
