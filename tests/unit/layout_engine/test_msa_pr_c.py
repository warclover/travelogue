"""MSA PR-C · MTSO×MSA switch matrix + non-goal guards (AC-10 / N01–N03)."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from itertools import product

import pytest

from travelogue.config import get_config
from travelogue.config.mosaic import (
    SelectionOptimizationConfig,
    SlotAdaptationConfig,
    TemplateContractConfig,
    TemplateExperimentsConfig,
    effective_selection_optimization_enabled,
    effective_slot_adaptation_enabled,
    mosaic_from_dict,
)
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,
    PATTERN_MOSAIC_5_2P3L_EQUAL,
)
from travelogue.layout_engine.mosaic.lifecycle import lifecycle_admit
from travelogue.layout_engine.mosaic.lte_adapter import mosaic_registry
from travelogue.layout_engine.mosaic.msa_apply import maybe_apply_slot_adaptation
from travelogue.layout_templates.geometry_solidify import solidify_screen_geometry
from travelogue.layout_templates.registry import get_engine, reset_engine_cache_for_tests

PATTERN_6 = "screen-mosaic-6-main-hero-plus-5"
TRIP = "msa-mtso-matrix-trip"


@pytest.fixture(autouse=True)
def _reset_engine() -> None:
    reset_engine_cache_for_tests()
    yield
    reset_engine_cache_for_tests()


def _land(aid: str, *, w: int = 3000, h: int = 2000) -> dict:
    return {
        "id": aid,
        "width": w,
        "height": h,
        "aspectKind": "landscape",
        "quality": {"sharpness": 0.9},
    }


def _mosaic(
    *,
    msa: bool,
    so: bool,
    experiments: bool,
) -> object:
    base = mosaic_from_dict({})
    return replace(
        base,
        template_contract=TemplateContractConfig(enabled=True, shadow_log=False),
        selection_optimization=SelectionOptimizationConfig(enabled=so),
        template_experiments=TemplateExperimentsConfig(
            enabled=experiments,
            allowlist=(PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,) if experiments else (),
            cohort_trip_ids=(TRIP,) if experiments else (),
        ),
        slot_adaptation=SlotAdaptationConfig(enabled=msa),
    )


@pytest.mark.parametrize(
    "msa,so,experiments",
    list(product([False, True], [False, True], [False, True])),
)
def test_ac10_lifecycle_orthogonal_to_msa(
    msa: bool, so: bool, experiments: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """MSA ON/OFF must not change experimental lifecycle admit (AC-10 / N-03)."""
    mosaic = _mosaic(msa=msa, so=so, experiments=experiments)
    app = replace(get_config(), mosaic=mosaic)
    monkeypatch.setattr("travelogue.config.get_config", lambda: app)

    assert effective_slot_adaptation_enabled(mosaic) is msa
    assert effective_selection_optimization_enabled(mosaic) is so

    # Deprecated / equal rail never visible
    assert not lifecycle_admit(PATTERN_MOSAIC_5_2P3L_EQUAL, app=app, trip_id=TRIP).ok

    admit = lifecycle_admit(
        PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO, app=app, trip_id=TRIP
    )
    if experiments:
        assert admit.ok, (msa, so, experiments, admit)
        assert PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO in mosaic_registry(
            cfg=app, trip_id=TRIP
        )
    else:
        assert not admit.ok
        assert PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO not in mosaic_registry(
            cfg=app, trip_id=TRIP
        )


def test_ac10_msa_off_zero_writes_under_mtso_on(monkeypatch: pytest.MonkeyPatch) -> None:
    assets = {f"a{i}": _land(f"a{i}") for i in range(6)}
    screen = {
        "patternId": PATTERN_6,
        "slots": [
            {
                "slot": i,
                "assetId": f"a{i}",
                "role": "main" if i == 0 else "tile",
                "fit": "cover",
            }
            for i in range(6)
        ],
    }
    mosaic = _mosaic(msa=False, so=True, experiments=True)
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.msa_apply.get_effective_mosaic_config",
        lambda: mosaic,
    )
    solidify_screen_geometry(screen, PATTERN_6, assets_map=assets)
    before = deepcopy(screen["layoutGeometry"])
    summary = maybe_apply_slot_adaptation(
        screen, PATTERN_6, assets_map=assets, cfg=mosaic
    )
    assert summary["msaOutcome"] == "skipped_parent_off"
    assert "trackOverride" not in (screen.get("layoutGeometry") or {})
    assert screen["layoutGeometry"]["cols"] == before["cols"]


def test_ac10_msa_on_does_not_alter_stage_aspect(monkeypatch: pytest.MonkeyPatch) -> None:
    """N-01 · stage AR stays 16:9 contract; topology rects unchanged."""
    assets = {f"a{i}": _land(f"a{i}") for i in range(6)}
    screen = {
        "patternId": PATTERN_6,
        "slots": [
            {
                "slot": i,
                "assetId": f"a{i}",
                "role": "main" if i == 0 else "tile",
                "fit": "cover",
            }
            for i in range(6)
        ],
    }
    mosaic = _mosaic(msa=True, so=True, experiments=False)
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.msa_apply.get_effective_mosaic_config",
        lambda: mosaic,
    )
    tpl = get_engine().get(PATTERN_6)
    rects_before = [tuple(s.rect) for s in tpl.slots]
    solidify_screen_geometry(screen, PATTERN_6, assets_map=assets)
    maybe_apply_slot_adaptation(screen, PATTERN_6, assets_map=assets, cfg=mosaic)
    geo = screen["layoutGeometry"]
    assert geo.get("stageAspect") == "16:9"
    assert [tuple(s.rect) for s in tpl.slots] == rects_before
    assert len(screen["slots"]) == 6
    # N-02 · no parallel pattern id rewrite
    assert screen.get("patternId") == PATTERN_6


def test_ac11_repo_default_slot_adaptation_off() -> None:
    """Default-on decision holds false until blind review signs (AC-11)."""
    cfg = mosaic_from_dict({})
    assert cfg.slot_adaptation.enabled is False
    assert effective_slot_adaptation_enabled(cfg) is False
