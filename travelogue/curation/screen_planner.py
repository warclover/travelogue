"""
Web screens layout engine (layoutEngine=screens).

See docs/web端模板.prd and docs/web端模板升级计划.md.
"""

from __future__ import annotations

from typing import Literal

from travelogue.config import AppConfig
from travelogue.curation.aspect_buckets import prefix_same_bucket
from travelogue.curation.asset_subject import (
    any_asset_has_person,
    asset_has_person,
    portrait_fit_for_asset,
)
from travelogue.curation.collage_routing import single_asset_screen_pattern
from travelogue.curation.layout_planner import (
    _effective_profile,
    _is_std_landscape,
    _is_std_portrait,
)
from travelogue.curation.screen_layout_state import (  # noqa: F401 — re-exported API
    MAX_PORTRAIT_PAIR_STREAK,
    ScreenLayoutPlannerState,
    is_nine_grid_pattern,
    is_portrait_single_pattern,
    is_six_grid_pattern,
    is_triple_row_pattern,
    layout_kind_from_pattern,
    nine_grid_limits_for_trip,
    pattern_slot_count,
    portrait_grid8_allowed,
)
from travelogue.media.image_ops import AspectKind

LayoutEngine = Literal["legacy", "screens"]
LayoutFit = Literal["cover", "contain"]
SlotRole = Literal["portrait", "landscape", "main"]

LAYOUT_ENGINE_LEGACY: LayoutEngine = "legacy"
LAYOUT_ENGINE_SCREENS: LayoutEngine = "screens"
LAYOUT_ENGINE_VERSION_SCREENS = "screens-2"
MAX_SLOTS_PER_SCREEN = 9
MIN_TRIP_PHOTOS_FOR_MOSAIC = 35
DEFAULT_FEATURED_WEIGHT = 1.35

PATTERN_PORTRAIT_1_LANDSCAPE_2 = "screen-portrait-1-landscape-2"
PATTERN_PORTRAIT_2_LANDSCAPE_2 = "screen-portrait-2-landscape-2"
PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND = "screen-mosaic-5-main-portrait-3land"
PATTERN_PORTRAIT_GRID_8 = "screen-portrait-grid-8"
PERSON_LAYOUT_GRID_8 = "person-grid-8"
FOOD_GRID_LAYOUT_HINT = "food-grid"
_MUNDANE_GRID_LAYOUT_HINTS: dict[str, str] = {
    "food": FOOD_GRID_LAYOUT_HINT,
    "sign": "sign-grid",
    "ticket": "ticket-grid",
    "shop": "shop-grid",
}

_GRID_SIZES = (9, 6, 4, 3, 2, 1)

PATTERN_GRID_CLASS: dict[str, str] = {
    "screen-portrait-1": "layout-screen__grid--1col",
    "screen-portrait-2": "layout-screen__grid--2col",
    "screen-portrait-3": "layout-screen__grid--3col",
    "screen-portrait-4": "layout-screen__grid--2x2",
    "screen-portrait-6": "layout-screen__grid--3x2",
    "screen-portrait-9": "layout-screen__grid--3x3",
    PATTERN_PORTRAIT_GRID_8: "layout-screen__grid--portrait-2x4",
    PATTERN_PORTRAIT_1_LANDSCAPE_2: "layout-screen__grid--portrait-left-2landscape",
    PATTERN_PORTRAIT_2_LANDSCAPE_2: "layout-screen__grid--2x2",
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND: "layout-screen__grid--mosaic-5-main-portrait-3land",
    "screen-mosaic-5-2p3l-equal": "layout-screen__grid--mosaic-5-2p3l-equal",
    "screen-mosaic-5-hero-3-2-plus-4": "layout-screen__grid--mosaic-5-hero-3-2-plus-4",
    "screen-mosaic-5-main-landscape-2portrait-2land": "layout-screen__grid--mosaic-5-main-landscape-2portrait-2land",
    "screen-mosaic-5-2portrait-3land-balanced": "layout-screen__grid--mosaic-5-2portrait-3land-balanced",
    "screen-mosaic-5-3portrait-2land-balanced": "layout-screen__grid--mosaic-5-3portrait-2land-balanced",
    "screen-mosaic-5-main-hero-plus-4": "layout-screen__grid--mosaic-5-main-hero-plus-4",
    "screen-mosaic-6-main-hero-plus-5": "layout-screen__grid--mosaic-6-main-hero-plus-5",
    "screen-landscape-1": "layout-screen__grid--1col",
    "screen-landscape-2": "layout-screen__grid--landscape-stack-2",
    "screen-landscape-3": "layout-screen__grid--landscape-stack-3",
    "screen-landscape-4": "layout-screen__grid--2x2",
    "screen-landscape-6": "layout-screen__grid--3x2",
    "screen-landscape-9": "layout-screen__grid--3x3",
    "screen-square-1": "layout-screen__grid--1col",
    "screen-square-2": "layout-screen__grid--2col",
    "screen-square-3": "layout-screen__grid--3col",
    "screen-square-4": "layout-screen__grid--2x2",
    "screen-square-6": "layout-screen__grid--3x2",
    "screen-square-9": "layout-screen__grid--3x3",
    "screen-panorama-1": "layout-screen__grid--1col",
    "screen-tall-1": "layout-screen__grid--1col",
    "screen-full-frame": "layout-screen__grid--1col",
    "screen-plate": "layout-screen__grid--1col",
    "screen-spread": "layout-screen__grid--1col",
}

