"""SSG mosaic cross-group / same-group anti-slice hard reject."""

from __future__ import annotations

from travelogue.config.shot_grouping import ShotGroupingConfig, shot_grouping_from_dict
from travelogue.layout_engine.mosaic.shot_group_gate import (
    hard_reject_cross_shot_group,
    hard_reject_same_shot_group_anti_slice,
    screen_exempt_from_shot_group_hard_reject,
    ssg_hard_reject_active,
)
from travelogue.layout_engine.mosaic.shot_group_metrics import fake_slice_reduction_rate


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


def test_same_group_anti_slice_tight_window() -> None:
    assets = {
        "a": {"shotGroupId": "sg-1", "takenAt": "2025-01-01T10:00:00Z"},
        "b": {"shotGroupId": "sg-1", "takenAt": "2025-01-01T10:00:30Z"},
        "c": {"shotGroupId": "sg-1", "takenAt": "2025-01-01T10:01:00Z"},
    }
    assert hard_reject_same_shot_group_anti_slice(
        "screen-mosaic-4-2l2p-weighted",
        ["a", "b", "c"],
        assets,
    )


def test_same_group_anti_slice_skips_wide_span() -> None:
    assets = {
        "a": {"shotGroupId": "sg-1", "takenAt": "2025-01-01T10:00:00Z"},
        "b": {"shotGroupId": "sg-1", "takenAt": "2025-01-01T10:05:00Z"},
        "c": {"shotGroupId": "sg-1", "takenAt": "2025-01-01T10:20:00Z"},
    }
    assert not hard_reject_same_shot_group_anti_slice(
        "screen-mosaic-4-2l2p-weighted",
        ["a", "b", "c"],
        assets,
    )


def test_look_kind_same_mosaic_contract() -> None:
    """AC-SSG-15 · look groups use the same shotGroupId hard-reject path."""
    assets = {
        "a": {"shotGroupId": "sg-look-00", "shotGroupKind": "look"},
        "b": {"shotGroupId": "sg-look-01", "shotGroupKind": "look"},
        "c": {"shotGroupId": "sg-look-00", "shotGroupKind": "look"},
    }
    assert hard_reject_cross_shot_group(
        "screen-mosaic-4-2l2p-weighted",
        ["a", "b", "c"],
        assets,
    )


def test_fake_slice_reduction_at_least_40pct() -> None:
    """AC-SSG-05 · same-group anti-slice reduces tight fake-slice windows ≥40%."""
    assets = {
        f"a{i}": {
            "shotGroupId": "sg-scene-1",
            "takenAt": f"2025-01-01T10:00:{i:02d}Z",
        }
        for i in range(6)
    }
    # Five overlapping tight windows on a slice pattern
    windows = [
        ("screen-mosaic-4-2l2p-weighted", [f"a{i}", f"a{i+1}", f"a{i+2}"])
        for i in range(4)
    ]
    # One wide-span control (should not count as fake slice)
    assets["w0"] = {"shotGroupId": "sg-scene-1", "takenAt": "2025-01-01T10:00:00Z"}
    assets["w1"] = {"shotGroupId": "sg-scene-1", "takenAt": "2025-01-01T10:10:00Z"}
    assets["w2"] = {"shotGroupId": "sg-scene-1", "takenAt": "2025-01-01T10:30:00Z"}
    windows.append(("screen-mosaic-4-2l2p-weighted", ["w0", "w1", "w2"]))
    rate = fake_slice_reduction_rate(windows, assets)
    assert rate >= 0.40, rate
