"""Tests for per-trip purpose pilot profiles."""

from __future__ import annotations

from travelogue.config import AestheticConfig
from travelogue.config.aesthetic_purpose_profiles import (
    apply_purpose_pilot_overlay,
    infer_purpose_profile_kind,
    profile_template,
    purpose_profile_for_trip,
)
from travelogue.config.aesthetic_stratified import landscape_pilot_config


def test_apply_purpose_pilot_overlay_mixed():
    base = landscape_pilot_config(
        __import__("pathlib").Path("docs/acceptance-records/aesthetic-stratum-calibration.merged.v4.json"),
        use_album_relative=True,
    )
    profile = {
        "stratumPreference": "mixed",
        "coverSubjectClarity": 0.35,
        "heroSubjectClarity": 0.3,
        "heroStrata": ["landscape", "person", "group"],
    }
    out = apply_purpose_pilot_overlay(base, profile)
    assert out.stratum_blend_only == ("landscape", "person", "group")
    assert out.stratum_blend_only_by_purpose.get("hero") == ("landscape", "person", "group")
    assert abs(out.presets.cover.subject_clarity - 0.35) < 0.01
    assert abs(out.presets.hero.subject_clarity - 0.3) < 0.01


def test_apply_purpose_pilot_overlay_landscape_cover_comp():
    base = AestheticConfig(use_stratum_blend=True, ml_calibrate=True)
    out = apply_purpose_pilot_overlay(
        base,
        {
            "stratumPreference": "landscape",
            "coverComposition": 0.45,
            "heroColor": 0.3,
        },
    )
    assert out.stratum_blend_only == ("landscape",)
    assert abs(out.presets.cover.composition - 0.45) < 0.01
    assert abs(out.presets.hero.color - 0.3) < 0.01


def test_profile_template_mixed_v4():
    tpl = profile_template("mixed")
    assert tpl is not None
    assert tpl.get("stratumPreference") == "mixed"


def test_purpose_profile_for_trip_kind_map():
    trip = {"tripId": "demo-ecc41072d7", "curation": {}}
    prof = purpose_profile_for_trip(trip)
    assert prof is not None
    assert prof.get("stratumPreference") == "mixed"


def test_infer_purpose_profile_kind_landscape_dominant():
    trip = {
        "curation": {
            "albumProfile": {
                "dominantStratum": "landscape",
                "strata": {"landscape": 0.8, "person": 0.2},
            }
        }
    }
    assert infer_purpose_profile_kind(trip) == "landscape"
