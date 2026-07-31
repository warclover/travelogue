"""Build screen dicts for mosaic patterns."""

from __future__ import annotations

from typing import TYPE_CHECKING

from travelogue.layout_contract.orientations import (
    AspectKind,
    aspect_kind_for_asset,
)
from travelogue.layout_contract.subject import asset_has_person, portrait_fit_for_asset
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_LANDSCAPE_3,
    PATTERN_LANDSCAPE_4,
    PATTERN_LANDSCAPE_6,
    PATTERN_LANDSCAPE_9,
    PATTERN_MOSAIC_4_2P2L_PORTRAIT_BOOKENDS,
    PATTERN_MOSAIC_5_1P4L_PORTRAIT_CENTER_RAILS,
    PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,
    PATTERN_MOSAIC_5_2P3L_PORTRAIT_HERO_RAIL,
    PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK,
    PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD,
    PATTERN_MOSAIC_5_3P_2L_BALANCED,
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    PATTERN_PORTRAIT_1_LANDSCAPE_2,
    PATTERN_PORTRAIT_2_LANDSCAPE_2,
    PATTERN_PORTRAIT_3,
    PATTERN_PORTRAIT_4,
    PATTERN_PORTRAIT_6,
    PATTERN_PORTRAIT_9,
    PATTERN_PORTRAIT_GRID_8,
)
from travelogue.layout_engine.mosaic.lte_adapter import read_templates_from_lte
from travelogue.layout_engine.mosaic.pattern_catalog import MosaicPattern
from travelogue.layout_engine.planner.screen_planner import (
    PERSON_LAYOUT_TRIPLE,
    _can_mixed_p1_l2,
    _can_mosaic_5_main_portrait_3land,
    _can_portrait_grid8_window,
    _is_landscape_id,
    _is_std_portrait_id,
    _make_mixed_portrait_landscape_screen,
    _make_mosaic_5_main_portrait_3land_screen,
    _make_portrait_grid8_screen,
    _make_screen,
    _pick_main_landscape_id,
    _sort_asset_ids_by_taken,
    _time_near_chain,
)

if TYPE_CHECKING:
    from travelogue.config.mosaic import MosaicConfig


def _portrait_fit(aid: str, assets_map: dict[str, dict]) -> str:
    return portrait_fit_for_asset(assets_map.get(aid), default="cover")


def _split_portrait_landscape(
    asset_ids: list[str], aspects: dict[str, AspectKind]
) -> tuple[list[str], list[str]]:
    portraits = [a for a in asset_ids if _is_std_portrait_id(a, aspects)]
    landscapes = [a for a in asset_ids if _is_landscape_id(a, aspects)]
    return portraits, landscapes


def _pick_solo_portrait_for_mosaic(
    portrait_ids: list[str],
    assets_map: dict[str, dict],
) -> str | None:
    """U-SOLO · prefer aesthetic solo score when choosing the portrait tile."""
    if not portrait_ids:
        return None
    if len(portrait_ids) == 1:
        return portrait_ids[0]
    from travelogue.layout_engine.scoring.solo import pick_solo_asset_id

    picked = pick_solo_asset_id(
        portrait_ids,
        assets_map,
        chapter_peer_ids=list(assets_map.keys()),
    )
    return picked or portrait_ids[0]


