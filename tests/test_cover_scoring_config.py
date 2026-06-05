"""Cover scoring S1 config + portrait-dominant demote (cover-selection-plan v0.2)."""

from __future__ import annotations

from travelogue.curation.cover_scoring_params import (
    CoverScoringParams,
    person_tag_ratio,
    resolve_person_demote,
)
from travelogue.curation.curate_scoring import (
    cover_score,
    pick_cover_asset_id,
    score_ranked_cover_ids,
)


def _asset(aid: str, **extra) -> dict:
    base = {
        "id": aid,
        "type": "image",
        "width": 1200,
        "height": 1800,
        "quality": {"sharpness": 100.0},
        "mediaClass": "photo",
        "dateConfidence": "high",
    }
    base.update(extra)
    return base


def test_cover_scoring_params_from_mapping_snake_and_camel() -> None:
    p = CoverScoringParams.from_mapping(
        {"personDemote": 0.65, "person_dominant_tag_ratio": 0.5}
    )
    assert p.person_demote == 0.65
    assert p.person_dominant_tag_ratio == 0.5


def test_person_tag_ratio_counts_tagged_assets() -> None:
    assets = [
        _asset("a1", tags=["face"]),
        _asset("a2", tags=["landscape"]),
        _asset("a3"),
    ]
    assert abs(person_tag_ratio(assets) - 1 / 3) < 1e-6


def test_resolve_person_demote_portrait_dominant_trip() -> None:
    params = CoverScoringParams(person_demote=0.72, person_demote_portrait_trip=1.0)
    portrait_pool = [_asset(f"p{i}", tags=["person"]) for i in range(4)] + [
        _asset("l1", tags=["landscape"])
    ]
    landscape_only = [_asset("l1", tags=["landscape"])]
    assert resolve_person_demote(params, portrait_pool) == 1.0
    assert resolve_person_demote(params, landscape_only) == 0.72


def test_person_demote_mult_scales_tagged_asset_score() -> None:
    person = _asset("person", tags=["person"], focalPoint={"x": 0.5, "y": 0.5})
    assert cover_score(person, "mobile", person_demote_mult=1.0) > cover_score(
        person, "mobile", person_demote_mult=0.5
    )


def test_score_ranked_cover_ids_is_pure_score_order() -> None:
    assets = [
        _asset("low", quality={"sharpness": 10.0}),
        _asset("high", quality={"sharpness": 200.0}),
    ]
    ranked = score_ranked_cover_ids(assets, export_layout="mobile", limit=3)
    assert ranked[0]["assetId"] == "high"
    assert ranked[0]["rank"] == 1
