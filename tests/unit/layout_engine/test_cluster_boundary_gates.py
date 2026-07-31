"""Extra Cluster-Boundary-First gate coverage (attach / legacy / P0-2 / soft)."""

from __future__ import annotations

from travelogue.config.shot_grouping import (
    AtomConfig,
    ShotGroupingConfig,
    ShotGroupingMosaicConfig,
    policy_resolve_fallback_count,
    reset_policy_resolve_fallback_count,
    resolve_shot_group_mosaic_policy,
    shot_grouping_from_dict,
)
from travelogue.layout_engine.mosaic.legacy import build_legacy_screen
from travelogue.layout_engine.planner.scene_atoms import window_category_jump_count
from travelogue.layout_engine.planner.screen_planner_attach import (
    _consolidate_adjacent_portrait_singles,
)


def test_atom_config_extra_observe_fields() -> None:
    cfg = shot_grouping_from_dict(
        {
            "mosaic": {
                "atom": {
                    "enabled": True,
                    "strongTemplateMaxSpanSeconds": None,
                    "strongTemplateSpanSoftSeconds": 900,
                    "mosaicShareFloorObserve": 0.65,
                }
            }
        }
    )
    assert cfg.mosaic.atom.strong_template_max_span_seconds is None
    assert cfg.mosaic.atom.strong_template_span_soft_seconds == 900.0
    assert cfg.mosaic.atom.mosaic_share_floor_observe == 0.65


def test_policy_resolve_fallback_fail_loud_counter() -> None:
    reset_policy_resolve_fallback_count()
    before = policy_resolve_fallback_count()
    resolve_shot_group_mosaic_policy(object(), warn_if_missing=False)
    assert policy_resolve_fallback_count() == before + 1


def test_legacy_screen_refuses_cross_atom_window() -> None:
    assets = {
        "a": {
            "shotGroupId": "sg-a",
            "sceneClusterId": -1,
            "takenAt": "2015-04-27T10:00:00Z",
            "width": 1000,
            "height": 1500,
        },
        "b": {
            "shotGroupId": "sg-b",
            "sceneClusterId": -1,
            "takenAt": "2015-04-27T10:01:00Z",
            "width": 1000,
            "height": 1500,
        },
        "c": {
            "shotGroupId": "sg-c",
            "sceneClusterId": -1,
            "takenAt": "2015-04-27T10:02:00Z",
            "width": 1000,
            "height": 1500,
        },
    }
    aspects = {"a": "portrait", "b": "portrait", "c": "portrait"}
    out = build_legacy_screen(
        ["a", "b", "c"],
        3,
        aspects,
        assets,
        atom_policy=AtomConfig(enabled=True),
    )
    assert out is None


def test_category_jump_soft_count() -> None:
    assets = {
        "a": {
            "takenAt": "2015-04-27T10:00:00Z",
            "semanticTag": {"category": "person"},
        },
        "b": {
            "takenAt": "2015-04-27T10:01:00Z",
            "semanticTag": {"category": "street"},
        },
    }
    assert window_category_jump_count(["a", "b"], assets) == 1


def test_attach_consolidate_respects_atom_boundary() -> None:
    class _App:
        shot_grouping = ShotGroupingConfig(
            mosaic=ShotGroupingMosaicConfig(atom=AtomConfig(enabled=True))
        )

    assets = {
        "a": {
            "shotGroupId": "sg-a",
            "sceneClusterId": -1,
            "takenAt": "2015-04-27T10:00:00Z",
            "width": 1000,
            "height": 1500,
            "tags": ["person"],
        },
        "b": {
            "shotGroupId": "sg-b",
            "sceneClusterId": -1,
            "takenAt": "2015-04-27T10:01:00Z",
            "width": 1000,
            "height": 1500,
            "tags": ["person"],
        },
    }
    aspects = {"a": "portrait", "b": "portrait"}
    screens = [
        {"patternId": "screen-portrait-1", "slots": [{"assetId": "a"}]},
        {"patternId": "screen-portrait-1", "slots": [{"assetId": "b"}]},
    ]
    out = _consolidate_adjacent_portrait_singles(
        screens, aspects, assets_map=assets, cfg=_App()
    )
    assert len(out) == 2
    assert all(s.get("patternId") == "screen-portrait-1" for s in out)


def test_missing_shot_group_time_bridge_allows_near_pair() -> None:
    """Weak-SSG albums: both missing shotGroupId → join on time (+ half-hard sc)."""
    from travelogue.layout_engine.planner.scene_atoms import adjacent_compatible

    policy = AtomConfig(enabled=True, missing_shot_group_mode="time_bridge")
    base = {"sceneClusterId": -1, "takenAt": "2015-04-27T10:00:00Z"}
    ok, _ = adjacent_compatible(
        {**base},
        {**base, "takenAt": "2015-04-27T10:05:00Z"},
        policy,
    )
    assert ok
    ok, reason = adjacent_compatible(
        {**base},
        {**base, "takenAt": "2015-04-27T10:20:00Z"},  # >600s
        policy,
    )
    assert not ok
    assert reason == "atom_gap"


def test_missing_shot_group_reject_mode_still_fail_closed() -> None:
    from travelogue.layout_engine.planner.scene_atoms import adjacent_compatible

    policy = AtomConfig(enabled=True, missing_shot_group_mode="reject")
    ok, reason = adjacent_compatible(
        {"sceneClusterId": -1, "takenAt": "2015-04-27T10:00:00Z"},
        {"sceneClusterId": -1, "takenAt": "2015-04-27T10:01:00Z"},
        policy,
    )
    assert not ok
    assert reason == "shot_group_missing"


def test_shot_group_present_absent_mix_hard_reject() -> None:
    from travelogue.layout_engine.planner.scene_atoms import adjacent_compatible

    policy = AtomConfig(enabled=True, missing_shot_group_mode="time_bridge")
    ok, reason = adjacent_compatible(
        {
            "shotGroupId": "sg-1",
            "sceneClusterId": -1,
            "takenAt": "2015-04-27T10:00:00Z",
        },
        {"sceneClusterId": -1, "takenAt": "2015-04-27T10:01:00Z"},
        policy,
    )
    assert not ok
    assert reason == "shot_group_present_absent_mix"
