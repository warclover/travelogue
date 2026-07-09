"""Editorial 4mix (screen-editorial-4mix) · planner/MCS hook."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Literal

from travelogue.layout_contract.patterns import (
    EDITORIAL_COMPOSITE_PATTERN_PREFIX,  # noqa: F401
    is_editorial_composite_pattern,  # noqa: F401
)
from travelogue.layout_contract.subject import asset_has_person
from travelogue.layout_engine.mosaic.constants import PATTERN_PORTRAIT_2_LANDSCAPE_2

if TYPE_CHECKING:
    from travelogue.config import AppConfig
    from travelogue.layout_contract.orientations import AspectKind

LayoutFit = Literal["cover", "contain"]

PATTERN_EDITORIAL_4MIX = "screen-editorial-4mix"
LAYOUT_HINT_EDITORIAL_4MIX = "editorial-4mix"

# Chess order: TL land, TR port, BL port, BR land
CHESS_SLOT_ROLES: tuple[str, ...] = ("landscape", "portrait", "portrait", "landscape")


def editorial_4mix_config(cfg: AppConfig | None = None):
    from travelogue.config import get_config

    app = cfg or get_config()
    return app.layout.editorial_4mix


def is_editorial_4mix_enabled(
    trip: dict | None,
    cfg: AppConfig | None = None,
) -> bool:
    """trip.export.editorial4Mix > trip_allowlist > global enabled."""
    e4 = editorial_4mix_config(cfg)
    if trip:
        export = trip.get("export") or {}
        override = export.get("editorial4Mix")
        if override is not None:
            return bool(override)
        trip_id = str(trip.get("tripId") or "").strip()
        if trip_id and trip_id in e4.trip_allowlist:
            return True
    return bool(e4.enabled)


def _aspect_kind_for_id(
    aid: str,
    assets_map: dict[str, dict],
    aspects: dict[str, AspectKind] | None,
) -> str:
    if aspects and aid in aspects:
        return str(aspects[aid])
    from travelogue.layout_contract.orientations import aspect_kind_for_asset

    return aspect_kind_for_asset(assets_map.get(aid, {}))


def chess_window_matches(
    asset_ids: list[str],
    assets_map: dict[str, dict],
    *,
    aspects: dict[str, AspectKind] | None = None,
) -> bool:
    if len(asset_ids) != 4:
        return False
    from travelogue.layout_engine.planner.screen_planner import (
        _is_landscape_id,
        _is_std_portrait_id,
    )

    asp = aspects or {
        aid: _aspect_kind_for_id(aid, assets_map, None) for aid in asset_ids  # type: ignore[misc]
    }
    n_portrait = sum(1 for aid in asset_ids if _is_std_portrait_id(aid, asp))
    n_landscape = sum(1 for aid in asset_ids if _is_landscape_id(aid, asp))
    return n_portrait >= 2 and n_landscape >= 2


def _rank_landscapes_by_hero(
    landscape_ids: list[str],
    assets_map: dict[str, dict],
) -> list[str]:
    from travelogue.layout_contract.scoring import median_sharpness
    from travelogue.layout_engine.scoring.hero import effective_hero_score

    med = median_sharpness(list(assets_map.values()))

    def _score(aid: str) -> float:
        asset = assets_map.get(aid) or {}
        return float(
            effective_hero_score(asset, median_sharp=med, featured_weight=1.0) or 0.0
        )

    return sorted(landscape_ids, key=_score, reverse=True)


def chess_order_asset_ids(
    asset_ids: list[str],
    assets_map: dict[str, dict],
    *,
    aspects: dict[str, AspectKind] | None = None,
) -> list[str] | None:
    """Reorder to [L, P, P, L] · hero landscape → TL, second → BR."""
    if not chess_window_matches(asset_ids, assets_map, aspects=aspects):
        return None
    from travelogue.layout_engine.mosaic.builders import _sort_asset_ids_by_taken
    from travelogue.layout_engine.planner.screen_planner import (
        _is_landscape_id,
        _is_std_portrait_id,
    )

    asp = aspects or {
        aid: _aspect_kind_for_id(aid, assets_map, None) for aid in asset_ids  # type: ignore[misc]
    }
    portraits = [aid for aid in asset_ids if _is_std_portrait_id(aid, asp)]
    landscapes = [aid for aid in asset_ids if _is_landscape_id(aid, asp)]
    if len(portraits) < 2 or len(landscapes) < 2:
        return None
    lands = _rank_landscapes_by_hero(landscapes, assets_map)[:2]
    ports = _sort_asset_ids_by_taken(portraits, assets_map)[:2]
    return [lands[0], ports[0], ports[1], lands[1]]


def editorial_4mix_scenery_portrait_fit_mode(
    *,
    trip_id: str,
    screen_id: str,
    asset_id: str,
    slot_index: int,
) -> LayoutFit:
    """Deterministic pseudo-random cover/contain for scenery portrait slots (PRD §6 P2)."""
    key = f"{trip_id}:{screen_id}:{asset_id}:{slot_index}"
    digest = hashlib.sha256(key.encode()).hexdigest()
    return "cover" if int(digest[:8], 16) % 2 == 0 else "contain"


def resolve_4mix_slot_fit(
    aid: str,
    *,
    role: str,
    assets_map: dict[str, dict],
    screen: dict | None = None,
    trip: dict | None = None,
    cfg: AppConfig | None = None,
) -> LayoutFit:
    asset = assets_map.get(aid) or {}
    if asset_has_person(asset):
        return "contain"
    if role == "landscape":
        return "cover"
    e4 = editorial_4mix_config(cfg)
    if not e4.scenery_portrait_cover_random:
        return "contain"
    screen_id = str((screen or {}).get("screenId") or "").strip()
    if not screen_id:
        return "contain"
    slot_index = 0
    for idx, slot in enumerate((screen or {}).get("slots") or []):
        if str(slot.get("assetId") or "") == aid:
            slot_index = int(slot.get("slot", idx))
            break
    trip_id = str((trip or {}).get("tripId") or "")
    return editorial_4mix_scenery_portrait_fit_mode(
        trip_id=trip_id,
        screen_id=screen_id,
        asset_id=aid,
        slot_index=slot_index,
    )


def slot_fit_for_4mix(aid: str, *, role: str, assets_map: dict[str, dict]) -> LayoutFit:
    asset = assets_map.get(aid) or {}
    if asset_has_person(asset):
        return "contain"
    if role == "landscape":
        return "cover"
    return "contain"


def apply_editorial_4mix_slot_fits(
    screen: dict,
    assets_map: dict[str, dict],
    *,
    trip: dict | None = None,
    cfg: AppConfig | None = None,
) -> dict:
    """Finalize per-slot fits after ``screenId`` is stable (scenery portrait random)."""
    if str(screen.get("patternId") or "") != PATTERN_EDITORIAL_4MIX:
        return screen
    slots = screen.get("slots") or []
    if not slots:
        return screen
    updated: list[dict] = []
    for idx, slot in enumerate(slots):
        aid = str(slot.get("assetId") or "")
        role = str(
            slot.get("role")
            or (CHESS_SLOT_ROLES[idx] if idx < len(CHESS_SLOT_ROLES) else "")
        )
        fit = resolve_4mix_slot_fit(
            aid,
            role=role,
            assets_map=assets_map,
            screen=screen,
            trip=trip,
            cfg=cfg,
        )
        updated.append({**dict(slot), "fit": fit})
    screen["slots"] = updated
    return screen


def build_4mix_slots(
    ordered_ids: list[str],
    assets_map: dict[str, dict],
) -> list[dict]:
    slots: list[dict] = []
    for idx, aid in enumerate(ordered_ids):
        role = CHESS_SLOT_ROLES[idx]
        slots.append(
            {
                "assetId": aid,
                "slot": idx,
                "fit": slot_fit_for_4mix(aid, role=role, assets_map=assets_map),
                "role": role,
            }
        )
    return slots


def maybe_editorial_4mix(
    pattern_id: str,
    asset_ids: list[str],
    assets_map: dict[str, dict],
    *,
    trip: dict | None = None,
    cfg: AppConfig | None = None,
    aspects: dict[str, AspectKind] | None = None,
) -> tuple[str, str | None]:
    """Return (pattern_id, layout_hint). hint None = leave existing hint unchanged."""
    e4 = editorial_4mix_config(cfg)
    if not is_editorial_4mix_enabled(trip, cfg):
        return pattern_id, None
    if pattern_id not in e4.replace_patterns:
        return pattern_id, None
    if not chess_window_matches(asset_ids, assets_map, aspects=aspects):
        return pattern_id, None
    return PATTERN_EDITORIAL_4MIX, LAYOUT_HINT_EDITORIAL_4MIX


def apply_editorial_4mix_to_screen(
    screen: dict,
    assets_map: dict[str, dict],
    *,
    trip: dict | None = None,
    cfg: AppConfig | None = None,
    aspects: dict[str, AspectKind] | None = None,
) -> dict:
    pid = str(screen.get("patternId") or "")
    slots = screen.get("slots") or []
    asset_ids = [str(s.get("assetId") or "") for s in slots if s.get("assetId")]
    new_pid, new_hint = maybe_editorial_4mix(
        pid,
        asset_ids,
        assets_map,
        trip=trip,
        cfg=cfg,
        aspects=aspects,
    )
    if new_pid == pid:
        return screen
    ordered = chess_order_asset_ids(asset_ids, assets_map, aspects=aspects)
    if not ordered:
        return screen
    out = dict(screen)
    out["patternId"] = new_pid
    out["layoutHint"] = new_hint
    out["slots"] = build_4mix_slots(ordered, assets_map)
    return out


def default_replace_patterns() -> tuple[str, ...]:
    return (PATTERN_PORTRAIT_2_LANDSCAPE_2,)
