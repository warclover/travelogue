"""Cross-pattern mosaic grid audit — overlaps, gaps, coverage."""

from __future__ import annotations

from travelogue.curation.mosaic.constants import PATTERN_MOSAIC_5_HERO_3_2_PLUS_4
from travelogue.curation.mosaic.grid_specs import (
    ALL_MOSAIC_PATTERN_IDS,
    EXPLICIT_GRID_SPECS,
    audit_all,
    gap_cells,
    overlapping_pairs,
)


def test_every_mosaic_pattern_is_audited():
    report = audit_all()
    missing = [pid for pid in ALL_MOSAIC_PATTERN_IDS if pid not in report]
    assert not missing, f"no audit entry: {missing}"


def test_no_explicit_pattern_has_slot_overlap():
    for pid, specs in EXPLICIT_GRID_SPECS.items():
        hits = overlapping_pairs(specs)
        assert not hits, f"{pid} overlap at slot indices {hits}"


def test_full_coverage_explicit_3x3_mosaic_patterns():
    """3×3 跨格拼版应铺满 9 格（避免「缺一张」视觉）。2P+3L 变体除外 — 见 test_2p3l_known_gap."""
    full_cover = {
        "screen-mosaic-5-main-portrait-3land",
        "screen-mosaic-5-main-landscape-2portrait-2land",
        "screen-mosaic-5-2p3l-equal",
        # main-land-2p2l: 3×3 full after right column tall-portrait fix
        PATTERN_MOSAIC_5_HERO_3_2_PLUS_4,
        "screen-mosaic-5-main-hero-plus-4",
        "screen-mosaic-6-main-hero-plus-5",
    }
    for pid in full_cover:
        cols, rows = (3, 2) if pid == PATTERN_MOSAIC_5_HERO_3_2_PLUS_4 else (3, 3)
        gaps = gap_cells(EXPLICIT_GRID_SPECS[pid], cols=cols, rows=rows)
        assert gaps == set(), f"{pid} has gap cells {sorted(gaps)}"


def test_2p3l_balanced_has_known_top_right_gap():
    """已知：右上两格留空，全横图时可能像缺图 — 待产品确认是否改 CSS。"""
    gaps = gap_cells(EXPLICIT_GRID_SPECS["screen-mosaic-5-2portrait-3land-balanced"])
    assert gaps == {(3, 1), (3, 2)}


def test_portrait_left_2landscape_fills_2x2():
    from travelogue.curation.mosaic.constants import PATTERN_PORTRAIT_1_LANDSCAPE_2

    specs = EXPLICIT_GRID_SPECS[PATTERN_PORTRAIT_1_LANDSCAPE_2]
    assert gap_cells(specs, cols=2, rows=2) == set()


def test_audit_report_snapshot():
    report = audit_all()
    risky = {
        pid: info
        for pid, info in report.items()
        if info.get("gap_cells") or info.get("overlaps")
    }
    assert "screen-mosaic-5-2portrait-3land-balanced" in risky
    assert not any(info.get("overlaps") for info in report.values())
