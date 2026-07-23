"""MCR P0-a · mosaic_from_dict defaults match MosaicConfig dataclass."""

from __future__ import annotations

import pytest

from travelogue.config import MosaicConfig, load_config, reset_config_cache
from travelogue.config.mosaic import mosaic_from_dict


@pytest.fixture(autouse=True)
def _restore_config_cache() -> None:
    yield
    reset_config_cache()


def test_empty_dict_matches_dataclass_defaults() -> None:
    defaults = MosaicConfig()
    cfg = mosaic_from_dict({})
    assert cfg.enabled_window_sizes == defaults.enabled_window_sizes
    assert cfg.enabled is defaults.enabled
    assert cfg.density_budget.enabled is defaults.density_budget.enabled
    assert cfg.template_contract.enabled is False
    assert cfg.template_contract.shadow_log is False
    assert cfg.template_experiments.enabled is False
    assert cfg.selection_optimization.enabled is False
    assert cfg.near_scene_clone_gate.enabled is defaults.near_scene_clone_gate.enabled


def test_template_contract_parses_known_keys() -> None:
    cfg = mosaic_from_dict(
        {"template_contract": {"enabled": True, "shadow_log": True}}
    )
    assert cfg.template_contract.enabled is True
    assert cfg.template_contract.shadow_log is True


def test_template_contract_unknown_key_fail_loud() -> None:
    with pytest.raises(ValueError, match="unknown keys"):
        mosaic_from_dict({"template_contract": {"enabled": False, "softPenalty": 0.1}})


def test_near_scene_clone_gate_parses_and_fails_loud() -> None:
    cfg = mosaic_from_dict({"near_scene_clone_gate": {"enabled": True}})
    assert cfg.near_scene_clone_gate.enabled is True
    cfg2 = mosaic_from_dict({"nearSceneCloneGate": {"enabled": True}})
    assert cfg2.near_scene_clone_gate.enabled is True
    with pytest.raises(ValueError, match="unknown keys"):
        mosaic_from_dict({"near_scene_clone_gate": {"enabled": True, "bogus": 1}})


def test_partial_dict_merges_defaults() -> None:
    defaults = MosaicConfig()
    cfg = mosaic_from_dict({"enabled": False})
    assert cfg.enabled is False
    assert cfg.enabled_window_sizes == defaults.enabled_window_sizes
    assert cfg.min_candidate_score == defaults.min_candidate_score


def test_load_config_without_mosaic_section(tmp_path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        """
trips_dir: ./trips
layout:
  web_layout_engine: screens
""".strip(),
        encoding="utf-8",
    )
    defaults = MosaicConfig()
    cfg = load_config(cfg_path)
    assert cfg.mosaic.enabled_window_sizes == defaults.enabled_window_sizes


def test_load_config_verbose_logs_mosaic_defaults(tmp_path, caplog) -> None:
    import os

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("trips_dir: ./trips\n", encoding="utf-8")
    caplog.set_level("INFO")
    prev = os.environ.get("TRAVELOGUE_CONFIG_VERBOSE")
    os.environ["TRAVELOGUE_CONFIG_VERBOSE"] = "1"
    try:
        load_config(cfg_path)
    finally:
        if prev is None:
            os.environ.pop("TRAVELOGUE_CONFIG_VERBOSE", None)
        else:
            os.environ["TRAVELOGUE_CONFIG_VERBOSE"] = prev
    assert any("enabled_window_sizes" in r.message for r in caplog.records)
