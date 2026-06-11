"""P19 S2-07/08 · rollout util + mosaic auto groups."""

from __future__ import annotations

from travelogue.config import AppConfig
from travelogue.config.layout import LayoutConfig
from travelogue.config.rollout import in_rollout_cohort, rollout_bucket
from travelogue.config.runtime import config_override
from travelogue.curation.mosaic import _legacy_generated as legacy_gen
from travelogue.curation.mosaic import constants as mosaic_constants
from travelogue.curation.mosaic.legacy_specs import reset_legacy_specs_cache_for_tests
from travelogue.curation.phase6_rollout import phase6_in_rollout_cohort
from travelogue.layout_engine.rollout import lse_in_rollout_cohort
from travelogue.layout_templates.mosaic_groups import build_mosaic_unified_groups
from travelogue.layout_templates.registry import LayoutTemplateEngine, reset_engine_cache_for_tests


def test_rollout_bucket_is_stable() -> None:
    a = rollout_bucket("trip-a", cohort_salt="salt", traffic_percent=50.0)
    b = rollout_bucket("trip-a", cohort_salt="salt", traffic_percent=50.0)
    assert a == b
    assert 0 <= a < 100


def test_lse_and_phase6_off_policy_differ() -> None:
    from travelogue.config import AppConfig

    cfg = AppConfig()
    tid = "demo-rollout-test"
    assert not lse_in_rollout_cohort(tid, cfg)
    assert phase6_in_rollout_cohort(tid, cfg)


def test_in_rollout_cohort_allowlist_wins() -> None:
    assert in_rollout_cohort(
        "trip-x",
        cohort_salt="s",
        traffic_percent=0.0,
        stage="off",
        allowlist=("trip-x",),
        off_policy="deny_all",
    )


def test_auto_mosaic_groups_when_lte_on() -> None:
    reset_engine_cache_for_tests()
    reset_legacy_specs_cache_for_tests()
    cfg = AppConfig(layout=LayoutConfig())
    with config_override(cfg):
        engine = LayoutTemplateEngine.load(rebuild_cache=True)
        groups = build_mosaic_unified_groups(engine)
        auto5 = groups["MOSAIC_5_PATTERN_IDS"]
        legacy5 = legacy_gen.MOSAIC_5_PATTERN_IDS
        assert set(auto5).issubset(set(legacy5))
        assert "screen-mosaic-5-main-portrait-3land" in auto5
        assert mosaic_constants.MOSAIC_5_PATTERN_IDS == auto5