# Multi-column grids in 16:9 create portrait-shaped slots — only for portrait family.
_LANDSCAPE_GRID_SIZES = (9, 6, 4)
_PORTRAIT_COLUMN_GRID_SIZES = (9, 6, 3, 2, 1)


def grid_class_for_pattern(pattern_id: str) -> str:
    return PATTERN_GRID_CLASS.get(pattern_id, "layout-screen__grid--1col")


def resolve_layout_engine(trip: dict, *, override: str | None = None) -> LayoutEngine:
    raw = override or trip.get("layoutEngine") or LAYOUT_ENGINE_LEGACY
    if raw not in (LAYOUT_ENGINE_LEGACY, LAYOUT_ENGINE_SCREENS):
        return LAYOUT_ENGINE_LEGACY
    return raw  # type: ignore[return-value]


def screens_layout_active(trip: dict, *, override: str | None = None) -> bool:
    if resolve_layout_engine(trip, override=override) != LAYOUT_ENGINE_SCREENS:
        return False
    export_layout = trip.get("exportLayout", "auto")
    if export_layout == "auto":
        return True
    return _effective_profile(export_layout) == "web"  # type: ignore[arg-type]


def _fits_for_screen(
    pattern_id: str,
    asset_ids: list[str],
    *,
    assets_map: dict[str, dict] | None = None,
    fits_override: list[LayoutFit] | None = None,
) -> list[LayoutFit]:
    if fits_override is not None:
        return list(fits_override)
    assets_map = assets_map or {}
    n = len(asset_ids)
    if pattern_id in ("screen-panorama-1", "screen-plate"):
        return ["cover"] * n
    if pattern_id in ("screen-tall-1", "screen-square-1"):
        return ["contain"] * n
    if pattern_id == "screen-full-frame":
        from travelogue.curation.asset_subject import full_frame_fit_for_asset

        return [
            full_frame_fit_for_asset(assets_map.get(aid), default="cover")
            for aid in asset_ids
        ]
    if pattern_id == "screen-portrait-1":
        # Single full-screen portrait: the container is portrait-aspect, so cover
        # fills edge-to-edge with negligible cropping. Person/face shots still use
        # contain so faces are never cropped (face safety wins over full-bleed),
        # which also keeps person portraits face-safe when a hero-first plan
        # strands one as a trailing single rather than a multi-portrait grid.
        return [
            portrait_fit_for_asset(assets_map.get(aid), default="cover")
            for aid in asset_ids
        ]
    if pattern_id in (
        "screen-portrait-2",
        "screen-portrait-3",
        PATTERN_PORTRAIT_GRID_8,
    ):
        return [
            portrait_fit_for_asset(assets_map.get(aid), default="cover")
            for aid in asset_ids
        ]
    if pattern_id == PATTERN_PORTRAIT_1_LANDSCAPE_2:
        fits: list[LayoutFit] = []
        for idx, aid in enumerate(asset_ids):
            if idx == 0:
                fits.append(portrait_fit_for_asset(assets_map.get(aid), default="cover"))
            else:
                fits.append("cover")
        return fits
    if pattern_id == PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND:
        fits: list[LayoutFit] = []
        for idx, aid in enumerate(asset_ids):
            if idx == 1:
                fits.append(portrait_fit_for_asset(assets_map.get(aid), default="cover"))
            else:
                fits.append("cover")
        return fits
    if pattern_id.startswith("screen-mosaic-5-"):
        fits_m: list[LayoutFit] = []
        for aid in asset_ids:
            role_portrait = portrait_fit_for_asset(assets_map.get(aid), default="cover")
            fits_m.append(role_portrait)
        return fits_m
    return ["cover"] * n


def _pattern_family(pattern_id: str) -> str:
    if pattern_id.startswith("screen-portrait"):
        return "portrait"
    if pattern_id.startswith("screen-landscape"):
        return "landscape"
    if pattern_id.startswith("screen-square"):
        return "square"
    if pattern_id.startswith("screen-panorama"):
        return "panorama"
    if pattern_id.startswith("screen-tall"):
        return "tall"
    return "landscape"


def _slot_allowed_in_pattern(aid: str, pattern_id: str, aspects: dict[str, AspectKind]) -> bool:
    kind = aspects.get(aid, "square")
    fam = _pattern_family(pattern_id)
    if fam == "portrait":
        return kind in ("portrait", "tall")
    if fam == "landscape":
        return kind in ("landscape", "panorama", "square")
    if fam == "panorama":
        return kind == "panorama"
    if fam == "tall":
        return kind == "tall"
    if fam == "square":
        return kind == "square"
    return True


def _filter_ids_for_pattern(
    asset_ids: list[str],
    pattern_id: str,
    aspects: dict[str, AspectKind],
) -> list[str]:
    return [aid for aid in asset_ids if _slot_allowed_in_pattern(aid, pattern_id, aspects)]


def _make_screen(
    pattern_id: str,
    asset_ids: list[str] | None = None,
    *,
    screen_id: str,
    slots: list[dict] | None = None,
    fits: list[LayoutFit] | None = None,
    tone: dict | None = None,
    aspects: dict[str, AspectKind] | None = None,
    assets_map: dict[str, dict] | None = None,
) -> dict:
    if slots is None and asset_ids and len(asset_ids) == 1:
        pattern_id = single_asset_screen_pattern(
            pattern_id,
            asset_ids[0],
            assets_map,
        )
    if slots is None:
        ids = list(asset_ids or [])
        if aspects is not None:
            ids = _filter_ids_for_pattern(ids, pattern_id, aspects)
        fit_list = _fits_for_screen(
            pattern_id,
            ids,
            assets_map=assets_map,
            fits_override=fits,
        )
        slots = []
        for idx, aid in enumerate(ids):
            fit: LayoutFit = fit_list[idx] if idx < len(fit_list) else fit_list[-1]
            slots.append({"assetId": aid, "slot": idx, "fit": fit})
    return {
        "screenId": screen_id,
        "patternId": pattern_id,
        "tone": tone,
        "slots": slots,
    }


