"""MTSO PR-A · lifecycle_admit + funnel schema + registry guard."""

from __future__ import annotations

from dataclasses import replace

import pytest

from travelogue.config import get_config
from travelogue.config.mosaic import (
    TemplateContractConfig,
    TemplateExperimentsConfig,
    effective_selection_optimization_enabled,
    mosaic_from_dict,
)
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_MOSAIC_5_2P3L_EQUAL,
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
)
from travelogue.layout_engine.mosaic.legacy import build_legacy_screen
from travelogue.layout_engine.mosaic.lifecycle import (
    SIX_HERO_FAMILY_CANONICAL,
    lifecycle_admit,
    six_hero_family_id,
)
from travelogue.layout_engine.mosaic.log import MosaicWindowLog
from travelogue.layout_engine.mosaic.lte_adapter import (
    mosaic_pattern_disabled,
    mosaic_registry,
    read_templates_from_lte,
)
from travelogue.layout_templates.registry import get_engine, reset_engine_cache_for_tests


@pytest.fixture(autouse=True)
def _reset_engine() -> None:
    reset_engine_cache_for_tests()
    yield
    reset_engine_cache_for_tests()


def test_contract_on_experiments_off_excludes_rails_from_registry() -> None:
    app = replace(
        get_config(),
        mosaic=replace(
            get_config().mosaic,
            template_contract=TemplateContractConfig(enabled=True),
            template_experiments=TemplateExperimentsConfig(enabled=False),
        ),
    )
    keys = set(mosaic_registry(cfg=app).keys())
    assert "screen-mosaic-4-1l3p-rail" not in keys
    assert "screen-mosaic-5-2p3l-rail" not in keys


def test_experiments_empty_cohort_fail_closed() -> None:
    app = replace(
        get_config(),
        mosaic=replace(
            get_config().mosaic,
            template_experiments=TemplateExperimentsConfig(
                enabled=True,
                allowlist=("screen-mosaic-4-1l3p-rail",),
                cohort_trip_ids=(),
            ),
        ),
    )
    admit = lifecycle_admit(
        "screen-mosaic-4-1l3p-rail",
        app=app,
        mosaic_cfg=app.mosaic,
        trip_id="any-trip",
    )
    assert not admit.ok
    assert admit.reason == "lifecycle_cohort_miss"
    assert "screen-mosaic-4-1l3p-rail" not in mosaic_registry(cfg=app, trip_id="any-trip")


def test_experiments_triple_admits_rail() -> None:
    trip_id = "mtso-a-cohort"
    app = replace(
        get_config(),
        mosaic=replace(
            get_config().mosaic,
            template_experiments=TemplateExperimentsConfig(
                enabled=True,
                allowlist=("screen-mosaic-4-1l3p-rail",),
                cohort_trip_ids=(trip_id,),
            ),
        ),
    )
    admit = lifecycle_admit(
        "screen-mosaic-4-1l3p-rail",
        app=app,
        mosaic_cfg=app.mosaic,
        trip_id=trip_id,
    )
    assert admit.ok
    assert "screen-mosaic-4-1l3p-rail" in mosaic_registry(cfg=app, trip_id=trip_id)


def test_deprecated_equal_never_admitted() -> None:
    assert not lifecycle_admit(PATTERN_MOSAIC_5_2P3L_EQUAL).ok
    assert mosaic_pattern_disabled(PATTERN_MOSAIC_5_2P3L_EQUAL)


def test_lte_off_hard_denies_equal() -> None:
    if read_templates_from_lte():
        pytest.skip("LTE on in this environment")
    assert not lifecycle_admit(PATTERN_MOSAIC_5_2P3L_EQUAL).ok


def test_legacy_construct_rejects_deprecated_dense() -> None:
    ids = [f"p{i}" for i in range(6)]
    aspects = {aid: "portrait" for aid in ids}
    assets = {
        aid: {"id": aid, "width": 900, "height": 1600, "takenAt": f"2024-01-01T0{i}:00:00Z"}
        for i, aid in enumerate(ids)
    }
    assert build_legacy_screen(ids, 6, aspects, assets) is None

    ids9 = [f"p{i}" for i in range(9)]
    aspects9 = {aid: "portrait" for aid in ids9}
    assets9 = {
        aid: {"id": aid, "width": 900, "height": 1600, "takenAt": f"2024-01-01T0{i}:00:00Z"}
        for i, aid in enumerate(ids9)
    }
    assert build_legacy_screen(ids9, 9, aspects9, assets9) is None


def test_six_hero_family_resolver() -> None:
    assert six_hero_family_id(PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4) == SIX_HERO_FAMILY_CANONICAL
    assert six_hero_family_id(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5) == SIX_HERO_FAMILY_CANONICAL
    assert six_hero_family_id("screen-landscape-4") is None


def test_funnel_fields_present_in_raw_log() -> None:
    raw = MosaicWindowLog(
        base_window_order=[5, 4, 6],
        effective_window_order=[5, 4, 6],
        reject_funnel=[{"templateId": "x", "reason": "geometry_invalid"}],
    ).to_dict()
    for key in (
        "baseWindowOrder",
        "effectiveWindowOrder",
        "reorderReason",
        "structurallyQualifiedSix",
        "admitSixHero",
        "sixHeroOpportunityState",
        "sixHeroFamilyId",
        "quotaSnapshot",
        "rejectFunnel",
    ):
        assert key in raw
    assert raw["sixHeroOpportunityState"] == "idle"
    assert raw["structurallyQualifiedSix"] is False
    assert raw["admitSixHero"] is False


def test_default_registry_has_zero_experimental() -> None:
    """T-MTSO-07 · default emit set must not expose experimental / deprecated."""
    keys = set(mosaic_registry().keys())
    engine = get_engine()
    for pid in keys:
        try:
            tpl = engine.get(pid)
        except KeyError:
            continue
        status = str(getattr(tpl, "status", "") or "")
        assert status not in ("experimental", "deprecated", "disabled"), pid
        rollout = getattr(tpl, "rollout", None) or {}
        if isinstance(rollout, dict):
            assert int(rollout.get("percent", 100)) > 0, pid


def test_selection_optimization_shell_defaults() -> None:
    cfg = mosaic_from_dict({})
    assert cfg.template_experiments.enabled is False
    assert cfg.selection_optimization.enabled is False
    assert effective_selection_optimization_enabled(cfg) is False
    on = mosaic_from_dict({"selection_optimization": {"enabled": True}})
    assert effective_selection_optimization_enabled(on) is True
    with pytest.raises(ValueError, match="unknown keys"):
        mosaic_from_dict({"template_experiments": {"enabled": True, "bogus": 1}})
