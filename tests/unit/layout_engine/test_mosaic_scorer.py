"""Phase 15 mosaic scorer determinism."""

from __future__ import annotations

from travelogue.config import MosaicConfig
from travelogue.layout_engine.mosaic.compose import pick_best_five_window
from travelogue.layout_engine.mosaic.scorer import weights_hash


def _five_assets():
    aspects = {}
    assets_map = {}
    for i, kind in enumerate(["portrait", "portrait", "landscape", "landscape", "landscape"]):
        aid = f"a{i}"
        aspects[aid] = kind
        assets_map[aid] = {
            "id": aid,
            "width": 1600 if kind == "landscape" else 900,
            "height": 900 if kind == "landscape" else 1600,
            "takenAt": "2024-06-01T10:00:00Z",
            "quality": {"sharpness": 0.8},
        }
    return aspects, assets_map


def test_pick_best_deterministic():
    aspects, assets_map = _five_assets()
    cfg = MosaicConfig(enabled=True, enabled_window_sizes=(5,), deterministic_strict=True)
    ids = list(aspects.keys())
    r1 = pick_best_five_window(ids, aspects, assets_map, cfg=cfg, trip_photo_total=40)
    r2 = pick_best_five_window(ids, aspects, assets_map, cfg=cfg, trip_photo_total=40)
    assert r1.log.winner_pattern_id == r2.log.winner_pattern_id
    assert abs(r1.log.winner_score - r2.log.winner_score) < 1e-6


def test_weights_hash_stable():
    cfg = MosaicConfig()
    assert weights_hash(cfg) == weights_hash(cfg)