def _order_mixed_p1_l2(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    burst_seconds: float,
) -> list[str] | None:
    portraits, landscapes = _split_portrait_landscape(asset_ids, aspects)
    if len(portraits) < 1 or len(landscapes) < 2:
        return None
    non_person_portraits = [
        p for p in portraits if not asset_has_person(assets_map.get(p, {}))
    ]
    if not non_person_portraits:
        return None
    preferred = _pick_solo_portrait_for_mosaic(non_person_portraits, assets_map)
    portrait_order = [preferred] if preferred else []
    portrait_order.extend(p for p in non_person_portraits if p != preferred)
    for p_id in portrait_order:
        for pair in (
            landscapes[:2],
            landscapes[-2:],
            [landscapes[0], landscapes[-1]],
        ):
            if len(pair) < 2:
                continue
            if _can_mixed_p1_l2(
                p_id, pair, aspects, assets_map, burst_seconds=burst_seconds
            ):
                return [p_id, pair[0], pair[1]]
    # Soft MCS path: allow without strict time chain, but never pull a person
    # portrait into a wide mixed cell (the face would be cropped) — mirrors the
    # _can_mixed_p1_l2 person guard so the strict and soft paths agree.
    non_person_portraits = [
        p for p in portraits if not asset_has_person(assets_map.get(p, {}))
    ]
    if not non_person_portraits:
        return None
    p0 = _pick_solo_portrait_for_mosaic(
        _sort_asset_ids_by_taken(non_person_portraits, assets_map),
        assets_map,
    ) or _sort_asset_ids_by_taken(non_person_portraits, assets_map)[0]
    l_sorted = _sort_asset_ids_by_taken(landscapes, assets_map)
    return [p0, l_sorted[0], l_sorted[1]]


def _order_mixed_p2_l2(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    burst_seconds: float,
) -> list[str] | None:
    portraits, landscapes = _split_portrait_landscape(asset_ids, aspects)
    if len(portraits) < 2 or len(landscapes) < 2:
        return None
    p_sorted = _sort_asset_ids_by_taken(portraits, assets_map)[:2]
    l_sorted = _sort_asset_ids_by_taken(landscapes, assets_map)[:2]
    if any(asset_has_person(assets_map.get(aid, {})) for aid in p_sorted):
        return None
    orders = [
        [p_sorted[0], l_sorted[0], l_sorted[1], p_sorted[1]],
        [l_sorted[0], p_sorted[0], p_sorted[1], l_sorted[1]],
    ]
    for order in orders:
        if _time_near_chain(order, assets_map, burst_seconds=burst_seconds):
            return order
    return orders[0]


def _pick_strongest_portrait(
    portrait_ids: list[str],
    assets_map: dict[str, dict],
    *,
    median_sharp: float | None,
) -> str | None:
    if not portrait_ids:
        return None
    from travelogue.layout_engine.scoring.hero import effective_hero_score

    med = float(median_sharp or 0.0)

    def key(aid: str) -> tuple[float, float]:
        asset = assets_map.get(aid) or {}
        sharp = float((asset.get("quality") or {}).get("sharpness") or 0.0)
        hero = effective_hero_score(asset, median_sharp=med)
        return (sharp, hero)

    return max(portrait_ids, key=key)


def _order_1p4l_portrait_hero(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    median_sharp: float | None,
) -> list[str] | None:
    """MTSO · portrait main + 4 landscapes (takenAt order for rails)."""
    portraits, landscapes = _split_portrait_landscape(asset_ids, aspects)
    if len(portraits) != 1 or len(landscapes) < 4:
        return None
    main = portraits[0]
    rails = _sort_asset_ids_by_taken(landscapes, assets_map)[:4]
    if len(rails) < 4:
        return None
    return [main, rails[0], rails[1], rails[2], rails[3]]


def _order_1p4l_portrait_center_rails(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    median_sharp: float | None,
) -> list[str] | None:
    """Tri-col · center portrait main + L/R double landscape rails (takenAt)."""
    # Slot order: [center, LT, LB, RT, RB] — same id order as left-hero 1p4l.
    return _order_1p4l_portrait_hero(
        asset_ids, aspects, assets_map, median_sharp=median_sharp
    )


def _order_2p2l_portrait_bookends(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    median_sharp: float | None,
) -> list[str] | None:
    """Tri-col · left/right portraits + center stacked landscapes."""
    portraits, landscapes = _split_portrait_landscape(asset_ids, aspects)
    if len(portraits) < 2 or len(landscapes) < 2:
        return None
    p_sorted = _sort_asset_ids_by_taken(portraits, assets_map)[:2]
    l_sorted = _sort_asset_ids_by_taken(landscapes, assets_map)[:2]
    if len(p_sorted) < 2 or len(l_sorted) < 2:
        return None
    # Prefer stronger portrait on the left bookend when sharpness differs.
    left = _pick_strongest_portrait(
        p_sorted, assets_map, median_sharp=median_sharp
    ) or p_sorted[0]
    right = next(p for p in p_sorted if p != left)
    return [left, l_sorted[0], l_sorted[1], right]


