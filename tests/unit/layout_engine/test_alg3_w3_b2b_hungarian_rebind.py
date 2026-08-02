"""ALG-V3 W3-B2b · Hungarian rebind avoids second build_screen."""

from __future__ import annotations

from unittest.mock import patch

from travelogue.config.mosaic import MosaicConfig
from travelogue.config.shot_grouping import AtomConfig, ShotGroupMosaicPolicy
from travelogue.layout_engine.mosaic.builders import (
    get_build_screen_calls,
    rebind_screen_asset_order,
    reset_build_screen_calls,
)
from travelogue.layout_engine.mosaic.candidates import (
    generate_window_candidates_with_rejections,
)


def test_b2b_rebind_updates_assets_without_new_build() -> None:
    screen = {
        "patternId": "screen-mosaic-4-2x2",
        "slots": [
            {"assetId": "a1", "slot": 0, "role": "main", "fit": "cover"},
            {"assetId": "a2", "slot": 1, "role": "landscape", "fit": "cover"},
            {"assetId": "a3", "slot": 2, "role": "portrait", "fit": "contain"},
            {"assetId": "a4", "slot": 3, "role": "landscape", "fit": "cover"},
        ],
    }
    assets = {
        "a1": {"id": "a1", "width": 1600, "height": 900},
        "a2": {"id": "a2", "width": 1600, "height": 900},
        "a3": {"id": "a3", "width": 900, "height": 1600},
        "a4": {"id": "a4", "width": 1600, "height": 900},
    }
    reset_build_screen_calls()
    before = get_build_screen_calls()
    ok = rebind_screen_asset_order(
        screen, ["a4", "a3", "a2", "a1"], assets_map=assets
    )
    assert ok is True
    assert [s["assetId"] for s in screen["slots"]] == ["a4", "a3", "a2", "a1"]
    assert get_build_screen_calls() == before


def test_b2b_rebind_mismatch_returns_false() -> None:
    screen = {"patternId": "x", "slots": [{"assetId": "a1", "role": "main"}]}
    assert (
        rebind_screen_asset_order(screen, ["a1", "a2"], assets_map={"a1": {}, "a2": {}})
        is False
    )


def test_b2b_hungarian_path_does_not_double_build_per_pattern() -> None:
    """When refine always succeeds, inplace rebind beats force-rebuild call counts."""
    cfg = MosaicConfig(
        enabled=True,
        lse_hungarian_assignment=True,
        lse_quality_unified=False,
        enabled_window_sizes=(4,),
    )
    asset_ids = ["a1", "a2", "a3", "a4"]
    aspects = {
        "a1": "landscape",
        "a2": "landscape",
        "a3": "portrait",
        "a4": "landscape",
    }
    rich_assets = {
        aid: {
            "id": aid,
            "aspect": aspects[aid],
            "width": 1200 if aspects[aid] == "landscape" else 800,
            "height": 800 if aspects[aid] == "landscape" else 1200,
            "sharpness": 0.9,
            "shotGroupId": "sg",
            "sceneClusterId": 1,
            "takenAt": f"2025-01-01T10:0{i}:00Z",
        }
        for i, aid in enumerate(asset_ids)
    }
    policy = ShotGroupMosaicPolicy(
        cross_group_hard_reject=False,
        same_group_anti_slice=False,
        atom=AtomConfig(enabled=False),
    )

    def _fake_refine(ids, _screen, _assets, **_kwargs):
        return list(reversed(ids)), None

    def _count(force_rebuild: bool) -> int:
        reset_build_screen_calls()
        with (
            patch(
                "travelogue.layout_engine.mosaic.candidates.try_order_for_pattern",
                return_value=list(asset_ids),
            ),
            patch(
                "travelogue.layout_engine.slot_assignment.refine_asset_order_hungarian",
                _fake_refine,
            ),
            patch(
                "travelogue.layout_engine.mosaic.candidates.pattern_geometry_precheck",
                return_value=True,
            ),
            patch(
                "travelogue.layout_engine.mosaic.candidates.screen_slots_geometry_ok",
                return_value=True,
            ),
            patch(
                "travelogue.layout_engine.mosaic.candidates.screen_main_slot_eligible",
                return_value=(True, "ok"),
            ),
        ):
            if force_rebuild:
                with patch(
                    "travelogue.layout_engine.mosaic.candidates.rebind_screen_asset_order",
                    return_value=False,
                ):
                    generate_window_candidates_with_rejections(
                        asset_ids,
                        aspects,  # type: ignore[arg-type]
                        rich_assets,
                        cfg=cfg,
                        ssg_policy=policy,
                    )
            else:
                generate_window_candidates_with_rejections(
                    asset_ids,
                    aspects,  # type: ignore[arg-type]
                    rich_assets,
                    cfg=cfg,
                    ssg_policy=policy,
                )
        return get_build_screen_calls()

    inplace = _count(False)
    rebuilt = _count(True)
    assert inplace >= 1
    assert inplace < rebuilt
