"""Tests for album profile + stratified config."""

from __future__ import annotations

from travelogue.config import AestheticConfig, resolve_learned_blend
from travelogue.config.aesthetic_stratified import (
    apply_stratum_preference_overlay,
    landscape_pilot_config,
)
from travelogue.curation.aesthetic_score import stratum_score_percentiles
from travelogue.curation.album_profile import (
    compute_album_profile,
    effective_priority_strata,
    profile_priority_strata,
)


def _asset(aid: str, *, width: int = 4000, height: int = 3000, overall: float = 0.5):
    return {
        "id": aid,
        "type": "image",
        "layoutEligible": True,
        "width": width,
        "height": height,
        "aspectKind": "landscape",
        "quality": {
            "aesthetic": {
                "overall": overall,
                "dims": {
                    "composition": overall,
                    "exposure": overall,
                    "color": overall,
                    "lighting": overall,
                    "subjectClarity": overall,
                },
            }
        },
    }


def test_compute_album_profile_landscape_dominant():
    trip = {"assets": [_asset("a1", overall=0.6), _asset("a2", overall=0.7)]}
    profile = compute_album_profile(trip)
    assert profile["eligibleImages"] == 2
    assert profile["dominantStratum"] == "landscape"
    assert profile["strata"]["landscape"] == 1.0


def test_stratum_blend_only_landscape():
    asset = _asset("l1")
    cfg = AestheticConfig(
        ml_calibrate_blend=0.4,
        use_stratum_blend=True,
        stratum_blends={"landscape": 0.6, "person": 0.6},
        stratum_blend_only=("landscape",),
    )
    assert resolve_learned_blend(asset, cfg) == 0.6
    portrait = dict(asset)
    portrait["faces"] = [{"bbox": [0, 0, 10, 10]}]
    portrait["subjectClass"] = "person"
    assert resolve_learned_blend(portrait, cfg) == 0.0


def test_stratum_score_percentiles():
    assets = [
        _asset("a1", overall=0.2),
        _asset("a2", overall=0.4),
        _asset("a3", overall=0.8),
    ]
    p75 = stratum_score_percentiles(assets, percentile=0.75)
    assert p75["landscape"] == 0.8


def test_landscape_pilot_config_loads(tmp_path):
    cal = tmp_path / "cal.json"
    cal.write_text('{"recommendedBlends": {"landscape": 0.55}}', encoding="utf-8")
    cfg = landscape_pilot_config(cal)
    assert cfg.stratum_blend_only == ("landscape",)
    assert cfg.stratum_blends["landscape"] == 0.55


def test_profile_priority_strata_dominant_and_secondary():
    profile = {
        "dominantStratum": "landscape",
        "strata": {"landscape": 0.7, "group": 0.2, "person": 0.1},
    }
    assert profile_priority_strata(profile) == frozenset({"landscape", "group"})


def test_profile_priority_strata_falls_back_to_dominant():
    profile = {"dominantStratum": "person", "strata": {}}
    assert profile_priority_strata(profile) == frozenset({"person"})


def test_effective_priority_strata_portrait_override():
    profile = {
        "dominantStratum": "landscape",
        "strata": {"landscape": 0.9, "person": 0.1},
    }
    assert effective_priority_strata(profile, preference="portrait") == frozenset(
        {"person", "group"}
    )


def test_apply_stratum_preference_overlay_landscape():
    cfg = AestheticConfig(
        use_stratum_blend=True,
        stratum_blend_only=("landscape", "person"),
    )
    out = apply_stratum_preference_overlay(cfg, "landscape")
    assert out.stratum_blend_only == ("landscape",)
    assert out.stratum_blend_only_by_purpose.get("cover") == ("landscape",)


def test_stratum_blend_only_by_purpose():
    landscape = _asset("l1")
    portrait = dict(landscape)
    portrait["faces"] = [{"bbox": [0, 0, 10, 10]}]
    portrait["subjectClass"] = "person"
    cfg = AestheticConfig(
        use_stratum_blend=True,
        stratum_blends={"landscape": 0.6, "person": 0.6},
        stratum_blend_only=("landscape", "person"),
        stratum_blend_only_by_purpose={"hero": ("landscape",)},
    )
    assert resolve_learned_blend(portrait, cfg, purpose="cover") == 0.6
    assert resolve_learned_blend(portrait, cfg, purpose="hero") == 0.0
    assert resolve_learned_blend(landscape, cfg, purpose="hero") == 0.6
