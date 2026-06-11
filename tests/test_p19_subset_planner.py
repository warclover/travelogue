"""P19 S5-04 · subset_planner spike."""

from __future__ import annotations

from travelogue.curation.subset_planner import (
    SubsetConfig,
    apply_subset_plan,
    plan_asset_subset,
    resolve_target_reduction,
)


def _asset(
    aid: str,
    *,
    day: str = "2024-06-01",
    sharp: float = 50.0,
    subject: str = "landscape",
    featured: bool = False,
    cluster: int | None = None,
) -> dict:
    out: dict = {
        "id": aid,
        "type": "image",
        "layoutEligible": True,
        "takenAt": f"{day}T12:00:00Z",
        "quality": {"sharpness": sharp},
        "subjectClass": subject,
    }
    if featured:
        out["userTier"] = "featured"
    if cluster is not None:
        out["sceneClusterId"] = cluster
    return out


def test_resolve_target_reduction_tiers() -> None:
    assert resolve_target_reduction(50, SubsetConfig())[0] == 0.40
    assert resolve_target_reduction(150, SubsetConfig())[0] == 0.30
    assert resolve_target_reduction(400, SubsetConfig())[0] == 0.25


def test_plan_asset_subset_keeps_featured_and_reduces_pool() -> None:
    assets = [_asset("f1", featured=True, sharp=80)]
    for i in range(20):
        assets.append(
            _asset(
                f"a{i}",
                day=f"2024-06-{1 + i % 5:02d}",
                sharp=30 + i,
                subject="landscape" if i % 3 else "person",
                cluster=i % 4,
            )
        )
    trip = {
        "assets": assets,
        "curation": {
            "clustering": {
                "clusters": [
                    {"id": c, "assetIds": [f"a{i}" for i in range(20) if i % 4 == c], "medoidAssetId": f"a{c}"}
                    for c in range(4)
                ],
            },
        },
    }
    plan = plan_asset_subset(trip, cfg=SubsetConfig(enabled=True))
    assert "f1" in plan.kept_asset_ids
    assert plan.baseline_pool_count == 20
    assert len(plan.dropped_asset_ids) > 0
    assert plan.to_dict()["actualReduction"] >= 0.25


def test_apply_subset_plan_marks_layout_eligible() -> None:
    trip = {"assets": [_asset("a1"), _asset("a2", sharp=10)]}
    plan = plan_asset_subset(trip, cfg=SubsetConfig(enabled=True, target_reduction=0.5))
    n = apply_subset_plan(trip, plan)
    assert n >= 0
    assert "subsetPlan" in trip.get("curation", {})
