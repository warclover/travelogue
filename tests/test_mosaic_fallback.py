"""Low-score winner falls back to legacy (AC-P15-08)."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import get_config
from travelogue.curation.mosaic.compose import pick_best_window
from travelogue.curation.mosaic.scorer import MosaicScoreResult


def test_low_score_fallback_reason(monkeypatch):
    aspects = {f"a{i}": "landscape" for i in range(5)}
    assets_map = {
        f"a{i}": {
            "id": f"a{i}",
            "width": 2000,
            "height": 1200,
            "takenAt": "2024-06-01T10:00:00Z",
        }
        for i in range(5)
    }
    cfg = replace(
        get_config().mosaic,
        self_heal_enabled=False,
        min_candidate_score=0.99,
        fallback_to_legacy=True,
    )

    def fake_score(screen, **kwargs):
        return MosaicScoreResult(total=0.1, base=0.1, penalties={}, reason_codes=[])

    monkeypatch.setattr("travelogue.curation.mosaic.compose.score_candidate", fake_score)
    monkeypatch.setattr("travelogue.curation.mosaic.selfheal.score_candidate", fake_score)
    pick = pick_best_window(
        list(aspects.keys()),
        aspects,
        assets_map,
        cfg=cfg,
        window_size=5,
        trip_photo_total=40,
    )
    assert pick.used_legacy
    assert pick.log.fallback_reason == "low_score"
