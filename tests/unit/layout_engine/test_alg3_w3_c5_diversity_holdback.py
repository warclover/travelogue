"""ALG-V3 W3-C5 · diversity holdback flag skeleton (PL-C5)."""

from __future__ import annotations

from travelogue.config import AppConfig
from travelogue.config.layout import (
    LayoutConfig,
    LayoutTemplateEngineConfig,
    layout_template_engine_from_dict,
)
from travelogue.config.misc import LlmConfig
from travelogue.curation.algo_v3_summary import build_algo_v3_summary
from travelogue.layout_engine.mosaic.lte_adapter import mcs_diversity_config


def test_diversity_holdback_defaults_false() -> None:
    te = LayoutTemplateEngineConfig()
    assert te.diversity_holdback is False
    loaded = layout_template_engine_from_dict({})
    assert loaded.diversity_holdback is False


def test_diversity_holdback_from_dict() -> None:
    te = layout_template_engine_from_dict(
        {
            "mcs_integration": {
                "scoring": {"diversity": {"mode": "mmr", "holdback": True}}
            }
        }
    )
    assert te.diversity_holdback is True


def test_holdback_forces_diversity_mode_off(monkeypatch) -> None:
    cfg = AppConfig(
        layout=LayoutConfig(
            template_engine=LayoutTemplateEngineConfig(
                diversity_mode="mmr",
                diversity_holdback=True,
                read_templates_from_lte=True,
            )
        )
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.lte_adapter.read_templates_from_lte",
        lambda cfg=None: True,
    )
    div = mcs_diversity_config(cfg=cfg)
    assert div["holdback"] is True
    assert div["mode"] == "off"


def test_algo_v3_exposes_holdback(monkeypatch) -> None:
    monkeypatch.setattr(
        "travelogue.llm.ready.probe_llm_ready",
        lambda *, cfg=None: False,
    )
    cfg = AppConfig(
        llm=LlmConfig(capability="auto"),
        layout=LayoutConfig(
            template_engine=LayoutTemplateEngineConfig(diversity_holdback=False)
        ),
    )
    summary = build_algo_v3_summary({"assets": [], "curation": {}}, cfg=cfg)
    assert summary["diversityHoldback"] is False
    assert "diversityModeEffective" in summary
