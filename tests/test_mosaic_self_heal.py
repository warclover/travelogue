"""Phase 15 S3 · self-heal before legacy fallback."""

from __future__ import annotations

from dataclasses import replace

from tests._golden.helpers import build_mosaic_five_2p3l_window
from travelogue.config import get_config
from travelogue.curation.mosaic.compose import pick_best_window
from travelogue.curation.mosaic.scorer import MosaicScoreResult


def _window5():
    ids, aspects, assets_map = build_mosaic_five_2p3l_window()
    return ids, aspects, assets_map


def test_self_heal_tightened_rescore(monkeypatch, lte_pattern_enabled):
    ids, aspects, assets_map = _window5()
    cfg = replace(get_config().mosaic, self_heal_enabled=True, min_candidate_score=0.6)

    def fake_score(screen, **kwargs):
        cfg_kw = kwargs.get("cfg") or cfg
        boosted = (cfg_kw.penalties or {}).get("face_crop", 0) > 0.38
        total = 0.72 if boosted else 0.4
        return MosaicScoreResult(total=total, base=total, penalties={}, reason_codes=[])

    monkeypatch.setattr("travelogue.curation.mosaic.compose.score_candidate", fake_score)
    monkeypatch.setattr("travelogue.curation.mosaic.selfheal.score_candidate", fake_score)
    pick = pick_best_window(
        ids,
        aspects,
        assets_map,
        cfg=cfg,
        window_size=5,
        trip_photo_total=40,
    )
    assert not pick.used_legacy
    assert pick.log.self_heal_applied
    assert pick.log.self_heal_step == "tightened_rescore"
    assert pick.screen is not None


def test_self_heal_disabled_uses_legacy(monkeypatch, lte_pattern_enabled):
    ids, aspects, assets_map = _window5()
    cfg = replace(
        get_config().mosaic,
        self_heal_enabled=False,
        min_candidate_score=0.9,
        fallback_to_legacy=True,
    )

    def fake_score(screen, **kwargs):
        return MosaicScoreResult(total=0.1, base=0.1, penalties={}, reason_codes=[])

    monkeypatch.setattr(
        "travelogue.curation.mosaic.compose.score_candidate",
        fake_score,
    )
    pick = pick_best_window(
        ids,
        aspects,
        assets_map,
        cfg=cfg,
        window_size=5,
        trip_photo_total=40,
    )
    assert pick.used_legacy
    assert pick.log.fallback_reason == "low_score"
    assert not pick.log.self_heal_applied


def test_self_heal_degrade_stable_pattern() -> None:
    from travelogue.curation.mosaic.candidates import ScreenCandidate
    from travelogue.curation.mosaic.constants import PATTERN_PORTRAIT_3
    from travelogue.curation.mosaic.selfheal import try_self_heal_pick

    cfg = replace(get_config().mosaic, self_heal_enabled=True, min_candidate_score=0.6)
    unstable = ScreenCandidate(
        pattern_id="screen-experimental",
        ordered_asset_ids=["a", "b", "c"],
        screen={"patternId": "screen-experimental", "slots": []},
    )
    stable = ScreenCandidate(
        pattern_id=PATTERN_PORTRAIT_3,
        ordered_asset_ids=["a", "b", "c"],
        screen={"patternId": PATTERN_PORTRAIT_3, "slots": []},
    )
    scored = [(unstable, 0.55, [], {}), (stable, 0.52, [], {})]
    healed = try_self_heal_pick(
        scored,
        asset_ids=["a", "b", "c"],
        aspects={},
        assets_map={},
        cfg=cfg,
        layout_state=None,
        trip_photo_total=10,
        burst_seconds=12.0,
        min_score=0.6,
    )
    assert healed is not None
    assert healed[3] == "degrade_stable_pattern"
    assert healed[0].pattern_id == PATTERN_PORTRAIT_3


def test_self_heal_pick_disabled_returns_none() -> None:
    from travelogue.curation.mosaic.candidates import ScreenCandidate
    from travelogue.curation.mosaic.selfheal import try_self_heal_pick

    cfg = replace(get_config().mosaic, self_heal_enabled=False)
    cand = ScreenCandidate(
        pattern_id="screen-portrait-3",
        ordered_asset_ids=["a"],
        screen={"patternId": "screen-portrait-3", "slots": []},
    )
    assert (
        try_self_heal_pick(
            [(cand, 0.1, [], {})],
            asset_ids=["a"],
            aspects={},
            assets_map={},
            cfg=cfg,
            layout_state=None,
            trip_photo_total=10,
            burst_seconds=12.0,
            min_score=0.9,
        )
        is None
    )


def test_self_heal_pick_winner_above_min_returns_none() -> None:
    from travelogue.curation.mosaic.candidates import ScreenCandidate
    from travelogue.curation.mosaic.selfheal import try_self_heal_pick

    cfg = replace(get_config().mosaic, self_heal_enabled=True)
    cand = ScreenCandidate(
        pattern_id="screen-portrait-3",
        ordered_asset_ids=["a"],
        screen={"patternId": "screen-portrait-3", "slots": []},
    )
    assert (
        try_self_heal_pick(
            [(cand, 0.85, [], {})],
            asset_ids=["a"],
            aspects={},
            assets_map={},
            cfg=cfg,
            layout_state=None,
            trip_photo_total=10,
            burst_seconds=12.0,
            min_score=0.6,
        )
        is None
    )


def test_asset_drop_penalty_skips_featured() -> None:
    from travelogue.curation.mosaic.selfheal import _asset_drop_penalty

    penalty = _asset_drop_penalty(
        "hero",
        aspects={},
        assets_map={"hero": {"id": "hero", "featured": True}},
        cfg=get_config().mosaic,
    )
    assert penalty < 0


def test_allow_drop_false_never_sets_dropped_ids(monkeypatch):
    ids, aspects, assets_map = _window5()
    cfg = replace(
        get_config().mosaic,
        self_heal_enabled=True,
        allow_drop=False,
        min_candidate_score=0.99,
    )

    def fake_score(screen, **kwargs):
        return MosaicScoreResult(total=0.05, base=0.05, penalties={}, reason_codes=[])

    monkeypatch.setattr(
        "travelogue.curation.mosaic.compose.score_candidate",
        fake_score,
    )
    pick = pick_best_window(
        ids,
        aspects,
        assets_map,
        cfg=cfg,
        window_size=5,
        trip_photo_total=40,
    )
    assert pick.used_legacy
    assert pick.log.dropped_asset_ids == []
