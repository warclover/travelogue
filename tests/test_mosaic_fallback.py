"""Low-score winner falls back to legacy (AC-P15-08)."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import get_config
from travelogue.curation.mosaic.compose import pick_best_window
from travelogue.curation.mosaic.scorer import MosaicScoreResult


def test_low_score_fallback_reason(monkeypatch):
    aspects = {
        "p0": "portrait",
        "p1": "portrait",
        "p2": "portrait",
        "l0": "landscape",
        "l1": "landscape",
    }
    assets_map = {
        "p0": {"id": "p0", "width": 1200, "height": 1800, "takenAt": "2024-06-01T10:00:00Z"},
        "p1": {"id": "p1", "width": 1200, "height": 1800, "takenAt": "2024-06-01T10:01:00Z"},
        "p2": {"id": "p2", "width": 1200, "height": 1800, "takenAt": "2024-06-01T10:02:00Z"},
        "l0": {"id": "l0", "width": 2000, "height": 1200, "takenAt": "2024-06-01T10:03:00Z"},
        "l1": {"id": "l1", "width": 2000, "height": 1200, "takenAt": "2024-06-01T10:04:00Z"},
    }
    cfg = replace(
        get_config().mosaic,
        self_heal_enabled=False,
        min_candidate_score=0.99,
        fallback_to_legacy=True,
        # Keep 5-slot enabled so this test exercises the low_score path rather than
        # the disabled-window guard (no_candidates).
        enabled_window_sizes=(3, 4, 5, 8, 9),
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
