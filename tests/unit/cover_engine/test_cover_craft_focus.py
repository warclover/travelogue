"""Cover Craft Focus (CCF) · hero-only filter + one-click rollback."""

from __future__ import annotations

from dataclasses import replace

import pytest

from travelogue.config.app import AppConfig
from travelogue.config.cover_craft import (
    CoverCraftConfig,
    cover_craft_config_from_dict,
    is_cover_craft_css_enabled,
    is_cover_craft_enabled,
    is_cover_craft_hero_only,
)
from travelogue.cover_engine import assignable_style_ids, is_assignable
from travelogue.cover_engine.craft import HERO_SET, craft_attr_value
from travelogue.cover_engine.fit import style_avoid_penalty, style_fit_score
from travelogue.cover_engine.registry import get_profile


_FIVE = (
    "veil-footer",
    "folio-overlap",
    "band-cut",
    "scroll-head",
    "contact-stamp",
)


@pytest.fixture
def ccf_on(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = replace(AppConfig(), cover_craft=CoverCraftConfig(enabled=True, hero_only=True, craft_css=True))
    monkeypatch.setattr("travelogue.config.get_config", lambda **_: cfg)
    monkeypatch.delenv("TRAVELOGUE_COVER_CRAFT", raising=False)


@pytest.fixture
def ccf_off(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = replace(AppConfig(), cover_craft=CoverCraftConfig(enabled=False))
    monkeypatch.setattr("travelogue.config.get_config", lambda **_: cfg)
    monkeypatch.delenv("TRAVELOGUE_COVER_CRAFT", raising=False)


def test_hero_set_constant() -> None:
    assert HERO_SET == ("veil-footer", "folio-overlap", "band-cut")


def test_assignable_hero_only_when_ccf_on(ccf_on: None) -> None:
    assert assignable_style_ids() == HERO_SET
    assert is_assignable("veil-footer")
    assert is_assignable("band-cut")
    assert not is_assignable("scroll-head")
    assert not is_assignable("contact-stamp")
    assert craft_attr_value() == "ccf-v1"


def test_assignable_five_when_ccf_off(ccf_off: None) -> None:
    assert assignable_style_ids() == _FIVE
    assert is_assignable("scroll-head")
    assert is_assignable("contact-stamp")
    assert craft_attr_value() is None


def test_env_override_disables_ccf(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = replace(AppConfig(), cover_craft=CoverCraftConfig(enabled=True))
    monkeypatch.setattr("travelogue.config.get_config", lambda **_: cfg)
    monkeypatch.setenv("TRAVELOGUE_COVER_CRAFT", "0")
    # Env is read at from_dict time; helpers re-read get_config().enabled which
    # is already True — so re-parse via from_dict with env set.
    parsed = cover_craft_config_from_dict({"enabled": True})
    assert parsed.enabled is False
    assert is_cover_craft_enabled(parsed) is False
    assert is_cover_craft_hero_only(parsed) is False
    assert is_cover_craft_css_enabled(parsed) is False


def test_hero_fit_goldens() -> None:
    """AC-CCF-05 · three prefer/avoid fixtures per hero style."""
    upper = {"focalPoint": {"x": 0.5, "y": 0.35}, "faces": []}
    bottom = {"focalPoint": {"x": 0.5, "y": 0.82}, "faces": [{"x": 0.5, "y": 0.8}]}
    left = {"focalPoint": {"x": 0.12, "y": 0.4}, "faces": []}
    right = {"focalPoint": {"x": 0.78, "y": 0.4}, "faces": []}
    band_hit = {"focalPoint": {"x": 0.4, "y": 0.63}, "faces": [{"x": 0.4, "y": 0.63}]}

    veil = get_profile("veil-footer")
    assert style_fit_score(upper, veil) > style_fit_score(bottom, veil)
    assert style_avoid_penalty(bottom, veil) >= style_avoid_penalty(upper, veil)
    assert style_fit_score(upper, veil) > 0

    band = get_profile("band-cut")
    assert style_fit_score(upper, band) > 0
    assert style_avoid_penalty(band_hit, band) > 0
    assert style_fit_score(upper, band) >= style_fit_score(bottom, band)

    folio = get_profile("folio-overlap")
    assert style_fit_score(right, folio) >= style_fit_score(left, folio)
    assert style_avoid_penalty(left, folio) > style_avoid_penalty(right, folio)
    assert style_fit_score(right, folio) > 0
