"""Phase 20 · UC 用例选版加分（AR 阈值 + pattern 匹配）."""

from __future__ import annotations

from typing import Any

from travelogue.config import get_config
from travelogue.config.layout import LayoutAssetAspectConfig
from travelogue.curation.layout_planner import AspectKind
from travelogue.curation.mosaic.constants import (
    PATTERN_LANDSCAPE_2,
    PATTERN_LANDSCAPE_3,
)

PATTERN_LANDSCAPE_3_WIDE_TOP_2 = "screen-landscape-3-wide-top-2"
PATTERN_LANDSCAPE_3_SQUARE_LEFT_2 = "screen-landscape-3-square-left-2"

_BONUS_STRONG = 1.10
_BONUS_MILD = 1.06
_PENALTY_MILD = 0.88
_PENALTY_STRONG = 0.75


def _asset_aspect_cfg() -> LayoutAssetAspectConfig:
    return get_config().layout.asset_aspect


def asset_width_height_ratio(asset: dict | None) -> float:
    if not asset:
        return 1.0
    w = int(asset.get("width") or 0)
    h = int(asset.get("height") or 0)
    if w <= 0 or h <= 0:
        return 1.0
    return w / h


def is_panorama_ratio(ratio: float, cfg: LayoutAssetAspectConfig) -> bool:
    return ratio >= cfg.panorama_min


def is_square_ratio(ratio: float, cfg: LayoutAssetAspectConfig) -> bool:
    return cfg.square_min <= ratio <= cfg.square_max


def is_panorama_asset(asset: dict | None, cfg: LayoutAssetAspectConfig | None = None) -> bool:
    cfg = cfg or _asset_aspect_cfg()
    ratio = asset_width_height_ratio(asset)
    if is_panorama_ratio(ratio, cfg):
        return True
    kind = (asset or {}).get("aspectKind")
    return kind == "panorama" and ratio >= cfg.panorama_min


def is_square_asset(asset: dict | None, cfg: LayoutAssetAspectConfig | None = None) -> bool:
    cfg = cfg or _asset_aspect_cfg()
    ratio = asset_width_height_ratio(asset)
    if is_square_ratio(ratio, cfg):
        return True
    kind = (asset or {}).get("aspectKind")
    return kind == "square" and is_square_ratio(ratio, cfg)


def _slot_asset_id(screen: dict, slot_index: int) -> str | None:
    for sl in screen.get("slots") or []:
        if int(sl.get("slot", -1)) == slot_index:
            aid = sl.get("assetId")
            return str(aid) if aid else None
    return None


def _window_all_panorama(
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
    cfg: LayoutAssetAspectConfig,
) -> bool:
    if not asset_ids:
        return False
    return all(is_panorama_asset(assets_by_id.get(aid), cfg) for aid in asset_ids)


def _count_square_landscape(
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
    aspects: dict[str, AspectKind],
    cfg: LayoutAssetAspectConfig,
) -> tuple[int, int]:
    squares = 0
    landscapes = 0
    for aid in asset_ids:
        asset = assets_by_id.get(aid) or {}
        if is_square_asset(asset, cfg):
            squares += 1
        elif aspects.get(aid) in ("landscape", "panorama") or not is_panorama_asset(asset, cfg):
            landscapes += 1
    return squares, landscapes


def use_case_layout_multiplier(
    screen: dict,
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
    aspects: dict[str, AspectKind],
) -> tuple[float, list[str]]:
    """Return score multiplier and reason codes for UC pattern ↔ asset AR fit."""
    cfg = _asset_aspect_cfg()
    if not cfg.use_case_scoring_enabled:
        return 1.0, []

    pattern_id = str(screen.get("patternId") or "")
    n = len(asset_ids)
    reasons: list[str] = []
    multiplier = 1.0

    if n == 2:
        if _window_all_panorama(asset_ids, assets_by_id, cfg):
            if pattern_id == PATTERN_LANDSCAPE_2:
                return _BONUS_STRONG, ["R_UC_PANO_STACK_2"]
            if pattern_id != PATTERN_LANDSCAPE_2:
                return _PENALTY_MILD, ["R_UC_PANO_MISMATCH_2"]
        return 1.0, []

    if n != 3:
        return 1.0, []

    all_pano = _window_all_panorama(asset_ids, assets_by_id, cfg)
    squares, landscapes = _count_square_landscape(asset_ids, assets_by_id, aspects, cfg)
    top_id = _slot_asset_id(screen, 0)
    left_id = _slot_asset_id(screen, 0)
    top_asset = assets_by_id.get(top_id or "") if top_id else None
    left_asset = assets_by_id.get(left_id or "") if left_id else None

    if all_pano:
        if pattern_id == PATTERN_LANDSCAPE_3:
            multiplier = _BONUS_STRONG
            reasons.append("R_UC_PANO_STACK_3")
        elif pattern_id == PATTERN_LANDSCAPE_3_WIDE_TOP_2:
            multiplier = _PENALTY_MILD
            reasons.append("R_UC_PANO_WIDE_TOP_MISMATCH")
        elif pattern_id == PATTERN_LANDSCAPE_3_SQUARE_LEFT_2:
            multiplier = _PENALTY_STRONG
            reasons.append("R_UC_PANO_SQUARE_MISMATCH")
        return multiplier, reasons

    if pattern_id == PATTERN_LANDSCAPE_3:
        multiplier = _PENALTY_MILD
        reasons.append("R_UC_STACK_NOT_ALL_PANO")

    if pattern_id == PATTERN_LANDSCAPE_3_WIDE_TOP_2:
        if top_asset and is_panorama_asset(top_asset, cfg):
            multiplier = max(multiplier, _BONUS_MILD)
            reasons.append("R_UC_WIDE_TOP_MATCH")
        else:
            multiplier = min(multiplier, _PENALTY_MILD)
            reasons.append("R_UC_WIDE_TOP_MISMATCH")

    if pattern_id == PATTERN_LANDSCAPE_3_SQUARE_LEFT_2:
        if left_asset and is_square_asset(left_asset, cfg) and squares >= 1 and landscapes >= 2:
            multiplier = max(multiplier, _BONUS_MILD)
            reasons.append("R_UC_SQUARE_LEFT_MATCH")
        else:
            multiplier = min(multiplier, _PENALTY_MILD)
            reasons.append("R_UC_SQUARE_LEFT_MISMATCH")

    return multiplier, reasons
