"""AAD-21 LayoutUtility combine (layout_contract kernel)."""

from __future__ import annotations

from travelogue.layout_contract.scoring import combine_utility


def test_combine_utility_identity_when_no_penalties() -> None:
    bd = combine_utility(0.8, {})
    assert bd.soft == 0.8
    assert bd.utility == 0.8
    assert bd.penalties_applied == {}


def test_combine_utility_weighted_penalty() -> None:
    bd = combine_utility(1.0, {"face_crop": 1.0}, {"face_crop": 0.5})
    assert bd.utility == 0.5
    assert bd.penalties_applied["face_crop"] == 1.0


def test_combine_utility_skips_zero_weight() -> None:
    bd = combine_utility(0.9, {"x": 1.0}, {"x": 0.0})
    assert bd.utility == 0.9
    assert bd.penalties_applied == {}
