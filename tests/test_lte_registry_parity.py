"""LTE export parity vs 6 legacy mosaic sources (PRD V-P16-11, AC-P16-02)."""

from __future__ import annotations

import re
import time
from dataclasses import asdict
from pathlib import Path

import pytest

from travelogue.curation.mosaic.constants import PATTERN_GRID_CLASS
from travelogue.curation.mosaic.grid_specs import (
    AUTO_FLOW_GRIDS,
    EXPLICIT_GRID_SPECS,
    STACK_PATTERNS,
)
from travelogue.curation.mosaic.pattern_catalog import default_registry
from travelogue.curation.mosaic.slot_geometry import (
    _LANDSCAPE_FORBIDDEN_TALL,
    _PORTRAIT_FORBIDDEN_WIDE,
)
from travelogue.layout_templates.css_gen import _marker_block_region, normalize_grid_template
from travelogue.layout_templates.registry import LayoutTemplateEngine, reset_engine_cache_for_tests
from travelogue.paths import JOURNAL_SCREENS_CSS


@pytest.fixture
def lte_engine() -> LayoutTemplateEngine:
    reset_engine_cache_for_tests()
    return LayoutTemplateEngine.load(rebuild_cache=True)


def _parse_journal_grid_css(css_text: str) -> dict[str, dict[str, str]]:
    """Extract grid-template-* for layout-screen__grid--* classes from journal-screens.css."""
    out: dict[str, dict[str, str]] = {}
    blocks = re.findall(
        r"(\.layout-screen__grid--[a-z0-9-]+)\s*\{([^}]+)\}",
        css_text,
        flags=re.IGNORECASE,
    )
    for selector, body in blocks:
        cls = selector.lstrip(".")
        cols_m = re.search(r"grid-template-columns:\s*([^;]+);", body)
        rows_m = re.search(r"grid-template-rows:\s*([^;]+);", body)
        if not cols_m and not rows_m:
            continue
        out.setdefault(cls, {})
        if cols_m:
            out[cls]["gridTemplateColumns"] = normalize_grid_template(cols_m.group(1))
        if rows_m:
            out[cls]["gridTemplateRows"] = normalize_grid_template(rows_m.group(1))
    return out


@pytest.mark.unit
def test_lte_cli_validate_all_templates(lte_engine: LayoutTemplateEngine) -> None:
    from travelogue.layout_templates import cli

    assert cli.main(["validate"]) == 0
    assert len(lte_engine._templates) >= 20


@pytest.mark.unit
def test_mosaic_pattern_parity(lte_engine: LayoutTemplateEngine) -> None:
    exported = lte_engine.export_legacy_registry()["mosaic_patterns"]
    legacy = default_registry()
    assert set(exported) == set(legacy)
    for pid, leg in legacy.items():
        got = exported[pid]
        assert got.pattern_id == leg.pattern_id
        assert got.slot_count == leg.slot_count
        assert got.grid_class == leg.grid_class
        assert got.roles == leg.roles
        assert asdict(got.accepts) == asdict(leg.accepts)
        assert got.css_verified == leg.css_verified


@pytest.mark.unit
def test_explicit_grid_specs_parity(lte_engine: LayoutTemplateEngine) -> None:
    exported = lte_engine.export_legacy_registry()["explicit_grid_specs"]
    assert exported == EXPLICIT_GRID_SPECS


@pytest.mark.unit
def test_auto_flow_grids_parity(lte_engine: LayoutTemplateEngine) -> None:
    exported = lte_engine.export_legacy_registry()["auto_flow_grids"]
    assert exported == AUTO_FLOW_GRIDS


@pytest.mark.unit
def test_stack_patterns_parity(lte_engine: LayoutTemplateEngine) -> None:
    exported = lte_engine.export_legacy_registry()["stack_patterns"]
    assert exported == STACK_PATTERNS


@pytest.mark.unit
def test_pattern_grid_class_parity(lte_engine: LayoutTemplateEngine) -> None:
    exported = lte_engine.export_legacy_registry()["pattern_grid_class"]
    assert exported == PATTERN_GRID_CLASS


@pytest.mark.unit
def test_forbidden_slot_maps_parity(lte_engine: LayoutTemplateEngine) -> None:
    exported = lte_engine.export_legacy_registry()
    assert exported["portrait_forbidden_wide"] == dict(_PORTRAIT_FORBIDDEN_WIDE)
    assert exported["landscape_forbidden_tall"] == dict(_LANDSCAPE_FORBIDDEN_TALL)


@pytest.mark.unit
def test_grid_template_strings_parity(lte_engine: LayoutTemplateEngine) -> None:
    # Compare YAML export against the authoritative LTE-generated marker block only.
    # Pattern overlays (e.g. screen-portrait-2's person-pair --2col) legitimately
    # redefine the same grid class with variant tracks and must not be compared.
    css_text = _marker_block_region(Path(JOURNAL_SCREENS_CSS).read_text(encoding="utf-8"))
    css_grids = _parse_journal_grid_css(css_text)
    exported = lte_engine.export_legacy_registry()["grid_templates"]
    for pid, grid_class in PATTERN_GRID_CLASS.items():
        if pid in STACK_PATTERNS:
            continue
        expected = css_grids.get(grid_class)
        if not expected:
            continue
        got = exported[pid]
        if "gridTemplateColumns" in expected:
            assert normalize_grid_template(got["gridTemplateColumns"]) == expected["gridTemplateColumns"], pid
        if "gridTemplateRows" in expected:
            assert normalize_grid_template(got["gridTemplateRows"]) == expected["gridTemplateRows"], pid


@pytest.mark.unit
def test_main_hero_plus_4_dirty_data_preserved(lte_engine: LayoutTemplateEngine) -> None:
    t = lte_engine.get("screen-mosaic-5-main-hero-plus-4")
    assert len(t.slots) == 6
    assert t.photo_count_max == 6
    assert t.render_grid_class == PATTERN_GRID_CLASS["screen-mosaic-5-main-hero-plus-4"]


@pytest.mark.unit
def test_list_active_p99_under_1ms(lte_engine: LayoutTemplateEngine) -> None:
    samples: list[float] = []
    for _ in range(2000):
        t0 = time.perf_counter()
        lte_engine.list_active(window_size=5)
        samples.append(time.perf_counter() - t0)
    samples.sort()
    p99 = samples[int(len(samples) * 0.99)]
    assert p99 < 0.001, f"list_active p99={p99*1000:.3f}ms"
