"""P19 S4-04 · justified-row layout algorithm and MCS integration."""

from __future__ import annotations

from travelogue.curation.layout.justified_row import (
    build_justified_screen,
    can_use_justified_row,
    layout_justified_rows,
)
from travelogue.curation.layout_planner import AspectKind
from travelogue.curation.mosaic.builders import build_screen, try_order_for_pattern
from travelogue.curation.mosaic.pattern_catalog import MosaicPattern, patterns_for_window_size
from travelogue.curation.mosaic.pattern_catalog import AspectProfile
from travelogue.layout_templates.registry import LayoutTemplateEngine, reset_engine_cache_for_tests


def _portrait_assets(n: int) -> tuple[list[str], dict[str, AspectKind], dict[str, dict]]:
    ids = [f"a{i}" for i in range(n)]
    aspects = {aid: "portrait" for aid in ids}
    assets_map = {
        aid: {
            "id": aid,
            "width": 900,
            "height": 1200,
            "aspectRatio": 0.75,
        }
        for aid in ids
    }
    return ids, aspects, assets_map


def test_layout_justified_rows_pack_all_assets() -> None:
    ids, _, assets_map = _portrait_assets(6)
    rows = layout_justified_rows(ids, assets_map)
    assert rows
    packed = [item.asset_id for row in rows for item in row.items]
    assert packed == ids
    for row in rows:
        total_w = sum(item.width_ratio for item in row.items)
        assert 0.9 <= total_w <= 1.05


def test_can_use_justified_row_requires_portrait_majority() -> None:
    ids, aspects, _ = _portrait_assets(5)
    assert can_use_justified_row(ids, aspects)
    for aid in ("a0", "a1", "a2"):
        aspects[aid] = "landscape"
    assert not can_use_justified_row(ids, aspects)


def test_build_justified_screen_shape() -> None:
    ids, _, assets_map = _portrait_assets(5)
    screen = build_justified_screen("screen-justified-row", ids, assets_map, screen_id="s1")
    assert screen["layoutKind"] == "justified"
    assert len(screen["slots"]) == 5
    assert len(screen["justifiedRows"]) >= 1


def test_mcs_try_order_and_build_for_justified_pattern() -> None:
    reset_engine_cache_for_tests()
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    tpl = engine.get("screen-justified-row")
    pat = MosaicPattern(
        pattern_id=tpl.id,
        slot_count=8,
        grid_class=tpl.render_grid_class,
        roles=tuple("portrait" for _ in range(8)),
        accepts=AspectProfile(min_portrait=4, max_portrait=8),
    )
    ids, aspects, assets_map = _portrait_assets(6)
    ordered = try_order_for_pattern(
        pat.pattern_id,
        ids,
        aspects,
        assets_map,
        burst_seconds=12.0,
        median_sharp=None,
    )
    assert ordered == ids
    screen = build_screen(pat, ordered, assets_map=assets_map)
    assert screen["layoutKind"] == "justified"


def test_patterns_for_window_size_includes_justified() -> None:
    reset_engine_cache_for_tests()
    from travelogue.curation.mosaic.lte_adapter import mosaic_registry

    reg = mosaic_registry()
    pats = patterns_for_window_size(6, reg)
    ids = {p.pattern_id for p in pats}
    assert "screen-justified-row" in ids
