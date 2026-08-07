"""Unit tests · title_art Opening whitelist (PRD §5.4 · D-CAL-10)."""

from __future__ import annotations

import pytest

from travelogue.cover_engine.title_art.whitelist import (
    DEFAULT_ENABLED_STYLES,
    is_whitelisted,
    placement_preset,
)

pytestmark = pytest.mark.unit


def test_veil_footer_is_whitelisted_by_default() -> None:
    assert is_whitelisted("veil-footer") is True


def test_folio_overlap_registered_but_disabled_by_default() -> None:
    # D-CAL-10: folio-overlap 已注册 preset，但默认不进 DEFAULT_ENABLED_STYLES
    # （W2 狗粮后再开）。
    assert placement_preset("folio-overlap") is not None
    assert "folio-overlap" not in DEFAULT_ENABLED_STYLES
    assert is_whitelisted("folio-overlap") is False


@pytest.mark.parametrize(
    "style_id",
    ["type-monument", "band-cut", "scroll-head", "diptych-seam", "", "unknown-style"],
)
def test_other_styles_are_not_whitelisted(style_id: str) -> None:
    assert is_whitelisted(style_id) is False


def test_explicit_enabled_styles_override_default() -> None:
    assert is_whitelisted("folio-overlap", enabled_styles=frozenset({"folio-overlap"})) is True
    assert is_whitelisted("veil-footer", enabled_styles=frozenset({"folio-overlap"})) is False


def test_placement_preset_unknown_returns_none() -> None:
    assert placement_preset("does-not-exist") is None
