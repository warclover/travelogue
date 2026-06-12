"""LSE adapter · audit A mapping parity (IMPLEMENTATION §3)."""

from __future__ import annotations

from dataclasses import replace

import travelogue.curation.screen_planner  # noqa: F401 — complete adapter import cycle
from travelogue.config import get_config
from travelogue.layout_engine.adapter import (
    mixed_proximity_from_pack,
    mosaic_config_from_pack,
    resolve_pack,
    strategy_trace_meta,
)
from travelogue.layout_engine.registry import get_strategy_pack


def _cfg_lse_on():
    base = get_config(reload=True)
    se = replace(base.layout.strategy_engine, enabled=True)
    layout = replace(base.layout, strategy_engine=se)
    return replace(base, layout=layout)


def test_default_pack_mosaic_weights_match_config() -> None:
    cfg = _cfg_lse_on()
    pack = get_strategy_pack("lse-default-2026-06")
    injected = mosaic_config_from_pack(cfg, pack=pack)
    baseline = cfg.mosaic
    profile = (pack.raw.get("scoring_profiles") or {}).get("default") or {}
    for key, val in (profile.get("weights") or {}).items():
        assert injected.weights[str(key)] == float(val)
    for key, val in (profile.get("penalties") or {}).items():
        assert injected.penalties[str(key)] == float(val)
    assert injected.min_candidate_score == baseline.min_candidate_score
    assert injected.enabled_window_sizes == baseline.enabled_window_sizes


def test_default_pack_layout_state_matches_config_path() -> None:
    """LSE pack path must inherit P21 dense/large-mosaic quotas from config path."""
    import travelogue.curation.screen_planner  # noqa: F401

    from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState, RhythmRules
    from travelogue.layout_engine.adapter import layout_state_for_trip

    cfg = _cfg_lse_on()
    pack = get_strategy_pack("lse-default-2026-06")
    total = 100
    off = ScreenLayoutPlannerState.from_trip_total(
        total,
        density="balanced",
        rhythm=RhythmRules.from_config(cfg),
    )
    on = layout_state_for_trip(total, cfg=cfg, density="balanced", pack=pack)
    assert on.nine_min == off.nine_min
    assert on.nine_max == off.nine_max
    assert on.dense_collage_max == off.dense_collage_max
    assert on.portrait_grid8_max == off.portrait_grid8_max
    assert on.large_mosaic_min_slots == off.large_mosaic_min_slots
    assert on.large_mosaic_max_per_template_trip == off.large_mosaic_max_per_template_trip
    assert on.large_mosaic_max_per_chapter == off.large_mosaic_max_per_chapter


def test_mixed_proximity_from_default_pack() -> None:
    cfg = _cfg_lse_on()
    pack = resolve_pack(cfg)
    assert mixed_proximity_from_pack(pack, cfg=cfg) == 12.0


def test_strategy_trace_disabled() -> None:
    cfg = get_config(reload=True)
    se = replace(cfg.layout.strategy_engine, enabled=False)
    meta = strategy_trace_meta(replace(cfg, layout=replace(cfg.layout, strategy_engine=se)))
    assert meta == {"enabled": False}
    assert "strategyId" not in meta
    assert "weightsHash" not in meta