def _order_2p3l_portrait_hero_rail(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    median_sharp: float | None,
) -> list[str] | None:
    """MTSO · strongest portrait main, second portrait aux, 3 landscape rails."""
    portraits, landscapes = _split_portrait_landscape(asset_ids, aspects)
    if len(portraits) < 2 or len(landscapes) < 3:
        return None
    main = _pick_strongest_portrait(
        portraits, assets_map, median_sharp=median_sharp
    )
    if not main:
        return None
    aux_pool = [p for p in portraits if p != main]
    aux = _sort_asset_ids_by_taken(aux_pool, assets_map)[0]
    rails = _sort_asset_ids_by_taken(landscapes, assets_map)[:3]
    if len(rails) < 3:
        return None
    return [main, aux, rails[0], rails[1], rails[2]]


def _order_3p2l_portrait_hero_quad(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    median_sharp: float | None,
) -> list[str] | None:
    """3P2L · strongest portrait main, 2 aux portraits, 2 landscape rails (quad)."""
    portraits, landscapes = _split_portrait_landscape(asset_ids, aspects)
    if len(portraits) < 3 or len(landscapes) < 2:
        return None
    main = _pick_strongest_portrait(
        portraits, assets_map, median_sharp=median_sharp
    )
    if not main:
        return None
    aux = _sort_asset_ids_by_taken([p for p in portraits if p != main], assets_map)[:2]
    rails = _sort_asset_ids_by_taken(landscapes, assets_map)[:2]
    if len(aux) < 2 or len(rails) < 2:
        return None
    return [main, aux[0], aux[1], rails[0], rails[1]]


def _order_3p2l_portrait_hero_lp_stack(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    median_sharp: float | None,
) -> list[str] | None:
    """3P2L · main + (L|P) × 2 stack: [main, l0, p0, l1, p1]."""
    portraits, landscapes = _split_portrait_landscape(asset_ids, aspects)
    if len(portraits) < 3 or len(landscapes) < 2:
        return None
    main = _pick_strongest_portrait(
        portraits, assets_map, median_sharp=median_sharp
    )
    if not main:
        return None
    tips = _sort_asset_ids_by_taken([p for p in portraits if p != main], assets_map)[:2]
    rails = _sort_asset_ids_by_taken(landscapes, assets_map)[:2]
    if len(tips) < 2 or len(rails) < 2:
        return None
    return [main, rails[0], tips[0], rails[1], tips[1]]


def _order_hero_six_detailed(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    median_sharp: float | None,
    cfg: "MosaicConfig | None" = None,
) -> tuple[list[str] | None, str]:
    """Order six-hero window; return (order, reason). D-MTSO-10 stable reject codes."""
    from travelogue.layout_engine.mosaic.main_eligibility import (
        main_ar_guard_enabled,
        pick_best_main_eligible,
    )
    from travelogue.layout_engine.mosaic.runtime import get_effective_mosaic_config

    portraits, landscapes = _split_portrait_landscape(asset_ids, aspects)
    if len(portraits) >= 2:
        return None, "six_hero_portrait_overflow"
    if len(landscapes) < 4:
        return None, "six_hero_insufficient_landscape"
    eff = cfg if cfg is not None else get_effective_mosaic_config()
    if main_ar_guard_enabled(eff):
        main = pick_best_main_eligible(
            landscapes,
            assets_map,
            pattern_id=PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
            median_sharp=median_sharp,
            cfg=eff,
        )
        if not main:
            return None, "six_hero_no_main"
    else:
        main = _pick_main_landscape_id(landscapes, assets_map, median_sharp=median_sharp)
        if not main:
            return None, "six_hero_no_main"
    bottom_pool = _sort_asset_ids_by_taken(
        [a for a in landscapes if a != main], assets_map
    )
    if len(bottom_pool) < 3:
        return None, "six_hero_insufficient_landscape"
    bottom = bottom_pool[:3]
    side: list[str] = _sort_asset_ids_by_taken(portraits, assets_map)[:1]
    side_candidates = _sort_asset_ids_by_taken(
        [a for a in landscapes if a not in {main, *bottom}], assets_map
    )
    for aid in side_candidates:
        if len(side) >= 2:
            break
        side.append(aid)
    if len(side) < 2:
        return None, "six_hero_insufficient_landscape"
    return [main, side[0], side[1], bottom[0], bottom[1], bottom[2]], ""


