"""Cover scoring V2 (additive logit) tests."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.curation.cover_scoring_v2 import (
    CoverScoringParamsV2,
    build_cover_explain_v2,
    cover_logit_v2,
    cover_score_v2,
    extract_cover_features,
    hero_score_v2,
)
from travelogue.curation.curate_scoring import (
    cover_score,
    effective_cover_score,
    pick_cover_asset_id,
    score_ranked_cover_ids,
)
from travelogue.media.sharpness import sharpness_score, sharpness_score_v2
from PIL import Image, ImageDraw

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "cover_v2_quality_priority.json"


def _asset(**extra) -> dict:
    base = {
        "id": "a1",
        "type": "image",
        "width": 1200,
        "height": 1800,
        "quality": {"sharpness": 200.0},
        "mediaClass": "photo",
        "dateConfidence": "high",
    }
    base.update(extra)
    return base


def test_cover_logit_v2_prefers_quality_landscape_over_panorama() -> None:
    pool = [
        _asset(
            id="landscape_16_9",
            width=1920,
            height=1080,
            quality={"sharpness": 420.0},
            dominantTone="#4488cc",
            meanLuma=0.55,
            focalPoint={"x": 0.33, "y": 0.33},
        ),
        _asset(
            id="panorama_dull",
            width=3000,
            height=1000,
            quality={"sharpness": 180.0},
            dominantTone="#888888",
            meanLuma=0.45,
            focalPoint={"x": 0.5, "y": 0.5},
        ),
    ]
    land = pool[0]
    pano = pool[1]
    assert cover_logit_v2(land, "web", pool) > cover_logit_v2(pano, "web", pool)
    assert cover_score_v2(land, "web", pool=pool) > cover_score_v2(pano, "web", pool=pool)


def test_cover_score_routes_v2_when_version_set() -> None:
    sharp = _asset(id="sharp", quality={"sharpness": 400.0})
    dull = _asset(id="dull", quality={"sharpness": 50.0})
    pool = [sharp, dull]
    assert cover_score(
        sharp, "mobile", scoring_version="v2", pool=pool
    ) > cover_score(dull, "mobile", scoring_version="v2", pool=pool)


def test_build_cover_explain_v2_has_contribution() -> None:
    asset = _asset(dominantTone="#4488cc", meanLuma=0.55)
    pool = [asset, _asset(id="b", quality={"sharpness": 80.0})]
    rows = build_cover_explain_v2(asset, "mobile", pool)
    assert rows
    assert "contribution" in rows[0]
    assert "feature" in rows[0]


def test_pick_cover_v2_quality_priority_fixtures() -> None:
    data = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    for case in data["cases"]:
        assets = case["assets"]
        layout = case["export_layout"]
        if case.get("winner_in_top3"):
            from travelogue.curation.curate_scoring import score_ranked_cover_ids

            fid = case["winner_in_top3"]
            ranked = score_ranked_cover_ids(
                assets, export_layout=layout, scoring_version="v2", limit=3
            )
            top3 = {row["assetId"] for row in ranked[:3]}
            assert fid in top3, case["id"]
            continue
        winner = pick_cover_asset_id(
            assets,
            export_layout=layout,
            scoring_version="v2",
        )
        if case.get("assert_equal_ids"):
            assert winner in case["assert_equal_ids"], case["id"]
        else:
            assert winner == case["winner_id"], case["id"]


def test_featured_effective_in_top3_when_logit_close() -> None:
    base = _asset(
        id="material",
        quality={"sharpness": 210.0},
        userTier="material",
    )
    featured = _asset(
        id="featured",
        quality={"sharpness": 200.0},
        userTier="featured",
    )
    pool = [base, featured]
    ranked = score_ranked_cover_ids(
        [base, featured],
        export_layout="mobile",
        scoring_version="v2",
        featured_weight=1.35,
        limit=3,
    )
    ids = [row["assetId"] for row in ranked]
    assert "featured" in ids


def test_hero_score_v2_excludes_portrait() -> None:
    assert hero_score_v2(_asset(width=1200, height=1800)) == 0.0
    assert hero_score_v2(_asset(width=2400, height=1350)) > 0.0


def test_extract_cover_features_bounded() -> None:
    feats = extract_cover_features(_asset(), "mobile", [_asset()])
    for value in feats.values():
        assert 0.0 <= value <= 1.0


def test_sharpness_v2_laplacian_on_synthetic_image() -> None:
    img = Image.new("RGB", (256, 256), color=(128, 128, 128))
    draw = ImageDraw.Draw(img)
    for i in range(0, 256, 8):
        draw.line((i, 0, i, 255), fill=(0, 0, 0), width=1)
    assert sharpness_score_v2(img) > sharpness_score(img) * 0.01
