"""Food Role Policy helpers (cover / closing / hero / moment / grid)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from travelogue.config.food_role import FoodRoleConfig
from travelogue.layout_contract.subject_tagging import (
    is_food_asset,
    is_mundane_clusterable,
)

FOOD_L1 = frozenset({"food", "meal", "cafe", "restaurant"})


def get_food_role_config(cfg: FoodRoleConfig | None = None) -> FoodRoleConfig:
    if cfg is not None:
        return cfg
    try:
        from travelogue.config import get_config

        return get_config().curate.food_role
    except Exception:
        return FoodRoleConfig()


def food_cover_score_multiplier(
    asset: dict,
    *,
    cfg: FoodRoleConfig | None = None,
    override: bool = False,
) -> float:
    if override or not is_food_asset(asset):
        return 1.0
    role = get_food_role_config(cfg)
    if role.cover_policy == "off":
        return 1.0
    if role.cover_policy == "exclude":
        return 0.0
    return max(0.0, float(role.cover_multiplier))


def food_closing_score_multiplier(
    asset: dict,
    *,
    cfg: FoodRoleConfig | None = None,
    override: bool = False,
) -> float:
    if override or not is_food_asset(asset):
        return 1.0
    role = get_food_role_config(cfg)
    if role.closing_policy == "off":
        return 1.0
    if role.closing_policy == "exclude":
        return 0.0
    return max(0.0, float(role.closing_multiplier))


def filter_food_for_policy(
    assets: list[dict],
    *,
    policy: str,
    cfg: FoodRoleConfig | None = None,
) -> tuple[list[dict], bool]:
    """Return (filtered, used_fallback).

    For exclude: drop food; if empty, fall back to original and mark fallback.
    For demote/off: return original unchanged (scoring applies multiplier).
    """
    get_food_role_config(cfg)
    effective = policy if policy in {"demote", "exclude", "off"} else "demote"
    if effective != "exclude":
        return assets, False
    kept = [a for a in assets if not is_food_asset(a)]
    if kept:
        return kept, False
    return assets, True


def should_skip_food_hero(
    asset: dict,
    *,
    cfg: FoodRoleConfig | None = None,
) -> bool:
    role = get_food_role_config(cfg)
    if role.hero_policy == "allow":
        return False
    return is_food_asset(asset)


def moment_allows_food(*, cfg: FoodRoleConfig | None = None) -> bool:
    return bool(get_food_role_config(cfg).allow_food_in_moment)


def food_moment_score_multiplier(
    asset: dict,
    *,
    cfg: FoodRoleConfig | None = None,
) -> float:
    """Soft demote for food in peak_moment_score (pool may still include via allow/fallback)."""
    if not is_food_asset(asset):
        return 1.0
    role = get_food_role_config(cfg)
    return max(0.0, float(role.moment_multiplier))


def annotate_food_policy(
    meta: dict[str, Any],
    *,
    slot: str,
    applied: str,
) -> dict[str, Any]:
    block = meta.get("foodPolicy")
    if not isinstance(block, dict):
        block = {}
    block[slot] = applied
    meta["foodPolicy"] = block
    return meta


def annotate_trip_food_policy(trip: dict, *, slot: str, applied: str) -> None:
    curation = trip.setdefault("curation", {})
    if not isinstance(curation, dict):
        return
    annotate_food_policy(curation, slot=slot, applied=applied)


def record_food_grid_decision(
    trip: dict | None,
    *,
    asset_ids: list[str],
    window_seconds: float,
    pattern: str,
    layout_hint: str,
) -> None:
    """Append FRP §4.7 foodPolicy.grids[] entry onto trip.curation."""
    if not isinstance(trip, dict):
        return
    curation = trip.setdefault("curation", {})
    if not isinstance(curation, dict):
        return
    block = curation.get("foodPolicy")
    if not isinstance(block, dict):
        block = {}
    grids = block.get("grids")
    if not isinstance(grids, list):
        grids = []
    grids.append(
        {
            "assetIds": list(asset_ids),
            "windowSeconds": float(window_seconds),
            "pattern": pattern,
            "layoutHint": layout_hint,
        }
    )
    block["grids"] = grids
    curation["foodPolicy"] = block


def _parse_taken_at(raw: Any) -> datetime | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def collect_mundane_cluster_at_cursor(
    ids: list[str],
    assets_map: dict[str, dict],
    start: int,
    *,
    target_bucket: str,
    allowed_buckets: tuple[str, ...] = ("food",),
    max_items: int = 9,
    max_interruptions: int = 2,
    window_seconds: float = 3600.0,
) -> list[str]:
    """Collect same-bucket mundane ids near cursor with interruption + time window.

    Allows a few leading non-target inserts (same as Phase 10 collect), then
    requires at least one target. Scans forward only. When takenAt is missing,
    falls back to interruption-only consecutive collection.
    """
    if start < 0 or start >= len(ids):
        return []
    allowed = set(allowed_buckets)
    if target_bucket not in allowed:
        return []

    out: list[str] = []
    misses = 0
    i = start
    anchor_dt: datetime | None = None
    use_window = target_bucket == "food" and window_seconds > 0

    while i < len(ids) and len(out) < max_items:
        aid = ids[i]
        bucket = is_mundane_clusterable(assets_map.get(aid, {}))
        if bucket == target_bucket:
            if use_window:
                dt = _parse_taken_at((assets_map.get(aid) or {}).get("takenAt"))
                if anchor_dt is None and dt is not None:
                    anchor_dt = dt
                elif anchor_dt is not None and dt is not None:
                    if abs((dt - anchor_dt).total_seconds()) > float(window_seconds):
                        break
            out.append(aid)
            i += 1
            continue
        misses += 1
        if misses > max_interruptions:
            break
        i += 1
    return out


__all__ = [
    "FOOD_L1",
    "annotate_food_policy",
    "annotate_trip_food_policy",
    "collect_mundane_cluster_at_cursor",
    "filter_food_for_policy",
    "food_closing_score_multiplier",
    "food_cover_score_multiplier",
    "food_moment_score_multiplier",
    "get_food_role_config",
    "is_food_asset",
    "moment_allows_food",
    "record_food_grid_decision",
    "should_skip_food_hero",
]
