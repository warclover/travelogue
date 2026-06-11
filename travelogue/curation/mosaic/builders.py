"""Build screen dicts for mosaic patterns."""

from __future__ import annotations

from travelogue.curation.asset_subject import asset_has_person, portrait_fit_for_asset
from travelogue.curation.layout_planner import AspectKind, aspect_kind_for_asset
from travelogue.curation.mosaic.constants import PATTERN_PORTRAIT_3
from travelogue.curation.mosaic.lte_adapter import (
    read_templates_from_lte,
    template_is_justified,
    template_matches_mix,
    template_mix_requirements,
    template_uses_main_hero_ordering,
    template_uses_main_hero_tile_scoring,
    template_uses_main_portrait_3land_layout,
    template_uses_mixed_p1_l2_layout,
    template_uses_mixed_p2_l2_layout,
    template_uses_portrait_grid8_layout,
)
from travelogue.curation.mosaic.pattern_catalog import MosaicPattern
from travelogue.curation.screen_planner import (
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
    from travelogue.curation.solo_scoring import pick_solo_asset_id

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


def _order_hero_six(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    pattern_id: str,
    median_sharp: float | None,
) -> list[str] | None:
    """Main 2×2 landscape + 2 side tiles (prefer portrait) + 3 bottom landscapes."""
    from travelogue.curation.mosaic.main_eligibility import (
        main_ar_guard_enabled,
        pick_best_main_eligible,
    )
    from travelogue.curation.mosaic.runtime import get_effective_mosaic_config

    portraits, landscapes = _split_portrait_landscape(asset_ids, aspects)
    if len(landscapes) < 4:
        return None
    cfg = get_effective_mosaic_config()
    if main_ar_guard_enabled(cfg):
        main = pick_best_main_eligible(
            landscapes,
            assets_map,
            pattern_id=pattern_id,
            median_sharp=median_sharp,
            cfg=cfg,
        )
        if not main:
            return None
    else:
        main = _pick_main_landscape_id(landscapes, assets_map, median_sharp=median_sharp)
    bottom_pool = _sort_asset_ids_by_taken(
        [a for a in landscapes if a != main], assets_map
    )
    if len(bottom_pool) < 3:
        return None
    bottom = bottom_pool[:3]
    side: list[str] = _sort_asset_ids_by_taken(portraits, assets_map)[:2]
    side_candidates = _sort_asset_ids_by_taken(
        [a for a in landscapes if a not in {main, *bottom}], assets_map
    )
    for aid in side_candidates:
        if len(side) >= 2:
            break
        side.append(aid)
    if len(side) < 2:
        return None
    return [main, side[0], side[1], bottom[0], bottom[1], bottom[2]]


def _order_by_roles(
    pattern_id: str,
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
) -> list[str] | None:
    from travelogue.curation.mosaic.lte_adapter import mosaic_registry

    pat = mosaic_registry().get(pattern_id)
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

    if template_is_justified(pattern_id):
        from travelogue.curation.layout.justified_row import can_use_justified_row

        if not can_use_justified_row(asset_ids, aspects):
            return None
        from travelogue.curation.screen_planner import _sort_asset_ids_by_taken

        portraits = [a for a in asset_ids if _is_std_portrait_id(a, aspects)]
        ordered = _sort_asset_ids_by_taken(portraits, assets_map)
        return ordered if len(ordered) == len(asset_ids) else None

    if template_uses_main_portrait_3land_layout(pattern_id):
        return _can_mosaic_5_main_portrait_3land(
            asset_ids,
            aspects,
            assets_map,
            burst_seconds=burst_seconds,
            median_sharp=median_sharp,
        )

    if n == 3:
        if template_matches_mix(pattern_id, 3, 0) and len(portraits) >= 3:
            return _sort_asset_ids_by_taken(portraits[:3], assets_map)
        if template_matches_mix(pattern_id, 0, 3) and len(landscapes) >= 3:
            return _sort_asset_ids_by_taken(landscapes[:3], assets_map)
        if template_uses_mixed_p1_l2_layout(pattern_id):
            return _order_mixed_p1_l2(
                asset_ids, aspects, assets_map, burst_seconds=burst_seconds
            )
        return None

    if n == 4:
        if template_uses_mixed_p2_l2_layout(pattern_id):
            return _order_mixed_p2_l2(
                asset_ids, aspects, assets_map, burst_seconds=burst_seconds
            )
        if template_matches_mix(pattern_id, 4, 0) and len(portraits) >= 4:
            return _sort_asset_ids_by_taken(portraits[:4], assets_map)
        if template_matches_mix(pattern_id, 0, 4) and len(landscapes) >= 4:
            return _sort_asset_ids_by_taken(landscapes[:4], assets_map)
        return None

    if n == 5:
        mix_p, mix_l = template_mix_requirements(pattern_id)
        if mix_p == 3 and mix_l == 2:
            if len(portraits) < 3 or len(landscapes) < 2:
                return None
            p_sorted = _sort_asset_ids_by_taken(portraits[:3], assets_map)
            l_sorted = _sort_asset_ids_by_taken(landscapes[:2], assets_map)
            return [p_sorted[0], p_sorted[1], p_sorted[2], l_sorted[0], l_sorted[1]]

    if n == 6:
        if template_uses_main_hero_ordering(pattern_id):
            return _order_hero_six(
                asset_ids,
                aspects,
                assets_map,
                pattern_id=pattern_id,
                median_sharp=median_sharp,
            )
        if template_matches_mix(pattern_id, 6, 0) and len(portraits) >= 6:
            return _sort_asset_ids_by_taken(portraits[:6], assets_map)
        if template_matches_mix(pattern_id, 0, 6) and len(landscapes) >= 6:
            return _sort_asset_ids_by_taken(landscapes[:6], assets_map)
        return None

    if n == 8:
        if template_uses_portrait_grid8_layout(pattern_id):
            if _can_portrait_grid8_window(
                asset_ids, aspects, assets_map, burst_seconds=burst_seconds
            ):
                return _sort_asset_ids_by_taken(portraits[:8], assets_map)
        return None

    if n == 9:
        if template_matches_mix(pattern_id, 9, 0) and len(portraits) >= 9:
            return _sort_asset_ids_by_taken(portraits[:9], assets_map)
        if template_matches_mix(pattern_id, 0, 9) and len(landscapes) >= 9:
            return _sort_asset_ids_by_taken(landscapes[:9], assets_map)
        return None

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
) -> dict:
    if template_is_justified(pattern.pattern_id):
        from travelogue.curation.layout.justified_row import build_justified_screen

        return _finalize_mosaic_screen(
            build_justified_screen(
                pattern.pattern_id,
                ordered_ids,
                assets_map,
                screen_id=screen_id,
            ),
            pattern.pattern_id,
            assets_map,
        )
    if template_uses_main_portrait_3land_layout(pattern.pattern_id):
        return _finalize_mosaic_screen(
            _make_mosaic_5_main_portrait_3land_screen(
                ordered_ids, screen_id=screen_id, assets_map=assets_map
            ),
            pattern.pattern_id,
            assets_map,
        )
    if template_uses_mixed_p1_l2_layout(pattern.pattern_id):
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
    if template_uses_mixed_p2_l2_layout(pattern.pattern_id):
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
        return _finalize_mosaic_screen(
            _make_screen(pattern.pattern_id, screen_id=screen_id, slots=slots),
            pattern.pattern_id,
            assets_map,
        )
    if template_uses_portrait_grid8_layout(pattern.pattern_id):
        return _finalize_mosaic_screen(
            _make_portrait_grid8_screen(
                ordered_ids, screen_id=screen_id, assets_map=assets_map
            ),
            pattern.pattern_id,
            assets_map,
        )
    if template_uses_main_hero_tile_scoring(pattern.pattern_id):
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
    from travelogue.curation.mosaic.lte_adapter import resolve_slot_fit

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
    return _finalize_mosaic_screen(screen, pattern.pattern_id, assets_map)
