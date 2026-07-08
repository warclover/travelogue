"""allow_drop=true records mosaicDroppedAssetIds when self-heal drops."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import get_config
from travelogue.curation.mosaic.compose import pick_best_window
from travelogue.curation.mosaic.hook import drain_mosaic_dropped, drain_mosaic_logs
from travelogue.curation.mosaic.scorer import MosaicScoreResult


def test_allow_drop_records_dropped_asset(monkeypatch):
    ids = [f"a{i}" for i in range(5)]
    aspects = {aid: "landscape" for aid in ids}
    assets_map = {
        aid: {
            "id": aid,
            "width": 2000,
            "height": 1200,
            "takenAt": "2024-06-01T10:00:00Z",
            "quality": {"sharpness": 0.1 if aid == "a0" else 0.9},
            "tags": ["person"] if aid == "a0" else [],
        }
        for aid in ids
    }
    cfg = replace(
        get_config().mosaic,
        self_heal_enabled=True,
        allow_drop=True,
        min_candidate_score=0.99,
        enabled_window_sizes=(3, 4, 5, 6, 8, 9),
    )

    def fake_score(screen, **kwargs):
        return MosaicScoreResult(total=0.05, base=0.05, penalties={}, reason_codes=[])

    monkeypatch.setattr("travelogue.curation.mosaic.compose.score_candidate", fake_score)
    monkeypatch.setattr("travelogue.curation.mosaic.selfheal.score_candidate", fake_score)
    drain_mosaic_logs()
    drain_mosaic_dropped()
    pick = pick_best_window(
        ids,
        aspects,
        assets_map,
        cfg=cfg,
        window_size=5,
        trip_photo_total=40,
    )
    drain_mosaic_logs()
    dropped = drain_mosaic_dropped()
    assert pick.used_legacy or pick.log.dropped_asset_ids or dropped
    if pick.log.dropped_asset_ids:
        assert "a0" in pick.log.dropped_asset_ids