def _order_hero_six(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    median_sharp: float | None,
) -> list[str] | None:
    """Main 2×2 landscape + 2 side tiles (at most 1 portrait) + 3 bottom landscapes."""
    ordered, _reason = _order_hero_six_detailed(
        asset_ids, aspects, assets_map, median_sharp=median_sharp
    )
    return ordered


def _order_by_roles(
    pattern_id: str,
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
) -> list[str] | None:
    from travelogue.layout_engine.mosaic.lte_adapter import mosaic_registry
    from travelogue.layout_templates.legacy_bridge import export_mosaic_pattern
    from travelogue.layout_templates.registry import get_engine

    pat = mosaic_registry().get(pattern_id)
    if pat is None:
        # Ordering helper: experimental SKUs may be absent from the emit registry
        # until mosaic.template_experiments admits them.
        try:
            pat = export_mosaic_pattern(get_engine().get(pattern_id))
        except KeyError:
            return None
    if pat is None or len(pat.roles) != len(asset_ids):
        return None
    portraits = _sort_asset_ids_by_taken(
        [a for a in asset_ids if not _is_landscape_id(a, aspects)],
        assets_map,
    )
    landscapes = _sort_asset_ids_by_taken(
        [a for a in asset_ids if _is_landscape_id(a, aspects)],
        assets_map,
    )
    pools: dict[str, list[str]] = {
        "portrait": portraits,
        "landscape": landscapes,
        "main": landscapes,
        "tile": portraits,
    }
    used: set[str] = set()
    ordered: list[str] = []
    for role in pat.roles:
        pool = pools.get(role)
        if not pool:
            return None
        picked = next((aid for aid in pool if aid not in used), None)
        if picked is None:
            return None
        used.add(picked)
        ordered.append(picked)
    return ordered


def _finalize_mosaic_screen(
    screen: dict,
    pattern_id: str,
    assets_map: dict[str, dict] | None = None,
) -> dict:
    if read_templates_from_lte():
        from travelogue.layout_templates.geometry_solidify import solidify_screen_geometry

        solidify_screen_geometry(screen, pattern_id, assets_map=assets_map)
        from travelogue.layout_engine.mosaic.msa_apply import maybe_apply_slot_adaptation

        maybe_apply_slot_adaptation(screen, pattern_id, assets_map=assets_map)
    return screen


