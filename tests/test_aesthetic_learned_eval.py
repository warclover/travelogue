"""AA · M1 learned aesthetic eval."""

from __future__ import annotations

from travelogue.config import AestheticConfig
from travelogue.curation.aesthetic_learned_eval import build_eval_rows, srcc_comparison
from travelogue.curation.aesthetic_score import _read_learned_aesthetic_score, compute_aesthetic


def _asset_with_dims(overall: float = 0.5):
    base = {
        "id": "a1",
        "quality": {
            "sharpness": 200,
            "meanLuma": 0.5,
            "aesthetic": compute_aesthetic(
                {"id": "a1", "quality": {"sharpness": 200, "meanLuma": 0.5}},
                signals={
                    "dynamicRange": 0.5,
                    "midtoneCenter": 0.5,
                    "colorHarmony": 0.5,
                    "lumaGradient": 0.5,
                    "contrast": 0.5,
                    "balance": 0.5,
                    "subjectContrast": 0.5,
                },
            ),
        },
    }
    base["quality"]["aesthetic"]["overall"] = overall
    return base


def test_read_learned_aesthetic_prefers_signals():
    asset = _asset_with_dims()
    asset["quality"]["aesthetic"]["signals"] = {"learnedAesthetic": 0.88}
    assert _read_learned_aesthetic_score(asset) == 0.88


def test_read_learned_aesthetic_falls_back_to_flat_field():
    asset = _asset_with_dims()
    asset["quality"]["aestheticScore"] = 0.42
    assert _read_learned_aesthetic_score(asset) == 0.42


def test_srcc_comparison_orders_learned_above_noise():
    rows = []
    for i, hs in enumerate([1, 2, 3, 4, 5]):
        rows.append(
            {
                "humanScore": hs,
                "baselinePredicted": 3 - abs(hs - 3) * 0.1,
                "rulesOnly": 3 - abs(hs - 3) * 0.15,
                "learnedOnly": hs / 5.0,
                "blendedOverall": 0.5 * (3 - abs(hs - 3) * 0.15) / 5 + 0.5 * (hs / 5.0),
            }
        )
    rep = srcc_comparison(rows)
    learned = rep["metrics"]["learned_nima"]["srcc"]
    baseline = rep["metrics"]["baseline_rules_export"]["srcc"]
    assert learned is not None and baseline is not None
    assert learned > baseline


def test_build_eval_rows_from_assets():
    asset = _asset_with_dims(0.55)
    asset["quality"]["aesthetic"]["signals"] = {"learnedAesthetic": 0.7}
    rows = build_eval_rows(
        {"a1": asset},
        [{"assetId": "a1", "humanScore": 4, "predictedOverall": 0.55, "stratum": "person"}],
        cfg=AestheticConfig(ml_calibrate=True, ml_calibrate_blend=0.4),
    )
    assert len(rows) == 1
    assert rows[0]["learnedOnly"] == 0.7
    assert rows[0]["rulesOnly"] is not None


def test_blended_score_interpolates():
    from travelogue.curation.aesthetic_learned_eval import blended_score

    assert blended_score(0.5, 1.0, 0.0) == 0.5
    assert blended_score(0.5, 1.0, 1.0) == 1.0
    assert blended_score(0.5, 1.0, 0.4) == 0.7


def test_grid_search_blend_finds_better_weight():
    from travelogue.curation.aesthetic_learned_eval import grid_search_blend

    assets = {}
    labels = []
    for i in range(10):
        aid = f"a{i}"
        hs = i + 1
        rules = 0.3 + (i % 3) * 0.1
        learned = hs / 10.0
        assets[aid] = {
            "id": aid,
            "quality": {
                "aesthetic": {
                    "overall": rules,
                    "dims": {
                        "composition": rules,
                        "exposure": rules,
                        "color": rules,
                        "lighting": rules,
                        "subjectClarity": rules,
                    },
                    "signals": {"learnedAesthetic": learned},
                }
            },
        }
        labels.append({"assetId": aid, "humanScore": hs, "stratum": "person"})
    out = grid_search_blend(
        assets,
        labels,
        blend_min=0.0,
        blend_max=1.0,
        blend_step=0.1,
        baseline_rules_srcc=0.2,
    )
    best = out["purposes"]["default"]["bestSrcc"]
    learned = out["learnedOnly"]["srcc"]
    assert best is not None and learned is not None
    assert best >= learned - 0.01
    assert out["recommended"]["blend"] is not None
