"""Main-slot aspect eligibility for hero+tile mosaic patterns (PRD-6张拼图优化 · R-MAIN-AR-01)."""

from __future__ import annotations

from typing import Any

from travelogue.config import MosaicConfig
from travelogue.layout_contract.asset_geometry import asset_native_ar
from travelogue.layout_contract.orientations import (
    AspectKind,
    aspect_kind_for_asset,
)
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
)
from travelogue.layout_engine.mosaic.runtime import get_effective_mosaic_config
from travelogue.layout_engine.planner.screen_planner import DEFAULT_FEATURED_WEIGHT
from travelogue.layout_templates.aspect_constants import (
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

DEFAULT_MAIN_FORBID_KINDS: frozenset[str] = frozenset(
    {"panorama", "tall", "portrait", "square"}
)
DEFAULT_MAIN_ELIGIBLE_KINDS: frozenset[str] = frozenset({"landscape"})


def template_main_slot_policy(pattern_id: str) -> dict[str, Any] | None:
    """Prefer ``constraints.eligibility`` AR fields; bridge ``mainSlotPolicy`` (AC-TPC-04)."""
    try:
        from travelogue.layout_templates.registry import get_engine

        template = get_engine().get(pattern_id)
        constraints = template.constraints or {}
        elig = constraints.get("eligibility")
        if isinstance(elig, dict) and (
            elig.get("eligibleAspectKinds")
            or elig.get("forbidKinds")
            or elig.get("targetDisplayAspect")
        ):
            # Synthesize policy shape expected by resolve_* helpers
            return {
                "slotIndex": elig.get("slotIndex", 0),
                "targetDisplayAspect": elig.get(
                    "targetDisplayAspect", elig.get("target_display_aspect", MAIN_HERO_TARGET_AR)
                ),
                "eligibleAspectKinds": elig.get("eligibleAspectKinds")
                or elig.get("eligible_aspect_kinds")
                or list(DEFAULT_MAIN_ELIGIBLE_KINDS),
                "forbidKinds": elig.get("forbidKinds")
                or elig.get("forbid_kinds")
                or list(DEFAULT_MAIN_FORBID_KINDS),
                "arLadderTol": elig.get("arLadderTol", elig.get("ar_ladder_tol", AR_LADDER_TOL)),
                "preferLadder": elig.get("preferLadder", elig.get("prefer_ladder", list(AR_LADDER))),
            }
        raw = constraints.get("mainSlotPolicy")
        if isinstance(raw, dict) and raw:
            return raw
    except (KeyError, AttributeError, TypeError):
        pass
    return None


def pattern_requires_main_ar_guard(pattern_id: str) -> bool:
    if pattern_id in MAIN_HERO_PATTERNS:
        return True
    return template_main_slot_policy(pattern_id) is not None


def _kind_set_from_policy(
    policy: dict[str, Any] | None,
    *,
    primary_key: str,
    alt_key: str,
    default: frozenset[str],
) -> frozenset[str]:
    if not policy:
        return default
    raw = policy.get(primary_key, policy.get(alt_key))
    if raw is None:
        return default
    if isinstance(raw, (list, tuple)):
        kinds = frozenset(str(x).strip().lower() for x in raw if str(x).strip())
        return kinds or default
    return default


def resolve_main_forbid_kinds(pattern_id: str | None) -> frozenset[str]:
    policy = template_main_slot_policy(pattern_id) if pattern_id else None
    return _kind_set_from_policy(
        policy,
        primary_key="forbidKinds",
        alt_key="forbid_kinds",
        default=DEFAULT_MAIN_FORBID_KINDS,
    )


def resolve_main_eligible_kinds(pattern_id: str | None) -> frozenset[str]:
    policy = template_main_slot_policy(pattern_id) if pattern_id else None
    return _kind_set_from_policy(
        policy,
        primary_key="eligibleAspectKinds",
        alt_key="eligible_aspect_kinds",
        default=DEFAULT_MAIN_ELIGIBLE_KINDS,
    )


def resolve_main_target_display_ar(pattern_id: str | None) -> float:
    policy = template_main_slot_policy(pattern_id) if pattern_id else None
    if policy:
        raw = policy.get("targetDisplayAspect", policy.get("target_display_aspect"))
        if raw is not None:
            try:
                return float(raw)
            except (TypeError, ValueError):
                pass
    return MAIN_HERO_TARGET_AR


def resolve_prefer_ladder(pattern_id: str | None) -> tuple[float, ...]:
    policy = template_main_slot_policy(pattern_id) if pattern_id else None
    if policy:
        raw = policy.get("preferLadder", policy.get("prefer_ladder"))
        if isinstance(raw, (list, tuple)) and raw:
            try:
                return tuple(float(x) for x in raw)
            except (TypeError, ValueError):
                pass
    return (MAIN_HERO_TARGET_AR, 1.5, 4 / 3)


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


# asset_native_ar lives in layout_contract (TPC W2 shared-tool decoupling);
# re-exported here for existing call sites until W3 deletes this module.


def nearest_ladder_delta(ar: float) -> float:
    return min(abs(ar - ladder) for ladder in AR_LADDER)


def ar_preference_boost(
    ar: float,
    *,
    target_ar: float = MAIN_HERO_TARGET_AR,
    prefer_ladder: tuple[float, ...] | None = None,
    prefer_enabled: bool = True,
) -> float:
    if not prefer_enabled:
        return 1.0
    rungs = prefer_ladder if prefer_ladder else (target_ar,)
    best = 0.0
    for i, rung in enumerate(rungs):
        dist = abs(ar - rung)
        score = (0.15 / (1 + i)) / (1.0 + dist)
        if score > best:
            best = score
    return 1.0 + best


def _blocked_kind_reason(kind: AspectKind) -> str:
    return f"blocked_{kind}"


def asset_eligible_for_main_slot(
    asset: dict,
    *,
    pattern_id: str | None = None,
    tol: float | None = None,
    forbid_kinds: frozenset[str] | None = None,
    eligible_kinds: frozenset[str] | None = None,
) -> tuple[bool, str]:
    """Hard eligibility for role=main; kind gates driven by template mainSlotPolicy."""
    pid = pattern_id or ""
    ladder_tol = tol if tol is not None else AR_LADDER_TOL
    forbid = (
        forbid_kinds
        if forbid_kinds is not None
        else resolve_main_forbid_kinds(pid or None)
    )
    eligible = (
        eligible_kinds
        if eligible_kinds is not None
        else resolve_main_eligible_kinds(pid or None)
    )

    ar = asset_native_ar(asset)
    if ar is None:
        return False, "blocked_no_dims"

    kind = aspect_kind_for_asset(asset)
    if kind in forbid:
        return False, _blocked_kind_reason(kind)
    if kind not in eligible:
        return False, "blocked_not_eligible_kind"
    if ar > LANDSCAPE_AR_BLOCK_HIGH:
        return False, "blocked_ultra_wide"
    if nearest_ladder_delta(ar) > ladder_tol:
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
    from travelogue.layout_engine.scoring.hero import effective_hero_score

    cfg = cfg or get_effective_mosaic_config()
    pid = pattern_id or ""
    ladder_tol = tol if tol is not None else resolve_main_ar_ladder_tol(pid, cfg)
    prefer = (
        prefer_16_9
        if prefer_16_9 is not None
        else resolve_main_ar_prefer_16_9(pid, cfg)
    )
    target_ar = resolve_main_target_display_ar(pid or None)
    prefer_ladder = resolve_prefer_ladder(pid or None) if prefer else None
    forbid = resolve_main_forbid_kinds(pid or None)
    eligible = resolve_main_eligible_kinds(pid or None)
    eligible_ids = [
        aid
        for aid in candidate_ids
        if asset_eligible_for_main_slot(
            assets_map.get(aid) or {},
            pattern_id=pid or None,
            tol=ladder_tol,
            forbid_kinds=forbid,
            eligible_kinds=eligible,
        )[0]
    ]
    if not eligible_ids:
        return None

    def sort_key(aid: str) -> tuple[float, float]:
        asset = assets_map.get(aid) or {}
        hero = effective_hero_score(
            asset,
            median_sharp=median_sharp or 0.0,
            featured_weight=featured_weight,
        )
        ar = asset_native_ar(asset) or 1.0
        boost = ar_preference_boost(
            ar,
            target_ar=target_ar,
            prefer_ladder=prefer_ladder,
            prefer_enabled=prefer,
        )
        return hero * boost, hero

    return max(eligible_ids, key=sort_key)


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
    forbid = resolve_main_forbid_kinds(pattern_id)
    eligible = resolve_main_eligible_kinds(pattern_id)
    for slot in screen.get("slots") or []:
        if slot.get("role") != "main":
            continue
        aid = slot.get("assetId")
        if not aid:
            return False, "blocked_no_main"
        ok, reason = asset_eligible_for_main_slot(
            assets_map.get(aid) or {},
            pattern_id=pattern_id,
            tol=tol,
            forbid_kinds=forbid,
            eligible_kinds=eligible,
        )
        return ok, reason
    return True, "ok"
