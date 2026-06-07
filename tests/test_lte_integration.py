"""Phase 16 integration: disabled vs deprecated, lifecycle promotion, admission S5."""

from __future__ import annotations

import json

import pytest
import yaml

from travelogue.config import AppConfig
from travelogue.config.layout import LayoutConfig, LayoutTemplateEngineConfig
from travelogue.curation.mosaic.candidates import generate_window_candidates
from travelogue.curation.mosaic.constants import (
    PATTERN_MOSAIC_5_2P3L_EQUAL,
    PATTERN_MOSAIC_5_3P_2L_BALANCED,
)
from travelogue.curation.mosaic.log import MosaicWindowLog, format_log_entry
from travelogue.curation.mosaic.lte_adapter import mosaic_registry
from travelogue.layout_templates.admission import run_layout_template_admission
from travelogue.layout_templates.promotion import apply_layout_template_yaml_patch
from travelogue.layout_templates.registry import LayoutTemplateEngine, reset_engine_cache_for_tests
from travelogue.media.image_ops import AspectKind
from travelogue.templating.review import approve_review, submit_for_review


@pytest.fixture(autouse=True)
def _fresh_lte_engine(tmp_path, monkeypatch) -> None:
    reset_engine_cache_for_tests()
    state = tmp_path / "template_admin_state.json"
    state.write_text(
        json.dumps({"revision": 1, "templates": {}, "audit": [], "runtime": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr("travelogue.templating.admin_store._STATE_PATH", state)


@pytest.mark.integration
def test_deprecated_pattern_excluded_from_mcs_candidates() -> None:
    """AC-P16-06 · deprecated 模板不出现在新 trip MCS 候选中."""
    reg = mosaic_registry()
    assert PATTERN_MOSAIC_5_3P_2L_BALANCED not in reg
    asset_ids = ["p1", "p2", "p3", "l1", "l2"]
    aspects: dict[str, AspectKind] = {
        "p1": "portrait",
        "p2": "portrait",
        "p3": "portrait",
        "l1": "landscape",
        "l2": "landscape",
    }
    assets_map = {aid: {"id": aid} for aid in asset_ids}
    from travelogue.config import MosaicConfig

    out = generate_window_candidates(asset_ids, aspects, assets_map, cfg=MosaicConfig())
    assert all(c.pattern_id != PATTERN_MOSAIC_5_3P_2L_BALANCED for c in out)


@pytest.mark.integration
def test_disabled_status_excluded_from_registry(tmp_path, monkeypatch) -> None:
    """§13.2 · status=disabled 与 deprecated 独立：disabled 不进 active registry."""
    tpl_dir = tmp_path / "templates"
    tpl_dir.mkdir()
    doc = {
        "id": "screen-test-disabled",
        "version": 1,
        "status": "disabled",
        "kind": "composite",
        "displayName": "disabled probe",
        "stage": {"aspect": "16:9", "grid": [3, 3]},
        "photoCount": {"min": 3, "max": 3},
        "slots": [
            {"index": i, "rect": [1, 1, 1, 1], "role": "any", "fit": "auto"}
            for i in range(3)
        ],
        "render": {
            "gridClass": "layout-screen__grid--test-disabled",
            "cssBundle": "journal-screens.css",
        },
    }
    (tpl_dir / "screen-test-disabled.yaml").write_text(
        yaml.safe_dump(doc, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "travelogue.layout_templates.registry.DEFAULT_TEMPLATES_DIR",
        tpl_dir,
    )
    reset_engine_cache_for_tests()
    engine = LayoutTemplateEngine.load(tpl_dir, rebuild_cache=True)
    active = engine.list_active(window_size=3)
    assert "screen-test-disabled" not in {t.id for t in active}


@pytest.mark.integration
def test_overrides_disable_independent_from_deprecated_status(monkeypatch) -> None:
    """§13.2 · overrides.disable 与 deprecated 是不同关停路径."""
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
    assert PATTERN_MOSAIC_5_2P3L_EQUAL in reg
    assert PATTERN_MOSAIC_5_3P_2L_BALANCED not in reg


@pytest.mark.integration
def test_lifecycle_experimental_to_ga_admission_chain(tmp_path, monkeypatch) -> None:
    """AC-P16-09 · experimental→beta→ga admission 链（GitOps patch + review）."""
    tpl_dir = tmp_path / "templates"
    tpl_dir.mkdir()
    from travelogue.layout_templates import geometry_diff as gd_mod

    monkeypatch.setattr(gd_mod, "VERSION_HISTORY_DIR", tpl_dir / ".version_history")
    monkeypatch.setattr(
        "travelogue.layout_templates.promotion.DEFAULT_TEMPLATES_DIR",
        tpl_dir,
    )
    doc = {
        "id": "screen-test-lifecycle",
        "version": 1,
        "status": "experimental",
        "kind": "composite",
        "displayName": "lifecycle test",
        "stage": {"aspect": "16:9", "grid": [3, 3]},
        "photoCount": {"min": 5, "max": 5},
        "mix": {"portrait": 2, "landscape": 3},
        "slots": [
            {"index": 0, "rect": [1, 1, 1, 3], "role": "portrait", "fit": "auto"},
            {"index": 1, "rect": [2, 2, 1, 3], "role": "portrait", "fit": "auto"},
            {"index": 2, "rect": [3, 3, 1, 1], "role": "landscape", "fit": "cover"},
            {"index": 3, "rect": [3, 3, 2, 2], "role": "landscape", "fit": "cover"},
            {"index": 4, "rect": [3, 3, 3, 3], "role": "landscape", "fit": "cover"},
        ],
        "render": {
            "gridClass": "layout-screen__grid--test-lifecycle",
            "cssBundle": "journal-screens.css",
        },
    }
    yaml_path = tpl_dir / "screen-test-lifecycle.yaml"
    yaml_path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(
        "travelogue.layout_templates.registry.DEFAULT_TEMPLATES_DIR",
        tpl_dir,
    )
    reset_engine_cache_for_tests()

    beta_adm = run_layout_template_admission("screen-test-lifecycle", target="beta")
    assert beta_adm["ok"] is True
    probe = next(s for s in beta_adm["steps"] if s["name"] == "probe_regression")
    assert probe["ok"] is True

    apply_layout_template_yaml_patch(
        "screen-test-lifecycle",
        {"status": "beta", "version": 2},
        templates_dir=tpl_dir,
    )
    reset_engine_cache_for_tests()

    ga_adm = run_layout_template_admission("screen-test-lifecycle", target="ga")
    assert ga_adm["ok"] is False
    submit_for_review("screen-test-lifecycle", operator="test")
    approve_review("screen-test-lifecycle", reviewer="admin")
    ga_adm = run_layout_template_admission("screen-test-lifecycle", target="ga")
    assert ga_adm["ok"] is True
    assert any(s["name"] == "review_gate" and s["ok"] for s in ga_adm["steps"])

    apply_layout_template_yaml_patch(
        "screen-test-lifecycle",
        {"status": "ga", "version": 3},
        templates_dir=tpl_dir,
    )
    final = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    assert final["status"] == "ga"
    assert final["version"] == 3


@pytest.mark.unit
def test_rejected_templates_debug_only_in_mosaic_log() -> None:
    raw = MosaicWindowLog(
        rejected_templates=[{"templateId": "x", "reason": "pattern_disabled"}]
    ).to_dict()
    assert "rejectedTemplates" in format_log_entry(raw, "debug")
    assert "rejectedTemplates" not in format_log_entry(raw, "window")
    assert "rejectedTemplates" not in format_log_entry(raw, "summary")


@pytest.mark.unit
def test_admission_includes_probe_regression_step() -> None:
    report = run_layout_template_admission(PATTERN_MOSAIC_5_2P3L_EQUAL, target="beta")
    assert any(s["name"] == "probe_regression" for s in report["steps"])
