"""AC-P15-02/06 · grid_class mapping for all MCS 5-slot patterns."""



from __future__ import annotations

from tests._repo_root import repo_root
from travelogue.layout_engine.mosaic.constants import (
    MOSAIC_4_PATTERN_IDS,
    MOSAIC_5_PATTERN_IDS,
    PATTERN_GRID_CLASS,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
)
from travelogue.layout_engine.planner.screen_planner import grid_class_for_pattern

ROOT = repo_root(__file__)
SCREENS_CSS = ROOT / "templates" / "visual-journal" / "journal-screens.css"


def test_all_mosaic5_patterns_have_grid_class():
    for pid in MOSAIC_5_PATTERN_IDS:
        gc = grid_class_for_pattern(pid)
        assert gc == PATTERN_GRID_CLASS[pid]
        assert gc.startswith("layout-screen__grid--")


def test_mosaic5_grid_classes_present_in_css():
    css = SCREENS_CSS.read_text(encoding="utf-8")
    for pid in MOSAIC_5_PATTERN_IDS:
        gc = PATTERN_GRID_CLASS[pid]
        assert gc in css, f"missing CSS for {pid} -> {gc}"


def test_all_mosaic4_patterns_have_grid_class():
    for pid in MOSAIC_4_PATTERN_IDS:
        gc = grid_class_for_pattern(pid)
        assert gc == PATTERN_GRID_CLASS[pid]


def test_mosaic4_p2_l2_pattern_in_css():
    css = SCREENS_CSS.read_text(encoding="utf-8")
    assert 'data-pattern="screen-portrait-2-landscape-2"' in css


def test_mosaic6_hero_pattern_has_grid_class():
    gc = grid_class_for_pattern(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5)
    assert gc == PATTERN_GRID_CLASS[PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5]
    css = SCREENS_CSS.read_text(encoding="utf-8")
    assert gc in css
