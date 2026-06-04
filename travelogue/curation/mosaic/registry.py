"""Mosaic pattern registry (M3)."""

from __future__ import annotations

from dataclasses import dataclass

from travelogue.curation.mosaic.constants import (
    MOSAIC_3_PATTERN_IDS,
    MOSAIC_4_PATTERN_IDS,
    MOSAIC_5_PATTERN_IDS,
    MOSAIC_6_PATTERN_IDS,
    MOSAIC_8_PATTERN_IDS,
    MOSAIC_9_PATTERN_IDS,
    PATTERN_LANDSCAPE_9,
    PATTERN_PORTRAIT_9,
    PATTERN_PORTRAIT_GRID_8,
    PATTERN_GRID_CLASS,
    PATTERN_LANDSCAPE_3,
    PATTERN_LANDSCAPE_4,
    PATTERN_LANDSCAPE_6,
    PATTERN_MOSAIC_5_2P_3L_BALANCED,
    PATTERN_MOSAIC_5_3P_2L_BALANCED,
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_5_MAIN_LAND_2P_2L,
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    PATTERN_PORTRAIT_1_LANDSCAPE_2,
    PATTERN_PORTRAIT_2_LANDSCAPE_2,
    PATTERN_PORTRAIT_3,
    PATTERN_PORTRAIT_4,
    PATTERN_PORTRAIT_6,
)


@dataclass(frozen=True)
class AspectProfile:
    min_portrait: int = 0
    min_landscape: int = 0
    max_portrait: int = 9
    max_landscape: int = 9


@dataclass(frozen=True)
class MosaicPattern:
    pattern_id: str
    slot_count: int
    grid_class: str
    roles: tuple[str, ...]
    accepts: AspectProfile
    css_verified: bool = True


