"""Mosaic grid slot placements must not overlap on the 3×3 stage."""



from __future__ import annotations
from tests._repo_root import repo_root

from travelogue.curation.mosaic.constants import (
    MOSAIC_5_PATTERN_IDS,
    PATTERN_GRID_CLASS,
    PATTERN_MOSAIC_5_2P3L_EQUAL,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
)

# (col_start, col_end, row_start, row_end) — 1-based inclusive, on 3×3 grid
MOSAIC_GRID_SPECS: dict[str, list[tuple[int, int, int, int]]] = {
    "screen-mosaic-5-main-portrait-3land": [
        (1, 2, 1, 2),
        (3, 3, 1, 2),
        (1, 1, 3, 3),
        (2, 2, 3, 3),
        (3, 3, 3, 3),
    ],
    "screen-mosaic-5-hero-3-2-plus-4": [
        (1, 1, 1, 2),
        (2, 2, 1, 1),
        (3, 3, 1, 1),
        (2, 2, 2, 2),
        (3, 3, 2, 2),
    ],
    "screen-mosaic-5-main-landscape-2portrait-2land": [
        (1, 2, 1, 2),
        (3, 3, 1, 2),
        (1, 1, 3, 3),
        (2, 2, 3, 3),
        (3, 3, 3, 3),
    ],
    "screen-mosaic-5-2portrait-3land-balanced": [
        (1, 1, 1, 1),
        (2, 2, 1, 1),
        (1, 1, 2, 3),
        (2, 2, 2, 2),
        (2, 3, 3, 3),
    ],
    "screen-mosaic-5-3portrait-2land-balanced": [
        (1, 1, 1, 2),
        (2, 2, 1, 2),
        (3, 3, 1, 2),
        (1, 2, 3, 3),
        (3, 3, 3, 3),
    ],
    PATTERN_MOSAIC_5_2P3L_EQUAL: [
        (1, 1, 1, 3),
        (2, 2, 1, 3),
        (3, 3, 1, 1),
        (3, 3, 2, 2),
        (3, 3, 3, 3),
    ],
    "screen-mosaic-5-main-hero-plus-4": [
        (1, 2, 1, 2),
        (3, 3, 1, 1),
        (3, 3, 2, 2),
        (1, 1, 3, 3),
        (2, 2, 3, 3),
        (3, 3, 3, 3),
    ],
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5: [
        (1, 2, 1, 2),
        (3, 3, 1, 1),
        (3, 3, 2, 2),
        (1, 1, 3, 3),
        (2, 2, 3, 3),
        (3, 3, 3, 3),
    ],
}


def _cells(spec: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    c0, c1, r0, r1 = spec
    return {(c, r) for c in range(c0, c1 + 1) for r in range(r0, r1 + 1)}


def _overlaps(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return bool(_cells(a) & _cells(b))


def test_mosaic5_patterns_have_non_overlapping_slots():
    for pid in MOSAIC_5_PATTERN_IDS:
        specs = MOSAIC_GRID_SPECS[pid]
        assert len(specs) == 5, pid
        for i, a in enumerate(specs):
            for b in specs[i + 1 :]:
                assert not _overlaps(a, b), f"{pid}: slot overlap {a} vs {b}"


def test_mosaic6_hero_plus_5_non_overlapping():
    specs = MOSAIC_GRID_SPECS[PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5]
    assert len(specs) == 6
    for i, a in enumerate(specs):
        for b in specs[i + 1 :]:
            assert not _overlaps(a, b)


def test_hero_plus_4_has_six_slots():
    specs = MOSAIC_GRID_SPECS["screen-mosaic-5-main-hero-plus-4"]
    assert len(specs) == 6


def test_hero_plus_4_main_is_two_by_two_not_three_rows():
    main = MOSAIC_GRID_SPECS["screen-mosaic-5-main-hero-plus-4"][0]
    assert main == (1, 2, 1, 2)


def test_hero_plus_4_bottom_left_tile_not_on_main_column_two():
    bottom_left = MOSAIC_GRID_SPECS["screen-mosaic-5-main-hero-plus-4"][3]
    assert bottom_left[0] == 1


def test_hero_plus_4_bottom_row_has_no_gap():
    bottom = MOSAIC_GRID_SPECS["screen-mosaic-5-main-hero-plus-4"][3:]
    assert bottom == [(1, 1, 3, 3), (2, 2, 3, 3), (3, 3, 3, 3)]


def test_mosaic6_fills_bottom_row():
    bottom = MOSAIC_GRID_SPECS[PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5][3:]
    assert bottom == [(1, 1, 3, 3), (2, 2, 3, 3), (3, 3, 3, 3)]


def test_mosaic6_grid_class_in_css():
    from pathlib import Path

    css = (
        repo_root(__file__)
        / "templates"
        / "visual-journal"
        / "journal-screens.css"
    ).read_text(encoding="utf-8")
    gc = PATTERN_GRID_CLASS[PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5]
    assert gc in css