def _pick_main_landscape_id(
    landscape_ids: list[str],
    assets_map: dict[str, dict],
    *,
    median_sharp: float | None = None,
    featured_weight: float = DEFAULT_FEATURED_WEIGHT,
    aesthetic_enabled: bool | None = None,
) -> str:
    from travelogue.curation.asset_quality import asset_sharpness
    from travelogue.curation.curate_scoring import effective_hero_score, median_sharpness

    med = (
        median_sharp
        if median_sharp is not None
        else median_sharpness(list(assets_map.values()))
    )
    return max(
        landscape_ids,
        key=lambda aid: (
            effective_hero_score(
                assets_map.get(aid) or {},
                median_sharp=med,
                featured_weight=featured_weight,
                aesthetic_enabled=aesthetic_enabled,
            ),
            asset_sharpness(assets_map.get(aid) or {}),
        ),
    )


def _can_mosaic_5_main_portrait_3land(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets: dict[str, dict],
    *,
    burst_seconds: float,
    median_sharp: float | None = None,
) -> list[str] | None:
    """
    Five-photo mosaic: 1 main landscape (top-left), 1 portrait (top-right),
    3 landscapes (bottom row). Returns slot order or None.
    """
    if len(asset_ids) != 5:
        return None
    portraits = [a for a in asset_ids if _is_std_portrait_id(a, aspects)]
    landscapes = [a for a in asset_ids if _is_landscape_id(a, aspects)]
    if len(portraits) != 1 or len(landscapes) != 4:
        return None
    if not _time_near_chain(asset_ids, assets, burst_seconds=burst_seconds):
        return None
    from travelogue.curation.mosaic.main_eligibility import (
        main_ar_guard_enabled,
        pick_best_main_eligible,
    )
    from travelogue.curation.mosaic.runtime import get_effective_mosaic_config

    cfg = get_effective_mosaic_config()
    if main_ar_guard_enabled(cfg):
        main = pick_best_main_eligible(
            landscapes,
            assets,
            pattern_id=PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
            median_sharp=median_sharp,
            cfg=cfg,
        )
        if not main:
            return None
    else:
        main = _pick_main_landscape_id(landscapes, assets, median_sharp=median_sharp)
    bottom = _sort_asset_ids_by_taken([a for a in landscapes if a != main], assets)
    return [main, portraits[0], bottom[0], bottom[1], bottom[2]]


def _make_mosaic_5_main_portrait_3land_screen(
    ordered_ids: list[str],
    *,
    screen_id: str = "",
    assets_map: dict[str, dict] | None = None,
) -> dict:
    assets_map = assets_map or {}
    main_id, portrait_id, b1, b2, b3 = ordered_ids
    p_fit = portrait_fit_for_asset(assets_map.get(portrait_id), default="cover")
    return _make_screen(
        PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
        screen_id=screen_id,
        slots=[
            {"assetId": main_id, "slot": 0, "fit": "cover", "role": "main"},
            {"assetId": portrait_id, "slot": 1, "fit": p_fit, "role": "portrait"},
            {"assetId": b1, "slot": 2, "fit": "cover", "role": "landscape"},
            {"assetId": b2, "slot": 3, "fit": "cover", "role": "landscape"},
            {"assetId": b3, "slot": 4, "fit": "cover", "role": "landscape"},
        ],
    )


def _time_near_sequential(
    asset_ids: list[str],
    assets: dict[str, dict],
    *,
    burst_seconds: float,
) -> bool:
    stamps = [_parse_taken_ts(assets.get(aid, {})) for aid in asset_ids]
    known = [(i, t) for i, t in enumerate(stamps) if t is not None]
    if len(known) < 2:
        return True
    for (_, t0), (_, t1) in zip(known, known[1:]):
        if abs(t1 - t0) > burst_seconds:
            return False
    return True


def _can_portrait_grid8_window(
    portrait_ids: list[str],
    aspects: dict[str, AspectKind],
    assets: dict[str, dict],
    *,
    burst_seconds: float,
) -> bool:
    if len(portrait_ids) != 8:
        return False
    if not all(_is_std_portrait_id(aid, aspects) for aid in portrait_ids):
        return False
    return _time_near_sequential(portrait_ids, assets, burst_seconds=burst_seconds)


def _make_portrait_grid8_screen(
    portrait_ids: list[str],
    *,
    screen_id: str = "",
    assets_map: dict[str, dict] | None = None,
) -> dict:
    assets_map = assets_map or {}
    slots = [
        {
            "assetId": aid,
            "slot": idx,
            "fit": portrait_fit_for_asset(assets_map.get(aid), default="cover"),
            "role": "portrait",
        }
        for idx, aid in enumerate(portrait_ids)
    ]
    screen = _make_screen(
        PATTERN_PORTRAIT_GRID_8,
        screen_id=screen_id,
        slots=slots,
    )
    if any_asset_has_person(portrait_ids, assets_map):
        screen["layoutHint"] = PERSON_LAYOUT_GRID_8
    return screen


