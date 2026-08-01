"""Phase 15 S3 · self-heal before legacy fallback."""

from __future__ import annotations

from dataclasses import replace

from tests._golden.helpers import build_mosaic_five_2p3l_window
from travelogue.config import get_config
from travelogue.layout_engine.mosaic.compose import pick_best_window
from travelogue.layout_engine.mosaic.scorer import MosaicScoreResult


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

    monkeypatch.setattr("travelogue.layout_engine.mosaic.compose.score_candidate", fake_score)
    monkeypatch.setattr("travelogue.layout_engine.mosaic.selfheal.score_candidate", fake_score)
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
        "travelogue.layout_engine.mosaic.compose.score_candidate",
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
    from travelogue.layout_engine.mosaic.candidates import ScreenCandidate
    from travelogue.layout_engine.mosaic.constants import PATTERN_PORTRAIT_3
    from travelogue.layout_engine.mosaic.selfheal import try_self_heal_pick

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
    from travelogue.layout_engine.mosaic.candidates import ScreenCandidate
    from travelogue.layout_engine.mosaic.selfheal import try_self_heal_pick

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
    from travelogue.layout_engine.mosaic.candidates import ScreenCandidate
    from travelogue.layout_engine.mosaic.selfheal import try_self_heal_pick

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
    from travelogue.layout_engine.mosaic.selfheal import _asset_drop_penalty

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
        "travelogue.layout_engine.mosaic.compose.score_candidate",
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


def test_self_heal_drop_respects_usage_reject(monkeypatch):
    """BLK-10 / AC-TPC-05: drop_worst_asset must not bypass usage hard reject."""
    from travelogue.layout_engine.mosaic.candidates import (
        ScreenCandidate,
        WindowCandidateResult,
    )
    from travelogue.layout_engine.mosaic.selfheal import try_self_heal_pick

    cfg = replace(
        get_config().mosaic,
        self_heal_enabled=True,
        allow_drop=True,
        max_drop_ratio=0.5,
        min_candidate_score=0.9,
    )
    # 5 → drop 1 → remaining 4 (in default enabled_window_sizes)
    asset_ids = ["a", "b", "c", "d", "e"]
    cand = ScreenCandidate(
        pattern_id="screen-experimental",
        ordered_asset_ids=asset_ids,
        screen={"patternId": "screen-experimental", "slots": []},
    )
    scored = [(cand, 0.1, [], {})]
    captured: dict = {}

    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.selfheal._asset_drop_penalty",
        lambda aid, **_kw: 0.9 if aid == "a" else 0.1,
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.selfheal.score_candidate",
        lambda *_a, **_k: MosaicScoreResult(
            total=0.1, base=0.1, penalties={}, reason_codes=[]
        ),
    )

    def _fake_gen(*_args, **kwargs):
        captured["window_ctx"] = kwargs.get("window_ctx")
        return WindowCandidateResult(
            candidates=[],
            rejected=[
                {
                    "templateId": "screen-portrait-4",
                    "reason": "usage_rule:UR-04",
                }
            ],
        )

    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.candidates."
        "generate_window_candidates_with_rejections",
        _fake_gen,
    )

    healed = try_self_heal_pick(
        scored,
        asset_ids=asset_ids,
        aspects={},
        assets_map={aid: {"id": aid} for aid in asset_ids},
        cfg=cfg,
        layout_state=None,
        trip_photo_total=10,
        burst_seconds=12.0,
        min_score=0.9,
        median_sharp=0.5,
    )
    assert healed is None
    assert captured.get("window_ctx") is not None
    assert list(captured["window_ctx"].window_asset_ids) == ["b", "c", "d", "e"]
    assert "a" not in captured["window_ctx"].window_asset_ids


def test_self_heal_max_rescore_zero_skips_tightened_branch(monkeypatch):
    """ALG-V3 B6 · self_heal_max_rescore=0 disables tightened rescore."""
    from travelogue.layout_engine.mosaic.candidates import ScreenCandidate
    from travelogue.layout_engine.mosaic.selfheal import try_self_heal_pick

    screen = {"patternId": "screen-portrait-3", "slots": []}
    cand = ScreenCandidate(
        pattern_id="screen-portrait-3",
        ordered_asset_ids=["a", "b", "c"],
        screen=screen,
        hard_valid=True,
    )
    scored = [(cand, 0.2, [], {})]
    cfg = replace(
        get_config().mosaic,
        self_heal_enabled=True,
        self_heal_max_rescore=0,
        allow_drop=False,
        min_candidate_score=0.6,
    )
    calls = {"n": 0}

    def _score(*_a, **_k):
        calls["n"] += 1
        return MosaicScoreResult(total=0.9, base=0.9, penalties={}, reason_codes=[])

    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.selfheal.score_candidate",
        _score,
    )
    healed = try_self_heal_pick(
        scored,
        asset_ids=["a", "b", "c"],
        aspects={},
        assets_map={"a": {"id": "a"}, "b": {"id": "b"}, "c": {"id": "c"}},
        cfg=cfg,
        layout_state=None,
        trip_photo_total=10,
        burst_seconds=12.0,
        min_score=0.6,
    )
    assert calls["n"] == 0
    assert healed is None


def test_self_heal_max_drop_attempts_zero_skips_drop(monkeypatch):
    """ALG-V3 B6 · self_heal_max_drop_attempts=0 disables drop_worst_asset."""
    from travelogue.layout_engine.mosaic.candidates import ScreenCandidate
    from travelogue.layout_engine.mosaic.selfheal import try_self_heal_pick

    screen = {"patternId": "screen-portrait-3", "slots": []}
    cand = ScreenCandidate(
        pattern_id="screen-x",
        ordered_asset_ids=["a", "b", "c"],
        screen=screen,
        hard_valid=True,
    )
    scored = [(cand, 0.1, [], {})]
    cfg = replace(
        get_config().mosaic,
        self_heal_enabled=True,
        self_heal_max_rescore=0,
        self_heal_max_drop_attempts=0,
        allow_drop=True,
        min_candidate_score=0.9,
    )
    gen_calls = {"n": 0}

    def _fake_gen(*_a, **_k):
        gen_calls["n"] += 1
        from travelogue.layout_engine.mosaic.candidates import WindowCandidateResult

        return WindowCandidateResult(candidates=[], rejected=[])

    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.candidates."
        "generate_window_candidates_with_rejections",
        _fake_gen,
    )
    healed = try_self_heal_pick(
        scored,
        asset_ids=["a", "b", "c"],
        aspects={},
        assets_map={"a": {"id": "a"}, "b": {"id": "b"}, "c": {"id": "c"}},
        cfg=cfg,
        layout_state=None,
        trip_photo_total=10,
        burst_seconds=12.0,
        min_score=0.9,
    )
    assert gen_calls["n"] == 0
    assert healed is None
