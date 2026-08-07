"""Unit tests · title_art Opening whitelist (PRD §5.4 · D-CAL-10；坐标 D-CAL-20)."""

from __future__ import annotations

import pytest

from travelogue.cover_engine.registry import get_profile
from travelogue.cover_engine.title_art.whitelist import (
    DEFAULT_ENABLED_STYLES,
    is_whitelisted,
    placement_preset,
)

pytestmark = pytest.mark.unit


def test_veil_footer_is_whitelisted_by_default() -> None:
    assert is_whitelisted("veil-footer") is True


def test_band_cut_is_whitelisted_by_default() -> None:
    # D-CAL-20 优先顺位①：registry text_safe_regions 与真实断带位置精确吻合。
    assert is_whitelisted("band-cut") is True


def test_contact_stamp_is_whitelisted_by_default() -> None:
    # D-CAL-20 优先顺位②：仅占 registry 左块候选，避让右下角 hook/日戳号。
    assert is_whitelisted("contact-stamp") is True


def test_folio_overlap_registered_but_disabled_by_default() -> None:
    # D-CAL-10 · D-CAL-20 优先顺位③: folio-overlap 已注册 preset，但默认不进
    # DEFAULT_ENABLED_STYLES（W2 狗粮后再开）。
    assert placement_preset("folio-overlap") is not None
    assert "folio-overlap" not in DEFAULT_ENABLED_STYLES
    assert is_whitelisted("folio-overlap") is False


@pytest.mark.parametrize(
    "style_id",
    [
        "type-monument",
        "scroll-head",
        "diptych-seam",
        "cameo-aperture",
        "portal-arch",
        "horizon-split",
        "",
        "unknown-style",
    ],
)
def test_other_styles_are_not_whitelisted(style_id: str) -> None:
    assert is_whitelisted(style_id) is False


def test_explicit_enabled_styles_override_default() -> None:
    assert is_whitelisted("folio-overlap", enabled_styles=frozenset({"folio-overlap"})) is True
    assert is_whitelisted("veil-footer", enabled_styles=frozenset({"folio-overlap"})) is False


def test_placement_preset_unknown_returns_none() -> None:
    assert placement_preset("does-not-exist") is None


@pytest.mark.parametrize(
    ("style_id", "region_index"),
    [
        ("band-cut", 0),
        ("contact-stamp", 0),
        ("folio-overlap", 1),
    ],
)
def test_placement_preset_rect_matches_registry_text_safe_region(
    style_id: str, region_index: int
) -> None:
    # D-CAL-20: 矩形数值须与 Opening Registry 的 text_safe_regions 一致，
    # 不允许 whitelist.py 里再手搓一份可能脱节的数值。
    preset = placement_preset(style_id)
    assert preset is not None
    region = get_profile(style_id).text_safe_regions[region_index]
    assert preset.rect == {
        "x": float(region["x"]),
        "y": float(region["y"]),
        "w": float(region["w"]),
        "h": float(region["h"]),
    }


def test_contact_stamp_rect_avoids_hook_region() -> None:
    # 左块（title）与右块（hook/日戳号）不应重叠，确认贴纸只占左块。
    preset = placement_preset("contact-stamp")
    assert preset is not None
    hook_region = get_profile("contact-stamp").text_safe_regions[1]
    assert preset.rect["x"] + preset.rect["w"] <= hook_region["x"]
