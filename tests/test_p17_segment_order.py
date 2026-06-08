"""P17 CAP-06 segment order optimizer."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from travelogue.config import get_config
from travelogue.layout_engine.segment_order import (
    apply_segment_order_to_buckets,
    optimize_bucket_asset_ids,
    same_person_run_lengths,
)
from scripts.phase3_ig2_report import _cfg_for_mode, load_fixture_trip
from travelogue.layout_engine.metrics import curate_trip_chapters, same_person_run_p50


def test_burst_reorder_improves_person_runs() -> None:
    assets = [
        {"id": "p1", "tags": ["person"], "takenAt": "2025-01-01T10:00:00Z", "burstGroupId": "b1"},
        {"id": "l1", "tags": ["landscape"], "takenAt": "2025-01-01T10:00:00Z", "burstGroupId": "b1"},
        {"id": "p2", "tags": ["person"], "takenAt": "2025-01-01T10:00:00Z", "burstGroupId": "b1"},
        {"id": "l2", "tags": ["landscape"], "takenAt": "2025-01-01T10:00:00Z", "burstGroupId": "b1"},
    ]
    assets_map = {a["id"]: a for a in assets}
    base = ["p1", "l1", "p2", "l2"]
    optimized = optimize_bucket_asset_ids(base, assets_map)
    assert same_person_run_lengths(optimized, assets_map) >= same_person_run_lengths(base, assets_map)


def test_segment_order_cap_on_fixture(tmp_path: Path) -> None:
    trip = load_fixture_trip("golden-p17-mixed-person")
    assets_map = {a["id"]: a for a in trip["assets"]}
    base_cfg = _cfg_for_mode("p3_full")
    se = replace(base_cfg.layout.strategy_engine, enabled=True)
    caps = replace(
        se.capabilities,
        segment_order_optimizer=True,
        saliency_scoring=False,
    )
    se = replace(se, capabilities=caps)
    layout = replace(base_cfg.layout, strategy_engine=se)
    cfg_on = replace(base_cfg, layout=layout)

    off_chapters = curate_trip_chapters(trip, work_dir=tmp_path / "off", cfg=base_cfg)
    on_chapters = curate_trip_chapters(trip, work_dir=tmp_path / "on", cfg=cfg_on)
    off_p50 = same_person_run_p50(off_chapters, assets_map)
    on_p50 = same_person_run_p50(on_chapters, assets_map)
    assert off_p50 is not None
    assert on_p50 is not None
    assert on_p50 >= off_p50


def test_lse_pack_segment_order_flag() -> None:
    from travelogue.layout_engine.adapter import resolve_pack
    from travelogue.layout_engine.capabilities import effective_capabilities

    cfg = get_config(reload=True)
    se = replace(cfg.layout.strategy_engine, enabled=True)
    cfg_on = replace(cfg, layout=replace(cfg.layout, strategy_engine=se))
    pack = resolve_pack(cfg_on)
    caps = effective_capabilities(cfg_on, pack)
    assert caps.segment_order_optimizer is False
