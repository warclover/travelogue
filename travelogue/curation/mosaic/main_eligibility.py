"""Main-slot aspect eligibility for hero+tile mosaic patterns (PRD-6张拼图优化 · R-MAIN-AR-01)."""

from __future__ import annotations

from typing import Any

from travelogue.config import MosaicConfig
from travelogue.curation.layout_planner import aspect_kind_for_asset
from travelogue.curation.mosaic.constants import (
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
)
from travelogue.curation.mosaic.runtime import get_effective_mosaic_config
from travelogue.curation.screen_planner import DEFAULT_FEATURED_WEIGHT
from travelogue.layout_templates.validator import (
    AR_LADDER,
    AR_LADDER_TOL,
    LANDSCAPE_AR_BLOCK_HIGH,
)

MAIN_HERO_TARGET_AR = 16 / 9

MAIN_HERO_PATTERNS: frozenset[str] = frozenset(
    {
        PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
        PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    }
)


def template_main_slot_policy(pattern_id: str) -> dict[str, Any] | None:
    try:
        from travelogue.layout_templates.registry import get_engine

        template = get_engine().get(pattern_id)
        raw = (template.constraints or {}).get("mainSlotPolicy")
        if isinstance(raw, dict) and raw:
            return raw
    except (KeyError, AttributeError, TypeError):
        pass
    return None


def pattern_requires_main_ar_guard(pattern_id: str) -> bool:
    if pattern_id in MAIN_HERO_PATTERNS:
        return True
    return template_main_slot_policy(pattern_id) is not None


def resolve_main_ar_ladder_tol(pattern_id: str, cfg: MosaicConfig) -> float:
    policy = template_main_slot_policy(pattern_id)
    if policy:
        raw = policy.get("arLadderTol", policy.get("ar_ladder_tol"))
        if raw is not None:
            return float(raw)
    return cfg.main_ar_ladder_tol


def resolve_main_ar_prefer_16_9(pattern_id: str, cfg: MosaicConfig) -> bool:
    policy = template_main_slot_policy(pattern_id)
    if policy and policy.get("preferLadder", policy.get("prefer_ladder")):
        prefer = policy.get("preferLadder", policy.get("prefer_ladder"))
        if isinstance(prefer, (list, tuple)) and prefer:
            try:
                return abs(float(prefer[0]) - MAIN_HERO_TARGET_AR) <= AR_LADDER_TOL
            except (TypeError, ValueError):
                pass
    return cfg.main_ar_prefer_16_9


def main_ar_guard_enabled(cfg: MosaicConfig | None = None) -> bool:
    cfg = cfg or get_effective_mosaic_config()
    return bool(getattr(cfg, "main_ar_guard", True))


def asset_native_ar(asset: dict) -> float | None:
    w = int(asset.get("nativeWidth") or asset.get("width") or 0)
    h = int(asset.get("nativeHeight") or asset.get("height") or 0)
    if w > 0 and h > 0:
        return w / h
    return None


def nearest_ladder_delta(ar: float) -> float:
    return min(abs(ar - ladder) for ladder in AR_LADDER)


def ar_preference_boost(ar: float, *, prefer_16_9: bool) -> float:
    if not prefer_16_9:
        return 1.0
    return 1.0 + 0.15 / (1.0 + abs(ar - MAIN_HERO_TARGET_AR))


def asset_eligible_for_main_slot(
    asset: dict,
    *,
    tol: float = AR_LADDER_TOL,
) -> tuple[bool, str]:
    """Hard eligibility for role=main on 16:9 hero+tile templates."""
    kind = aspect_kind_for_asset(asset)
    if kind == "panorama":
        return False, "blocked_panorama"
    if kind in ("portrait", "tall"):
        return False, "blocked_portrait"
    if kind == "square":
        return False, "blocked_square"
    ar = asset_native_ar(asset)
    if ar is None:
        return False, "blocked_no_dims"
    if ar > LANDSCAPE_AR_BLOCK_HIGH:
        return False, "blocked_ultra_wide"
    if nearest_ladder_delta(ar) > tol:
        return False, "blocked_off_ladder"
    return True, "ok"


def pick_best_main_eligible(
    candidate_ids: list[str],
    assets_map: dict[str, dict],
    *,
    pattern_id: str | None = None,
    tol: float | None = None,
    prefer_16_9: bool | None = None,
    median_sharp: float | None = None,
    featured_weight: float = DEFAULT_FEATURED_WEIGHT,
    cfg: MosaicConfig | None = None,
) -> str | None:
    """Pick highest-scoring main among AR-eligible landscape candidates."""
    from travelogue.curation.curate_scoring import effective_hero_score

    cfg = cfg or get_effective_mosaic_config()
    pid = pattern_id or ""
    ladder_tol = tol if tol is not None else resolve_main_ar_ladder_tol(pid, cfg)
    prefer = (
        prefer_16_9
        if prefer_16_9 is not None
        else resolve_main_ar_prefer_16_9(pid, cfg)
    )
    eligible = [
        aid
        for aid in candidate_ids
        if asset_eligible_for_main_slot(assets_map.get(aid) or {}, tol=ladder_tol)[0]
    ]
    if not eligible:
        return None

    def sort_key(aid: str) -> tuple[float, float]:
        asset = assets_map.get(aid) or {}
        hero = effective_hero_score(
            asset,
            median_sharp=median_sharp or 0.0,
            featured_weight=featured_weight,
        )
        ar = asset_native_ar(asset) or 1.0
        return hero * ar_preference_boost(ar, prefer_16_9=prefer), hero

    return max(eligible, key=sort_key)


def screen_main_slot_eligible(
    screen: dict,
    assets_map: dict[str, dict],
    *,
    pattern_id: str,
    cfg: MosaicConfig | None = None,
) -> tuple[bool, str]:
    cfg = cfg or get_effective_mosaic_config()
    if not main_ar_guard_enabled(cfg):
        return True, "ok"
    if not pattern_requires_main_ar_guard(pattern_id):
        return True, "ok"
    tol = resolve_main_ar_ladder_tol(pattern_id, cfg)
    for slot in screen.get("slots") or []:
        if slot.get("role") != "main":
            continue
        aid = slot.get("assetId")
        if not aid:
            return False, "blocked_no_main"
        ok, reason = asset_eligible_for_main_slot(
            assets_map.get(aid) or {},
            tol=tol,
        )
        return ok, reason
    return True, "ok"