def default_registry() -> dict[str, MosaicPattern]:
    reg: dict[str, MosaicPattern] = {
        PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND: MosaicPattern(
            pattern_id=PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
            slot_count=5,
            grid_class=PATTERN_GRID_CLASS[PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND],
            roles=("main", "portrait", "landscape", "landscape", "landscape"),
            accepts=AspectProfile(min_portrait=1, min_landscape=4),
        ),
        PATTERN_MOSAIC_5_MAIN_LAND_2P_2L: MosaicPattern(
            pattern_id=PATTERN_MOSAIC_5_MAIN_LAND_2P_2L,
            slot_count=5,
            grid_class=PATTERN_GRID_CLASS[PATTERN_MOSAIC_5_MAIN_LAND_2P_2L],
            roles=("main", "portrait", "portrait", "landscape", "landscape"),
            accepts=AspectProfile(min_portrait=2, min_landscape=3),
        ),
        PATTERN_MOSAIC_5_2P_3L_BALANCED: MosaicPattern(
            pattern_id=PATTERN_MOSAIC_5_2P_3L_BALANCED,
            slot_count=5,
            grid_class=PATTERN_GRID_CLASS[PATTERN_MOSAIC_5_2P_3L_BALANCED],
            roles=("portrait", "portrait", "landscape", "landscape", "landscape"),
            accepts=AspectProfile(min_portrait=2, min_landscape=3),
        ),
        PATTERN_MOSAIC_5_3P_2L_BALANCED: MosaicPattern(
            pattern_id=PATTERN_MOSAIC_5_3P_2L_BALANCED,
            slot_count=5,
            grid_class=PATTERN_GRID_CLASS[PATTERN_MOSAIC_5_3P_2L_BALANCED],
            roles=("portrait", "portrait", "portrait", "landscape", "landscape"),
            accepts=AspectProfile(min_portrait=3, min_landscape=2),
        ),
        PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4: MosaicPattern(
            pattern_id=PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
            slot_count=6,
            grid_class=PATTERN_GRID_CLASS[PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5],
            roles=("main", "tile", "tile", "tile", "tile", "tile"),
            accepts=AspectProfile(min_landscape=5),
        ),
        PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5: MosaicPattern(
            pattern_id=PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
            slot_count=6,
            grid_class=PATTERN_GRID_CLASS[PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5],
            roles=("main", "tile", "tile", "tile", "tile", "tile"),
            accepts=AspectProfile(min_landscape=5),
        ),
        PATTERN_PORTRAIT_3: MosaicPattern(
            pattern_id=PATTERN_PORTRAIT_3,
            slot_count=3,
            grid_class=PATTERN_GRID_CLASS[PATTERN_PORTRAIT_3],
            roles=("portrait", "portrait", "portrait"),
            accepts=AspectProfile(min_portrait=3),
        ),
        PATTERN_LANDSCAPE_3: MosaicPattern(
            pattern_id=PATTERN_LANDSCAPE_3,
            slot_count=3,
            grid_class=PATTERN_GRID_CLASS[PATTERN_LANDSCAPE_3],
            roles=("landscape", "landscape", "landscape"),
            accepts=AspectProfile(min_landscape=3),
        ),
        PATTERN_PORTRAIT_1_LANDSCAPE_2: MosaicPattern(
            pattern_id=PATTERN_PORTRAIT_1_LANDSCAPE_2,
            slot_count=3,
            grid_class=PATTERN_GRID_CLASS[PATTERN_PORTRAIT_1_LANDSCAPE_2],
            roles=("portrait", "landscape", "landscape"),
            accepts=AspectProfile(min_portrait=1, min_landscape=2),
        ),
        PATTERN_PORTRAIT_2_LANDSCAPE_2: MosaicPattern(
            pattern_id=PATTERN_PORTRAIT_2_LANDSCAPE_2,
            slot_count=4,
            grid_class=PATTERN_GRID_CLASS[PATTERN_PORTRAIT_2_LANDSCAPE_2],
            roles=("portrait", "landscape", "landscape", "portrait"),
            accepts=AspectProfile(min_portrait=2, min_landscape=2),
        ),
        PATTERN_PORTRAIT_4: MosaicPattern(
            pattern_id=PATTERN_PORTRAIT_4,
            slot_count=4,
            grid_class=PATTERN_GRID_CLASS[PATTERN_PORTRAIT_4],
            roles=("portrait", "portrait", "portrait", "portrait"),
            accepts=AspectProfile(min_portrait=4),
        ),
        PATTERN_LANDSCAPE_4: MosaicPattern(
            pattern_id=PATTERN_LANDSCAPE_4,
            slot_count=4,
            grid_class=PATTERN_GRID_CLASS[PATTERN_LANDSCAPE_4],
            roles=("landscape", "landscape", "landscape", "landscape"),
            accepts=AspectProfile(min_landscape=4),
        ),
        PATTERN_PORTRAIT_6: MosaicPattern(
            pattern_id=PATTERN_PORTRAIT_6,
            slot_count=6,
            grid_class=PATTERN_GRID_CLASS[PATTERN_PORTRAIT_6],
            roles=("portrait",) * 6,
            accepts=AspectProfile(min_portrait=6),
        ),
        PATTERN_LANDSCAPE_6: MosaicPattern(
            pattern_id=PATTERN_LANDSCAPE_6,
            slot_count=6,
            grid_class=PATTERN_GRID_CLASS[PATTERN_LANDSCAPE_6],
            roles=("landscape",) * 6,
            accepts=AspectProfile(min_landscape=6),
        ),
        PATTERN_PORTRAIT_GRID_8: MosaicPattern(
            pattern_id=PATTERN_PORTRAIT_GRID_8,
            slot_count=8,
            grid_class=PATTERN_GRID_CLASS[PATTERN_PORTRAIT_GRID_8],
            roles=("portrait",) * 8,
            accepts=AspectProfile(min_portrait=8),
        ),
        PATTERN_PORTRAIT_9: MosaicPattern(
            pattern_id=PATTERN_PORTRAIT_9,
            slot_count=9,
            grid_class=PATTERN_GRID_CLASS[PATTERN_PORTRAIT_9],
            roles=("portrait",) * 9,
            accepts=AspectProfile(min_portrait=9),
        ),
        PATTERN_LANDSCAPE_9: MosaicPattern(
            pattern_id=PATTERN_LANDSCAPE_9,
            slot_count=9,
            grid_class=PATTERN_GRID_CLASS[PATTERN_LANDSCAPE_9],
            roles=("landscape",) * 9,
            accepts=AspectProfile(min_landscape=9),
        ),
    }
    return reg


_BY_SIZE: dict[int, tuple[str, ...]] = {
    3: MOSAIC_3_PATTERN_IDS,
    4: MOSAIC_4_PATTERN_IDS,
    5: MOSAIC_5_PATTERN_IDS,
    6: MOSAIC_6_PATTERN_IDS,
    8: MOSAIC_8_PATTERN_IDS,
    9: MOSAIC_9_PATTERN_IDS,
}


def patterns_for_window_size(size: int, registry: dict[str, MosaicPattern] | None = None) -> list[MosaicPattern]:
    reg = registry or default_registry()
    ids = _BY_SIZE.get(size)
    if ids:
        return [reg[pid] for pid in ids if pid in reg]
    return [p for p in reg.values() if p.slot_count == size]
