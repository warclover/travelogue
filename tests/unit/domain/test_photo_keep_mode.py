"""P9-F3 · photoKeepMode 派生与旧盘推断。"""

from __future__ import annotations

from travelogue.domain.photo_keep_mode import (
    derive_from_mode,
    infer_mode_from_bools,
    resolve_photo_keep_prefs,
    should_skip_low_res_exclusion,
)


def test_derive_from_mode_matrix() -> None:
    rec = derive_from_mode("recommended")
    assert rec.photo_cull_enabled is True
    assert rec.keep_near_duplicates is False
    assert rec.skip_low_res_exclusion is False

    bursts = derive_from_mode("keep_bursts")
    assert bursts.photo_cull_enabled is True
    assert bursts.keep_near_duplicates is True
    assert bursts.skip_low_res_exclusion is False

    all_mode = derive_from_mode("keep_all")
    assert all_mode.photo_cull_enabled is False
    assert all_mode.keep_near_duplicates is True
    assert all_mode.skip_low_res_exclusion is True


def test_mode_forces_bools_over_contradictory_payload() -> None:
    resolved = resolve_photo_keep_prefs(
        photo_keep_mode="keep_all",
        photo_cull_enabled=True,
        keep_near_duplicates=False,
    )
    assert resolved.mode == "keep_all"
    assert resolved.photo_cull_enabled is False
    assert resolved.keep_near_duplicates is True
    assert resolved.skip_low_res_exclusion is True


def test_legacy_bools_never_skip_low_res() -> None:
    resolved = resolve_photo_keep_prefs(
        photo_keep_mode=None,
        photo_cull_enabled=False,
        keep_near_duplicates=True,
    )
    assert resolved.mode == "keep_bursts"
    assert resolved.photo_cull_enabled is False
    assert resolved.keep_near_duplicates is True
    assert resolved.skip_low_res_exclusion is False


def test_infer_never_keep_all() -> None:
    assert (
        infer_mode_from_bools(photo_cull_enabled=False, keep_near_duplicates=True)
        == "keep_bursts"
    )
    assert (
        infer_mode_from_bools(photo_cull_enabled=True, keep_near_duplicates=True)
        == "keep_bursts"
    )
    assert (
        infer_mode_from_bools(photo_cull_enabled=False, keep_near_duplicates=False)
        == "recommended"
    )


def test_should_skip_low_res_exclusion() -> None:
    assert should_skip_low_res_exclusion({"photoKeepMode": "keep_all"}) is True
    assert should_skip_low_res_exclusion({"photoKeepMode": "keep_bursts"}) is False
    assert should_skip_low_res_exclusion({"photoCullEnabled": False}) is False
    assert should_skip_low_res_exclusion({"skipLowResExclusion": True}) is True