def _layout_hint_for_mundane_bucket(bucket: str) -> str:
    return _MUNDANE_GRID_LAYOUT_HINTS.get(bucket, f"{bucket}-grid")


def _make_mundane_grid_screen(
    asset_ids: list[str],
    *,
    bucket: str = "food",
    screen_id: str = "",
    assets_map: dict[str, dict] | None = None,
) -> dict:
    assets_map = assets_map or {}
    count = len(asset_ids)
    if count >= 9:
        pattern = "screen-square-9"
        use_ids = asset_ids[:9]
    elif count >= 6:
        pattern = "screen-square-6"
        use_ids = asset_ids[:6]
    else:
        pattern = "screen-square-4"
        use_ids = asset_ids[:4]
    slots = [
        {
            "assetId": aid,
            "slot": idx,
            "fit": "cover",
            "role": bucket,
        }
        for idx, aid in enumerate(use_ids)
    ]
    screen = _make_screen(
        pattern,
        screen_id=screen_id,
        slots=slots,
    )
    screen["layoutHint"] = _layout_hint_for_mundane_bucket(bucket)
    return screen


def _make_food_grid_screen(
    asset_ids: list[str],
    *,
    screen_id: str = "",
    assets_map: dict[str, dict] | None = None,
) -> dict:
    return _make_mundane_grid_screen(
        asset_ids,
        bucket="food",
        screen_id=screen_id,
        assets_map=assets_map,
    )


def _make_mixed_portrait_landscape_screen(
    portrait_id: str,
    landscape_ids: list[str],
    *,
    screen_id: str = "",
    assets_map: dict[str, dict] | None = None,
) -> dict:
    assets_map = assets_map or {}
    p_fit = portrait_fit_for_asset(assets_map.get(portrait_id), default="cover")
    return _make_screen(
        PATTERN_PORTRAIT_1_LANDSCAPE_2,
        screen_id=screen_id,
        slots=[
            {"assetId": portrait_id, "slot": 0, "fit": p_fit, "role": "portrait"},
            {"assetId": landscape_ids[0], "slot": 1, "fit": "cover", "role": "landscape"},
            {"assetId": landscape_ids[1], "slot": 2, "fit": "cover", "role": "landscape"},
        ],
    )


def _family_kind(k: AspectKind) -> str:
    if k == "panorama":
        return "panorama"
    if k == "tall":
        return "tall"
    if k == "square":
        return "square"
    if _is_std_portrait(k):
        return "portrait"
    if _is_std_landscape(k):
        return "landscape"
    return "landscape"


# Solo ultra-wide stage only when native w/h ≥ this (aligns with render ultra tier).
ULTRA_WIDE_SOLO_AR = 2.8


def _asset_native_aspect_ratio(asset: dict) -> float | None:
    w = int(asset.get("nativeWidth") or asset.get("width") or 0)
    h = int(asset.get("nativeHeight") or asset.get("height") or 0)
    if w > 0 and h > 0:
        return w / h
    return None


def _layout_family_for_asset(
    aid: str,
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict] | None = None,
) -> str:
    """Map ingest panorama (≥2:1) to landscape unless truly ultra-wide."""
    fam = _family_kind(aspects.get(aid, "square"))
    if fam != "panorama" or not assets_map:
        return fam
    ar = _asset_native_aspect_ratio(assets_map.get(aid, {}))
    if ar is not None and ar < ULTRA_WIDE_SOLO_AR:
        return "landscape"
    return "panorama"


def _is_std_portrait_id(aid: str, aspects: dict[str, AspectKind]) -> bool:
    return _family_kind(aspects.get(aid, "square")) == "portrait"


def _is_landscape_id(aid: str, aspects: dict[str, AspectKind]) -> bool:
    return _family_kind(aspects.get(aid, "square")) == "landscape"


def _pattern_id(family: str, count: int) -> str:
    if family == "panorama":
        return "screen-panorama-1"
    if family == "tall":
        return "screen-portrait-1"
    if count in (1, 2, 3, 4, 6, 9):
        return f"screen-{family}-{count}"
    if count >= 7:
        return f"screen-{family}-9"
    return f"screen-{family}-1"


def _parse_taken_ts(asset: dict) -> float | None:
    from travelogue.curation.burst_utils import parse_taken_ts

    return parse_taken_ts(asset)


def _time_near_chain(
    asset_ids: list[str],
    assets: dict[str, dict],
    *,
    burst_seconds: float,
) -> bool:
    from travelogue.curation.burst_utils import time_near_chain

    return time_near_chain(asset_ids, assets, burst_seconds=burst_seconds)


def burst_group_map(
    asset_ids: list[str],
    assets: dict[str, dict],
    aspects: dict[str, AspectKind],
    *,
    burst_seconds: float = 3.0,
) -> dict[str, int]:
    from travelogue.curation.burst_utils import burst_group_map as _map

    return _map(asset_ids, assets, aspects, burst_seconds=burst_seconds)


def _same_burst_group(
    asset_ids: list[str],
    burst_groups: dict[str, int],
) -> bool:
    from travelogue.curation.burst_utils import same_burst_group

    return same_burst_group(asset_ids, burst_groups)


