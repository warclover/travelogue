"""SSG mosaic cross-group hard reject."""

from __future__ import annotations

from travelogue.config.shot_grouping import ShotGroupingConfig, shot_grouping_from_dict
from travelogue.layout_engine.mosaic.shot_group_gate import (
    hard_reject_cross_shot_group,
    screen_exempt_from_shot_group_hard_reject,
    ssg_hard_reject_active,
)


def test_cross_group_hard_reject_on_slice_pattern() -> None:
    assets = {
        "a": {"shotGroupId": "sg-1"},
        "b": {"shotGroupId": "sg-2"},
        "c": {"shotGroupId": "sg-1"},
    }
    # prefers_burst false pattern
    assert hard_reject_cross_shot_group(
        "screen-mosaic-4-2l2p-weighted",
        ["a", "b", "c"],
        assets,
    )


def test_same_group_not_rejected() -> None:
    assets = {
        "a": {"shotGroupId": "sg-1"},
        "b": {"shotGroupId": "sg-1"},
        "c": {"shotGroupId": "sg-1"},
    }
    assert not hard_reject_cross_shot_group(
        "screen-mosaic-4-2l2p-weighted",
        ["a", "b", "c"],
        assets,
    )


def test_prefers_burst_true_allows_cross_group() -> None:
    assets = {
        "a": {"shotGroupId": "sg-1"},
        "b": {"shotGroupId": "sg-2"},
        "c": {"shotGroupId": "sg-3"},
    }
    assert not hard_reject_cross_shot_group(
        "screen-mosaic-5-2p3l-rail",
        ["a", "b", "c"],
        assets,
    )


def test_solo_pattern_exempt() -> None:
    assert screen_exempt_from_shot_group_hard_reject(pattern_id="screen-full-frame-hero")
    assert screen_exempt_from_shot_group_hard_reject(slot_count=1)


def test_ssg_hard_reject_follows_config() -> None:
    on = type("C", (), {"shot_grouping": ShotGroupingConfig()})()
    assert ssg_hard_reject_active(on)
    off = type(
        "C",
        (),
        {"shot_grouping": shot_grouping_from_dict({"enabled": "false"})},
    )()
    assert not ssg_hard_reject_active(off)
