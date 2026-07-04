"""Mosaic unified scorer (M5) — multiplicative penalties."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from travelogue.config import MosaicConfig
from travelogue.curation.layout_constraints import FOCAL_EDGE_MARGIN
from travelogue.curation.layout_planner import AspectKind
from travelogue.curation.layout_scoring import ScoringWeights, score_screen_plan
from travelogue.curation.mosaic.constants import (
    PATTERN_LANDSCAPE_6,
    PATTERN_LANDSCAPE_9,
    PATTERN_MOSAIC_5_HERO_3_2_PLUS_4,
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    PATTERN_PORTRAIT_6,
)
from travelogue.curation.mosaic.main_eligibility import screen_main_slot_eligible
from travelogue.curation.mosaic.slot_geometry import screen_slots_geometry_ok
from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState
from travelogue.curation.screen_planner import _is_landscape_id, _is_std_portrait_id


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
            from travelogue.curation.aesthetic_score import aesthetic_overall

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


def _duplicate_density_penalty(asset_ids: list[str], assets_by_id: dict[str, dict]) -> float:
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
    from travelogue.curation.mosaic.pattern_catalog import default_registry

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
) -> MosaicScoreResult:
    quality_pool = None
    if cfg.lse_quality_unified:
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
    penalties: dict[str, float] = {
        "face_crop": max(face_pen, salient_pen),
        "salient_crop": salient_pen,
        "main_quality": _main_quality_penalty(
            screen,
            assets_by_id,
            cfg=cfg,
            quality_pool=quality_pool,
        ),
        "duplicate_density": _duplicate_density_penalty(asset_ids, assets_by_id),
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
    }
    # Soft trip_total prior (was hard MIN_TRIP_PHOTOS_FOR_MOSAIC)
    if trip_photo_total > 0 and trip_photo_total < 20:
        penalties["trip_small"] = 0.7
    elif trip_photo_total < 35:
        penalties["trip_small"] = 0.25

    total = base
    reasons: list[str] = []
    for key, pen in penalties.items():
        weight = cfg.penalties.get(key, 0.15 if key != "trip_small" else 0.0)
        if key == "trip_small":
            weight = 0.2
        if pen <= 0 or weight <= 0:
            continue
        total *= 1.0 - _clamp01(weight) * _clamp01(pen)
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
    if screen.get("patternId") == PATTERN_LANDSCAPE_9 and penalties.get(
        "hero_slot_aspect", 0.0
    ) <= 0.0:
        all_land = asset_ids and all(_is_landscape_id(aid, aspects) for aid in asset_ids)
        if all_land and len(asset_ids) == 9:
            total = min(1.0, total * 1.06)
            reasons.append("R_GRID9_LAND")
    if layout_state and layout_state.can_emit_pattern(screen.get("patternId", "")):
        reasons.append("R_RHYTHM_OK")
    else:
        total *= 0.5
        reasons.append("R_RHYTHM_BLOCK")

    pattern_id = str(screen.get("patternId") or "")
    from travelogue.curation.mosaic.lte_adapter import (
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

    return MosaicScoreResult(
        total=_clamp01(total),
        base=base,
        penalties=penalties,
        reason_codes=reasons,
    )
