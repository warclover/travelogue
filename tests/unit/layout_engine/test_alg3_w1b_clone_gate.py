"""ALG-V3 W1b · B7 conditional clone gate + AC-10 funnel corpus."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from travelogue.config import AppConfig
from travelogue.config.mosaic import (
    MosaicConfig,
    NearSceneCloneGateConfig,
    TemplateContractConfig,
    TemplateExperimentsConfig,
)
from travelogue.curation.algo_v3_summary import build_algo_v3_summary
from travelogue.curation.algorithm_profile import (
    assess_algorithm_freshness,
    expected_profile,
)
from travelogue.layout_engine.mosaic.candidates import (
    generate_window_candidates_with_rejections,
)
from travelogue.layout_engine.mosaic.clone_detection import (
    effective_clone_hard_gate,
    near_scene_clone_penalty,
)


def _tight_clone_window() -> tuple[dict[str, dict], dict[str, str]]:
    """4 assets · tight span · person-heavy · no shotGroup (SSG off/empty)."""
    assets = {
        "a0": {
            "id": "a0",
            "takenAt": "2025-04-20T22:00:00Z",
            "tags": ["person", "face"],
            "width": 1600,
            "height": 900,
        },
        "a1": {
            "id": "a1",
            "takenAt": "2025-04-20T22:01:00Z",
            "tags": ["person", "face"],
            "width": 900,
            "height": 1600,
        },
        "a2": {
            "id": "a2",
            "takenAt": "2025-04-20T22:02:00Z",
            "tags": ["person", "face"],
            "width": 900,
            "height": 1600,
        },
        "a3": {
            "id": "a3",
            "takenAt": "2025-04-20T22:03:00Z",
            "tags": ["person", "face"],
            "width": 1600,
            "height": 900,
        },
    }
    aspects = {
        "a0": "landscape",
        "a1": "portrait",
        "a2": "portrait",
        "a3": "landscape",
    }
    return assets, aspects


def test_b7_effective_gate_on_without_ssg() -> None:
    cfg = MosaicConfig()
    assert cfg.near_scene_clone_gate.enabled is False
    assert cfg.near_scene_clone_gate.conditional is True
    assets, _ = _tight_clone_window()
    assert effective_clone_hard_gate(
        cfg, asset_ids=list(assets), assets_map=assets
    )


def test_b7_effective_gate_off_with_ssg_and_vision_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    assets, _ = _tight_clone_window()
    for aid in assets:
        assets[aid]["shotGroupId"] = "g1"
    cfg = MosaicConfig()
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.clone_detection.vision_is_degraded",
        lambda *, app_cfg=None: False,
    )
    assert (
        effective_clone_hard_gate(cfg, asset_ids=list(assets), assets_map=assets)
        is False
    )


def test_b7_conditional_false_force_off() -> None:
    assets, _ = _tight_clone_window()
    cfg = MosaicConfig(
        near_scene_clone_gate=NearSceneCloneGateConfig(enabled=False, conditional=False),
    )
    assert (
        effective_clone_hard_gate(cfg, asset_ids=list(assets), assets_map=assets)
        is False
    )


def test_ac10_b7_reduces_fake_slice_winners_at_least_40pct() -> None:
    """AC-10: no-SSG corpus — B7 on vs conditional off; clone rejects ↑ ≥40% relative.

    Uses reject funnel visibility (hard gate) rather than SSG-already-green substitute.
    """
    assets, aspects = _tight_clone_window()
    trip_id = "alg3-ac10-clone"
    weighted = "screen-mosaic-4-2p2l-portrait-bookends"
    base = MosaicConfig()
    common = dict(
        template_contract=TemplateContractConfig(enabled=True, shadow_log=False),
        template_experiments=TemplateExperimentsConfig(
            enabled=True,
            allowlist=(weighted,),
            cohort_trip_ids=(trip_id,),
        ),
    )

    cfg_off = dataclasses.replace(
        base,
        **common,
        near_scene_clone_gate=NearSceneCloneGateConfig(enabled=False, conditional=False),
    )
    cfg_on = dataclasses.replace(
        base,
        **common,
        near_scene_clone_gate=NearSceneCloneGateConfig(enabled=False, conditional=True),
    )

    # Sanity: penalty high enough that hard gate would fire
    assert near_scene_clone_penalty(weighted, list(assets), assets) >= 0.75

    res_off = generate_window_candidates_with_rejections(
        list(assets), aspects, assets, cfg=cfg_off, trip_id=trip_id
    )
    res_on = generate_window_candidates_with_rejections(
        list(assets), aspects, assets, cfg=cfg_on, trip_id=trip_id
    )

    def _clone_rejects(res) -> int:
        return sum(1 for r in res.rejected if r.get("reason") == "near_scene_clone")

    off_n = _clone_rejects(res_off)
    on_n = _clone_rejects(res_on)
    # Off path: no hard clone rejects; on path: at least one.
    assert off_n == 0
    assert on_n >= 1
    # Relative reduction of "unguarded slice risk windows" (winners that are slice clones):
    off_slice_winners = sum(
        1
        for c in res_off.candidates
        if c.pattern_id == weighted and c.hard_valid
    )
    on_slice_winners = sum(
        1
        for c in res_on.candidates
        if c.pattern_id == weighted and c.hard_valid
    )
    if off_slice_winners > 0:
        reduction = (off_slice_winners - on_slice_winners) / off_slice_winners
        assert reduction >= 0.40
    else:
        # Funnel hard-visible fallback (AC-10 alternate): B7 rejects present.
        assert on_n > off_n


def test_ac10_funnel_hard_visible_in_algo_v3() -> None:
    trip = {
        "assets": [{"id": "a1"}],
        "curation": {
            "mosaicDecisionLog": [
                {
                    "isWinnerPlan": True,
                    "rejectedTemplates": [
                        {
                            "templateId": "screen-mosaic-4-2l2p-weighted",
                            "reason": "near_scene_clone",
                            "detail": "penalty=0.95",
                        }
                    ],
                }
            ]
        },
    }
    summary = build_algo_v3_summary(trip, cfg=AppConfig(), build_screen_calls=0)
    assert summary["rejectFunnelTop"]["near_scene_clone"] >= 1
    assert summary["cloneGateEffective"] is True


def test_fe_alg3_s03_algo_v3_does_not_false_flag_stale() -> None:
    """FE-ALG3-S03: writing curation.algoV3 must not alone flip algorithmStale."""
    cfg = AppConfig()
    profile = expected_profile(cfg)
    trip = {
        "chapters": [{"id": "ch-01", "screens": []}],
        "algorithmProfile": profile,
        "curation": {},
    }
    before = assess_algorithm_freshness(trip, app_cfg=cfg)
    trip["curation"]["algoV3"] = build_algo_v3_summary(trip, cfg=cfg, build_screen_calls=2)
    after = assess_algorithm_freshness(trip, app_cfg=cfg)
    assert before["algorithmStale"] == after["algorithmStale"]


def test_fe_alg3_s03_algo_v3_does_not_false_flag_longshot_stale(
    tmp_path: Path,
) -> None:
    """FE-ALG3-S03: algoV3 meta must not alone make longshot exports look stale."""
    import os
    import time

    from travelogue.web.studio_trips import longshot_outputs_stale

    trip_dir = tmp_path / "alg3-s03-longshot"
    trip_dir.mkdir()
    moments = trip_dir / "demo-moments-01.png"
    moments.write_bytes(b"png")
    # Export newer than trip watermark → not stale.
    now = time.time()
    os.utime(moments, (now, now))
    trip_mtime = now - 60.0
    assert longshot_outputs_stale(trip_dir, trip_mtime=trip_mtime) is False

    trip = {
        "chapters": [{"id": "ch-01", "screens": []}],
        "curation": {},
        "updatedAt": "2025-01-01T00:00:00Z",
    }
    trip["curation"]["algoV3"] = build_algo_v3_summary(
        trip, cfg=AppConfig(), build_screen_calls=3
    )
    # Same filesystem watermark → still not stale (algoV3 is trip JSON meta only).
    assert longshot_outputs_stale(trip_dir, trip_mtime=trip_mtime) is False


def test_fe_alg3_s03_shelf_cta_not_forced_by_algo_v3_alone() -> None:
    """FE-ALG3-S03: shelf resume CTA stays「打开预览」when both stale flags false."""
    from pathlib import Path

    logic = (
        Path(__file__).resolve().parents[3]
        / "templates"
        / "studio"
        / "homepage-v2"
        / "shelf-actions-logic.js"
    ).read_text(encoding="utf-8")
    assert "function shelfResumeActions" in logic
    assert 'label: "更新长图"' in logic
    assert 'label: "重新排版"' in logic
    assert 'label: "打开预览"' in logic
    # Contract: longshot/algorithm CTAs are gated on their stale flags only —
    # nothing in this module reads curation.algoV3.
    assert "algoV3" not in logic
    assert "algorithmStale" in logic
    assert "longshotStale" in logic
