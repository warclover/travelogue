"""cover_candidates respects cover scoring version."""

from __future__ import annotations

from travelogue.curation.curate_scoring import cover_candidates, pick_cover_asset_id


def _asset(aid: str, **extra) -> dict:
    base = {
        "id": aid,
        "type": "image",
        "width": 1200,
        "height": 1800,
        "quality": {"sharpness": 200.0},
        "mediaClass": "photo",
        "dateConfidence": "high",
        "takenAt": "2025-04-01T10:00:00Z",
    }
    base.update(extra)
    return base


def test_cover_candidates_uses_scoring_version_for_alternate_ranking() -> None:
    assets = [
        _asset("good", quality={"sharpness": 250}),
        _asset("lowd", quality={"sharpness": 400}, dateConfidence="low"),
    ]
    v1_cover = pick_cover_asset_id(assets, export_layout="mobile", scoring_version="v1")
    v2_cover = pick_cover_asset_id(assets, export_layout="mobile", scoring_version="v2")
    assert v1_cover == "lowd"
    assert v2_cover == "good"

    v1_alts = cover_candidates(
        assets,
        v1_cover,
        export_layout="mobile",
        limit=2,
        scoring_version="v1",
        enable_phase6_cover_factors=False,
    )
    v2_alts = cover_candidates(
        assets,
        v2_cover,
        export_layout="mobile",
        limit=2,
        scoring_version="v2",
        enable_phase6_cover_factors=False,
    )
    assert v1_alts == ["lowd", "good"]
    assert v2_alts == ["good", "lowd"]
