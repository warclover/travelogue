"""AAD-20 PrefixBeam flag wiring."""

from __future__ import annotations

from travelogue.config import get_config
from travelogue.config.layout import LayoutScoringConfig


def test_prefix_beam_flag_defaults_off() -> None:
    cfg = LayoutScoringConfig()
    assert cfg.prefix_beam_enabled is False


def test_prefix_beam_flag_from_dict() -> None:
    from travelogue.config.layout import layout_scoring_from_dict

    on = layout_scoring_from_dict({"enabled": True, "prefix_beam_enabled": True})
    assert on.prefix_beam_enabled is True
    off = layout_scoring_from_dict({"enabled": True})
    assert off.prefix_beam_enabled is False


def test_prefix_beam_module_importable() -> None:
    from travelogue.layout_engine.mosaic.prefix_beam import prefix_beam_plan_bucket

    assert callable(prefix_beam_plan_bucket)


def test_default_config_prefix_beam_off() -> None:
    cfg = get_config(reload=True)
    assert cfg.layout.scoring.prefix_beam_enabled is False