def _pick_largest_allowed_grid(
    run_len: int,
    family: str,
    *,
    burst_run: bool = False,
    portrait_heavy: bool = False,
    layout_state: ScreenLayoutPlannerState | None = None,
) -> int:
    """Pick largest grid size that satisfies layout_state and pattern emit rules."""
    from travelogue.curation.mosaic.runtime import six_slot_layout_enabled

    allow_six = six_slot_layout_enabled()
    cap = min(run_len, MAX_SLOTS_PER_SCREEN)
    if family == "landscape":
        size_order = (9, 6, 4)
    elif family == "portrait":
        size_order = _PORTRAIT_COLUMN_GRID_SIZES
    else:
        size_order = _GRID_SIZES
    candidates: list[int] = []
    if layout_state is not None and layout_state.should_prefer_nine() and cap >= 9:
        candidates.append(9)
    if burst_run and cap >= 4:
        for s in (9, 6, 4, 3):
            if s == 6 and not allow_six:
                continue
            if s not in candidates and s in size_order:
                candidates.append(s)
    if portrait_heavy and family == "portrait":
        for s in (9, 6, 3):
            if s == 6 and not allow_six:
                continue
            if s not in candidates:
                candidates.append(s)
    for s in size_order:
        if s not in candidates:
            candidates.append(s)
    if layout_state is not None and layout_state.layout_density == "hero_first":
        hero_six = (6,) if allow_six else ()
        hero_order = (
            (1, 4, *hero_six, 9) if family == "landscape" else (1, 3, 4, *hero_six, 9)
        )
        seen = set(candidates)
        candidates = list(hero_order) + [s for s in candidates if s not in hero_order]
        for s in size_order:
            if s not in seen and s not in candidates:
                candidates.append(s)
                seen.add(s)
    elif layout_state is not None and layout_state.layout_density == "collage_first":
        collage_six = [6] if allow_six else []
        collage_order = (
            [9, *collage_six, 4, 1]
            if family == "landscape"
            else [9, *collage_six, 4, 3, 1]
        )
        seen = set(candidates)
        candidates = list(collage_order) + [s for s in candidates if s not in collage_order]
        for s in size_order:
            if s not in seen and s not in candidates:
                candidates.append(s)
                seen.add(s)
    for size in candidates:
        if size == 6 and not allow_six:
            continue
        if size > cap:
            continue
        if layout_state is not None:
            if not layout_state.can_pick_grid_size(size):
                continue
            if not layout_state.can_emit_pattern(_pattern_id(family, size)):
                continue
        return size
    return 1


def _pick_grid_count(
    run_len: int,
    family: str,
    *,
    burst_run: bool = False,
    portrait_heavy: bool = False,
    layout_state: ScreenLayoutPlannerState | None = None,
) -> int:
    """Pick largest grid ≤ run_len (landscape: 4/6/9 only; portrait: column grids)."""
    return _pick_largest_allowed_grid(
        run_len,
        family,
        burst_run=burst_run,
        portrait_heavy=portrait_heavy,
        layout_state=layout_state,
    )


def _run_length(
    remaining: list[str],
    aspects: dict[str, AspectKind],
    *,
    assets_map: dict[str, dict] | None = None,
) -> tuple[str, int]:
    if not remaining:
        return "landscape", 0
    fam = _layout_family_for_asset(remaining[0], aspects, assets_map)
    n = 1
    while (
        n < len(remaining)
        and _layout_family_for_asset(remaining[n], aspects, assets_map) == fam
    ):
        n += 1
    return fam, n


PERSON_LAYOUT_PAIR = "person-pair"
PERSON_LAYOUT_TRIPLE = "person-triple"


def _person_portrait_ids(buf: list[str], assets_map: dict[str, dict]) -> list[str]:
    return [a for a in buf if asset_has_person(assets_map.get(a, {}))]


def _tile_portrait_run(
    n: int,
    *,
    seed_pair_streak: int = 0,
    max_pair_streak: int = MAX_PORTRAIT_PAIR_STREAK,
) -> list[int]:
    """竖版游程分组（pair-first + R-06 + R-02）。

    返回每屏吃图数序列（2=双列, 3=三列, 1=单列兜底）：
    - 优先双列（pair-first）；
    - 连续双列不超过 ``max_pair_streak``（R-06，默认 2，G-07 可配置），
      触顶或会被逼入死角时用三列打断；
    - 不连续三列（R-02）；
    - 仅在收尾无法成对时落单列（1）。
    ``seed_pair_streak`` 为跨 flush 已累计的连续双列数。
    """
    groups: list[int] = []
    streak = max(0, seed_pair_streak)
    last_was_triple = False
    while n > 0:
        if n == 1:
            groups.append(1)
            n = 0
            continue
        if n == 2:
            groups.append(2)
            n = 0
            continue
        if n == 3:
            if last_was_triple:
                groups.extend((2, 1))
            else:
                groups.append(3)
            n = 0
            continue
        # n >= 4：判断是否需要用三列打断（触顶，或成对后会把恰好 2 张逼到顶）。
        corner_after_pair = (n - 2 == 2) and (streak + 1 >= max_pair_streak)
        if (streak >= max_pair_streak or corner_after_pair) and not last_was_triple:
            groups.append(3)
            n -= 3
            streak = 0
            last_was_triple = True
        else:
            groups.append(2)
            n -= 2
            streak += 1
            last_was_triple = False
    return groups


