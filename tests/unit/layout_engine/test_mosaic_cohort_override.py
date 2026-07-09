"""Mosaic config override for cohort_coherence during chapter planning."""

from __future__ import annotations

from dataclasses import replace

import pytest

from travelogue.config import AppConfig, CohortConfig, MosaicConfig
from travelogue.layout_engine.mosaic.hook import _mosaic_cfg
from travelogue.layout_engine.mosaic.runtime import (
    cohort_mosaic_override,
    reset_mosaic_config_override,
    set_mosaic_config_override,
)

pytestmark = pytest.mark.unit


def test_cohort_mosaic_override_adds_weight() -> None:
    app = AppConfig(
        cohort=CohortConfig(enabled=True, mosaic_weight=0.05),
        mosaic=MosaicConfig(weights={"aspect_match": 0.2, "cohort_coherence": 0.0}),
    )
    patched = cohort_mosaic_override(app)
    assert patched is not None
    assert patched.weights.get("cohort_coherence") == 0.05


def test_mosaic_hook_uses_override() -> None:
    base = _mosaic_cfg()
    custom = replace(base, scorer_version="override-test")
    set_mosaic_config_override(custom)
    try:
        assert _mosaic_cfg().scorer_version == "override-test"
    finally:
        reset_mosaic_config_override()
    assert _mosaic_cfg().scorer_version == base.scorer_version