def try_order_for_pattern(
    pattern_id: str,
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    burst_seconds: float,
    median_sharp: float | None,
) -> list[str] | None:
    n = len(asset_ids)
    portraits, landscapes = _split_portrait_landscape(asset_ids, aspects)

    if pattern_id == PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND:
        return _can_mosaic_5_main_portrait_3land(
            asset_ids,
            aspects,
            assets_map,
            burst_seconds=burst_seconds,
            median_sharp=median_sharp,
        )

    if n == 3:
        if pattern_id == PATTERN_PORTRAIT_3 and len(portraits) >= 3:
            return _sort_asset_ids_by_taken(portraits[:3], assets_map)
        if pattern_id == PATTERN_LANDSCAPE_3 and len(landscapes) >= 3:
            return _sort_asset_ids_by_taken(landscapes[:3], assets_map)
        if pattern_id == PATTERN_PORTRAIT_1_LANDSCAPE_2:
            return _order_mixed_p1_l2(
                asset_ids, aspects, assets_map, burst_seconds=burst_seconds
            )
        # else: fall through to role-based order (TPC AC-TPC-02)

    if n == 4:
        if pattern_id == PATTERN_PORTRAIT_2_LANDSCAPE_2:
            return _order_mixed_p2_l2(
                asset_ids, aspects, assets_map, burst_seconds=burst_seconds
            )
        if pattern_id == PATTERN_MOSAIC_4_2P2L_PORTRAIT_BOOKENDS:
            return _order_2p2l_portrait_bookends(
                asset_ids, aspects, assets_map, median_sharp=median_sharp
            )
        if pattern_id == PATTERN_PORTRAIT_4 and len(portraits) >= 4:
            return _sort_asset_ids_by_taken(portraits[:4], assets_map)
        if pattern_id == PATTERN_LANDSCAPE_4 and len(landscapes) >= 4:
            return _sort_asset_ids_by_taken(landscapes[:4], assets_map)
        # else: fall through to role-based order (TPC W3 new SKUs)

    if n == 5:
        if pattern_id == PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO:
            return _order_1p4l_portrait_hero(
                asset_ids, aspects, assets_map, median_sharp=median_sharp
            )
        if pattern_id == PATTERN_MOSAIC_5_1P4L_PORTRAIT_CENTER_RAILS:
            return _order_1p4l_portrait_center_rails(
                asset_ids, aspects, assets_map, median_sharp=median_sharp
            )
        if pattern_id == PATTERN_MOSAIC_5_2P3L_PORTRAIT_HERO_RAIL:
            return _order_2p3l_portrait_hero_rail(
                asset_ids, aspects, assets_map, median_sharp=median_sharp
            )
        if pattern_id == PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD:
            return _order_3p2l_portrait_hero_quad(
                asset_ids, aspects, assets_map, median_sharp=median_sharp
            )
        if pattern_id == PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK:
            return _order_3p2l_portrait_hero_lp_stack(
                asset_ids, aspects, assets_map, median_sharp=median_sharp
            )
        if pattern_id == PATTERN_MOSAIC_5_3P_2L_BALANCED:
            if len(portraits) < 3 or len(landscapes) < 2:
                return None
            p_sorted = _sort_asset_ids_by_taken(portraits[:3], assets_map)
            l_sorted = _sort_asset_ids_by_taken(landscapes[:2], assets_map)
            return [p_sorted[0], p_sorted[1], p_sorted[2], l_sorted[0], l_sorted[1]]

    if n == 6:
        if pattern_id in (PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5, PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4):
            return _order_hero_six(
                asset_ids, aspects, assets_map, median_sharp=median_sharp
            )
        if pattern_id == PATTERN_PORTRAIT_6 and len(portraits) >= 6:
            return _sort_asset_ids_by_taken(portraits[:6], assets_map)
        if pattern_id == PATTERN_LANDSCAPE_6 and len(landscapes) >= 6:
            return _sort_asset_ids_by_taken(landscapes[:6], assets_map)
        # else: fall through to role-based order

    if n == 8:
        if pattern_id == PATTERN_PORTRAIT_GRID_8:
            if _can_portrait_grid8_window(
                asset_ids, aspects, assets_map, burst_seconds=burst_seconds
            ):
                return _sort_asset_ids_by_taken(portraits[:8], assets_map)
            return None
        # else: fall through

    if n == 9:
        if pattern_id == PATTERN_PORTRAIT_9 and len(portraits) >= 9:
            return _sort_asset_ids_by_taken(portraits[:9], assets_map)
        if pattern_id == PATTERN_LANDSCAPE_9 and len(landscapes) >= 9:
            return _sort_asset_ids_by_taken(landscapes[:9], assets_map)
        # else: fall through

    role_order = _order_by_roles(pattern_id, asset_ids, aspects, assets_map)
    if role_order:
        return role_order
    return None