def _emit_person_portrait_screens(
    person_ids: list[str],
    aspects: dict[str, AspectKind],
    *,
    assets_map: dict[str, dict],
    layout_state: ScreenLayoutPlannerState | None = None,
    pending: list[str] | None = None,
    force: bool = False,
    solo_exclude: set[str] | None = None,
) -> list[dict]:
    """人物竖图：仅三列(≥3) / 双列(2)；单张不单独成屏（见余片 cover portrait-1）。"""
    screens: list[dict] = []
    buf = list(person_ids)
    defer: list[str] = []
    tail_singles: list[str] = []
    # 竖版分组优先级：两列(person-pair) > 三列(person-triple) > 单列。
    # 由 _tile_portrait_run 统一裁决（pair-first + R-06 连续上限 + R-02 不连三列）。
    seed = (
        layout_state.current_portrait_pair_streak() if layout_state is not None else 0
    )
    pair_max = (
        layout_state.rhythm.max_portrait_pair_streak
        if layout_state is not None
        else MAX_PORTRAIT_PAIR_STREAK
    )
    for size in _tile_portrait_run(len(buf), seed_pair_streak=seed, max_pair_streak=pair_max):
        if size == 3:
            trio = buf[:3]
            buf = buf[3:]
            if (
                not force
                and layout_state is not None
                and not layout_state.can_emit_pattern("screen-portrait-3")
            ):
                # 与上一屏冲突：降为双列并把第三张顺延（保持原退让行为）。
                if layout_state.can_emit_pattern("screen-portrait-2"):
                    screen = _make_screen(
                        "screen-portrait-2",
                        trio[:2],
                        screen_id="",
                        aspects=aspects,
                        assets_map=assets_map,
                    )
                    screen["layoutHint"] = PERSON_LAYOUT_PAIR
                    screens.append(screen)
                    defer.append(trio[2])
                else:
                    defer.extend(trio)
                continue
            screen = _make_screen(
                "screen-portrait-3",
                trio,
                screen_id="",
                aspects=aspects,
                assets_map=assets_map,
            )
            screen["layoutHint"] = PERSON_LAYOUT_TRIPLE
            screens.append(screen)
        elif size == 2:
            pair = buf[:2]
            buf = buf[2:]
            screen = _make_screen(
                "screen-portrait-2",
                pair,
                screen_id="",
                aspects=aspects,
                assets_map=assets_map,
            )
            screen["layoutHint"] = PERSON_LAYOUT_PAIR
            screens.append(screen)
        else:
            tail_singles.append(buf[0])
            buf = buf[1:]
    if tail_singles:
        screens.extend(
            _emit_portrait_single_screens(
                tail_singles,
                aspects,
                assets_map=assets_map,
                layout_state=layout_state,
                pending=pending or defer,
                force=force,
                solo_exclude=solo_exclude,
            )
        )
    if pending is not None and defer:
        pending[:0] = defer
    return screens


def _emit_portrait_single_screens(
    portrait_ids: list[str],
    aspects: dict[str, AspectKind],
    *,
    assets_map: dict[str, dict],
    layout_state: ScreenLayoutPlannerState | None,
    pending: list[str] | None = None,
    force: bool = False,
    solo_exclude: set[str] | None = None,
) -> list[dict]:
    """Emit screen-portrait-1, or defer when consecutive singles are banned.

    `force` bypasses the consecutive-single ban: used by the final/boundary
    flush where there is no future portrait to batch with, so deferring would
    either drop the asset or stall the planning loop.
    """
    if len(portrait_ids) > 1:
        from travelogue.curation.solo_scoring import sort_ids_by_solo_score

        portrait_ids = sort_ids_by_solo_score(
            portrait_ids,
            assets_map,
            chapter_peer_ids=list(assets_map.keys()),
            exclude=solo_exclude,
        )
    screens: list[dict] = []
    for aid in portrait_ids:
        if (
            not force
            and layout_state is not None
            and not layout_state.can_emit_pattern("screen-portrait-1")
        ):
            if pending is not None:
                pending.append(aid)
            continue
        screens.append(
            _make_screen(
                "screen-portrait-1",
                [aid],
                screen_id="",
                aspects=aspects,
                assets_map=assets_map,
            )
        )
    return screens


def _plan_portrait_triple_row(
    trio: list[str],
    aspects: dict[str, AspectKind],
    *,
    assets_map: dict[str, dict],
    layout_state: ScreenLayoutPlannerState | None,
    pending: list[str],
    force: bool = False,
) -> list[dict]:
    """三张一排；若与上一屏冲突则降为双列并回退余片。"""
    if force or layout_state is None or layout_state.can_emit_pattern("screen-portrait-3"):
        return [
            _make_screen(
                "screen-portrait-3",
                trio,
                screen_id="",
                aspects=aspects,
                assets_map=assets_map,
            )
        ]
    if layout_state and layout_state.can_emit_pattern("screen-portrait-2"):
        pending.insert(0, trio[2])
        return [
            _make_screen(
                "screen-portrait-2",
                trio[:2],
                screen_id="",
                aspects=aspects,
                assets_map=assets_map,
            )
        ]
    return []


def _can_mixed_p1_l2(
    portrait_id: str,
    landscape_ids: list[str],
    aspects: dict[str, AspectKind],
    assets: dict[str, dict],
    *,
    burst_seconds: float,
) -> bool:
    if len(landscape_ids) != 2:
        return False
    if not _is_std_portrait_id(portrait_id, aspects):
        return False
    if not all(_is_landscape_id(lid, aspects) for lid in landscape_ids):
        return False
    if asset_has_person(assets.get(portrait_id, {})):
        return False
    return _time_near_chain(
        [portrait_id, landscape_ids[0], landscape_ids[1]],
        assets,
        burst_seconds=burst_seconds,
    )


