"""LSE dogfood rollout gate (W3a-04)."""

from __future__ import annotations

from pathlib import Path

import yaml

import travelogue.curation.screen_planner  # noqa: F401
from travelogue.config import AppConfig
from travelogue.config.layout import LayoutConfig, LayoutStrategyEngineConfig
from travelogue.layout_engine.rollout import (
    effective_rollout,
    lse_in_rollout_cohort,
    resolve_lse_config_for_trip,
)
from travelogue.layout_engine.runtime_store import merge_approved_patch


def _cfg_with_policy(policy_path: Path, *, enabled: bool = False) -> AppConfig:
    se = LayoutStrategyEngineConfig(
        enabled=enabled,
        policy_path=str(policy_path),
        runtime_store="data/lse_runtime_test.json",
    )
    return AppConfig(layout=LayoutConfig(strategy_engine=se))


def test_allowlist_enables_lse_without_global_flag(tmp_path: Path, monkeypatch) -> None:
    policy = tmp_path / "lse_policy.yaml"
    policy.write_text(
        yaml.safe_dump(
            {
                "rollout": {
                    "stage": "dogfood",
                    "traffic_percent": 0,
                    "allowlist_trip_ids": ["dogfood-trip-a"],
                }
            }
        ),
        encoding="utf-8",
    )
    store = tmp_path / "lse_runtime.json"
    monkeypatch.setattr(
        "travelogue.layout_engine.runtime_store.resolve_store_path",
        lambda _path=None: store,
    )
    cfg = _cfg_with_policy(policy)
    assert lse_in_rollout_cohort("dogfood-trip-a", cfg) is True
    assert lse_in_rollout_cohort("other-trip", cfg) is False
    resolved = resolve_lse_config_for_trip(cfg, "dogfood-trip-a")
    assert resolved.layout.strategy_engine.enabled is True
    assert resolve_lse_config_for_trip(cfg, "other-trip").layout.strategy_engine.enabled is False


def test_runtime_rollout_overrides_policy_traffic(tmp_path: Path, monkeypatch) -> None:
    policy = tmp_path / "lse_policy.yaml"
    policy.write_text(
        yaml.safe_dump({"rollout": {"stage": "dogfood", "traffic_percent": 0}}),
        encoding="utf-8",
    )
    store = tmp_path / "lse_runtime.json"
    monkeypatch.setattr(
        "travelogue.layout_engine.runtime_store.resolve_store_path",
        lambda _path=None: store,
    )
    merge_approved_patch(
        {"layout_strategy_rollout": {"traffic_percent": 100, "stage": "active"}},
        store_path=store,
        change_id="rollout-100",
    )
    cfg = _cfg_with_policy(policy)
    rollout = effective_rollout(cfg)
    assert rollout.traffic_percent == 100
    assert lse_in_rollout_cohort("any-trip-id", cfg) is True


def test_blocklist_wins_over_allowlist(tmp_path: Path, monkeypatch) -> None:
    policy = tmp_path / "lse_policy.yaml"
    policy.write_text(
        yaml.safe_dump(
            {
                "rollout": {
                    "allowlist_trip_ids": ["trip-x"],
                    "blocklist_trip_ids": ["trip-x"],
                }
            }
        ),
        encoding="utf-8",
    )
    store = tmp_path / "lse_runtime.json"
    monkeypatch.setattr(
        "travelogue.layout_engine.runtime_store.resolve_store_path",
        lambda _path=None: store,
    )
    cfg = _cfg_with_policy(policy)
    assert lse_in_rollout_cohort("trip-x", cfg) is False


def test_global_enabled_short_circuits_rollout() -> None:
    cfg = AppConfig(
        layout=LayoutConfig(strategy_engine=LayoutStrategyEngineConfig(enabled=True))
    )
    assert lse_in_rollout_cohort("", cfg) is True
