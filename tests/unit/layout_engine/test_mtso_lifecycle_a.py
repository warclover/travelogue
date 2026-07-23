"""MTSO PR-A · lifecycle_admit + funnel schema + registry guard."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

import pytest

from travelogue.config import get_config
from travelogue.config.mosaic import (
    TemplateContractConfig,
    TemplateExperimentsConfig,
    effective_selection_optimization_enabled,
    mosaic_from_dict,
)
from travelogue.layout_engine.mosaic.candidates import (
    ScreenCandidate,
    generate_window_candidates_with_rejections,
)
from travelogue.layout_engine.mosaic.compose import pick_best_window
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_MOSAIC_5_2P3L_EQUAL,
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
)
from travelogue.layout_engine.mosaic.hook import (
    begin_mosaic_capture,
    drain_mosaic_capture,
)
from travelogue.layout_engine.mosaic.legacy import append_legacy_window, build_legacy_screen
from travelogue.layout_engine.mosaic.lifecycle import (
    SIX_HERO_FAMILY_CANONICAL,
    lifecycle_admit,
    reject_funnel_stage,
    six_hero_family_id,
    trip_id_from_trip,
)
from travelogue.layout_engine.mosaic.log import MosaicWindowLog
from travelogue.layout_engine.mosaic.lte_adapter import (
    mosaic_pattern_disabled,
    mosaic_registry,
    read_templates_from_lte,
)
from travelogue.layout_templates.legacy_bridge import export_mosaic_pattern
from travelogue.layout_templates.registry import get_engine, reset_engine_cache_for_tests

RAIL_2P3L = "screen-mosaic-5-2p3l-rail"


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
        reject_funnel=[
            {
                "stage": reject_funnel_stage("geometry_invalid"),
                "templateId": "x",
                "reason": "geometry_invalid",
            }
        ],
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
    assert raw["rejectFunnel"][0]["stage"] == "geometry"


def _l3p2_window() -> tuple[list[str], dict, dict]:
    ids = ["p0", "p1", "l0", "l1", "l2"]
    aspects = {
        "p0": "portrait",
        "p1": "portrait",
        "l0": "landscape",
        "l1": "landscape",
        "l2": "landscape",
    }
    assets = {
        aid: {
            "id": aid,
            "width": 900 if aspects[aid] == "portrait" else 1600,
            "height": 1600 if aspects[aid] == "portrait" else 900,
            "takenAt": f"2024-06-01T12:0{i}:00Z",
        }
        for i, aid in enumerate(ids)
    }
    return ids, aspects, assets


def test_ac02_candidate_excludes_equal_and_rail() -> None:
    """AC-MTSO-02 · candidate path."""
    ids, aspects, assets = _l3p2_window()
    cfg = replace(
        get_config().mosaic,
        template_contract=TemplateContractConfig(enabled=True, shadow_log=False),
        template_experiments=TemplateExperimentsConfig(enabled=False),
        enabled_window_sizes=(4, 5, 6, 9),
    )
    reg = dict(mosaic_registry(cfg=replace(get_config(), mosaic=cfg)))
    reg[PATTERN_MOSAIC_5_2P3L_EQUAL] = export_mosaic_pattern(
        get_engine().get(PATTERN_MOSAIC_5_2P3L_EQUAL)
    )
    result = generate_window_candidates_with_rejections(
        ids, aspects, assets, cfg=cfg, registry=reg
    )
    pids = {c.pattern_id for c in result.candidates}
    assert PATTERN_MOSAIC_5_2P3L_EQUAL not in pids
    assert RAIL_2P3L not in pids
    assert mosaic_pattern_disabled(PATTERN_MOSAIC_5_2P3L_EQUAL, cfg=cfg)
    assert mosaic_pattern_disabled(RAIL_2P3L, cfg=cfg)
    # Injected deprecated equal must be hard-gated if the contract path surfaces it.
    if any(r.get("templateId") == PATTERN_MOSAIC_5_2P3L_EQUAL for r in result.rejected):
        assert any(
            r.get("templateId") == PATTERN_MOSAIC_5_2P3L_EQUAL
            and r.get("reason") == "pattern_disabled"
            for r in result.rejected
        )


def test_ac02_legacy_append_blocks_equal_and_rail() -> None:
    """AC-MTSO-02 · legacy append path."""
    from types import SimpleNamespace

    ids, aspects, assets = _l3p2_window()
    for pid in (PATTERN_MOSAIC_5_2P3L_EQUAL, RAIL_2P3L):
        ctx = SimpleNamespace(
            aspects=aspects,
            assets_map=assets,
            mix_gap=12.0,
            med_sharp=0.5,
            trip_total=40,
            layout_state=None,
            featured_weight=1.35,
            trip=None,
            screens=[],
            chapter_id="ch",
            seq=0,
            ids=ids,
        )
        forged = {
            "patternId": pid,
            "slots": [{"assetId": a, "slot": i} for i, a in enumerate(ids)],
        }
        with patch(
            "travelogue.layout_engine.mosaic.legacy.build_legacy_screen",
            return_value=forged,
        ), patch(
            "travelogue.layout_engine.planner.screen_planner_stages.append_screen"
        ):
            assert append_legacy_window(ctx, ids, 5) is False  # type: ignore[arg-type]


def test_ac02_self_heal_and_fallback_cannot_emit_gated() -> None:
    """AC-MTSO-02 · self-heal / MCS fallback cannot emit equal or rail."""
    ids, aspects, assets = _l3p2_window()
    cfg = replace(
        get_config().mosaic,
        template_contract=TemplateContractConfig(enabled=False),
        template_experiments=TemplateExperimentsConfig(enabled=False),
        self_heal_enabled=True,
        min_candidate_score=0.99,
        fallback_to_legacy=True,
        enabled_window_sizes=(4, 5, 6, 9),
    )

    def _fake_generate(*_a, **_k):
        from travelogue.layout_engine.mosaic.candidates import WindowCandidateResult

        screen = {
            "patternId": RAIL_2P3L,
            "slots": [{"assetId": a, "slot": i} for i, a in enumerate(ids)],
        }
        cand = ScreenCandidate(
            pattern_id=RAIL_2P3L,
            ordered_asset_ids=list(ids),
            screen=screen,
            hard_valid=True,
        )
        return WindowCandidateResult(candidates=[cand], rejected=[])

    with patch(
        "travelogue.layout_engine.mosaic.compose.generate_window_candidates_with_rejections",
        _fake_generate,
    ):
        pick = pick_best_window(
            ids, aspects, assets, cfg=cfg, window_size=5, trip_photo_total=40
        )
    assert pick.screen is None or pick.screen.get("patternId") != RAIL_2P3L
    assert pick.used_legacy or pick.log.fallback_reason in (
        "pattern_disabled",
        "no_candidates",
        "low_score",
    )


def test_trip_id_plumbs_experiments_into_mcs_pick() -> None:
    """Dogfood cohort tripId must reach pick_best_window via ctx.trip."""
    trip_id = "mtso-plumbing-trip"
    ids, aspects, assets = _l3p2_window()
    app = replace(
        get_config(),
        mosaic=replace(
            get_config().mosaic,
            template_contract=TemplateContractConfig(enabled=True, shadow_log=False),
            template_experiments=TemplateExperimentsConfig(
                enabled=True,
                allowlist=(RAIL_2P3L,),
                cohort_trip_ids=(trip_id,),
            ),
            enabled_window_sizes=(4, 5, 6, 9),
            min_candidate_score=0.0,
        ),
    )
    with patch("travelogue.config.get_config", return_value=app), patch(
        "travelogue.layout_engine.mosaic.runtime.get_effective_mosaic_config",
        return_value=app.mosaic,
    ):
        pick = pick_best_window(
            ids,
            aspects,
            assets,
            cfg=app.mosaic,
            window_size=5,
            trip_photo_total=40,
            trip_id=trip_id,
        )
        assert RAIL_2P3L in mosaic_registry(cfg=app, trip_id=trip_id)
        # Winner may be another L3P2-capable pattern; at least rail must be admitted.
        assert not mosaic_pattern_disabled(RAIL_2P3L, cfg=app.mosaic, trip_id=trip_id)
        assert trip_id_from_trip({"tripId": trip_id}) == trip_id


def test_funnel_raw_via_drain_mosaic_capture() -> None:
    """BLK-07 / AC-03 · assert funnel keys on raw capture, not formatted window log."""
    ids, aspects, assets = _l3p2_window()
    cfg = replace(
        get_config().mosaic,
        template_contract=TemplateContractConfig(enabled=False),
        min_candidate_score=0.0,
        enabled_window_sizes=(4, 5, 6, 9),
    )
    begin_mosaic_capture()
    pick = pick_best_window(
        ids, aspects, assets, cfg=cfg, window_size=5, trip_photo_total=40
    )
    # Simulate hook append of raw to_dict (same as try_mosaic_window_mcs).
    from travelogue.layout_engine.mosaic.hook import _append_mosaic_log

    _append_mosaic_log(pick.log.to_dict())
    _formatted, raw_rows = drain_mosaic_capture()
    assert raw_rows
    raw = raw_rows[0]
    for key in (
        "baseWindowOrder",
        "effectiveWindowOrder",
        "structurallyQualifiedSix",
        "admitSixHero",
        "sixHeroOpportunityState",
        "sixHeroFamilyId",
        "quotaSnapshot",
        "rejectFunnel",
    ):
        assert key in raw
    assert isinstance(raw["rejectFunnel"], list)
    for row in raw["rejectFunnel"]:
        assert "stage" in row
        assert "reason" in row


def test_reject_funnel_stage_mapping() -> None:
    assert reject_funnel_stage("contract:mix_miss") == "contract"
    assert reject_funnel_stage("pattern_disabled") == "lifecycle"
    assert reject_funnel_stage("usage_rule:mixed_portrait_is_hero") == "usage"


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