def _flush_portrait_pending(
    pending: list[str],
    aspects: dict[str, AspectKind],
    *,
    assets_map: dict[str, dict] | None = None,
    layout_state: ScreenLayoutPlannerState | None = None,
    force: bool = False,
    solo_exclude: set[str] | None = None,
) -> list[dict]:
    """Emit portrait-3 (风景竖图) or portrait-1 (含人物) for buffered std portraits.

    `force` bypasses consecutive-pattern bans so a boundary/final flush always
    makes progress: deferring the last buffered portrait back to `pending` would
    otherwise stall the planning loop or silently drop the asset.
    """
    assets_map = assets_map or {}
    screens: list[dict] = []
    buf = [a for a in pending if _is_std_portrait_id(a, aspects)]
    overflow = [a for a in pending if a not in buf]
    pending.clear()
    pending.extend(overflow)

    person_buf = _person_portrait_ids(buf, assets_map)
    scenery_buf = [a for a in buf if a not in person_buf]

    # V-08 收紧：恰好 1 人物 + 1 风景竖版时合并为一屏双列，
    # 避免 person/scenery 分流各出一张连续竖单（如 carry 尾部 asset-001/003）。
    if len(person_buf) == 1 and len(scenery_buf) == 1:
        if (
            force
            or layout_state is None
            or layout_state.can_emit_pattern("screen-portrait-2")
        ):
            screens.append(
                _make_screen(
                    "screen-portrait-2",
                    list(buf),
                    screen_id="",
                    aspects=aspects,
                    assets_map=assets_map,
                )
            )
        else:
            pending.extend(buf)
        buf.clear()
        return screens

    buf.clear()
    buf.extend(scenery_buf)

    screens.extend(
        _emit_person_portrait_screens(
            person_buf,
            aspects,
            assets_map=assets_map,
            layout_state=layout_state,
            pending=pending,
            force=force,
            solo_exclude=solo_exclude,
        )
    )

    # 竖版分组优先级：两列(portrait-2) > 三列(portrait-3) > 单列(portrait-1)。
    # 由 _tile_portrait_run 统一裁决（pair-first + R-06 连续上限 + R-02 不连三列）。
    seed = (
        layout_state.current_portrait_pair_streak() if layout_state is not None else 0
    )
    pair_max = (
        layout_state.rhythm.max_portrait_pair_streak
        if layout_state is not None
        else MAX_PORTRAIT_PAIR_STREAK
    )
    for size in _tile_portrait_run(len(buf), seed_pair_streak=seed, max_pair_streak=pair_max):
        if size == 3:
            trio = buf[:3]
            placed = _plan_portrait_triple_row(
                trio,
                aspects,
                assets_map=assets_map,
                layout_state=layout_state,
                pending=pending,
                force=force,
            )
            if not placed:
                break
            screens.extend(placed)
            buf = buf[3:]
        elif size == 2:
            screens.append(
                _make_screen(
                    "screen-portrait-2",
                    buf[:2],
                    screen_id="",
                    aspects=aspects,
                    assets_map=assets_map,
                )
            )
            buf = buf[2:]
        else:
            screens.extend(
                _emit_portrait_single_screens(
                    buf[:1],
                    aspects,
                    assets_map=assets_map,
                    layout_state=layout_state,
                    pending=pending,
                    force=force,
                    solo_exclude=solo_exclude,
                )
            )
            buf = buf[1:]
    return screens


def _pick_solo_from_candidates(
    candidate_ids: list[str],
    assets_map: dict[str, dict],
    *,
    solo_exclude: set[str] | None = None,
) -> str | None:
    if len(candidate_ids) <= 1:
        return candidate_ids[0] if candidate_ids else None
    from travelogue.curation.solo_scoring import pick_solo_asset_id

    return pick_solo_asset_id(
        candidate_ids,
        assets_map,
        chapter_peer_ids=list(assets_map.keys()),
        exclude=solo_exclude,
    )


def _plan_one_screen(
    remaining: list[str],
    aspects: dict[str, AspectKind],
    *,
    burst_groups: dict[str, int] | None = None,
    portrait_heavy: bool = False,
    assets_map: dict[str, dict] | None = None,
    layout_state: ScreenLayoutPlannerState | None = None,
    solo_exclude: set[str] | None = None,
) -> tuple[dict | None, int]:
    if not remaining:
        return None, 0

    assets_map = assets_map or {}
    family, run_len = _run_length(remaining, aspects, assets_map=assets_map)

    if family == "landscape":
        land_run = remaining[:run_len]
        bucket_ids = prefix_same_bucket(land_run, assets_map)
        can_nine_pool = (
            layout_state is not None
            and run_len >= 9
            and layout_state.can_use_nine()
        )
        grid_pool = land_run if can_nine_pool else bucket_ids
        if len(grid_pool) <= 3:
            pool = grid_pool[: min(len(grid_pool), 3)]
            chosen = _pick_solo_from_candidates(pool, assets_map, solo_exclude=solo_exclude) or pool[0]
            return (
                _make_screen(
                    "screen-landscape-1",
                    [chosen],
                    screen_id="",
                    aspects=aspects,
                    assets_map=assets_map,
                ),
                1,
            )
        burst_groups = burst_groups or {}
        probe = grid_pool[: min(len(grid_pool), MAX_SLOTS_PER_SCREEN)]
        burst_run = _same_burst_group(probe, burst_groups) if len(probe) >= 4 else False
        n = _pick_grid_count(
            len(grid_pool),
            family,
            burst_run=burst_run,
            portrait_heavy=portrait_heavy,
            layout_state=layout_state,
        )
        ids = grid_pool[:n]
        pattern = _pattern_id(family, n)
        return _make_screen(
            pattern, ids, screen_id="", aspects=aspects, assets_map=assets_map
        ), n

    if family == "panorama":
        # 单张超宽图用 landscape-1 + 渲染时原生 aspect-ratio，避免 21:9 固定槽压扁
        return _make_screen("screen-landscape-1", [remaining[0]], screen_id=""), 1

    if family == "tall":
        return _make_screen("screen-tall-1", [remaining[0]], screen_id=""), 1

    if family == "portrait":
        return None, 0

    burst_groups = burst_groups or {}
    probe = remaining[: min(run_len, MAX_SLOTS_PER_SCREEN)]
    burst_run = _same_burst_group(probe, burst_groups) if len(probe) >= 4 else False

    n = _pick_grid_count(
        run_len,
        family,
        burst_run=burst_run,
        portrait_heavy=portrait_heavy,
        layout_state=layout_state,
    )
    ids = remaining[:n]
    pattern = _pattern_id(family, n)
    return _make_screen(
        pattern, ids, screen_id="", aspects=aspects, assets_map=assets_map
    ), n


