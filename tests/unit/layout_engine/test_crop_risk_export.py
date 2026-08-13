"""crop_risk authority is crop_solver; msa_fit re-exports (AC-AEL-23 / T-AEL-10)."""

from __future__ import annotations

import pytest

from travelogue.layout_engine.crop_solver import (
    aspect_mismatch,
    crop_risk_for_pair,
    group_face_count,
)
from travelogue.layout_engine.mosaic import msa_fit

pytestmark = pytest.mark.unit


def test_msa_fit_reexports_crop_solver_callables() -> None:
    assert msa_fit.crop_risk_for_pair is crop_risk_for_pair
    assert msa_fit.aspect_mismatch is aspect_mismatch


def test_crop_risk_proxy_still_rises_with_mismatch() -> None:
    mild = crop_risk_for_pair(
        {"id": "a", "width": 3000, "height": 2000, "aspectKind": "landscape"},
        1.50,
    )
    harsh = crop_risk_for_pair(
        {"id": "b", "width": 4000, "height": 1000, "aspectKind": "landscape"},
        1.50,
    )
    assert harsh > mild


def test_group_face_count_uses_max_of_quality_and_boxes() -> None:
    assert group_face_count({"quality": {"faceCount": 4}, "faces": [{}, {}]}) == 4
    assert group_face_count({"quality": {"faceCount": 1}, "faces": [{}, {}, {}]}) == 3
    assert group_face_count({"quality": {"faceCount": 0}, "faces": []}) == 0
    assert group_face_count(None) == 0
