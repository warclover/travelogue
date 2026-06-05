"""Mosaic unified scorer (M5) — multiplicative penalties."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from travelogue.config import MosaicConfig
from travelogue.curation.layout_constraints import FOCAL_EDGE_MARGIN
from travelogue.curation.layout_planner import AspectKind
from travelogue.curation.layout_scoring import ScoringWeights, score_screen_plan
from travelogue.curation.mosaic.constants import (
    PATTERN_LANDSCAPE_6,
    PATTERN_LANDSCAPE_9,
    PATTERN_MOSAIC_5_2P_3L_BALANCED,
    PATTERN_MOSAIC_5_MAIN_LAND_2P_2L,
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    PATTERN_PORTRAIT_6,
)
from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState
from travelogue.curation.mosaic.slot_geometry import screen_slots_geometry_ok
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


def _main_quality_penalty(screen: dict, assets_by_id: dict[str, dict]) -> float:
    for sl in screen.get("slots") or []:
        if sl.get("role") != "main":
            continue
        aid = sl.get("assetId")
        asset = assets_by_id.get(aid) or {}
        q = asset.get("quality") or {}
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


def _slot_geometry_penalty(
    screen: dict,
    aspects: dict[str, AspectKind],
) -> float:
    if not screen_slots_geometry_ok(screen, aspects):
        return 0.95
    pattern_id = str(screen.get("patternId") or "")
    if pattern_id == PATTERN_MOSAIC_5_2P_3L_BALANCED:
        for slot in screen.get("slots") or []:
            if int(slot.get("slot", -1)) == 3 and slot.get("assetId"):
                if _is_std_portrait_id(slot["assetId"], aspects):
                    return 0.35
    if pattern_id == PATTERN_MOSAIC_5_MAIN_LAND_2P_2L:
        for slot in screen.get("slots") or []:
            if int(slot.get("slot", -1)) == 3 and slot.get("assetId"):
                if _is_std_portrait_id(slot["assetId"], aspects):
                    return 0.4
    return 0.0


def _hero_slot_aspect_penalty(
    screen: dict,
    aspects: dict[str, AspectKind],
) -> float:
    """Side tiles prefer portrait; bottom row prefers landscape."""
    pattern_id = str(screen.get("patternId") or "")
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
) -> float:
    """Penalize all-landscape hero+tile patterns where side tiles are narrow strips."""
    pattern_id = str(screen.get("patternId") or "")
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


def score_candidate(
    screen: dict,
    *,
    aspects: dict[str, AspectKind],
    assets_by_id: dict[str, dict],
    cfg: MosaicConfig,
    layout_state: ScreenLayoutPlannerState | None = None,
    trip_photo_total: int = 0,
    burst_seconds: float = 12.0,
) -> MosaicScoreResult:
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
    penalties: dict[str, float] = {
        "face_crop": _face_crop_penalty(screen, assets_by_id),
        "main_quality": _main_quality_penalty(screen, assets_by_id),
        "duplicate_density": _duplicate_density_penalty(asset_ids, assets_by_id),
        "hero_narrow_tiles": _hero_narrow_tile_penalty(screen, asset_ids, aspects),
        "hero_slot_aspect": _hero_slot_aspect_penalty(screen, aspects),
        "slot_geometry": _slot_geometry_penalty(screen, aspects),
        "flat_six_grid": _flat_six_grid_penalty(
            str(screen.get("patternId") or ""), asset_ids, aspects
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
            reasons.append(f"R_{key.upper()}")

    if bd.temporal_coherence >= 0.7:
        reasons.append("R_TIME_COHESION")
    if bd.sharpness >= 0.6:
        reasons.append("R_SHARP")
    if screen.get("patternId") == PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5 and penalties.get(
        "hero_narrow_tiles", 0.0
    ) <= 0.0 and penalties.get("hero_slot_aspect", 0.0) <= 0.0:
        total = min(1.0, total * 1.08)
        reasons.append("R_HERO6_LAND")
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

    return MosaicScoreResult(
        total=_clamp01(total),
        base=base,
        penalties=penalties,
        reason_codes=reasons,
    )