CHAPTER_HERO_MIN_ASSETS = 5


def _pick_chapter_hero(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    preferred_id: str | None = None,
    median_sharp: float | None = None,
    featured_weight: float = DEFAULT_FEATURED_WEIGHT,
) -> tuple[str, str] | None:
    """Best landscape/panorama for opening 16:9 hero screen (web editorial rhythm)."""
    from travelogue.curation.curate_scoring import effective_hero_score, median_sharpness

    med = (
        median_sharp
        if median_sharp is not None
        else median_sharpness(list(assets_map.values()))
    )
    if preferred_id and preferred_id in asset_ids:
        kind = aspects.get(preferred_id, "square")
        if kind in ("landscape", "panorama"):
            asset = assets_map.get(preferred_id) or {}
            if effective_hero_score(asset, median_sharp=med, featured_weight=featured_weight) > 0:
                return preferred_id, "screen-landscape-1"

    best_id = ""
    best_score = 0.0
    for aid in asset_ids:
        kind = aspects.get(aid, "square")
        if kind not in ("landscape", "panorama"):
            continue
        asset = assets_map.get(aid) or {}
        score = effective_hero_score(asset, median_sharp=med, featured_weight=featured_weight)
        if score > best_score:
            best_score = score
            best_id = aid
    if not best_id:
        return None
    return best_id, "screen-landscape-1"


def _sort_asset_ids_by_taken(
    asset_ids: list[str],
    assets: dict[str, dict],
) -> list[str]:
    def key(aid: str) -> str:
        return str(assets.get(aid, {}).get("takenAt") or "")

    return sorted(asset_ids, key=key)


def _collect_asset_ids_from_chapter(ch: dict) -> list[str]:
    ids: list[str] = []
    for it in ch.get("items", []):
        itype = it.get("type")
        if itype == "media-card":
            ids.append(it["assetId"])
        elif itype in ("media-row", "media-scroll"):
            ids.extend(it.get("assetIds") or [])
    return ids


def plan_screens_for_chapter(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    *,
    chapter_id: str = "ch",
    max_per_screen: int = MAX_SLOTS_PER_SCREEN,
    assets: dict[str, dict] | None = None,
    burst_seconds: float = 3.0,
    mixed_proximity_seconds: float | None = None,
    orientation_summary: dict | None = None,
    skip_screen_asset_ids: set[str] | None = None,
    layout_state: ScreenLayoutPlannerState | None = None,
    trip_photo_total: int | None = None,
    preferred_hero_id: str | None = None,
    include_chapter_hero: bool = True,
    enable_mosaic: bool = True,
    featured_weight: float = DEFAULT_FEATURED_WEIGHT,
    enable_portrait_grid8: bool = True,
    enable_food_grid: bool = True,
    mundane_grid_buckets: tuple[str, ...] = ("food",),
    median_sharp: float | None = None,
) -> list[dict]:
    """
    Map ordered asset ids → screens[] (one pattern per screen; reset after each screen).

    Std portrait: prefer portrait-3 / portrait-2, then screen-portrait-1-landscape-2
    (竖左 + 双横右, takenAt ≤ burst_seconds), else cover portrait-1 fallback.
    """
    from travelogue.curation.screen_planner_stages import ChapterScreenPlanner

    return ChapterScreenPlanner.create(
        asset_ids,
        aspects,
        chapter_id=chapter_id,
        max_per_screen=max_per_screen,
        assets=assets,
        burst_seconds=burst_seconds,
        mixed_proximity_seconds=mixed_proximity_seconds,
        orientation_summary=orientation_summary,
        skip_screen_asset_ids=skip_screen_asset_ids,
        layout_state=layout_state,
        trip_photo_total=trip_photo_total,
        preferred_hero_id=preferred_hero_id,
        include_chapter_hero=include_chapter_hero,
        enable_mosaic=enable_mosaic,
        featured_weight=featured_weight,
        enable_portrait_grid8=enable_portrait_grid8,
        enable_food_grid=enable_food_grid,
        mundane_grid_buckets=mundane_grid_buckets,
        median_sharp=median_sharp,
    ).plan()


from travelogue.curation.screen_planner_attach import (  # noqa: E402
    attach_screens_day_buckets,
    attach_screens_to_chapters,
    gallery_chapter_uses_screens_not_scroll,
)
