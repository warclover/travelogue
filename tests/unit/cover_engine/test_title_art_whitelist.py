"""Unit tests · title_art Opening whitelist (PRD §5.4 · D-CAL-10；坐标 D-CAL-20)."""

from __future__ import annotations

import pytest

from travelogue.cover_engine.registry import get_profile
from travelogue.cover_engine.title_art.whitelist import (
    DEFAULT_ENABLED_STYLES,
    FALLBACK_PRESETS,
    is_whitelisted,
    placement_preset,
    placement_presets,
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


def test_folio_overlap_is_whitelisted_by_default() -> None:
    # OQ-CAL-09 收尾（v0.6.6）：手工纸面栏矩形 + assume_paper_bg 落地后转正，
    # 见 whitelist.py 该条目上方的详细注释。
    assert placement_preset("folio-overlap") is not None
    assert "folio-overlap" in DEFAULT_ENABLED_STYLES
    assert is_whitelisted("folio-overlap") is True


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
    assert is_whitelisted("band-cut", enabled_styles=frozenset({"band-cut"})) is True
    assert is_whitelisted("veil-footer", enabled_styles=frozenset({"band-cut"})) is False


def test_placement_preset_unknown_returns_none() -> None:
    assert placement_preset("does-not-exist") is None


@pytest.mark.parametrize(
    ("style_id", "region_index"),
    [
        ("band-cut", 0),
        ("contact-stamp", 0),
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


@pytest.mark.parametrize(
    ("style_id", "expected"),
    [
        ("veil-footer", False),
        ("band-cut", False),
        ("folio-overlap", False),
        ("contact-stamp", True),
    ],
)
def test_assume_dark_veil_flag(style_id: str, expected: bool) -> None:
    # 2026-08-07 真实视觉核对：contact-stamp 全幅深色渐罩与照片亮度无关，
    # 自动配色不能只信原始照片 ROI 采样（见 engine.py 消费该字段）。
    preset = placement_preset(style_id)
    assert preset is not None
    assert preset.assume_dark_veil is expected


def test_contact_stamp_rect_avoids_hook_region() -> None:
    # 左块（title）与右块（hook/日戳号）不应重叠，确认贴纸只占左块。
    preset = placement_preset("contact-stamp")
    assert preset is not None
    hook_region = get_profile("contact-stamp").text_safe_regions[1]
    assert preset.rect["x"] + preset.rect["w"] <= hook_region["x"]


@pytest.mark.parametrize("style_id", ["veil-footer", "band-cut"])
def test_placement_presets_single_candidate_styles_return_only_primary(style_id: str) -> None:
    # D-CAL-20 优先顺位⑤：目前只有 contact-stamp 有已验证安全的备选候选；
    # 其它风格没有备选时，placement_presets 应跟旧的单候选行为完全等价。
    primary = placement_preset(style_id)
    assert primary is not None
    assert placement_presets(style_id) == [primary]


def test_placement_presets_contact_stamp_has_primary_and_fallback() -> None:
    presets = placement_presets("contact-stamp")
    assert len(presets) == 2
    assert presets[0] is placement_preset("contact-stamp")  # 主候选永远在前
    assert presets[1] is FALLBACK_PRESETS["contact-stamp"][0]


def test_placement_presets_unknown_style_returns_empty_list() -> None:
    assert placement_presets("does-not-exist") == []


def test_primary_presets_have_no_conditional_occupant() -> None:
    # 主候选（WHITELIST 里的值）都是已验证坐标，不该带条件占用标记——那是
    # 专属于「备选」的机制。
    for style_id in ("veil-footer", "band-cut", "contact-stamp", "folio-overlap"):
        preset = placement_preset(style_id)
        assert preset is not None
        assert preset.conditional_occupant is None


def test_contact_stamp_fallback_has_conditional_occupant_tag() -> None:
    fallback = FALLBACK_PRESETS["contact-stamp"][0]
    assert fallback.conditional_occupant == "contact_stamp_hook_or_archive"
    assert fallback.assume_dark_veil is True
    # 备选矩形须对应 registry 候选 #1（右下角，跟主候选左下角不重叠）。
    hook_region = get_profile("contact-stamp").text_safe_regions[1]
    assert fallback.rect == {
        "x": float(hook_region["x"]),
        "y": float(hook_region["y"]),
        "w": float(hook_region["w"]),
        "h": float(hook_region["h"]),
    }


@pytest.mark.parametrize(
    ("style_id", "expected"),
    [
        ("veil-footer", False),
        ("band-cut", True),  # W3：D-CAL-23 纸签烧入后须固定纸色配深墨
        ("contact-stamp", False),
        ("folio-overlap", True),
    ],
)
def test_assume_paper_bg_flag(style_id: str, expected: bool) -> None:
    # folio-overlap：左侧纸面栏；band-cut：贴纸内烧入纸签——两者都不能采照片 ROI。
    preset = placement_preset(style_id)
    assert preset is not None
    assert preset.assume_paper_bg is expected


def test_folio_overlap_rect_stays_within_paper_column() -> None:
    # --cover-folio-margin: 13%——纸面栏止于此，主候选须留出安全边距，
    # 不能碰到骑缝渐变/照片区（OQ-CAL-09 的阻断根因）。
    preset = placement_preset("folio-overlap")
    assert preset is not None
    assert preset.rect["x"] >= 0.0
    assert preset.rect["x"] + preset.rect["w"] <= 0.13


def test_folio_overlap_fallback_has_conditional_occupant_and_larger_area() -> None:
    fallback = FALLBACK_PRESETS["folio-overlap"][0]
    primary = placement_preset("folio-overlap")
    assert primary is not None
    assert fallback.conditional_occupant == "folio_place_present"
    assert fallback.assume_paper_bg is True
    assert fallback.rect["x"] + fallback.rect["w"] <= 0.13
    # 备选（无地点标签占用时可用）覆盖的纸面栏纵向范围应比主候选更宽松。
    assert fallback.rect["h"] > primary.rect["h"]


def test_placement_presets_folio_overlap_has_primary_and_fallback() -> None:
    presets = placement_presets("folio-overlap")
    assert len(presets) == 2
    assert presets[0] is placement_preset("folio-overlap")  # 主候选永远在前
    assert presets[1] is FALLBACK_PRESETS["folio-overlap"][0]


def test_whitelist_registry_rects_resolvable_at_import() -> None:
    """契约：WHITELIST / FALLBACK 引用的 registry region 在当前 catalog 下可解析。

    防止 catalog 删减 text_safe_regions 后，``import title_art.whitelist`` 在
    模块顶层构造字典时直接炸（与 fail-open 气质相悖）。
    """
    from travelogue.cover_engine.title_art import whitelist as wl

    # 能 import 且 WHITELIST 非空已是最基本信号；再钉死 band-cut / contact-stamp
    # 与 registry 的索引契约。
    assert "band-cut" in wl.WHITELIST
    assert "contact-stamp" in wl.WHITELIST
    band = get_profile("band-cut").text_safe_regions
    contact = get_profile("contact-stamp").text_safe_regions
    assert len(band) >= 1
    assert len(contact) >= 2
    assert wl.WHITELIST["band-cut"].rect == {
        "x": float(band[0]["x"]),
        "y": float(band[0]["y"]),
        "w": float(band[0]["w"]),
        "h": float(band[0]["h"]),
    }
