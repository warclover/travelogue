"""MCR P0-a · mosaic_from_dict defaults match MosaicConfig dataclass."""

from __future__ import annotations

import pytest

from travelogue.config import MosaicConfig, get_config, load_config, reset_config_cache
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
