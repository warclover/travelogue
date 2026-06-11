"""P19 S6-01 · subset integration in run_curate path."""

from __future__ import annotations

import pytest

from travelogue.config.curate import CurateConfig, CurateSubsetConfig
from travelogue.curation.subset_planner import maybe_apply_asset_subset_in_curate


def _asset(aid: str, *, sharp: float = 40.0, day: str = "2024-06-01") -> dict:
    return {
        "id": aid,
        "type": "image",
        "layoutEligible": True,
        "takenAt": f"{day}T10:00:00Z",
        "quality": {"sharpness": sharp},
        "subjectClass": "landscape",
    }


@pytest.mark.unit
def test_maybe_apply_asset_subset_in_curate_when_disabled() -> None:
    trip = {"assets": [_asset("a1"), _asset("a2")]}
    cur_cfg = CurateConfig(subset=CurateSubsetConfig(enabled=False))
    assert maybe_apply_asset_subset_in_curate(trip, cur_cfg=cur_cfg) is None


@pytest.mark.unit
def test_maybe_apply_asset_subset_in_curate_marks_dropped() -> None:
    assets = [_asset(f"a{i}", sharp=20 + i, day=f"2024-06-{1 + i % 3:02d}") for i in range(12)]
    trip = {
        "assets": assets,
        "curation": {
            "clustering": {
                "clusters": [
                    {
                        "id": 0,
                        "assetIds": [a["id"] for a in assets[:6]],
                        "medoidAssetId": "a0",
                    },
                    {
                        "id": 1,
                        "assetIds": [a["id"] for a in assets[6:]],
                        "medoidAssetId": "a6",
                    },
                ],
            },
        },
    }
    cur_cfg = CurateConfig(
        subset=CurateSubsetConfig(enabled=True, target_reduction=0.5),
    )
    summary = maybe_apply_asset_subset_in_curate(trip, cur_cfg=cur_cfg)
    assert summary is not None
    assert trip["curation"]["subsetPlan"]["droppedAssetIds"]
    dropped = [a for a in trip["assets"] if a.get("layoutEligible") is False]
    assert dropped


@pytest.mark.unit
def test_curate_config_loads_subset_from_yaml_dict() -> None:
    from travelogue.config.loader import load_config

    cfg = load_config()
    assert hasattr(cfg.curate, "subset")
    assert cfg.curate.subset.enabled is False
