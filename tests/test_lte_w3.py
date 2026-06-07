"""W3: LTE default switch, geometry solidify, collage filter, admission."""

from __future__ import annotations

import pytest

from travelogue.config import AppConfig
from travelogue.config.layout import LayoutConfig, LayoutTemplateEngineConfig
from travelogue.curation.mosaic.builders import build_screen, try_order_for_pattern
from travelogue.curation.mosaic.candidates import generate_window_candidates
from travelogue.curation.mosaic.constants import (
    PATTERN_MOSAIC_5_2P3L_EQUAL,
    PATTERN_MOSAIC_5_3P_2L_BALANCED,
)
from travelogue.curation.mosaic.lte_adapter import mosaic_registry, read_templates_from_lte
from travelogue.curation.mosaic.pattern_catalog import patterns_for_window_size
from travelogue.layout_templates.admission import run_layout_template_admission
from travelogue.layout_templates.registry import reset_engine_cache_for_tests
from travelogue.media.image_ops import AspectKind


@pytest.fixture(autouse=True)
def _fresh_lte_engine() -> None:
    reset_engine_cache_for_tests()


@pytest.mark.unit
def test_read_templates_from_lte_defaults_true() -> None:
    cfg = AppConfig(layout=LayoutConfig())
    assert read_templates_from_lte(cfg) is True
    assert LayoutTemplateEngineConfig().read_templates_from_lte is True


@pytest.mark.unit
def test_lte_registry_excludes_deprecated_includes_flagship() -> None:
    reg = mosaic_registry()
    assert PATTERN_MOSAIC_5_3P_2L_BALANCED not in reg
    assert PATTERN_MOSAIC_5_2P3L_EQUAL in reg


@pytest.mark.unit
def test_patterns_for_window_size_includes_lte_extras() -> None:
    reg = mosaic_registry()
    five = patterns_for_window_size(5, reg)
    ids = [p.pattern_id for p in five]
    assert PATTERN_MOSAIC_5_2P3L_EQUAL in ids


@pytest.mark.unit
def test_geometry_solidify_on_build_screen() -> None:
    reg = mosaic_registry()
    pat = reg[PATTERN_MOSAIC_5_2P3L_EQUAL]
    assets_map = {
        f"a{i}": {"id": f"a{i}", "takenAt": f"2024-01-0{i}T12:00:00"}
        for i in range(1, 6)
    }
    aspects: dict[str, AspectKind] = {
        "a1": "portrait",
        "a2": "portrait",
        "a3": "landscape",
        "a4": "landscape",
        "a5": "landscape",
    }
    ordered = try_order_for_pattern(
        pat.pattern_id,
        list(aspects),
        aspects,
        assets_map,
        burst_seconds=12.0,
        median_sharp=None,
    )
    assert ordered is not None
    screen = build_screen(pat, ordered, assets_map=assets_map)
    assert "layoutGeometry" in screen
    assert screen["layoutGeometry"]["gridClass"] == pat.grid_class
    assert len(screen["slots"]) == 5
    assert all("displayAspect" in slot for slot in screen["slots"])


@pytest.mark.unit
def test_collage_assets_excluded_from_mosaic_candidates(monkeypatch) -> None:
    from travelogue.config import MosaicConfig, get_config

    cfg = get_config()
    monkeypatch.setattr(
        "travelogue.curation.mosaic.candidates.get_config",
        lambda: AppConfig(
            layout=LayoutConfig(
                template_engine=LayoutTemplateEngineConfig(exclude_collage_from_mosaic=True)
            ),
            mosaic=cfg.mosaic,
        ),
    )
    asset_ids = ["p1", "p2", "l1", "l2", "l3"]
    aspects: dict[str, AspectKind] = {
        "p1": "portrait",
        "p2": "portrait",
        "l1": "landscape",
        "l2": "landscape",
        "l3": "landscape",
    }
    assets_map = {
        "p1": {"id": "p1", "mediaClass": "collage"},
        "p2": {"id": "p2"},
        "l1": {"id": "l1"},
        "l2": {"id": "l2"},
        "l3": {"id": "l3"},
    }
    out = generate_window_candidates(
        asset_ids,
        aspects,
        assets_map,
        cfg=MosaicConfig(),
    )
    assert out == []


@pytest.mark.unit
def test_layout_template_admission_flagship_beta() -> None:
    report = run_layout_template_admission(PATTERN_MOSAIC_5_2P3L_EQUAL, target="beta")
    assert report["ok"] is True
    step_names = [s["name"] for s in report["steps"]]
    assert "registry" in step_names
    assert "geometry_static" in step_names


@pytest.mark.unit
def test_overrides_disable_removes_pattern_from_registry(monkeypatch) -> None:
    from travelogue.config import get_config

    cfg = get_config()
    monkeypatch.setattr(
        "travelogue.curation.mosaic.lte_adapter.get_config",
        lambda: AppConfig(
            layout=LayoutConfig(
                template_engine=LayoutTemplateEngineConfig(
                    read_templates_from_lte=True,
                    overrides_disable=("screen-portrait-3",),
                )
            ),
            mosaic=cfg.mosaic,
        ),
    )
    reg = mosaic_registry()
    assert "screen-portrait-3" not in reg


@pytest.mark.unit
def test_overrides_disable_excludes_from_window_candidates(monkeypatch) -> None:
    from travelogue.config import MosaicConfig, get_config

    cfg = get_config()
    app = AppConfig(
        layout=LayoutConfig(
            template_engine=LayoutTemplateEngineConfig(
                read_templates_from_lte=True,
                overrides_disable=("screen-portrait-3",),
            )
        ),
        mosaic=cfg.mosaic,
    )
    monkeypatch.setattr("travelogue.curation.mosaic.lte_adapter.get_config", lambda: app)
    monkeypatch.setattr("travelogue.curation.mosaic.candidates.get_config", lambda: app)
    asset_ids = ["a1", "a2", "a3"]
    aspects: dict[str, AspectKind] = {"a1": "portrait", "a2": "portrait", "a3": "portrait"}
    assets_map = {aid: {"id": aid} for aid in asset_ids}
    out = generate_window_candidates(
        asset_ids,
        aspects,
        assets_map,
        cfg=MosaicConfig(),
        registry=mosaic_registry(app),
    )
    assert all(c.pattern_id != "screen-portrait-3" for c in out)


@pytest.mark.unit
def test_template_engine_disabled_uses_legacy_registry(monkeypatch) -> None:
    from travelogue.curation.mosaic.pattern_catalog import default_registry

    monkeypatch.setattr(
        "travelogue.curation.mosaic.lte_adapter.get_config",
        lambda: AppConfig(
            layout=LayoutConfig(
                template_engine=LayoutTemplateEngineConfig(
                    enabled=False,
                    read_templates_from_lte=True,
                )
            )
        ),
    )
    assert read_templates_from_lte() is False
    assert mosaic_registry() == default_registry()
