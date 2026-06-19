"""AA · GAP-03/04/13 · purpose calibration + blind + pairwise export."""

from __future__ import annotations

from travelogue.curation.aesthetic_blind_review import normalize_human_score
from travelogue.curation.aesthetic_purpose_blind import (
    automated_purpose_win_report,
    export_pairwise_pairs,
    pick_top_asset,
)
from travelogue.curation.aesthetic_purpose_calibrate import (
    grid_search_purpose_weights,
    weights_with_dim_emphasis,
)
from travelogue.config import AestheticConfig, AestheticWeights


def _asset(aid: str, *, rules_cover: float, learned: float) -> dict:
    return {
        "id": aid,
        "type": "image",
        "layoutEligible": True,
        "quality": {
            "aesthetic": {
                "overall": rules_cover,
                "source": "rules+ml",
                "dims": {
                    "composition": rules_cover,
                    "exposure": rules_cover,
                    "color": rules_cover,
                    "lighting": rules_cover,
                    "subjectClarity": rules_cover,
                },
                "signals": {"learnedAesthetic": learned},
            }
        },
    }


def test_weights_with_dim_emphasis_sums_to_one():
    base = AestheticWeights()
    w = weights_with_dim_emphasis(base, dim="composition", emphasis=0.35)
    m = w.as_dim_map()
    assert abs(sum(m.values()) - 1.0) < 1e-6
    assert abs(m["composition"] - 0.35) < 1e-6


def test_grid_search_purpose_weights_returns_recommendations():
    assets = {
        "a": _asset("a", rules_cover=0.3, learned=0.3),
        "b": _asset("b", rules_cover=0.8, learned=0.8),
        "c": _asset("c", rules_cover=0.6, learned=0.6),
    }
    labels = [
        {"assetId": "a", "humanScore": 2, "stratum": "landscape"},
        {"assetId": "b", "humanScore": 5, "stratum": "landscape"},
        {"assetId": "c", "humanScore": 3, "stratum": "landscape"},
    ]
    cfg = AestheticConfig(ml_calibrate=True, use_purpose_presets=True)
    out = grid_search_purpose_weights(
        assets,
        labels,
        cfg=cfg,
        purposes=("cover",),
        emphasis_dims=("composition",),
        emphasis_min=0.10,
        emphasis_max=0.20,
        emphasis_step=0.05,
    )
    assert "cover" in out["purposes"]
    assert out["purposes"]["cover"]["recommended"]["dim"] == "composition"


def test_export_purpose_pick_pairs_diverse():
    from travelogue.config import AestheticConfig
    from travelogue.curation.aesthetic_purpose_blind import export_purpose_pick_pairs

    def _a(aid: str, overall: float, learned: float | None = None):
        q = {
            "aesthetic": {
                "overall": overall,
                "dims": {
                    "composition": overall,
                    "exposure": overall,
                    "color": overall,
                    "lighting": overall,
                    "subjectClarity": overall,
                },
                "signals": {"learnedAesthetic": learned if learned is not None else overall},
            }
        }
        return {
            "id": aid,
            "type": "image",
            "layoutEligible": True,
            "width": 4000,
            "height": 3000,
            "aspectKind": "landscape",
            "quality": q,
        }

    assets = [_a("a1", 0.9, 0.3), _a("a2", 0.5, 0.95), _a("a3", 0.7, 0.7)]
    rules_cfg = AestheticConfig(ml_calibrate=False, use_purpose_presets=True)
    aligned_cfg = AestheticConfig(
        ml_calibrate=True,
        use_stratum_blend=True,
        stratum_blends={"landscape": 0.6},
        stratum_blend_only=("landscape",),
        use_album_relative=False,
        use_purpose_presets=True,
    )
    out = export_purpose_pick_pairs(
        assets,
        rules_cfg=rules_cfg,
        aligned_cfg=aligned_cfg,
        trip_id="demo-test",
        purposes=("cover",),
        pairs_per_purpose=3,
        seed=1,
        album_relative=False,
    )
    assert out["pairCount"] >= 1
    pair = out["pairs"][0]
    assert pair["leftRole"] in ("rules", "aligned")
    assert pair["optionLeft"]["assetId"] != pair["optionRight"]["assetId"]

    rows = [
        {"assetId": "a", "stratum": "landscape", "predictedOverall": 0.2, "humanScore": 2},
        {"assetId": "b", "stratum": "landscape", "predictedOverall": 0.8, "humanScore": 5},
        {"assetId": "c", "stratum": "landscape", "predictedOverall": 0.5},
        {"assetId": "d", "stratum": "landscape", "predictedOverall": 0.55},
    ]
    out = export_pairwise_pairs(rows, pairs_per_stratum=2, seed=1)
    assert out["pairCount"] >= 1
    pair = out["pairs"][0]
    assert pair["optionA"]["assetId"] != pair["optionB"]["assetId"]


def test_automated_purpose_win_report_aligned_wins():
    assets = [
        _asset("rules_pick", rules_cover=0.85, learned=0.25),
        _asset("aligned_pick", rules_cover=0.35, learned=0.95),
    ]
    labels = [
        {"assetId": "rules_pick", "humanScore": 2},
        {"assetId": "aligned_pick", "humanScore": 5},
    ]
    cfg = AestheticConfig(
        ml_calibrate=True,
        ml_calibrate_blend=0.5,
        use_purpose_presets=True,
        use_stratum_blend=False,
    )
    report = automated_purpose_win_report(
        assets,
        labels,
        rules_cfg=AestheticConfig(ml_calibrate=False, use_purpose_presets=True),
        aligned_cfg=cfg,
        purposes=("cover",),
    )
    assert report["purposes"]["cover"]["rulesPick"] == "rules_pick"
    assert report["purposes"]["cover"]["alignedPick"] == "aligned_pick"
    assert report["purposes"]["cover"]["verdict"] == "aligned_wins"


def test_pick_top_asset_cover():
    assets = [_asset("a", rules_cover=0.2, learned=0.2), _asset("b", rules_cover=0.9, learned=0.9)]
    cfg = AestheticConfig(use_purpose_presets=True)
    assert pick_top_asset(assets, "cover", cfg=cfg) == "b"


def test_normalize_human_score_likert():
    assert normalize_human_score(5) == 1.0
    assert normalize_human_score(1) == 0.0
