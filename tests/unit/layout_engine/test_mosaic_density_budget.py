"""P21 · dense collage budget, window order, max_mosaic_slots."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import MosaicConfig, MosaicDensityBudgetConfig, get_config
from travelogue.curation.layout_density import (
    LayoutDensityParams,
    dense_collage_quota_adjusted,
)
from travelogue.layout_contract.planner_state import (
    ScreenLayoutPlannerState,
    dense_collage_limits_for_trip,
    is_dense_collage_pattern,
    is_large_mosaic_pattern,
)
from travelogue.layout_engine.mosaic.lte_adapter import mosaic_pattern_disabled
from travelogue.layout_engine.mosaic.runtime import (
    effective_mosaic_window_sizes,
    ordered_mosaic_window_sizes,
    planner_mosaic_window_sizes,
)


def test_dense_collage_limits_by_trip_size() -> None:
    assert dense_collage_limits_for_trip(40) == (0, 1)
    assert dense_collage_limits_for_trip(80) == (0, 3)
    assert dense_collage_limits_for_trip(150) == (0, 5)
    assert dense_collage_limits_for_trip(250) == (0, 7)


def test_hero_first_scales_dense_quota_down() -> None:
    params = LayoutDensityParams(density="hero_first")
    _lo, hi = params.adjust_dense_collage_limits(0, 5, total_photos=150)
    assert hi == 1


def test_collage_first_scales_dense_quota_up() -> None:
    params = LayoutDensityParams(density="collage_first")
    _lo, hi = params.adjust_dense_collage_limits(0, 3, total_photos=100)
    assert hi >= 3
    _lo44, hi44 = params.adjust_dense_collage_limits(0, 1, total_photos=44)
    assert hi44 >= 3


def test_planner_mosaic_window_sizes_append_aux_three_for_density_modes() -> None:
    cfg = MosaicConfig(
        enabled=True,
        enabled_window_sizes=(4, 5, 6, 9),
        density_budget=MosaicDensityBudgetConfig(enabled=True, window_order=(5, 4, 6, 9)),
    )
    assert planner_mosaic_window_sizes(cfg, density="balanced") == (5, 4, 6, 9, 3)
    assert planner_mosaic_window_sizes(cfg, density="collage_first") == (9, 6, 5, 4, 3)
    assert planner_mosaic_window_sizes(cfg, density="hero_first") == (9, 6, 5, 4)


def test_dense_collage_quota_adjusted_helper() -> None:
    out = dense_collage_quota_adjusted(100, "balanced")
    assert out["baseMax"] == 3
    assert out["max"] == 3


def test_is_dense_collage_pattern() -> None:
    assert is_dense_collage_pattern("screen-landscape-4")
    assert is_dense_collage_pattern("screen-mosaic-5-main-hero-plus-4")
    assert is_dense_collage_pattern("screen-landscape-9")
    assert not is_dense_collage_pattern("screen-portrait-2")
    assert not is_dense_collage_pattern("screen-landscape-3")


def test_planner_state_blocks_consecutive_dense() -> None:
    st = ScreenLayoutPlannerState.from_trip_total(100)
    assert st.dense_collage_max == 3
    assert st.can_emit_pattern("screen-landscape-4")
    st.note_screen("screen-landscape-4")
    assert st.dense_collage_used == 1
    assert not st.can_emit_pattern("screen-mosaic-5-main-hero-plus-4")
    assert not st.can_use_dense_collage_window(5)


def test_planner_state_resets_dense_streak_after_sparse() -> None:
    st = ScreenLayoutPlannerState.from_trip_total(100)
    st.note_screen("screen-landscape-4")
    st.note_screen("screen-landscape-1")
    assert st.can_emit_pattern("screen-landscape-4")


def test_planner_state_dense_max_cap() -> None:
    st = ScreenLayoutPlannerState.from_trip_total(50)
    assert st.dense_collage_max == 1
    st.note_screen("screen-landscape-4")
    assert not st.can_emit_pattern("screen-mosaic-5-main-hero-plus-4")


def test_balanced_window_order_prefers_five_four_six(monkeypatch) -> None:
    base = get_config()
    layout = replace(base.layout, template_engine=replace(base.layout.template_engine, max_mosaic_slots=9))
    import travelogue.config as config_mod

    monkeypatch.setattr(config_mod, "get_config", lambda: replace(base, layout=layout))
    cfg = MosaicConfig(
        enabled=True,
        enabled_window_sizes=(4, 5, 6),
        density_budget=MosaicDensityBudgetConfig(enabled=True, window_order=(5, 4, 6)),
    )
    assert ordered_mosaic_window_sizes(cfg, density="balanced") == (5, 4, 6)


def test_density_budget_off_falls_back_to_largest_first(monkeypatch) -> None:
    base = get_config()
    layout = replace(base.layout, template_engine=replace(base.layout.template_engine, max_mosaic_slots=9))
    import travelogue.config as config_mod

    monkeypatch.setattr(config_mod, "get_config", lambda: replace(base, layout=layout))
    cfg = MosaicConfig(
        enabled=True,
        enabled_window_sizes=(4, 5, 6),
        density_budget=MosaicDensityBudgetConfig(enabled=False),
    )
    assert ordered_mosaic_window_sizes(cfg, density="balanced") == (6, 5, 4)


def test_effective_sizes_respect_max_mosaic_slots(monkeypatch) -> None:
    base = get_config()
    layout = replace(base.layout, template_engine=replace(base.layout.template_engine, max_mosaic_slots=6))
    cfg = MosaicConfig(enabled=True, enabled_window_sizes=(4, 5, 6, 8, 9))
    import travelogue.config as config_mod

    monkeypatch.setattr(config_mod, "get_config", lambda: replace(base, layout=layout))
    assert effective_mosaic_window_sizes(cfg) == (4, 5, 6)


def test_mosaic_pattern_disabled_above_max_slots(monkeypatch) -> None:
    base = get_config()
    layout = replace(base.layout, template_engine=replace(base.layout.template_engine, max_mosaic_slots=6))
    mosaic = MosaicConfig(enabled=True, enabled_window_sizes=(4, 5, 6, 9))
    patched = replace(base, layout=layout, mosaic=mosaic)

    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.lte_adapter.get_config",
        lambda: patched,
    )
    assert mosaic_pattern_disabled("screen-landscape-9", cfg=mosaic)
    assert not mosaic_pattern_disabled("screen-landscape-4", cfg=mosaic)


def test_large_mosaic_per_template_trip_cap() -> None:
    st = ScreenLayoutPlannerState.from_trip_total(120)
    pid = "screen-landscape-5"
    assert is_large_mosaic_pattern(pid)
    for _ in range(2):
        st.begin_chapter_bucket()
        assert st.can_use_large_mosaic(pid)
        st.note_screen(pid)
    st.begin_chapter_bucket()
    assert not st.can_use_large_mosaic(pid)


def test_large_mosaic_per_chapter_cap() -> None:
    st = ScreenLayoutPlannerState.from_trip_total(120)
    a = "screen-landscape-5"
    b = "screen-landscape-6"
    st.begin_chapter_bucket()
    assert st.can_use_large_mosaic_window(5)
    st.note_screen(a)
    assert not st.can_use_large_mosaic_window(6)
    assert not st.can_use_large_mosaic(b)
    st.begin_chapter_bucket()
    assert st.can_use_large_mosaic(b)


def test_effective_sizes_includes_nine_when_max_slots_nine(monkeypatch) -> None:
    base = get_config()
    layout = replace(base.layout, template_engine=replace(base.layout.template_engine, max_mosaic_slots=9))
    cfg = MosaicConfig(enabled=True, enabled_window_sizes=(4, 5, 6, 9))
    import travelogue.config as config_mod

    monkeypatch.setattr(config_mod, "get_config", lambda: replace(base, layout=layout))
    assert effective_mosaic_window_sizes(cfg) == (4, 5, 6, 9)
