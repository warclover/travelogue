"""PRD §6 · layout.mosaic_v2 YAML alias merges into mosaic config."""

from __future__ import annotations

import pytest

from travelogue.config import get_config, reset_config_cache


@pytest.fixture(autouse=True)
def _restore_config_cache_after_alias_test() -> None:
    yield
    reset_config_cache()


def test_layout_mosaic_v2_alias_overridden_by_top_level_mosaic(tmp_path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        """
layout:
  mosaic_v2:
    enabled: false
    min_candidate_score: 0.99
mosaic:
  enabled: true
  min_candidate_score: 0.35
""".strip(),
        encoding="utf-8",
    )
    reset_config_cache()
    cfg = get_config(reload=True, path=cfg_path)
    assert cfg.mosaic.enabled is True
    assert cfg.mosaic.min_candidate_score == 0.35
