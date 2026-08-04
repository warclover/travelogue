"""Mosaic unified scorer (M5) — multiplicative penalties."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from travelogue.config import MosaicConfig
from travelogue.layout_contract.constraints import FOCAL_EDGE_MARGIN
from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_contract.scoring import ScoringWeights
from travelogue.layout_engine.mosaic.clone_detection import (
    NEAR_SCENE_CLONE_REJECT_THRESHOLD,
    near_scene_clone_penalty,
    template_prefers_burst,
)
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_LANDSCAPE_6,
    PATTERN_LANDSCAPE_9,
    PATTERN_MOSAIC_5_HERO_3_2_PLUS_4,
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    PATTERN_PORTRAIT_6,
)
from travelogue.layout_engine.mosaic.main_eligibility import screen_main_slot_eligible
from travelogue.layout_engine.mosaic.slot_geometry import screen_slots_geometry_ok
from travelogue.layout_engine.planner.beam_scoring import score_screen_plan
from travelogue.layout_engine.planner.screen_planner import _is_landscape_id, _is_std_portrait_id


@dataclass
class MosaicScoreResult:
    total: float
    base: float
    penalties: dict[str, float]
    reason_codes: list[str]


def weights_hash(cfg: MosaicConfig) -> str:
    payload = {
        "v": cfg.scorer_version,
        "w": cfg.weights,
        "p": cfg.penalties,
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()[:16]


def _mosaic_weights(cfg: MosaicConfig) -> ScoringWeights:
    return ScoringWeights.from_dict(cfg.weights).normalized()


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _focal_near_edge(asset: dict, margin: float = FOCAL_EDGE_MARGIN) -> bool:
    fp = asset.get("focalPoint") or {}
    x, y = fp.get("x"), fp.get("y")
    if x is None or y is None:
        return False
    return bool(x < margin or x > 1.0 - margin or y < margin or y > 1.0 - margin)


def _category_jump_soft_penalty(
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
) -> float:
    """W1 soft · semantic category jumps (never hard-reject here)."""
    if len(asset_ids) < 2:
        return 0.0
    from travelogue.layout_engine.planner.scene_atoms import window_category_jump_count

    jumps = window_category_jump_count(asset_ids, assets_by_id)
    if jumps <= 0:
        return 0.0
    return min(0.45, 0.12 * float(jumps))


def _face_crop_penalty(screen: dict, assets_by_id: dict[str, dict]) -> float:
    pen = 0.0
    for sl in screen.get("slots") or []:
        aid = sl.get("assetId")
        if not aid:
            continue
        asset = assets_by_id.get(aid) or {}
        tags = asset.get("tags") or []
        has_person = any(str(t).lower() in ("person", "people", "face") for t in tags)
        if not has_person:
            continue
        if sl.get("fit") == "cover" and _focal_near_edge(asset):
            pen = max(pen, 0.85)
    return pen


def _main_quality_penalty(
    screen: dict,
    assets_by_id: dict[str, dict],
    *,
    cfg: MosaicConfig | None = None,
    quality_pool: Any | None = None,
) -> float:
    for sl in screen.get("slots") or []:
        if sl.get("role") != "main":
            continue
        aid = sl.get("assetId")
        asset = assets_by_id.get(aid) or {}
        if cfg is not None and cfg.lse_quality_unified and quality_pool is not None and aid:
            sharp_pct = quality_pool.sharp_pct(str(aid))
            aesthetic_pct = quality_pool.aesthetic_pct(str(aid))
            combined = 0.55 * sharp_pct + 0.45 * aesthetic_pct
            if combined < 0.2:
                return 0.9
            if combined < 0.35:
                return 0.5
            return 0.0
        q = asset.get("quality") or {}
        try:
            from travelogue.layout_engine.scoring.aesthetic import aesthetic_overall

            overall = aesthetic_overall(asset)
        except Exception:
            overall = None
        if overall is not None:
            if overall < 0.35:
                return 0.9
            if overall < 0.45:
                return 0.5
            return 0.0
        sharp = float(q.get("sharpness") or 0.0)
        if sharp < 0.25:
            return 0.9
        if sharp < 0.4:
            return 0.5
    return 0.0


def _duplicate_density_penalty(
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
    *,
    pattern_id: str = "",
) -> float:
    # LTN H6/S1 · burst-preferring templates must not be born with a 0.8 penalty.
    if pattern_id and template_prefers_burst(pattern_id) is True:
        return 0.0
    groups: dict[str, int] = {}
    for aid in asset_ids:
        bg = (assets_by_id.get(aid) or {}).get("burstGroupId")
        if bg:
            groups[str(bg)] = groups.get(str(bg), 0) + 1
    if not groups:
        return 0.0
    max_run = max(groups.values())
    if max_run >= 4:
        return 0.8
    if max_run >= 3:
        return 0.4
    return 0.0


# Backward-compatible private aliases (moved to clone_detection · AC-TPC-15).
_template_prefers_burst = template_prefers_burst
_near_scene_clone_penalty = near_scene_clone_penalty


def _main_ar_penalty(
    screen: dict,
    assets_by_id: dict[str, dict],
    *,
    cfg: MosaicConfig,
) -> float:
    ok, _ = screen_main_slot_eligible(
        screen,
        assets_by_id,
        pattern_id=str(screen.get("patternId") or ""),
        cfg=cfg,
    )
    return 0.0 if ok else 0.95


def _slot_geometry_penalty(
    screen: dict,
    aspects: dict[str, AspectKind],
) -> float:
    if not screen_slots_geometry_ok(screen, aspects):
        return 0.95
    return 0.0


def _hero_slot_aspect_penalty(
    screen: dict,
    aspects: dict[str, AspectKind],
    *,
    cfg: MosaicConfig,
) -> float:
    """Side tiles prefer portrait; bottom row prefers landscape."""
    pattern_id = str(screen.get("patternId") or "")
    if pattern_id == PATTERN_MOSAIC_5_HERO_3_2_PLUS_4:
        if not cfg.hero_weighted_geometry_guard:
            return 0.0
        pen = 0.0
        for slot in screen.get("slots") or []:
            idx = int(slot.get("slot", -1))
            aid = slot.get("assetId")
            if not aid or idx != 0:
                continue
            if _is_landscape_id(aid, aspects):
                pen = max(pen, 0.9)
        return pen
    if pattern_id not in (
        PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
        PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    ):
        return 0.0
    pen = 0.0
    for slot in screen.get("slots") or []:
        idx = int(slot.get("slot", -1))
        aid = slot.get("assetId")
        if not aid:
            continue
        kind = aspects.get(aid)
        if kind is None:
            continue
        is_portrait = kind in ("portrait", "tall")
        is_landscape = _is_landscape_id(aid, aspects)
        if idx == 0 and is_portrait:
            pen = max(pen, 0.75)
        elif idx in (1, 2) and is_landscape:
            pen = max(pen, 0.45)
        elif idx >= 3 and is_portrait:
            pen = max(pen, 0.9)
    return pen


def _hero_narrow_tile_penalty(
    screen: dict,
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    *,
    cfg: MosaicConfig,
) -> float:
    """Penalize all-landscape hero+tile patterns where side tiles are narrow strips."""
    pattern_id = str(screen.get("patternId") or "")
    if pattern_id == PATTERN_MOSAIC_5_HERO_3_2_PLUS_4:
        if not cfg.hero_weighted_geometry_guard:
            return 0.0
        if not asset_ids:
            return 0.0
        if all(_is_landscape_id(aid, aspects) for aid in asset_ids):
            return 0.65
        return 0.0
    if pattern_id not in (
        PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
        PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    ):
        return 0.0
    if not asset_ids:
        return 0.0
    landscape_count = sum(
        1 for aid in asset_ids if _is_landscape_id(aid, aspects)
    )
    if landscape_count < len(asset_ids):
        return 0.0
    if pattern_id == PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4:
        return 0.55
    return 0.0


def _flat_six_grid_penalty(
    pattern_id: str,
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
) -> float:
    if pattern_id not in (PATTERN_LANDSCAPE_6, PATTERN_PORTRAIT_6):
        return 0.0
    if len(asset_ids) != 6:
        return 0.0
    all_land = all(_is_landscape_id(aid, aspects) for aid in asset_ids)
    all_port = all(_is_std_portrait_id(aid, aspects) for aid in asset_ids)
    if all_land or all_port:
        return 0.5
    return 0.0


def _flat_nine_grid_penalty(
    pattern_id: str,
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
) -> float:
    if pattern_id != PATTERN_LANDSCAPE_9:
        return 0.0
    if len(asset_ids) != 9:
        return 0.0
    all_land = all(_is_landscape_id(aid, aspects) for aid in asset_ids)
    all_port = all(_is_std_portrait_id(aid, aspects) for aid in asset_ids)
    if all_land or all_port:
        return 0.55
    return 0.0


def _dense_without_hero_penalty(screen: dict, pattern_id: str) -> float:
    """P21 · penalize 5/6-slot flat grids without a main hero slot."""
    from travelogue.layout_engine.mosaic.pattern_catalog import default_registry

    if not pattern_id.startswith("screen-mosaic-"):
        return 0.0
    pat = default_registry().get(pattern_id)
    if pat is None or "main" in pat.roles:
        return 0.0
    slots = screen.get("slots") or []
    n = len([s for s in slots if s.get("assetId")])
    if n in (5, 6):
        return 0.6
    return 0.0



def _wasted_hero_penalty(
    screen: dict,
    pattern_id: str,
    *,
    aspects: dict[str, AspectKind],
    assets_by_id: dict[str, dict],
    median_sharp: float | None = None,
) -> float:
    """LTN C3 · equal-weight patterns pay when the window had a clear hero gap."""
    from travelogue.config import get_config
    from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
    from travelogue.layout_contract.usage_context import build_window_context
    from travelogue.layout_engine.usage_rules.context import main_eligible_hero_score_gap

    if ScreenLayoutPlannerState.pattern_has_main_role(pattern_id):
        return 0.0
    asset_ids = [sl.get("assetId") for sl in screen.get("slots") or [] if sl.get("assetId")]
    if len(asset_ids) < 2:
        return 0.0
    # Probe against a main-role SKU for eligibility/gap.
    from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5

    wctx = build_window_context(
        list(asset_ids),
        aspects,
        assets_by_id,
        median_sharp=median_sharp,
    )
    gap, scores = main_eligible_hero_score_gap(wctx, PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5)
    if not scores:
        return 0.0
    thr = float(get_config().layout.usage_rules.hero_gap_threshold)
    if gap < thr:
        return 0.0
    return 0.35


def _ega_window_is_flat(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_by_id: dict[str, dict],
    *,
    cfg: MosaicConfig,
    median_sharp: float | None = None,
) -> bool:
    """D-EGA-07 · low hero separation (gap below threshold) ⇒ flat / no clear main."""
    from travelogue.config import get_config
    from travelogue.layout_contract.usage_context import build_window_context
    from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
    from travelogue.layout_engine.usage_rules.context import main_eligible_hero_score_gap

    aids = [a for a in asset_ids if a]
    if len(aids) < 2:
        return True
    wctx = build_window_context(
        list(aids),
        aspects,
        assets_by_id,
        median_sharp=median_sharp,
    )
    gap, scores = main_eligible_hero_score_gap(wctx, PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5)
    if not scores:
        return True
    so = getattr(cfg, "selection_optimization", None)
    thr = getattr(so, "hero_gap_threshold", None) if so is not None else None
    if thr is None:
        thr = float(get_config().layout.usage_rules.hero_gap_threshold)
    return float(gap) < float(thr)


def _apply_hero_gap_prior(
    total: float,
    reasons: list[str],
    *,
    pattern_id: str,
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_by_id: dict[str, dict],
    median_sharp: float | None = None,
) -> float:
    """LTN C3 · main-role patterns with a clear hero gap get ×1.10."""
    from travelogue.config import get_config
    from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
    from travelogue.layout_contract.usage_context import build_window_context
    from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
    from travelogue.layout_engine.usage_rules.context import main_eligible_hero_score_gap

    if not ScreenLayoutPlannerState.pattern_has_main_role(pattern_id):
        return total
    if len(asset_ids) < 2:
        return total
    wctx = build_window_context(
        list(asset_ids),
        aspects,
        assets_by_id,
        median_sharp=median_sharp,
    )
    gap, scores = main_eligible_hero_score_gap(wctx, PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5)
    if not scores:
        return total
    thr = float(get_config().layout.usage_rules.hero_gap_threshold)
    if gap < thr:
        return total
    reasons.append("R_HERO_GAP_PRIOR")
    return min(1.0, total * 1.10)

def score_candidate(
    screen: dict,
    *,
    aspects: dict[str, AspectKind],
    assets_by_id: dict[str, dict],
    cfg: MosaicConfig,
    layout_state: ScreenLayoutPlannerState | None = None,
    trip_photo_total: int = 0,
    burst_seconds: float = 12.0,
    prev_screen: dict | None = None,
    chapter_screen_index: int = 0,
    chapter_screen_count: int = 12,
    quality_pool: Any | None = None,
) -> MosaicScoreResult:
    # ALG-V3 W3-B1 · reuse window-hoisted pool when provided; only build if needed.
    if quality_pool is None and cfg.lse_quality_unified:
        from travelogue.layout_engine.quality_features import build_quality_pool

        quality_pool = build_quality_pool(list(assets_by_id.values()))
    weights = _mosaic_weights(cfg)
    plan = [screen]
    bd = score_screen_plan(
        plan,
        aspects=aspects,
        assets_by_id=assets_by_id,
        weights=weights,
        featured_beam=False,
    )
    base = _clamp01(bd.total)
    asset_ids = [sl.get("assetId") for sl in screen.get("slots") or [] if sl.get("assetId")]
    face_pen = _face_crop_penalty(screen, assets_by_id)
    salient_pen = 0.0
    if cfg.lse_saliency_scoring:
        from travelogue.layout_engine.features import salient_crop_penalty

        salient_pen = salient_crop_penalty(screen, assets_by_id)
    pattern_id_early = str(screen.get("patternId") or "")
    penalties: dict[str, float] = {
        "face_crop": max(face_pen, salient_pen),
        "salient_crop": salient_pen,
        "main_quality": _main_quality_penalty(
            screen,
            assets_by_id,
            cfg=cfg,
            quality_pool=quality_pool,
        ),
        "duplicate_density": max(
            _duplicate_density_penalty(
                asset_ids, assets_by_id, pattern_id=pattern_id_early
            ),
            _near_scene_clone_penalty(pattern_id_early, asset_ids, assets_by_id),
        ),
        "category_jump_soft": _category_jump_soft_penalty(asset_ids, assets_by_id),
        "hero_narrow_tiles": _hero_narrow_tile_penalty(screen, asset_ids, aspects, cfg=cfg),
        "hero_slot_aspect": _hero_slot_aspect_penalty(screen, aspects, cfg=cfg),
        "main_ar_ineligible": _main_ar_penalty(screen, assets_by_id, cfg=cfg),
        "slot_geometry": _slot_geometry_penalty(screen, aspects),
        "flat_six_grid": _flat_six_grid_penalty(
            str(screen.get("patternId") or ""), asset_ids, aspects
        ),
        "flat_nine_grid": _flat_nine_grid_penalty(
            str(screen.get("patternId") or ""), asset_ids, aspects
        ),
        "dense_without_hero": _dense_without_hero_penalty(
            screen, str(screen.get("patternId") or "")
        ),
        "wasted_hero": _wasted_hero_penalty(
            screen,
            str(screen.get("patternId") or ""),
            aspects=aspects,
            assets_by_id=assets_by_id,
            median_sharp=None,
        ),
    }
    # LTN C8 · D-03 slot-role soft penalties
    from travelogue.layout_engine.mosaic.slot_role_penalties import (
        main_area_ratio_penalty,
        main_clone_in_sidebar_penalty,
        main_not_window_best_penalty,
    )

    penalties["main_not_window_best"] = main_not_window_best_penalty(
        screen, assets_by_id=assets_by_id
    )
    penalties["main_clone_in_sidebar"] = main_clone_in_sidebar_penalty(
        screen, assets_by_id=assets_by_id
    )
    penalties["main_area_ratio"] = main_area_ratio_penalty(
        str(screen.get("patternId") or "")
    )
    # MSA · S-MSA-06 · prospective mismatch penalties (finalize applies real fit later)
    from travelogue.config.mosaic import effective_slot_adaptation_enabled

    if effective_slot_adaptation_enabled(cfg):
        from travelogue.layout_engine.mosaic.msa_fit import crop_risk_for_pair
        from travelogue.layout_templates.geometry import slot_display_aspect
        from travelogue.layout_templates.registry import get_engine

        risks: list[float] = []
        pid = str(screen.get("patternId") or "")
        try:
            tpl = get_engine().get(pid) if pid else None
        except KeyError:
            tpl = None
        if tpl is not None:
            for sl in screen.get("slots") or []:
                idx = int(sl.get("slot", -1))
                meta = next((s for s in tpl.slots if s.index == idx), None)
                if meta is None:
                    continue
                aid = sl.get("assetId")
                asset = assets_by_id.get(aid) if aid else None
                try:
                    da = float(sl.get("displayAspect") or 0.0)
                except (TypeError, ValueError):
                    da = 0.0
                if da <= 0:
                    da = float(slot_display_aspect(meta.rect, tpl.stage))
                risks.append(crop_risk_for_pair(asset, da))
        max_risk = max(risks) if risks else 0.0
        mean_risk = sum(risks) / len(risks) if risks else 0.0
        penalties["crop_risk_penalty"] = max_risk
        # aspect_fit as penalty = mean mismatch proxy (higher = worse fit)
        penalties["aspect_fit"] = mean_risk
        # whitespace unknown pre-contain; reserve key at 0 for weight_map stability
        penalties["whitespace_penalty"] = 0.0
    # Soft trip_total prior (was hard MIN_TRIP_PHOTOS_FOR_MOSAIC)
    if trip_photo_total > 0 and trip_photo_total < 20:
        penalties["trip_small"] = 0.7
    elif trip_photo_total < 35:
        penalties["trip_small"] = 0.25

    total = base
    reasons: list[str] = []
    from travelogue.layout_contract.scoring import combine_utility

    weight_map = {
        key: (
            0.2
            if key == "trip_small"
            else float(cfg.penalties.get(key, 0.15 if key != "trip_small" else 0.0))
        )
        for key in penalties
    }
    breakdown = combine_utility(base, penalties, weight_map)
    total = breakdown.utility
    for key, pen in breakdown.penalties_applied.items():
        if pen >= 0.5:
            code = "R_MAIN_AR_BLOCK" if key == "main_ar_ineligible" else f"R_{key.upper()}"
            reasons.append(code)

    if bd.temporal_coherence >= 0.7:
        reasons.append("R_TIME_COHESION")
    if bd.sharpness >= 0.6:
        reasons.append("R_SHARP")
    if screen.get("patternId") == PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5 and penalties.get(
        "hero_narrow_tiles", 0.0
    ) <= 0.0 and penalties.get("hero_slot_aspect", 0.0) <= 0.0:
        total = min(1.0, total * 1.08)
        reasons.append("R_HERO6_LAND")
    if (
        cfg.prefer_five_slot_single_portrait
        and screen.get("patternId") == PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND
        and asset_ids
    ):
        n_p = sum(1 for aid in asset_ids if _is_std_portrait_id(aid, aspects))
        n_l = sum(1 for aid in asset_ids if _is_landscape_id(aid, aspects))
        if n_p == 1 and n_l >= 4:
            total = min(1.0, total * 1.05)
            reasons.append("R_SINGLE_PORTRAIT_3LAND")
    # LTN H6/S2 · R_GRID9_LAND ×1.06 removed (conflicts with pruning 9-grid SKUs).
    # No layout_state ⇒ no rhythm constraints to enforce (unit/MCS probes).
    if layout_state is None or layout_state.can_emit_pattern(
        screen.get("patternId", "")
    ):
        reasons.append("R_RHYTHM_OK")
    else:
        total *= 0.5
        reasons.append("R_RHYTHM_BLOCK")

    pattern_id = str(screen.get("patternId") or "")
    from travelogue.layout_engine.mosaic.lte_adapter import (
        template_base_weight,
        template_diversity_bonus,
    )

    base_w = template_base_weight(pattern_id)
    if base_w != 1.0:
        total = min(1.0, total * base_w)
        if base_w > 1.0:
            reasons.append("R_LTE_WEIGHT_UP")
        elif base_w < 1.0:
            reasons.append("R_LTE_WEIGHT_DOWN")

    total = _apply_hero_gap_prior(
        total,
        reasons,
        pattern_id=pattern_id,
        asset_ids=[a for a in asset_ids if a],
        aspects=aspects,
        assets_by_id=assets_by_id,
    )

    div_bonus = template_diversity_bonus(pattern_id)
    if div_bonus > 0:
        total = min(1.0, total * (1.0 + div_bonus))
        reasons.append("R_LTE_DIVERSITY_BONUS")

    if cfg.lse_beat_profile and cfg.lse_beat_profile != "flat":
        from travelogue.layout_engine.beat import beat_score_multiplier

        beat_mul = beat_score_multiplier(
            pattern_id,
            screen_index=chapter_screen_index,
            chapter_screen_count=chapter_screen_count,
            beat_profile=cfg.lse_beat_profile,
        )
        if beat_mul != 1.0:
            total = min(1.0, total * beat_mul)
            reasons.append("R_BEAT_BIAS")

    if cfg.lse_highlight_boost and cfg.lse_highlight_boost > 1.0:
        from travelogue.layout_engine.highlight_windows import current_highlight_boost

        hl_boost = current_highlight_boost(asset_ids, default_boost=cfg.lse_highlight_boost)
        if hl_boost > 1.0:
            total = min(1.0, total * hl_boost)
            reasons.append("R_HIGHLIGHT_WINDOW")

    if cfg.lse_tone_harmony and prev_screen:
        from travelogue.layout_engine.tone_adjacency import adjacent_tone_penalty

        tone_pen = adjacent_tone_penalty(prev_screen, screen, assets_by_id)
        if tone_pen > 0:
            total *= 1.0 - 0.35 * tone_pen
            if tone_pen >= 0.45:
                reasons.append("R_TONE_JUMP")

    # MEGC · soft score_mul on non-cinema equal-grid peaks (SUP-MEGC-01/02)
    from travelogue.config.mosaic import effective_megc_selection_gate_enabled

    if effective_megc_selection_gate_enabled(cfg):
        from travelogue.layout_engine.mosaic.megc_gate import (
            evaluate_megc_gate,
            window_assets_for_megc,
        )

        megc_assets = window_assets_for_megc(
            [a for a in asset_ids if a], assets_by_id
        )
        megc = evaluate_megc_gate(pattern_id, megc_assets, cfg)
        if megc.active and megc.score_mul < 1.0:
            total = min(1.0, total * float(megc.score_mul))
            reasons.append("R_MEGC_PEAK_MISMATCH")

    # EGA · soft clone / anti-slice mul when hard gates were waived (PR-A)
    from travelogue.config.mosaic import (
        ega_anti_slice_mode,
        ega_anti_slice_score_mul,
        ega_clone_mode,
        ega_clone_score_mul,
        ega_flat_window_equal_bonus,
        ega_wasted_hero_extra,
        effective_equal_grid_admission_enabled,
        is_ega_equal_grid_pattern,
        is_ega_hero70_family,
    )

    if effective_equal_grid_admission_enabled(cfg) and is_ega_equal_grid_pattern(
        pattern_id, cfg
    ):
        aids = [a for a in asset_ids if a]
        if ega_clone_mode(cfg) == "soft_penalty":
            clone_pen = _near_scene_clone_penalty(pattern_id, aids, assets_by_id)
            if clone_pen >= NEAR_SCENE_CLONE_REJECT_THRESHOLD:
                total = min(1.0, total * float(ega_clone_score_mul(cfg)))
                reasons.append("R_EGA_CLONE_SOFT")
        if ega_anti_slice_mode(cfg) == "soft_penalty":
            from travelogue.layout_engine.mosaic.shot_group_gate import (
                hard_reject_same_shot_group_anti_slice,
            )

            if hard_reject_same_shot_group_anti_slice(pattern_id, aids, assets_by_id):
                total = min(1.0, total * float(ega_anti_slice_score_mul(cfg)))
                reasons.append("R_EGA_SLICE_SOFT")

    # EGA PR-C · flat-window bias: equal-grid bonus · hero-70 wasted extra
    if effective_equal_grid_admission_enabled(cfg):
        aids = [a for a in asset_ids if a]
        flat_bonus = ega_flat_window_equal_bonus(cfg)
        wasted_extra = ega_wasted_hero_extra(cfg)
        if flat_bonus > 0.0 or wasted_extra > 0.0:
            is_flat = _ega_window_is_flat(
                aids,
                aspects,
                assets_by_id,
                cfg=cfg,
            )
            main_not_best = float(penalties.get("main_not_window_best") or 0.0) >= 0.5
            bias_on = is_flat or main_not_best
            if bias_on and is_ega_equal_grid_pattern(pattern_id, cfg) and flat_bonus > 0.0:
                total = min(1.0, total + float(flat_bonus))
                reasons.append("R_EGA_FLAT_BONUS")
            if bias_on and is_ega_hero70_family(pattern_id) and wasted_extra > 0.0:
                total = max(0.0, min(1.0, total * (1.0 - float(wasted_extra))))
                reasons.append("R_EGA_WASTED_HERO")

    return MosaicScoreResult(
        total=_clamp01(total),
        base=base,
        penalties=penalties,
        reason_codes=reasons,
    )