def build_screen(
    pattern: MosaicPattern,
    ordered_ids: list[str],
    *,
    assets_map: dict[str, dict],
    screen_id: str = "",
    trip: dict | None = None,
    cfg=None,
) -> dict:
    if pattern.pattern_id == PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND:
        return _finalize_mosaic_screen(
            _make_mosaic_5_main_portrait_3land_screen(
                ordered_ids, screen_id=screen_id, assets_map=assets_map
            ),
            pattern.pattern_id,
            assets_map,
        )
    if pattern.pattern_id == PATTERN_PORTRAIT_1_LANDSCAPE_2:
        return _finalize_mosaic_screen(
            _make_mixed_portrait_landscape_screen(
                ordered_ids[0],
                ordered_ids[1:3],
                screen_id=screen_id,
                assets_map=assets_map,
            ),
            pattern.pattern_id,
            assets_map,
        )
    if pattern.pattern_id == PATTERN_PORTRAIT_2_LANDSCAPE_2:
        slots = []
        for idx, aid in enumerate(ordered_ids):
            kind = aspect_kind_for_asset(assets_map.get(aid, {}))
            role = (
                "portrait"
                if _is_std_portrait_id(aid, {aid: kind})
                else "landscape"
            )
            fit = _portrait_fit(aid, assets_map) if role == "portrait" else "cover"
            slots.append({"assetId": aid, "slot": idx, "fit": fit, "role": role})
        screen = _make_screen(
            PATTERN_PORTRAIT_2_LANDSCAPE_2,
            screen_id=screen_id,
            slots=slots,
        )
        from travelogue.layout_engine.editorial.four_mix import apply_editorial_4mix_to_screen

        screen = apply_editorial_4mix_to_screen(
            screen, assets_map, trip=trip, cfg=cfg
        )
        return _finalize_mosaic_screen(
            screen,
            str(screen.get("patternId") or pattern.pattern_id),
            assets_map,
        )
    if pattern.pattern_id == PATTERN_PORTRAIT_GRID_8:
        return _finalize_mosaic_screen(
            _make_portrait_grid8_screen(
                ordered_ids, screen_id=screen_id, assets_map=assets_map
            ),
            pattern.pattern_id,
            assets_map,
        )
    if pattern.pattern_id in (
        PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
        PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    ):
        slots = []
        for idx, aid in enumerate(ordered_ids):
            kind = aspect_kind_for_asset(assets_map.get(aid, {}))
            slot_aspects = {aid: kind}
            if idx == 0:
                role = "main"
            elif idx in (1, 2):
                role = (
                    "portrait"
                    if _is_std_portrait_id(aid, slot_aspects)
                    else "landscape"
                )
            else:
                role = "landscape"
            fit = _portrait_fit(aid, assets_map) if role == "portrait" else "cover"
            slots.append({"assetId": aid, "slot": idx, "fit": fit, "role": role})
        return _finalize_mosaic_screen(
            _make_screen(pattern.pattern_id, screen_id=screen_id, slots=slots),
            pattern.pattern_id,
            assets_map,
        )
    roles = pattern.roles
    slots = []
    from travelogue.layout_engine.mosaic.lte_adapter import resolve_slot_fit

    for idx, (aid, role) in enumerate(zip(ordered_ids, roles, strict=True)):
        fit = resolve_slot_fit(
            pattern.pattern_id,
            idx,
            role,
            assets_map.get(aid, {}),
        )
        slots.append({"assetId": aid, "slot": idx, "fit": fit, "role": role})
    screen = _make_screen(pattern.pattern_id, screen_id=screen_id, slots=slots)
    # Preserve the person-triple semantic when the MCS unified planner emits a
    # portrait-3 window for an all-person run (the legacy person-aware path sets
    # this hint; the MCS path must match so CSS/render treat it the same).
    if pattern.pattern_id == PATTERN_PORTRAIT_3 and ordered_ids and all(
        asset_has_person(assets_map.get(aid, {})) for aid in ordered_ids
    ):
        screen["layoutHint"] = PERSON_LAYOUT_TRIPLE
    from travelogue.layout_engine.editorial.portrait_row import (
        apply_editorial_portrait_row_to_screen,
    )

    screen = apply_editorial_portrait_row_to_screen(
        screen, assets_map, trip=trip, cfg=cfg
    )
    from travelogue.layout_engine.editorial.four_mix import apply_editorial_4mix_to_screen

    screen = apply_editorial_4mix_to_screen(
        screen, assets_map, trip=trip, cfg=cfg
    )
    final_pid = str(screen.get("patternId") or pattern.pattern_id)
    return _finalize_mosaic_screen(screen, final_pid, assets_map)
