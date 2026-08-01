"""TPC W3 · hand-authored templates hit mix index without Python branches."""

from __future__ import annotations

from dataclasses import replace

import pytest

from travelogue.config import get_config
from travelogue.config.mosaic import (
    TemplateContractConfig,
    TemplateExperimentsConfig,
)
from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_engine.contract.evaluator import (
    contract_pattern_ids_for_window,
    reset_evaluator_state_for_tests,
)
from travelogue.layout_engine.contract.mix_index import format_mix_key, mix_key_from_aspects
from travelogue.layout_engine.contract.shadow import reset_mix_index_cache_for_tests
from travelogue.layout_engine.mosaic.builders import try_order_for_pattern
from travelogue.layout_engine.mosaic.candidates import (
    generate_window_candidates_with_rejections,
)
from travelogue.layout_templates.registry import get_engine, reset_engine_cache_for_tests

TPC_W3_IDS = (
    "screen-mosaic-4-1l3p-rail",
    "screen-mosaic-5-2p3l-rail",
    "screen-mosaic-4-2l2p-weighted",
    "screen-mosaic-4-hero-70-sidebar",
)


@pytest.fixture(autouse=True)
def _reset_caches() -> None:
    reset_engine_cache_for_tests()
    reset_evaluator_state_for_tests()
    reset_mix_index_cache_for_tests()
    yield
    reset_engine_cache_for_tests()
    reset_evaluator_state_for_tests()
    reset_mix_index_cache_for_tests()


def _assets_for_mix(
    *, landscape: int, portrait: int
) -> tuple[list[str], dict[str, AspectKind], dict[str, dict]]:
    ids: list[str] = []
    aspects: dict[str, AspectKind] = {}
    assets: dict[str, dict] = {}
    seq = 0
    for i in range(landscape):
        aid = f"l{i}"
        ids.append(aid)
        aspects[aid] = "landscape"
        assets[aid] = {
            "id": aid,
            "width": 1600,
            "height": 900,
            # Keep all assets inside Scene Atom gap (≤10 min) for MCS tests.
            "takenAt": f"2024-06-01T12:00:{seq:02d}Z",
        }
        seq += 1
    for i in range(portrait):
        aid = f"p{i}"
        ids.append(aid)
        aspects[aid] = "portrait"
        assets[aid] = {
            "id": aid,
            "width": 900,
            "height": 1600,
            "takenAt": f"2024-06-01T12:00:{seq:02d}Z",
        }
        seq += 1
    return ids, aspects, assets


@pytest.mark.parametrize(
    "template_id,landscape,portrait",
    [
        ("screen-mosaic-4-1l3p-rail", 1, 3),
        ("screen-mosaic-5-2p3l-rail", 3, 2),
        ("screen-mosaic-4-2l2p-weighted", 2, 2),
        ("screen-mosaic-4-hero-70-sidebar", 4, 0),
    ],
)
def test_ac_tpc_02_yaml_only_mix_hit(
    template_id: str, landscape: int, portrait: int
) -> None:
    """AC-TPC-02: new YAML templates are mix-index hittable with zero Python branches."""
    engine = get_engine()
    tmpl = engine.get(template_id)
    # LTN C3 · 4-hero promoted to ga; rails remain experimental.
    assert tmpl.status in ("experimental", "ga")
    assert (tmpl.raw or {}).get("usage", {}).get("summary")
    assert (tmpl.constraints or {}).get("eligibility")

    ids, aspects, assets = _assets_for_mix(landscape=landscape, portrait=portrait)
    key = mix_key_from_aspects(ids, aspects)
    assert format_mix_key(key) == f"L{landscape}P{portrait}S0"

    hit_ids, source, _sq, _inf = contract_pattern_ids_for_window(ids, aspects)
    assert template_id in hit_ids
    assert source in ("exact", "fallback")

    ordered = try_order_for_pattern(
        template_id,
        ids,
        aspects,
        assets,
        burst_seconds=12.0,
        median_sharp=0.5,
    )
    assert ordered is not None
    assert len(ordered) == len(ids)


def test_w3_templates_in_list_active() -> None:
    active = {t.id for t in get_engine().list_active(enforce_quotas=False)}
    for tid in TPC_W3_IDS:
        assert tid in active


def test_enabled_contract_does_not_emit_w3_experimental() -> None:
    """MTSO D-01 · TPC ON alone must not unlock experimental rails."""
    ids, aspects, assets = _assets_for_mix(landscape=1, portrait=3)
    cfg = replace(
        get_config().mosaic,
        template_contract=TemplateContractConfig(enabled=True, shadow_log=False),
        template_experiments=TemplateExperimentsConfig(enabled=False),
        enabled_window_sizes=(4, 5, 6, 9),
    )
    result = generate_window_candidates_with_rejections(
        ids, aspects, assets, cfg=cfg
    )
    pattern_ids = {c.pattern_id for c in result.candidates}
    assert "screen-mosaic-4-1l3p-rail" not in pattern_ids


def test_template_experiments_emits_w3_candidate() -> None:
    """MTSO · experiments triple admits W3 experimental into candidates."""
    from travelogue.config.app import AppConfig

    ids, aspects, assets = _assets_for_mix(landscape=1, portrait=3)
    trip_id = "mtso-dogfood-trip"
    cfg = replace(
        AppConfig().mosaic,
        template_contract=TemplateContractConfig(enabled=True, shadow_log=False),
        template_experiments=TemplateExperimentsConfig(
            enabled=True,
            allowlist=("screen-mosaic-4-1l3p-rail",),
            cohort_trip_ids=(trip_id,),
        ),
        enabled_window_sizes=(4, 5, 6, 9),
    )
    result = generate_window_candidates_with_rejections(
        ids, aspects, assets, cfg=cfg, trip_id=trip_id
    )
    pattern_ids = {c.pattern_id for c in result.candidates}
    assert "screen-mosaic-4-1l3p-rail" in pattern_ids
